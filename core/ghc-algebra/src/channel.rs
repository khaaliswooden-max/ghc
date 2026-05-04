//! Contamination channels — runtime mirror of `Ghc/Info.lean` and the
//! Phase B+ `GhcMathlib/Channel.lean`.
//!
//! Two flavours:
//! * [`DetChannel`] — deterministic Bool→Bool channel matching the
//!   pure-Lean kernel.
//! * [`Channel`] — binary stochastic channel matching the mathlib
//!   extension; carries the `survival` invariants used by the
//!   exponential-decay theorem.

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// A deterministic channel: a function on the haram-bit.
/// Mirrors `Ghc.Info.DetChannel`.
#[derive(Copy, Clone, Debug, Serialize, Deserialize)]
pub struct DetChannel {
    /// Output of the channel on `false` input.
    pub on_false: bool,
    /// Output of the channel on `true` input.
    pub on_true: bool,
}

impl DetChannel {
    pub const IDENTITY: Self = Self {
        on_false: false,
        on_true: true,
    };

    pub const KILL: Self = Self {
        on_false: false,
        on_true: false,
    };

    /// Apply the channel.
    #[inline]
    pub fn apply(self, x: bool) -> bool {
        if x {
            self.on_true
        } else {
            self.on_false
        }
    }

    /// Mirrors `Ghc.Info.Kills`.
    pub fn kills(self) -> bool {
        !self.on_true && !self.on_false
    }

    /// Mirrors `Ghc.Info.NoInvent`: `W false = false`.
    pub fn no_invent(self) -> bool {
        !self.on_false
    }
}

/// Iterated composition of deterministic channels.
/// Mirrors `Ghc.Info.chain`.
pub fn chain(ws: &[DetChannel], x: bool) -> bool {
    ws.iter().fold(x, |acc, w| w.apply(acc))
}

/// A binary stochastic channel for the haram-bit.
/// `p01 = Pr[Y=1 | X=0]`, `p11 = Pr[Y=1 | X=1]`. Mirrors
/// `GhcMathlib.Channel.Binary`.
#[derive(Copy, Clone, Debug, Serialize, Deserialize)]
pub struct Channel {
    pub p01: f64,
    pub p11: f64,
}

impl Channel {
    /// Construct, validating that probabilities lie in `[0, 1]`.
    pub fn new(p01: f64, p11: f64) -> Result<Self, ChannelError> {
        for &p in &[p01, p11] {
            if !(0.0..=1.0).contains(&p) || p.is_nan() {
                return Err(ChannelError::OutOfRange);
            }
        }
        Ok(Self { p01, p11 })
    }

    /// Survival probability: `Pr[Y=1 | X=1]`. Mirrors
    /// `GhcMathlib.Channel.Binary.survival`.
    #[inline]
    pub fn survival(self) -> f64 {
        self.p11
    }

    /// Mirrors `GhcMathlib.Channel.Binary.NoInvent`.
    #[inline]
    pub fn no_invent(self) -> bool {
        self.p01 == 0.0
    }
}

/// Survival of a chain of stochastic channels: product of per-step
/// survivals. Mirrors `GhcMathlib.Channel.Chain.survival`.
pub fn chain_survival(ws: &[Channel]) -> f64 {
    ws.iter().fold(1.0, |acc, w| acc * w.survival())
}

#[derive(Debug, Error)]
pub enum ChannelError {
    #[error("transition probability outside [0, 1] or NaN")]
    OutOfRange,
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    /// Mirrors `Ghc.Info.chain_false_of_noinvent`.
    #[test]
    fn chain_false_of_noinvent() {
        let ws = vec![DetChannel::IDENTITY, DetChannel::IDENTITY];
        assert!(ws.iter().all(|w| w.no_invent()));
        assert!(!chain(&ws, false));
    }

    /// Mirrors `Ghc.Info.chain_kills_under_no_invent`.
    #[test]
    fn chain_kills_under_no_invent() {
        let ws = vec![DetChannel::IDENTITY, DetChannel::KILL, DetChannel::IDENTITY];
        assert!(ws.iter().all(|w| w.no_invent()));
        assert!(ws.iter().any(|w| w.kills()));
        for x in [false, true] {
            assert!(!chain(&ws, x));
        }
    }

    /// `IDENTITY` chain preserves input.
    #[test]
    fn identity_preserves() {
        let ws = vec![DetChannel::IDENTITY; 7];
        for x in [false, true] {
            assert_eq!(chain(&ws, x), x);
        }
    }

    proptest! {
        /// Mirrors `GhcMathlib.Channel.Chain.survival_le_pow`.
        #[test]
        fn survival_le_pow(
            ws in prop::collection::vec(0.0f64..=1.0, 0..16),
            rho in 0.0f64..=1.0
        ) {
            let chans: Vec<_> = ws.iter().map(|&p| Channel::new(0.0, p.min(rho)).unwrap()).collect();
            let s = chain_survival(&chans);
            let pow = rho.powi(chans.len() as i32);
            prop_assert!(s <= pow + 1e-12);
        }

        /// Mirrors `GhcMathlib.Channel.Chain.survival_le_one`.
        #[test]
        fn survival_le_one(ws in prop::collection::vec(0.0f64..=1.0, 0..16)) {
            let chans: Vec<_> = ws.iter().map(|&p| Channel::new(0.0, p).unwrap()).collect();
            prop_assert!(chain_survival(&chans) <= 1.0 + 1e-12);
        }

        /// Mirrors `GhcMathlib.Channel.Chain.survival_le_of_member`.
        #[test]
        fn survival_le_of_member(
            ws in prop::collection::vec(0.0f64..=1.0, 1..16),
            rho in 0.0f64..=1.0,
            idx in 0usize..16
        ) {
            let n = ws.len();
            let mut chans: Vec<_> =
                ws.iter().map(|&p| Channel::new(0.0, p).unwrap()).collect();
            chans[idx % n] = Channel::new(0.0, rho).unwrap();
            prop_assert!(chain_survival(&chans) <= rho + 1e-12);
        }
    }
}
