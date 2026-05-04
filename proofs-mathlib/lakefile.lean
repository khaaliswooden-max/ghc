import Lake
open Lake DSL

package ghcMathlib where
  -- Phase B+ extensions of the GHC kernel that depend on mathlib4:
  -- density matrix purity, Laplacian spectrum invariance, mutual
  -- information bounds, and Azuma-Hoeffding convergence.

@[default_target]
lean_lib GhcMathlib where
  roots := #[`GhcMathlib]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "v4.13.0"
