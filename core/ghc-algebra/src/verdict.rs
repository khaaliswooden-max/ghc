//! Compliance verdict lattice — runtime mirror of `Ghc/Lattice.lean`.

use serde::{Deserialize, Serialize};

/// The compliance lattice element: ḥalāl ≺ mashbūh ≺ ḥarām.
///
/// Mirrors `Ghc.Verdict`. The `Ord` derivation matches the linear
/// order proven in `Verdict.le` and the lattice meet/join below.
#[derive(
    Copy, Clone, Debug, Default, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize,
)]
#[serde(rename_all = "lowercase")]
pub enum Verdict {
    /// Permitted.
    #[default]
    Halal,
    /// Doubtful.
    Mashbuh,
    /// Forbidden.
    Haram,
}

impl Verdict {
    /// Lattice meet: more restrictive opinion wins (`max`).
    /// Mirrors `Ghc.Verdict.meet`.
    #[inline]
    pub fn meet(self, other: Self) -> Self {
        std::cmp::max(self, other)
    }

    /// Lattice join: less restrictive opinion wins (`min`).
    /// Mirrors `Ghc.Verdict.join`.
    #[inline]
    pub fn join(self, other: Self) -> Self {
        std::cmp::min(self, other)
    }

    /// Lattice bottom (`halal`).
    #[inline]
    pub const fn bot() -> Self {
        Verdict::Halal
    }

    /// Lattice top (`haram`).
    #[inline]
    pub const fn top() -> Self {
        Verdict::Haram
    }
}

impl std::fmt::Display for Verdict {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(match self {
            Verdict::Halal => "halal",
            Verdict::Mashbuh => "mashbuh",
            Verdict::Haram => "haram",
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// All verdicts in canonical order.
    const ALL: [Verdict; 3] = [Verdict::Halal, Verdict::Mashbuh, Verdict::Haram];

    /// Mirrors `Verdict.meet_comm`.
    #[test]
    fn meet_comm() {
        for &a in &ALL {
            for &b in &ALL {
                assert_eq!(a.meet(b), b.meet(a));
            }
        }
    }

    /// Mirrors `Verdict.meet_assoc`.
    #[test]
    fn meet_assoc() {
        for &a in &ALL {
            for &b in &ALL {
                for &c in &ALL {
                    assert_eq!(a.meet(b).meet(c), a.meet(b.meet(c)));
                }
            }
        }
    }

    /// Mirrors `Verdict.meet_idem`.
    #[test]
    fn meet_idem() {
        for &a in &ALL {
            assert_eq!(a.meet(a), a);
        }
    }

    /// Mirrors `Verdict.join_comm`.
    #[test]
    fn join_comm() {
        for &a in &ALL {
            for &b in &ALL {
                assert_eq!(a.join(b), b.join(a));
            }
        }
    }

    /// Mirrors `Verdict.absorb_meet_join` and `absorb_join_meet`.
    #[test]
    fn absorption() {
        for &a in &ALL {
            for &b in &ALL {
                assert_eq!(a.meet(a.join(b)), a);
                assert_eq!(a.join(a.meet(b)), a);
            }
        }
    }

    /// Mirrors `Verdict.meet_join_distrib`.
    #[test]
    fn meet_join_distrib() {
        for &a in &ALL {
            for &b in &ALL {
                for &c in &ALL {
                    assert_eq!(a.meet(b.join(c)), a.meet(b).join(a.meet(c)));
                    assert_eq!(a.join(b.meet(c)), a.join(b).meet(a.join(c)));
                }
            }
        }
    }

    /// Mirrors `Verdict.halal_bot`.
    #[test]
    fn halal_is_bot() {
        for &a in &ALL {
            assert_eq!(Verdict::Halal.meet(a), a);
            assert_eq!(Verdict::bot().meet(a), a);
        }
    }

    /// Mirrors `Verdict.haram_top`.
    #[test]
    fn haram_is_top() {
        for &a in &ALL {
            assert_eq!(Verdict::Haram.meet(a), Verdict::Haram);
            assert_eq!(Verdict::top().meet(a), Verdict::top());
        }
    }

    #[test]
    fn order_chain() {
        assert!(Verdict::Halal < Verdict::Mashbuh);
        assert!(Verdict::Mashbuh < Verdict::Haram);
    }

    #[test]
    fn json_roundtrip() {
        for &v in &ALL {
            let s = serde_json::to_string(&v).unwrap();
            let back: Verdict = serde_json::from_str(&s).unwrap();
            assert_eq!(v, back);
        }
    }
}
