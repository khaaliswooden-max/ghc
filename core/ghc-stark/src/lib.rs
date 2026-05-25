//! `ghc-stark` — transparent (post-quantum) zk-Halal STARK via winterfell.
//!
//! ## v0.2 status
//!
//! The crate implements a Poseidon-inspired hash-in-trace AIR over the
//! Goldilocks field. The trace carries a 2-element hash state `(h0, h1)`
//! and a verdict column `v`; each row applies one round of a degree-7
//! permutation with 8-periodic public round constants:
//!
//! ```text
//! h0' = h0^7 + 2·h1^7 + v + RC0[i % 8]
//! h1' = h0^7 +   h1^7 + v + RC1[i % 8]
//! ```
//!
//! The initial state is `(salt, 0)` and `h0` at the final row is the
//! public commitment. Because the round constants are non-zero the
//! transition polynomial has actual degree 7 at every row, satisfying
//! winterfell's degree-equality contract.
//!
//! ## What this proves
//!
//! Given a public `(salt, commitment)` pair, knowledge of a verdict
//! sequence whose running hash starting from `salt` yields `commitment`.
//! A prover whose verdicts differ from the committed values cannot
//! produce a matching commitment without breaking the hash.

#![forbid(unsafe_code)]

use thiserror::Error;
use winterfell::{
    crypto::{hashers::Blake3_256, DefaultRandomCoin, MerkleTree},
    math::{fields::f64::BaseElement, FieldElement, ToElements},
    matrix::ColMatrix,
    Air, AirContext, Assertion, BatchingMethod, CompositionPoly, CompositionPolyTrace,
    DefaultConstraintCommitment, DefaultConstraintEvaluator, DefaultTraceLde, EvaluationFrame,
    FieldExtension, PartitionOptions, Proof, ProofOptions, Prover, StarkDomain, Trace, TraceInfo,
    TracePolyTable, TraceTable, TransitionConstraintDegree,
};

// 8-periodic round constants — small distinct primes, never zero.
const RC0: [u64; 8] = [2, 5, 11, 17, 23, 31, 41, 47];
const RC1: [u64; 8] = [3, 7, 13, 19, 29, 37, 43, 53];

/// Public inputs: the salt that seeds the hash and the commitment
/// produced by hashing `(salt, verdicts)` through the trace.
#[derive(Clone, Copy, Debug)]
pub struct HalalPublicInputs {
    pub salt: u64,
    pub commitment: u64,
}

impl ToElements<BaseElement> for HalalPublicInputs {
    fn to_elements(&self) -> Vec<BaseElement> {
        vec![BaseElement::new(self.salt), BaseElement::new(self.commitment)]
    }
}

/// AIR for the GHC halal STARK.
///
/// Three trace columns over the Goldilocks field:
/// * column 0 (`h0`): hash state, component 0.
/// * column 1 (`h1`): hash state, component 1.
/// * column 2 (`v`):  per-step verdict (0 = halal, 1 = haram).
pub struct HalalAir {
    context: AirContext<BaseElement>,
    salt: BaseElement,
    commitment: BaseElement,
}

impl Air for HalalAir {
    type BaseField = BaseElement;
    type PublicInputs = HalalPublicInputs;

    fn new(trace_info: TraceInfo, pub_inputs: HalalPublicInputs, options: ProofOptions) -> Self {
        assert_eq!(trace_info.width(), 3);
        // Both constraints involve cur[0]^7 and cur[1]^7 — degree 7.
        let degrees = vec![
            TransitionConstraintDegree::new(7),
            TransitionConstraintDegree::new(7),
        ];
        // Three boundary assertions: h0[0]=salt, h1[0]=0, h0[last]=commitment.
        HalalAir {
            context: AirContext::new(trace_info, degrees, 3, options),
            salt: BaseElement::new(pub_inputs.salt),
            commitment: BaseElement::new(pub_inputs.commitment),
        }
    }

    fn evaluate_transition<E: FieldElement + From<Self::BaseField>>(
        &self,
        frame: &EvaluationFrame<E>,
        periodic_values: &[E],
        result: &mut [E],
    ) {
        let cur = frame.current();
        let nxt = frame.next();
        let rc0 = periodic_values[0];
        let rc1 = periodic_values[1];
        let two = E::from(BaseElement::new(2));
        let a0 = cur[0].exp(7u64.into());
        let a1 = cur[1].exp(7u64.into());
        let v = cur[2];
        result[0] = nxt[0] - (a0 + two * a1 + v + rc0);
        result[1] = nxt[1] - (a0 + a1 + v + rc1);
    }

