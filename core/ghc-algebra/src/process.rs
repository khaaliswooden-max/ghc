//! Halal-Closure Functor and Najis Density (discrete) — runtime
//! mirror of `Ghc/Category.lean` and `Ghc/Quantum.lean`.

use serde::{Deserialize, Serialize};

use crate::verdict::Verdict;

/// A supply-chain process: an ordered sequence of per-step verdicts.
/// Mirrors `Ghc.Process`.
pub type Process = Vec<Verdict>;

/// Halal-Closure Functor — iterated meet of per-step verdicts.
/// Empty process is `Halal`. Mirrors `Process.halalClosure`.
pub fn halal_closure(p: &[Verdict]) -> Verdict {
    p.iter().copied().fold(Verdict::bot(), Verdict::meet)
}

/// A single source contribution to a batch: source id, mass weight,
/// and the source's verdict. Mirrors `Ghc.Quantum.Contribution`.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Contribution {
    pub source: u64,
    pub weight: u64,
    pub verdict: Verdict,
}

impl Contribution {
    pub fn new(source: u64, weight: u64, verdict: Verdict) -> Self {
        Self {
            source,
            weight,
            verdict,
        }
    }
}

/// A batch is a collection of source contributions. Mirrors
/// `Ghc.Quantum.Batch`.
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Batch {
    pub contributions: Vec<Contribution>,
}

impl Batch {
    pub fn new(contributions: Vec<Contribution>) -> Self {
        Self { contributions }
    }

    /// Aggregate verdict of the batch (meet of per-source verdicts).
    /// Mirrors `Ghc.Quantum.Batch.verdict`.
    pub fn verdict(&self) -> Verdict {
        self.contributions
            .iter()
            .fold(Verdict::bot(), |acc, c| acc.meet(c.verdict))
    }

    /// Mix two batches via concatenation. Mirrors `Ghc.Quantum.Batch.mix`.
    pub fn mix(mut self, other: Batch) -> Batch {
        self.contributions.extend(other.contributions);
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    fn arb_verdict() -> impl Strategy<Value = Verdict> {
        prop_oneof![
            Just(Verdict::Halal),
            Just(Verdict::Mashbuh),
            Just(Verdict::Haram),
        ]
    }

    /// Mirrors `Process.halalClosure_nil`.
    #[test]
    fn closure_nil() {
        assert_eq!(halal_closure(&[]), Verdict::Halal);
    }

    /// Mirrors `Process.halalClosure_all_halal`.
    #[test]
    fn closure_all_halal() {
        let p: Process = vec![Verdict::Halal; 5];
        assert_eq!(halal_closure(&p), Verdict::Halal);
    }

    /// Mirrors `Process.halalClosure_haram_absorb`.
    #[test]
    fn closure_haram_absorb() {
        let p: Process = vec![Verdict::Halal, Verdict::Haram, Verdict::Halal];
        assert_eq!(halal_closure(&p), Verdict::Haram);
    }

    proptest! {
        /// Mirrors `Process.halalClosure_append`.
        #[test]
        fn closure_append(
            xs in prop::collection::vec(arb_verdict(), 0..16),
            ys in prop::collection::vec(arb_verdict(), 0..16)
        ) {
            let mut zs = xs.clone();
            zs.extend(ys.clone());
            prop_assert_eq!(
                halal_closure(&zs),
                halal_closure(&xs).meet(halal_closure(&ys))
            );
        }

        /// Halal closure is monotone: appending any step can only
        /// raise (more restrictive) the verdict.
        #[test]
        fn closure_monotone(
            xs in prop::collection::vec(arb_verdict(), 0..16),
            v in arb_verdict()
        ) {
            let mut ys = xs.clone();
            ys.push(v);
            prop_assert!(halal_closure(&ys) >= halal_closure(&xs));
        }

        /// Mirrors `Quantum.Batch.verdict_mix`.
        #[test]
        fn batch_mix(
            cs1 in prop::collection::vec(
                (0u64..1000, 1u64..1000, arb_verdict()), 0..16),
            cs2 in prop::collection::vec(
                (0u64..1000, 1u64..1000, arb_verdict()), 0..16)
        ) {
            let b1 = Batch::new(cs1.iter().map(|&(s, w, v)| Contribution::new(s, w, v)).collect());
            let b2 = Batch::new(cs2.iter().map(|&(s, w, v)| Contribution::new(s, w, v)).collect());
            let mixed = b1.clone().mix(b2.clone());
            prop_assert_eq!(mixed.verdict(), b1.verdict().meet(b2.verdict()));
        }
    }

    /// Mirrors `Quantum.Batch.verdict_haram_member`.
    #[test]
    fn batch_haram_taints() {
        let b = Batch::new(vec![
            Contribution::new(1, 100, Verdict::Halal),
            Contribution::new(2, 50, Verdict::Haram),
            Contribution::new(3, 25, Verdict::Halal),
        ]);
        assert_eq!(b.verdict(), Verdict::Haram);
    }
}
