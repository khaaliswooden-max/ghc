/-
  Ghc/Info.lean — Contamination Channel Capacity (kernel form).

  Whitepaper §4 (Survival bound). The full statement bounds
  Pr[Y_n = 1 | X = 1] in terms of mutual information; that requires
  real analysis from mathlib and lives on the Phase B+ track.

  The kernel proven here is the deterministic refinement: model each
  processing operation as a function `Bool → Bool` on the haram-bit;
  the survival of a haram-bit through a chain is the composite of the
  per-step functions. Operationally this is the "any-operation-kills-
  with-no-reinvention" upper bound: as soon as one step provably
  eliminates contamination (e.g. an autoclave at sufficient temperature)
  AND no downstream step reintroduces it, the chain inherits the
  guarantee.
-/
import Ghc.Lattice

namespace Ghc.Info

/-- A deterministic operation on the haram-bit. -/
abbrev DetChannel := Bool → Bool

/-- Iterated composition: the result of applying a list of channels
    in order. -/
def chain : List DetChannel → DetChannel
  | []      => id
  | W :: Ws => fun x => chain Ws (W x)

@[simp] theorem chain_nil : chain [] = id := rfl

@[simp] theorem chain_cons (W : DetChannel) (Ws : List DetChannel) (x : Bool) :
    chain (W :: Ws) x = chain Ws (W x) := rfl

/-- A channel **kills** if it sends every input to `false` (haram-bit
    eliminated regardless of upstream). -/
def Kills (W : DetChannel) : Prop := ∀ x, W x = false

/-- A channel respects **no-reinvention** if it does not fabricate
    contamination from a clean input: `W false = false`. All
    physically-realizable cleaning operations satisfy this; channels
    that violate it model re-contamination, captured separately. -/
def NoInvent (W : DetChannel) : Prop := W false = false

/-- Once the haram-bit is `false`, no chain of `NoInvent` channels can
    bring it back. -/
theorem chain_false_of_noinvent
    (Ws : List DetChannel) (h : ∀ W ∈ Ws, NoInvent W) :
    chain Ws false = false := by
  induction Ws with
  | nil => rfl
  | cons W Ws ih =>
      simp only [chain_cons]
      have hW : W false = false := h W (List.mem_cons_self _ _)
      rw [hW]
      exact ih (fun V hv => h V (List.mem_cons_of_mem _ hv))

/-- **Kernel survival lemma.** If any channel in a chain of
    `NoInvent` channels kills, the entire chain produces `false` on
    every input. This is the deterministic 0/1 refinement of
    Whitepaper §4 Theorem (survival bound): when every transition
    matrix is in `{0,1}`, capacity collapses and survival is zero. -/
theorem chain_kills_under_no_invent
    (Ws : List DetChannel) (hmono : ∀ W ∈ Ws, NoInvent W)
    (hkill : ∃ W ∈ Ws, Kills W) :
    ∀ x, chain Ws x = false := by
  induction Ws with
  | nil => rcases hkill with ⟨_, hmem, _⟩; cases hmem
  | cons W Ws ih =>
      intro x
      simp only [chain_cons]
      rcases hkill with ⟨W', hmem, hk⟩
      rcases List.mem_cons.mp hmem with rfl | hmem'
      · -- killer is the head; route through chain_false_of_noinvent
        rw [hk x]
        exact chain_false_of_noinvent Ws
          (fun V hv => hmono V (List.mem_cons_of_mem _ hv))
      · -- killer is in the tail; recurse on the post-W input
        exact ih
          (fun V hv => hmono V (List.mem_cons_of_mem _ hv))
          ⟨W', hmem', hk⟩
          (W x)

end Ghc.Info
