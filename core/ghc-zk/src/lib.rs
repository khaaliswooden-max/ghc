//! `ghc-zk` — zk-Halal SNARK circuits and verifier.
//!
//! Production zk-Halal Groth16 circuits over BLS12-381 (arkworks).
//! The circuit family proves, in zero knowledge, that a committed
//! witness of per-step verdicts encodes a process whose Halal-Closure
//! Functor verdict satisfies the requested upper bound on the
//! compliance lattice — without revealing the verdicts themselves.
//!
//! v0.0.x ships the [`HalalThresholdCircuit`] family with a
//! **Poseidon-on-BLS12-381** binding commitment (width 3, rate 2,
//! `alpha = 17`, 8 full rounds, 29 partial rounds). The native and
//! in-circuit hashers are kept in lock-step via the shared
//! [`poseidon_params::default_config`] so the off-circuit commitment
//! always matches the constraint-system commitment.
//!
//! The R1CS constraints encoded:
//!
//! 1. **Domain check.** Each witness slot `w_i` satisfies
//!    `w_i (w_i − 1)(w_i − 2) = 0`, forcing
//!    `w_i ∈ {0, 1, 2}` ↔ `{halal, mashbuh, haram}`.
//! 2. **Threshold check.** For each `w_i`, depending on the requested
//!    threshold `t ∈ {halal, mashbuh}`:
//!    * `t = halal`: `w_i = 0`.
//!    * `t = mashbuh`: `w_i (w_i − 1) = 0` (i.e. `w_i ∈ {0, 1}`).
//! 3. **Commitment.** A public input `c` equals
//!    `Poseidon(salt ‖ w_0 ‖ ... ‖ w_{n-1})`, where `salt` is a
//!    private witness; the in-circuit Poseidon sponge is
//!    `ark-crypto-primitives` `PoseidonSpongeVar`.

#![forbid(unsafe_code)]

mod poseidon_params;

use ark_bls12_381::{Bls12_381, Fr};
use ark_crypto_primitives::sponge::constraints::CryptographicSpongeVar;
use ark_crypto_primitives::sponge::poseidon::constraints::PoseidonSpongeVar;
use ark_crypto_primitives::sponge::poseidon::{PoseidonConfig, PoseidonSponge};
use ark_crypto_primitives::sponge::{CryptographicSponge, FieldBasedCryptographicSponge};
use ark_ff::Field;
use ark_groth16::{Groth16, PreparedVerifyingKey, Proof, ProvingKey, VerifyingKey};
use ark_r1cs_std::alloc::AllocVar;
use ark_r1cs_std::eq::EqGadget;
use ark_r1cs_std::fields::fp::FpVar;
use ark_relations::r1cs::{ConstraintSynthesizer, ConstraintSystemRef, SynthesisError};
use ark_snark::SNARK;
use ghc_algebra::Verdict;
use thiserror::Error;

pub use poseidon_params::default_config as poseidon_config;

/// The zk-Halal commitment — a single field element (Poseidon output).
pub type Commitment = Fr;

/// Allowed compliance threshold for the circuit. Any compliant
/// witness has every per-step verdict `≤ threshold`.
#[derive(Copy, Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Threshold {
    /// Only halal verdicts are admitted.
    Halal,
    /// Halal or mashbuh verdicts are admitted; haram is rejected.
    Mashbuh,
}

impl Threshold {
    /// Returns `true` if a verdict satisfies the threshold.
    fn admits(self, v: Verdict) -> bool {
        match (self, v) {
            (Threshold::Halal, Verdict::Halal) => true,
            (Threshold::Halal, _) => false,
            (Threshold::Mashbuh, Verdict::Halal) => true,
            (Threshold::Mashbuh, Verdict::Mashbuh) => true,
            (Threshold::Mashbuh, Verdict::Haram) => false,
        }
    }
}

/// Convert a verdict into its field-element encoding.
pub fn verdict_to_field(v: Verdict) -> Fr {
    match v {
        Verdict::Halal => Fr::ZERO,
        Verdict::Mashbuh => Fr::ONE,
        Verdict::Haram => Fr::from(2u64),
    }
}

/// Compute the Poseidon commitment of a witness with a salt.
pub fn commit(witness: &[Verdict], salt: Fr) -> Commitment {
    commit_field(
        &witness
            .iter()
            .copied()
            .map(verdict_to_field)
            .collect::<Vec<_>>(),
        salt,
    )
}

/// Native Poseidon commit on field elements.
fn commit_field(witness: &[Fr], salt: Fr) -> Fr {
    let cfg: PoseidonConfig<Fr> = poseidon_config();
    let mut sponge = PoseidonSponge::<Fr>::new(&cfg);
    sponge.absorb(&salt);
    for w in witness {
        sponge.absorb(w);
    }
    sponge.squeeze_native_field_elements(1)[0]
}