    fn get_assertions(&self) -> Vec<Assertion<Self::BaseField>> {
        vec![
            Assertion::single(0, 0, self.salt),
            Assertion::single(1, 0, BaseElement::ZERO),
            Assertion::single(0, self.trace_length() - 1, self.commitment),
        ]
    }

    fn get_periodic_column_values(&self) -> Vec<Vec<Self::BaseField>> {
        vec![
            RC0.iter().map(|&c| BaseElement::new(c)).collect(),
            RC1.iter().map(|&c| BaseElement::new(c)).collect(),
        ]
    }

    fn context(&self) -> &AirContext<Self::BaseField> {
        &self.context
    }
}

/// Minimum trace length winterfell can handle for our AIR at the chosen
/// blowup / query parameters.
pub const MIN_TRACE_LEN: usize = 256;

/// Build an execution trace for the halal STARK.
///
/// Returns `(trace, commitment)` where `commitment` is the final `h0`
/// value.  Verdicts are padded with `0` (halal) to the next power-of-2
/// trace length ≥ `MIN_TRACE_LEN`.
pub fn build_halal_trace(salt: u64, verdicts: &[u64]) -> (TraceTable<BaseElement>, u64) {
    let n = verdicts.len();
    let trace_length = n.max(MIN_TRACE_LEN).next_power_of_two();
    let v_pad: Vec<u64> = (0..trace_length)
        .map(|i| if i < n { verdicts[i] } else { 0 })
        .collect();
    let mut trace = TraceTable::new(3, trace_length);
    trace.fill(
        |state| {
            state[0] = BaseElement::new(salt);
            state[1] = BaseElement::ZERO;
            state[2] = BaseElement::new(v_pad[0]);
        },
        |i, state| {
            let a0 = state[0].exp(7u64);
            let a1 = state[1].exp(7u64);
            let v = state[2];
            let rc0 = BaseElement::new(RC0[i % 8]);
            let rc1 = BaseElement::new(RC1[i % 8]);
            state[0] = a0 + BaseElement::new(2) * a1 + v + rc0;
            state[1] = a0 + a1 + v + rc1;
            state[2] = BaseElement::new(v_pad[i + 1]);
        },
    );
    let commitment = trace.get(0, trace_length - 1).as_int();
    (trace, commitment)
}

/// The Prover.
pub struct HalalProver {
    options: ProofOptions,
}

impl HalalProver {
    pub fn new(options: ProofOptions) -> Self {
        Self { options }
    }
}

impl Prover for HalalProver {
    type BaseField = BaseElement;
    type Air = HalalAir;
    type Trace = TraceTable<Self::BaseField>;
    type HashFn = Blake3_256<Self::BaseField>;
    type VC = MerkleTree<Self::HashFn>;
    type RandomCoin = DefaultRandomCoin<Self::HashFn>;
    type TraceLde<E: FieldElement<BaseField = Self::BaseField>> =
        DefaultTraceLde<E, Self::HashFn, Self::VC>;
    type ConstraintCommitment<E: FieldElement<BaseField = Self::BaseField>> =
        DefaultConstraintCommitment<E, Self::HashFn, Self::VC>;
    type ConstraintEvaluator<'a, E: FieldElement<BaseField = Self::BaseField>> =
        DefaultConstraintEvaluator<'a, Self::Air, E>;

    fn get_pub_inputs(&self, trace: &Self::Trace) -> HalalPublicInputs {
        let salt = trace.get(0, 0).as_int();
        let commitment = trace.get(0, trace.length() - 1).as_int();
        HalalPublicInputs { salt, commitment }
    }

    fn options(&self) -> &ProofOptions {
        &self.options
    }

    fn new_trace_lde<E: FieldElement<BaseField = Self::BaseField>>(
        &self,
        trace_info: &TraceInfo,
        main_trace: &ColMatrix<Self::BaseField>,
        domain: &StarkDomain<Self::BaseField>,
        partition_option: PartitionOptions,
    ) -> (Self::TraceLde<E>, TracePolyTable<E>) {
        DefaultTraceLde::new(trace_info, main_trace, domain, partition_option)
    }

    fn build_constraint_commitment<E: FieldElement<BaseField = Self::BaseField>>(
        &self,
        composition_poly_trace: CompositionPolyTrace<E>,
        num_constraint_composition_columns: usize,
        domain: &StarkDomain<Self::BaseField>,
        partition_options: PartitionOptions,
    ) -> (Self::ConstraintCommitment<E>, CompositionPoly<E>) {
        DefaultConstraintCommitment::new(
            composition_poly_trace,
            num_constraint_composition_columns,
            domain,
            partition_options,
        )
    }

