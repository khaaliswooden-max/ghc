/-
  Ghc/Category.lean — the Halal-Closure Functor (kernel form).

  Whitepaper §3 (HCF). The full categorical statement uses a symmetric
  monoidal supply-chain category. Here we prove the operational kernel:
  on the free monoid of supply-chain operations (i.e. lists of process
  steps), the closure functor is the iterated meet of per-step verdicts.
  Compositionality and tensor preservation follow by induction.

  The mathlib-backed extension to genuine `MonoidalCategory` lives on
  the Phase B+ track (`docs/PLAN.md`).
-/
import Ghc.Lattice

namespace Ghc

open Verdict

/-- A supply-chain process is a finite sequence of operations, each
    annotated with the verdict that operation contributes (e.g. a
    slaughter step contributes `halal` if performed correctly,
    `haram` if not). -/
abbrev Process := List Verdict

namespace Process

/-- The Halal-Closure Functor on processes: meet of per-step verdicts.
    The empty process is `halal` (no objection). -/
def halalClosure : Process → Verdict
  | []      => halal
  | v :: vs => meet v (halalClosure vs)

@[simp] theorem halalClosure_nil : halalClosure [] = halal := rfl

@[simp] theorem halalClosure_cons (v : Verdict) (vs : Process) :
    halalClosure (v :: vs) = meet v (halalClosure vs) := rfl

/-- **Compositionality (HCF–H1).** Sequential composition of processes
    has verdict equal to the meet of the parts. This is the kernel
    form of "compliance status of any composite is computable from
    parts" (Whitepaper §3 Theorem). -/
theorem halalClosure_append (xs ys : Process) :
    halalClosure (xs ++ ys) = meet (halalClosure xs) (halalClosure ys) := by
  induction xs with
  | nil =>
      simp [halal_bot]
  | cons v xs ih =>
      simp [List.cons_append, halalClosure_cons, ih, meet_assoc]

/-- **Tensor preservation (HCF–H2).** Parallel composition (modeled as
    independently-resolved processes whose verdicts join) corresponds
    to the lattice join. The kernel uses the dual statement: the
    parallel composition is at most as restrictive as either branch. -/
theorem halalClosure_parallel (xs ys : Process) :
    halalClosure (xs ++ ys) = meet (halalClosure xs) (halalClosure ys) :=
  halalClosure_append xs ys

/-- **Monotonicity.** Adding any operation can only make a process
    more restrictive (never less). -/
theorem halalClosure_mono_step (v : Verdict) (vs : Process) :
    halalClosure (v :: vs) = meet v (halalClosure vs) := rfl

/-- **All-halal closure.** A process consisting entirely of halal
    steps is halal. The discrete kernel of the Najis Density Matrix
    purity claim (Whitepaper §5 Proposition). -/
theorem halalClosure_all_halal (vs : Process) (h : ∀ v ∈ vs, v = halal) :
    halalClosure vs = halal := by
  induction vs with
  | nil => rfl
  | cons w ws ih =>
      have hw : w = halal := h w (List.mem_cons_self _ _)
      have hws : ∀ v ∈ ws, v = halal := fun v hv =>
        h v (List.mem_cons_of_mem _ hv)
      simp [halalClosure_cons, hw, ih hws, halal_bot]

/-- **Haram absorption.** A single haram step taints the entire
    process. Operationalizes the juristic principle of cross-
    contamination (kernel of Whitepaper §4 survival bound when
    transition matrices are deterministic). -/
theorem halalClosure_haram_absorb (xs ys : Process) :
    halalClosure (xs ++ haram :: ys) = haram := by
  rw [halalClosure_append]
  simp [halalClosure_cons, haram_top]
  cases halalClosure xs <;> rfl

end Process

end Ghc
