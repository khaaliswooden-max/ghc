pragma circom 2.1.9;

include "halal_threshold.circom";

/*
 * Concrete instantiation: N = 3 process steps, T = 0 (halal-only).
 * Mirrors the v0.0.x reference demo in `core/ghc-cli`.
 */
component main = HalalThreshold(3, 0);

