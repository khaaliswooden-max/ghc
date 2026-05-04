//! `ghc-algebra` — supply-chain category + contamination channels.
//!
//! Mirrors the constructions of `proofs/Ghc/Category.lean` and
//! `proofs/Ghc/Info.lean`, but optimized for runtime use inside the
//! GHC services and the zk-Halal circuit witness generators.

#![forbid(unsafe_code)]

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Compliance verdicts in increasing order of restriction.
#[derive(Copy, Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Verdict {
    Halal,
    Mashbuh,
    Haram,
}

impl Verdict {
    /// Lattice meet (more restrictive wins).
    pub fn meet(self, other: Self) -> Self {
        self.max(other)
    }
    /// Lattice join (less restrictive wins).
    pub fn join(self, other: Self) -> Self {
        self.min(other)
    }
}

/// A binary discrete memoryless channel for the haram-bit.
///
/// `transition[x][y] = Pr[Y = y | X = x]`.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Channel {
    pub transition: [[f64; 2]; 2],
}

impl Channel {
    /// Construct a channel; row sums must be 1 within `tol`.
    pub fn new(transition: [[f64; 2]; 2], tol: f64) -> Result<Self, AlgebraError> {
        for row in &transition {
            for p in row {
                if !(0.0..=1.0).contains(p) {
                    return Err(AlgebraError::OutOfRange);
                }
            }
            if (row[0] + row[1] - 1.0).abs() > tol {
                return Err(AlgebraError::RowNotStochastic);
            }
        }
        Ok(Self { transition })
    }

    /// Sequential composition: `self` followed by `next`.
    pub fn compose(&self, next: &Channel) -> Channel {
        let mut t = [[0.0; 2]; 2];
        for x in 0..2 {
            for y in 0..2 {
                t[x][y] = self.transition[x][0] * next.transition[0][y]
                        + self.transition[x][1] * next.transition[1][y];
            }
        }
        Channel { transition: t }
    }

    /// Capacity `C_h = max_p I(X; Y)`. Computed via Blahut–Arimoto in
    /// Phase C; closed-form for this binary case lives in mathlib.
    pub fn capacity(&self) -> f64 {
        // Phase C: Blahut–Arimoto. For now, return the symmetric-binary
        // upper bound 1 - H(p) with p = self.transition[0][1].
        let p = self.transition[0][1];
        1.0 - h2(p)
    }
}

fn h2(p: f64) -> f64 {
    if p <= 0.0 || p >= 1.0 { 0.0 } else { -p * p.log2() - (1.0 - p) * (1.0 - p).log2() }
}

#[derive(Debug, Error)]
pub enum AlgebraError {
    #[error("transition probability outside [0,1]")]
    OutOfRange,
    #[error("transition row does not sum to 1")]
    RowNotStochastic,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn verdict_lattice_orders_correctly() {
        assert!(Verdict::Halal < Verdict::Mashbuh);
        assert!(Verdict::Mashbuh < Verdict::Haram);
        assert_eq!(Verdict::Halal.meet(Verdict::Haram), Verdict::Haram);
        assert_eq!(Verdict::Halal.join(Verdict::Haram), Verdict::Halal);
    }

    #[test]
    fn identity_channel_has_unit_capacity() {
        let id = Channel::new([[1.0, 0.0], [0.0, 1.0]], 1e-9).unwrap();
        assert!((id.capacity() - 1.0).abs() < 1e-9);
    }

    #[test]
    fn maximally_noisy_channel_has_zero_capacity() {
        let noisy = Channel::new([[0.5, 0.5], [0.5, 0.5]], 1e-9).unwrap();
        assert!(noisy.capacity().abs() < 1e-9);
    }
}
