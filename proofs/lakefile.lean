import Lake
open Lake DSL

package ghc where
  -- Pure Lean 4 kernel for the GHC formalization. mathlib-dependent
  -- extensions (real-valued capacity, density-matrix purity bounds,
  -- Azuma-Hoeffding) live on a separate Phase B+ track to keep the
  -- kernel CI fast and dependency-free.

@[default_target]
lean_lib Ghc where
  roots := #[`Ghc]