/// The zk-Halal circuit.
#[derive(Clone, Debug)]
pub struct HalalThresholdCircuit {
    /// Number of process steps the circuit accommodates.
    pub n: usize,
    /// Threshold to prove the witness verdict satisfies.
    pub threshold: Threshold,
    /// Private witness: per-step verdicts (encoded as field
    /// elements). `None` for verifier-side circuit construction.
    pub witness: Option<Vec<Fr>>,
    /// Private salt: prevents brute-force enumeration of small
    /// witnesses.
    pub salt: Option<Fr>,
    /// Public input: the binding Poseidon commitment.
    pub commitment: Fr,
}

impl HalalThresholdCircuit {
    /// Construct the prover-side circuit instance.
    pub fn new_prover(
        threshold: Threshold,
        witness: Vec<Verdict>,
        salt: Fr,
    ) -> Result<Self, ZkError> {
        for &v in &witness {
            if !threshold.admits(v) {
                return Err(ZkError::WitnessExceedsThreshold);
            }
        }
        let commitment = commit(&witness, salt);
        Ok(Self {
            n: witness.len(),
            threshold,
            witness: Some(witness.into_iter().map(verdict_to_field).collect()),
            salt: Some(salt),
            commitment,
        })
    }

    /// Construct the verifier-side / setup circuit instance with no
    /// witness (commits to the layout only).
    pub fn new_verifier(threshold: Threshold, n: usize, commitment: Fr) -> Self {
        Self {
            n,
            threshold,
            witness: None,
            salt: None,
            commitment,
        }
    }
}

impl ConstraintSynthesizer<Fr> for HalalThresholdCircuit {
    fn generate_constraints(self, cs: ConstraintSystemRef<Fr>) -> Result<(), SynthesisError> {
        // Public input: commitment.
        let c_var = FpVar::<Fr>::new_input(cs.clone(), || Ok(self.commitment))?;

        // Witness allocation.
        let w_vars: Vec<FpVar<Fr>> = (0..self.n)
            .map(|i| {
                FpVar::<Fr>::new_witness(cs.clone(), || {
                    self.witness
                        .as_ref()
                        .and_then(|w| w.get(i).copied())
                        .ok_or(SynthesisError::AssignmentMissing)
                })
            })
            .collect::<Result<_, _>>()?;

        let salt_var = FpVar::<Fr>::new_witness(cs.clone(), || {
            self.salt.ok_or(SynthesisError::AssignmentMissing)
        })?;

        // Constraint set 1: domain check.
        // Each w_i ∈ {0, 1, 2}: w_i (w_i - 1)(w_i - 2) = 0.
        let one = FpVar::<Fr>::Constant(Fr::ONE);
        let two = FpVar::<Fr>::Constant(Fr::from(2u64));
        for w in &w_vars {
            let lhs = w * (w - &one) * (w - &two);
            lhs.enforce_equal(&FpVar::<Fr>::Constant(Fr::ZERO))?;
        }

        // Constraint set 2: threshold.
        match self.threshold {
            Threshold::Halal => {
                // Each w_i = 0.
                for w in &w_vars {
                    w.enforce_equal(&FpVar::<Fr>::Constant(Fr::ZERO))?;
                }
            }
            Threshold::Mashbuh => {
                // Each w_i ∈ {0, 1}: w_i (w_i - 1) = 0.
                for w in &w_vars {
                    let lhs = w * (w - &one);
                    lhs.enforce_equal(&FpVar::<Fr>::Constant(Fr::ZERO))?;
                }
            }
        }

        // Constraint set 3: Poseidon commitment.
        let cfg: PoseidonConfig<Fr> = poseidon_config();
        let mut sponge = PoseidonSpongeVar::<Fr>::new(cs, &cfg);
        sponge.absorb(&salt_var)?;
        for w in &w_vars {
            sponge.absorb(w)?;
        }
        let squeezed = sponge.squeeze_field_elements(1)?;
        squeezed[0].enforce_equal(&c_var)?;

        Ok(())
    }
}

/// Setup, proving, and verification keys for a fixed `(threshold, n)`.
pub struct Keys {
    pub pk: ProvingKey<Bls12_381>,
    pub vk: VerifyingKey<Bls12_381>,
    pub pvk: PreparedVerifyingKey<Bls12_381>,
}

/// Generate Groth16 keys for the given circuit shape.
pub fn setup(threshold: Threshold, n: usize) -> Result<Keys, ZkError> {
    let mut rng = ark_std::rand::thread_rng();
    // Use a dummy witness (all halal) for setup; circuit shape only.
    let dummy = vec![Verdict::Halal; n];
    let circuit = HalalThresholdCircuit::new_prover(threshold, dummy, Fr::ONE)?;
    let (pk, vk) = Groth16::<Bls12_381>::circuit_specific_setup(circuit, &mut rng)
        .map_err(|e| ZkError::Setup(format!("{e:?}")))?;
    let pvk =
        Groth16::<Bls12_381>::process_vk(&vk).map_err(|e| ZkError::Setup(format!("{e:?}")))?;
    Ok(Keys { pk, vk, pvk })
}

