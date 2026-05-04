/-
  Ghc/Convergence.lean — Compliance Convergence Theorem (kernel form).

  Whitepaper §8. The full statement gives an Azuma–Hoeffding
  `O(1/√n)` rate; that requires real analysis from mathlib and lives
  on the Phase B+ track.

  The kernel proven here is the deterministic refinement: a count-
  based plurality vote over a list of audit verdicts. We prove
  unanimity recovery (perfect-noise case) and per-verdict zero counts
  for non-target verdicts under unanimity — the discrete substrate
  the probabilistic theorem refines.
-/
import Ghc.Lattice

namespace Ghc.Convergence

open Ghc Verdict

/-- Number of audits in the log that returned the target verdict `v`. -/
def count : List Verdict → Verdict → Nat
  | [],      _ => 0
  | a :: as, v => (if a = v then 1 else 0) + count as v

@[simp] theorem count_nil (v : Verdict) : count [] v = 0 := rfl

theorem count_le_length (audits : List Verdict) (v : Verdict) :
    count audits v ≤ audits.length := by
  induction audits with
  | nil => exact Nat.le_refl _
  | cons a as ih =>
      simp only [count, List.length_cons]
      split <;> omega

/-- **Unanimity recovery.** If every audit returned `v`, the count
    of `v` equals the audit-log length. -/
theorem count_unanimous (audits : List Verdict) (v : Verdict)
    (h : ∀ a ∈ audits, a = v) : count audits v = audits.length := by
  induction audits with
  | nil => rfl
  | cons a as ih =>
      have ha : a = v := h a (List.mem_cons_self _ _)
      have has : ∀ a' ∈ as, a' = v := fun a' h' =>
        h a' (List.mem_cons_of_mem _ h')
      simp [count, ha, ih has, List.length_cons]
      omega

/-- **Unanimity zero count.** If every audit returned `v`, every
    other verdict has count zero. -/
theorem count_unanimous_other (audits : List Verdict) (v w : Verdict)
    (hne : w ≠ v) (h : ∀ a ∈ audits, a = v) : count audits w = 0 := by
  induction audits with
  | nil => rfl
  | cons a as ih =>
      have ha : a = v := h a (List.mem_cons_self _ _)
      have has : ∀ a' ∈ as, a' = v := fun a' h' =>
        h a' (List.mem_cons_of_mem _ h')
      have hane : a ≠ w := fun heq => hne (heq.symm.trans ha)
      simp [count, hane, ih has]

/-- The plurality verdict, with `haram` as the conservative
    tiebreaker. -/
def plurality (audits : List Verdict) : Verdict :=
  let h := count audits halal
  let m := count audits mashbuh
  let r := count audits haram
  if h > m ∧ h > r then halal
  else if m > r ∧ m ≥ h then mashbuh
  else haram

/-- **Plurality on a unanimous nonempty log.** If every audit returned
    `v`, plurality recovers `v` exactly. (Kernel of "perfect-noise
    audits converge in one step", i.e. the deterministic boundary case
    of compliance convergence.) -/
theorem plurality_unanimous (audits : List Verdict) (v : Verdict)
    (hne : audits ≠ []) (h : ∀ a ∈ audits, a = v) :
    plurality audits = v := by
  have hlen : audits.length > 0 := by
    cases audits with
    | nil => exact absurd rfl hne
    | cons _ _ => simp [List.length_cons]
  have hv  : count audits v = audits.length := count_unanimous audits v h
  unfold plurality
  cases v with
  | halal =>
      have hm : count audits mashbuh = 0 :=
        count_unanimous_other audits halal mashbuh (by intro h'; cases h') h
      have hr : count audits haram = 0 :=
        count_unanimous_other audits halal haram (by intro h'; cases h') h
      simp only [hv, hm, hr]
      have : audits.length > 0 ∧ audits.length > 0 := ⟨hlen, hlen⟩
      simp [this]
  | mashbuh =>
      have hh : count audits halal = 0 :=
        count_unanimous_other audits mashbuh halal (by intro h'; cases h') h
      have hr : count audits haram = 0 :=
        count_unanimous_other audits mashbuh haram (by intro h'; cases h') h
      simp only [hv, hh, hr]
      have h1 : ¬ ((0 : Nat) > audits.length ∧ (0 : Nat) > 0) := by
        intro ⟨_, h2⟩; exact Nat.lt_irrefl 0 h2
      simp [h1, hlen]
  | haram =>
      have hh : count audits halal = 0 :=
        count_unanimous_other audits haram halal (by intro h'; cases h') h
      have hm : count audits mashbuh = 0 :=
        count_unanimous_other audits haram mashbuh (by intro h'; cases h') h
      simp only [hv, hh, hm]
      have h1 : ¬ ((0 : Nat) > 0 ∧ (0 : Nat) > audits.length) := by
        intro ⟨h2, _⟩; exact Nat.lt_irrefl 0 h2
      have h2 : ¬ ((0 : Nat) > audits.length ∧ (0 : Nat) ≥ 0) := by
        intro ⟨h3, _⟩; exact Nat.not_lt_zero _ h3
      simp [h1, h2]

end Ghc.Convergence
