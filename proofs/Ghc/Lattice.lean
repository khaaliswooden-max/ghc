/-
  Ghc/Lattice.lean — the compliance lattice 𝐋 = {ḥalāl ≺ mashbūh ≺ ḥarām}.

  Modeled as a three-element chain. Authority parametrization is a
  product over an authority index type, defined here so downstream
  files can reuse it.
-/
import Mathlib.Order.Lattice
import Mathlib.Order.CompleteLattice
import Mathlib.Order.Bounded.Basic

namespace Ghc

/-- Compliance verdicts in increasing order of restriction. -/
inductive Verdict
  | halal
  | mashbuh
  | haram
  deriving DecidableEq, Repr

namespace Verdict

/-- Verdicts are linearly ordered: ḥalāl ≺ mashbūh ≺ ḥarām. -/
instance : LinearOrder Verdict := by
  classical
  refine LinearOrder.lift'
    (fun v => match v with | halal => (0 : Nat) | mashbuh => 1 | haram => 2)
    (fun a b h => by cases a <;> cases b <;> simp_all)

end Verdict

/-- Authority-parametrized lattice value: one verdict per authority. -/
def AuthorityLattice (𝒜 : Type _) := 𝒜 → Verdict

end Ghc