/// Produce a proof for a given witness.
pub fn prove(
    keys: &Keys,
    threshold: Threshold,
    witness: Vec<Verdict>,
    salt: Fr,
) -> Result<(Commitment, Proof<Bls12_381>), ZkError> {
    let circuit = HalalThresholdCircuit::new_prover(threshold, witness, salt)?;
    let commitment = circuit.commitment;
    let mut rng = ark_std::rand::thread_rng();
    let proof = Groth16::<Bls12_381>::prove(&keys.pk, circuit, &mut rng)
        .map_err(|e| ZkError::Proving(format!("{e:?}")))?;
    Ok((commitment, proof))
}

/// Verify a proof against a public commitment.
pub fn verify(
    keys: &Keys,
    commitment: Commitment,
    proof: &Proof<Bls12_381>,
) -> Result<bool, ZkError> {
    Groth16::<Bls12_381>::verify_with_processed_vk(&keys.pvk, &[commitment], proof)
        .map_err(|e| ZkError::Verification(format!("{e:?}")))
}

#[derive(Debug, Error)]
pub enum ZkError {
    #[error("setup failed: {0}")]
    Setup(String),
    #[error("proving failed: {0}")]
    Proving(String),
    #[error("verification failed: {0}")]
    Verification(String),
    #[error("witness contains a verdict above the requested threshold")]
    WitnessExceedsThreshold,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn halal_only_witness_proves_and_verifies() {
        let n = 4;
        let keys = setup(Threshold::Halal, n).expect("setup");
        let witness = vec![Verdict::Halal; n];
        let salt = Fr::from(42u64);
        let (c, proof) = prove(&keys, Threshold::Halal, witness.clone(), salt).expect("prove");
        assert_eq!(c, commit(&witness, salt));
        assert!(verify(&keys, c, &proof).expect("verify"));
    }

    #[test]
    fn haram_witness_rejected_at_prover_input() {
        let mut witness = vec![Verdict::Halal; 4];
        witness[2] = Verdict::Haram;
        let salt = Fr::from(7u64);
        let err = HalalThresholdCircuit::new_prover(Threshold::Halal, witness, salt)
            .expect_err("haram should be rejected");
        matches!(err, ZkError::WitnessExceedsThreshold);
    }

    #[test]
    fn wrong_commitment_fails_verification() {
        let n = 3;
        let keys = setup(Threshold::Halal, n).expect("setup");
        let witness = vec![Verdict::Halal; n];
        let salt = Fr::from(99u64);
        let (c, proof) = prove(&keys, Threshold::Halal, witness, salt).expect("prove");
        let bad = c + Fr::ONE;
        assert!(!verify(&keys, bad, &proof).expect("verify"));
    }

    #[test]
    fn mashbuh_threshold_admits_mashbuh() {
        let n = 4;
        let keys = setup(Threshold::Mashbuh, n).expect("setup");
        let witness = vec![
            Verdict::Halal,
            Verdict::Mashbuh,
            Verdict::Halal,
            Verdict::Mashbuh,
        ];
        let salt = Fr::from(1234u64);
        let (c, proof) = prove(&keys, Threshold::Mashbuh, witness, salt).expect("prove");
        assert!(verify(&keys, c, &proof).expect("verify"));
    }

    #[test]
    fn mashbuh_threshold_rejects_haram() {
        let mut witness = vec![Verdict::Mashbuh; 3];
        witness[1] = Verdict::Haram;
        let salt = Fr::from(5u64);
        let err = HalalThresholdCircuit::new_prover(Threshold::Mashbuh, witness, salt)
            .expect_err("haram should be rejected at mashbuh threshold");
        matches!(err, ZkError::WitnessExceedsThreshold);
    }

    #[test]
    fn commit_separates_distinct_witnesses() {
        let salt = Fr::from(0u64);
        let w1 = vec![Verdict::Halal, Verdict::Mashbuh, Verdict::Halal];
        let w2 = vec![Verdict::Mashbuh, Verdict::Halal, Verdict::Halal];
        assert_ne!(commit(&w1, salt), commit(&w2, salt));
    }

    #[test]
    fn commit_separates_distinct_salts() {
        let w = vec![Verdict::Halal; 3];
        assert_ne!(commit(&w, Fr::from(1u64)), commit(&w, Fr::from(2u64)));
    }

    /// Native Poseidon and in-circuit Poseidon must agree:
    /// any honest witness that the native commit() produces a value
    /// for must be acceptable as the public input to a circuit
    /// instance built from the same witness+salt.
    #[test]
    fn native_and_circuit_poseidon_agree() {
        let n = 3;
        let keys = setup(Threshold::Halal, n).expect("setup");
        let witness = vec![Verdict::Halal; n];
        let salt = Fr::from(0xc0ffee_u64);
        let native = commit(&witness, salt);
        let (c, proof) = prove(&keys, Threshold::Halal, witness, salt).expect("prove");
        assert_eq!(native, c);
        assert!(verify(&keys, c, &proof).expect("verify"));
    }
}
