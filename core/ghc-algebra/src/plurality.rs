//! Audit plurality vote — runtime mirror of `Ghc/Convergence.lean`.

use crate::verdict::Verdict;

/// Number of audits returning the target verdict.
/// Mirrors `Ghc.Convergence.count`.
pub fn count(audits: &[Verdict], v: Verdict) -> usize {
    audits.iter().filter(|&&a| a == v).count()
}

/// Plurality verdict with `Haram` as conservative tiebreaker.
/// Mirrors `Ghc.Convergence.plurality`.
pub fn plurality(audits: &[Verdict]) -> Verdict {
    let h = count(audits, Verdict::Halal);
    let m = count(audits, Verdict::Mashbuh);
    let r = count(audits, Verdict::Haram);
    if h > m && h > r {
        Verdict::Halal
    } else if m > r && m >= h {
        Verdict::Mashbuh
    } else {
        Verdict::Haram
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

    /// Mirrors `Convergence.count_le_length`.
    #[test]
    fn count_le_length() {
        let audits = vec![Verdict::Halal, Verdict::Halal, Verdict::Mashbuh];
        for v in [Verdict::Halal, Verdict::Mashbuh, Verdict::Haram] {
            assert!(count(&audits, v) <= audits.len());
        }
    }

    /// Mirrors `Convergence.count_unanimous`.
    #[test]
    fn count_unanimous() {
        for v in [Verdict::Halal, Verdict::Mashbuh, Verdict::Haram] {
            let audits = vec![v; 7];
            assert_eq!(count(&audits, v), 7);
        }
    }

    /// Mirrors `Convergence.count_unanimous_other`.
    #[test]
    fn count_unanimous_other() {
        let audits = vec![Verdict::Halal; 5];
        assert_eq!(count(&audits, Verdict::Mashbuh), 0);
        assert_eq!(count(&audits, Verdict::Haram), 0);
    }

    /// Mirrors `Convergence.plurality_unanimous`.
    #[test]
    fn plurality_unanimous() {
        for v in [Verdict::Halal, Verdict::Mashbuh, Verdict::Haram] {
            let audits = vec![v; 5];
            assert_eq!(plurality(&audits), v);
        }
    }

    proptest! {
        #[test]
        fn count_bounds(
            audits in prop::collection::vec(arb_verdict(), 0..32),
            v in arb_verdict()
        ) {
            prop_assert!(count(&audits, v) <= audits.len());
        }

        #[test]
        fn plurality_unanimous_proptest(
            v in arb_verdict(),
            n in 1usize..32
        ) {
            let audits = vec![v; n];
            prop_assert_eq!(plurality(&audits), v);
        }
    }
}
