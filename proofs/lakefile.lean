import Lake
open Lake DSL

package ghc where
  -- options can be added here as needed.

@[default_target]
lean_lib Ghc where
  -- library options
  roots := #[`Ghc]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "master"
