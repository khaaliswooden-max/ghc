//! `ghc-algebra` — supply-chain category, contamination channels, and
//! audit plurality.
//!
//! This crate is the **runtime mirror** of the Lean kernel under
//! `proofs/Ghc/`.  Every public type / function corresponds to a
//! definition in the kernel, and every named property is enforced by
//! a Rust property test (`proptest`) so any drift between kernel and
//! runtime breaks the build.
//!
//! Kernel correspondences:
//!
//! | Rust                     | Lean                                          |
//! |--------------------------|-----------------------------------------------|
//! | [`Verdict`]              | `Ghc.Verdict`                                 |
//! | [`Verdict::meet`]        | `Ghc.Verdict.meet`                            |
//! | [`Verdict::join`]        | `Ghc.Verdict.join`                            |
//! | [`Process`]              | `Ghc.Process`                                 |
//! | [`Process::halal_closure`] | `Ghc.Process.halalClosure`                  |
//! | [`Batch`] / [`Contribution`] | `Ghc.Quantum.Batch` / `Contribution`      |
//! | [`Channel`] / [`chain`]  | `Ghc.Info.DetChannel` / `chain`               |
//! | [`plurality`]            | `Ghc.Convergence.plurality`                   |

#![forbid(unsafe_code)]

pub mod channel;
pub mod plurality;
pub mod process;
pub mod verdict;

pub use channel::{chain as channel_chain, Channel as ProbChannel, DetChannel};
pub use plurality::{count, plurality};
pub use process::{halal_closure, Batch, Contribution, Process};
pub use verdict::Verdict;

/// Library version.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");