    fn new_evaluator<'a, E: FieldElement<BaseField = Self::BaseField>>(
        &self,
        air: &'a Self::Air,
        aux_rand_elements: Option<winterfell::AuxRandElements<E>>,
        composition_coefficients: winterfell::ConstraintCompositionCoefficients<E>,
    ) -> Self::ConstraintEvaluator<'a, E> {
        DefaultConstraintEvaluator::new(air, aux_rand_elements, composition_coefficients)
    }
}

/// Default proof options (~96-bit conjectured security).
pub fn default_options() -> ProofOptions {
    ProofOptions::new(
        32,
        8,
        0,
        FieldExtension::Quadratic,
        8,
        31,
        BatchingMethod::Linear,
        BatchingMethod::Linear,
    )
}

/// Prove an all-halal trace of length `n` bound to `salt`.
///
/// Returns the public inputs (including the hash commitment) and the proof.
pub fn prove(salt: u64, n: usize) -> Result<(HalalPublicInputs, Proof), StarkError> {
    let verdicts = vec![0u64; n];
    let (trace, commitment) = build_halal_trace(salt, &verdicts);
    let prover = HalalProver::new(default_options());
    let pub_inputs = HalalPublicInputs { salt, commitment };
    let proof = prover
        .prove(trace)
        .map_err(|e| StarkError::Proving(format!("{e:?}")))?;
    Ok((pub_inputs, proof))
}

/// Verify a STARK proof against the given public inputs.
pub fn verify(pub_inputs: HalalPublicInputs, proof: Proof) -> Result<(), StarkError> {
    let min_opts = winterfell::AcceptableOptions::MinConjecturedSecurity(95);
    winterfell::verify::<
        HalalAir,
        Blake3_256<BaseElement>,
        DefaultRandomCoin<Blake3_256<BaseElement>>,
        MerkleTree<Blake3_256<BaseElement>>,
    >(proof, pub_inputs, &min_opts)
    .map_err(|e| StarkError::Verification(format!("{e:?}")))
}

#[derive(Debug, Error)]
pub enum StarkError {
    #[error("proving failed: {0}")]
    Proving(String),
    #[error("verification failed: {0}")]
    Verification(String),
}

#[cfg(test)]
mod tests {
    use super::*;
    use winterfell::Trace;

    #[test]
    fn halal_stark_proves_and_verifies() {
        let salt = 0xc0ffee_u64;
        let (pub_inputs, proof) = prove(salt, 8).expect("prove");
        verify(pub_inputs, proof).expect("verify");
    }

    #[test]
    fn halal_stark_with_different_salt_proves_and_verifies() {
        for salt in [1u64, 42, 0xdeadbeef] {
            let (pub_inputs, proof) = prove(salt, 16).expect("prove");
            verify(pub_inputs, proof).expect("verify");
        }
    }

    #[test]
    fn halal_stark_wrong_salt_fails_verification() {
        let salt = 7u64;
        let (_, proof) = prove(salt, 8).expect("prove");
        // Public inputs for a different salt are self-consistent but do not
        // match the proof transcript generated with salt = 7.
        let (bogus, _) = prove(salt + 1, 8).expect("prove with different salt");
        assert!(verify(bogus, proof).is_err());
    }

    // The commitment encodes every verdict: a single non-halal entry
    // produces a distinct commitment, so a verifier holding the halal
    // commitment cannot be fooled by a haram trace.
    #[test]
    fn haram_verdict_changes_commitment() {
        let salt = 0xc0ffee_u64;
        let n = 8;
        let (halal_pub, _) = prove(salt, n).expect("prove halal");
        let mut haram_verdicts = vec![0u64; n];
        haram_verdicts[3] = 1;
        let (_, haram_commitment) = build_halal_trace(salt, &haram_verdicts);
        assert_ne!(halal_pub.commitment, haram_commitment);
    }

    #[test]
    fn pads_to_power_of_two() {
        let (trace, _commitment) = build_halal_trace(123, &[0u64; 5]);
        assert_eq!(trace.length(), MIN_TRACE_LEN);
        assert_eq!(trace.get(0, 0), BaseElement::new(123));
        assert_eq!(trace.get(1, 0), BaseElement::ZERO);
        for i in 0..MIN_TRACE_LEN {
            assert_eq!(trace.get(2, i), BaseElement::ZERO);
        }
    }
}
