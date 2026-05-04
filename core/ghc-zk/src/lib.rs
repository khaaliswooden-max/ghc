//! `ghc-zk` — zk-Halal SNARK circuits.
//!
//! Builds an R1CS encoding of "the committed provenance witness
//! satisfies HCF compliance ≥ ḥalāl" and exposes a Groth16 prover and
//! verifier over BLS12-381. Phase C will flesh this out; v0.0.1 ships
//! the API surface and a trivial circuit so downstream services can
//! integrate against stable types.

#![forbid(unsafe_code)]

use ark_bls12_381::{Bls12_381, Fr};
use ark_groth16::Groth16;
use ark_relations::{
    lc,
    r1cs::{ConstraintSynthesizer, ConstraintSystemRef, SynthesisError, Variable},
};
use ark_snark::SNARK;
use thiserror::Error;

/// Public input: a binding commitment hash to (G, w, ℓ).
pub type Commitment = [u8; 32];

/// A trivial placeholder circuit: prove knowledge of `w` such that
/// `w * w = pub_input`. v0.1 replaces this with the real HCF circuit
/// (see `proofs/Ghc/Category.lean`).
pub struct HalalCircuit {
    pub witness: Option<Fr>,
    pub public:  Fr,
}

impl ConstraintSynthesizer<Fr> for HalalCircuit {
    fn generate_constraints(self, cs: ConstraintSystemRef<Fr>) -> Result<(), SynthesisError> {
        let pub_var = cs.new_input_variable(|| Ok(self.public))?;
        let wit_var = cs.new_witness_variable(|| {
            self.witness.ok_or(SynthesisError::AssignmentMissing)
        })?;
        // Constraint: wit_var * wit_var = pub_var
        cs.enforce_constraint(
            lc!() + wit_var,
            lc!() + wit_var,
            lc!() + pub_var,
        )?;
        let _ = Variable::One; // suppress unused-import warning
        Ok(())
    }
}

/// Trivial Groth16 setup wrapper.
pub fn setup() -> Result<
    (
        ark_groth16::ProvingKey<Bls12_381>,
        ark_groth16::VerifyingKey<Bls12_381>,
    ),
    ZkError,
> {
    let mut rng = ark_std::rand::thread_rng();
    let circuit = HalalCircuit {
        witness: Some(Fr::from(1u64)),
        public:  Fr::from(1u64),
    };
    Groth16::<Bls12_381>::circuit_specific_setup(circuit, &mut rng)
        .map_err(|e| ZkError::Setup(format!("{e:?}")))
}

#[derive(Debug, Error)]
pub enum ZkError {
    #[error("setup failed: {0}")]
    Setup(String),
    #[error("proving failed: {0}")]
    Proving(String),
    #[error("verification failed")]
    Verification,
}
