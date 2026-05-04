/-
  Ghc/Quantum.lean — The Najis Density Matrix (kernel form).

  Whitepaper §5. The full statement gives `1/n ≤ Tr(ρ²) ≤ 1` for the
  density-matrix representation of provenance, requiring linear
  algebra over ℝ from mathlib; that lives on the Phase B+ track.

  The kernel proven here is the operationally-decisive discrete
  refinement: model a batch as a list of (source-id, weight, verdict)
  contributions; the mix verdict is the meet (more restrictive wins);
  if every source is ḥalāl the mix is ḥalāl, and a single ḥarām
  source taints the entire mix. This corresponds to taking ρ to be
  diagonal with classical weights — the regime that covers the
  overwhelming majority of operational compliance decisions.
-/
import Ghc.Lattice

namespace Ghc.Quantum

open Ghc Verdict

/-- A single source contribution: source id, mass weight, verdict. -/
abbrev Contribution := Nat × Nat × Verdict

namespace Contribution

@[inline] def verdict (c : Contribution) : Verdict := c.2.2
@[inline] def weight  (c : Contribution) : Nat := c.2.1

end Contribution

/-- A batch is a list of source contributions (the "diagonal najis
    state"). -/
abbrev Batch := List Contribution

namespace Batch

/-- The aggregate verdict of a batch: meet of per-source verdicts.
    An empty batch has no objection. -/
def verdict : Batch → Verdict
  | []      => halal
  | c :: cs => meet c.verdict (verdict cs)

@[simp] theorem verdict_nil : verdict [] = halal := rfl

@[simp] theorem verdict_cons (c : Contribution) (cs : Batch) :
    verdict (c :: cs) = meet c.verdict (verdict cs) := rfl

/-- **Mixing is concatenation.** -/
def mix (b₁ b₂ : Batch) : Batch := b₁ ++ b₂

/-- **Compositionality of mixing.** The verdict of a mixed batch is
    the meet of the part verdicts. (Discrete kernel of the density-
    matrix partial-trace law.) -/
theorem verdict_append (b₁ b₂ : Batch) :
    verdict (b₁ ++ b₂) = meet (verdict b₁) (verdict b₂) := by
  induction b₁ with
  | nil => simp [halal_bot]
  | cons c b₁ ih =>
      rw [List.cons_append, verdict_cons, verdict_cons, ih, meet_assoc]

theorem verdict_mix (b₁ b₂ : Batch) :
    verdict (mix b₁ b₂) = meet (verdict b₁) (verdict b₂) :=
  verdict_append b₁ b₂

/-- **All-halal sources ⇒ halal mix.** -/
theorem verdict_all_halal (b : Batch) (h : ∀ c ∈ b, c.verdict = halal) :
    verdict b = halal := by
  induction b with
  | nil => rfl
  | cons c cs ih =>
      have hc : c.verdict = halal := h c (List.mem_cons_self _ _)
      have hcs : ∀ c' ∈ cs, c'.verdict = halal := fun c' hc' =>
        h c' (List.mem_cons_of_mem _ hc')
      simp [verdict_cons, hc, ih hcs, halal_bot]

/-- **One haram source taints the mix.** -/
theorem verdict_haram_member (b : Batch)
    (h : ∃ c ∈ b, c.verdict = haram) : verdict b = haram := by
  induction b with
  | nil => rcases h with ⟨_, hmem, _⟩; cases hmem
  | cons c cs ih =>
      rcases h with ⟨c', hmem, hv⟩
      rcases List.mem_cons.mp hmem with rfl | hmem'
      · -- the haram is the head
        simp [verdict_cons, hv, haram_top]
      · -- the haram is in the tail
        rw [verdict_cons, ih ⟨c', hmem', hv⟩]
        cases c.verdict <;> rfl

/-- **Discrete purity bound.** The "purity" surrogate of a batch
    counts how many sources contribute the dominant verdict. For a
    nonempty batch where every source is the same verdict `v`, all
    contributions concur — the extremal-purity case in the
    quantum-statistical formulation. -/
theorem verdict_uniform (b : Batch) (v : Verdict)
    (hne : b ≠ []) (h : ∀ c ∈ b, c.verdict = v) :
    verdict b = v := by
  induction b with
  | nil => exact absurd rfl hne
  | cons c cs ih =>
      have hc : c.verdict = v := h c (List.mem_cons_self _ _)
      cases cs with
      | nil =>
          simp [verdict_cons, verdict_nil, hc]
          cases v <;> rfl
      | cons c' cs' =>
          have hcs : ∀ c'' ∈ (c' :: cs'), c''.verdict = v := fun c'' hc'' =>
            h c'' (List.mem_cons_of_mem _ hc'')
          have ih' := ih (by simp) hcs
          simp [verdict_cons, hc, ih']
          cases v <;> rfl

end Batch

end Ghc.Quantum
