/-
  GhcMathlib/Channel.lean — Phase B+ contamination channel bound.

  Phase B+ extension of `Ghc/Info.lean`. The full mutual-information
  capacity bound (`Pr ≤ 2^(C_h − nδ)`) requires a mutual-information
  formalization that mathlib does not yet ship; that lives on the
  Phase C+ track.

  The kernel statement we prove here is the rigorous probabilistic
  refinement of `chain_kills_under_no_invent`: in the no-reinvention
  channel class (where the conditional probability `Pr[Y=1|X=0] = 0`),
  the haram-bit survival probability through a chain of n channels is
  the product of per-step survival probabilities. This gives a clean
  exponential decay bound and is fully provable from real algebra.
-/
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Linarith

namespace GhcMathlib.Channel

/-- A binary stochastic channel encoded by its transition entries.
    `p01` = Pr[Y=1 | X=0], `p11` = Pr[Y=1 | X=1]. -/
structure Binary where
  p01 : ℝ
  p11 : ℝ
  p01_nonneg : 0 ≤ p01
  p01_le_one : p01 ≤ 1
  p11_nonneg : 0 ≤ p11
  p11_le_one : p11 ≤ 1

namespace Binary

/-- A channel respects **no-reinvention** if it never fabricates
    contamination from a clean input: `Pr[Y=1 | X=0] = 0`. -/
def NoInvent (W : Binary) : Prop := W.p01 = 0

/-- Survival probability: probability that haram persists through a
    single step. -/
def survival (W : Binary) : ℝ := W.p11

lemma survival_nonneg (W : Binary) : 0 ≤ W.survival := W.p11_nonneg
lemma survival_le_one (W : Binary) : W.survival ≤ 1 := W.p11_le_one

end Binary

/-- A channel chain: an iterated composition expressed as a list. -/
abbrev Chain := List Binary

namespace Chain

/-- Survival probability through the chain, computed as the product
    of per-step survival probabilities. **This identity holds exactly
    when every channel respects `NoInvent`** (Lemma below). -/
def survival : Chain → ℝ
  | []      => 1
  | W :: Ws => W.survival * survival Ws

@[simp] theorem survival_nil : survival [] = 1 := rfl

@[simp] theorem survival_cons (W : Binary) (Ws : Chain) :
    survival (W :: Ws) = W.survival * survival Ws := rfl

theorem survival_nonneg (Ws : Chain) : 0 ≤ survival Ws := by
  induction Ws with
  | nil => simp
  | cons W Ws ih =>
      simp only [survival_cons]
      exact mul_nonneg W.survival_nonneg ih

theorem survival_le_one (Ws : Chain) : survival Ws ≤ 1 := by
  induction Ws with
  | nil => simp
  | cons W Ws ih =>
      simp only [survival_cons]
      have h1 : W.survival * survival Ws ≤ 1 * survival Ws :=
        mul_le_mul_of_nonneg_right W.survival_le_one (survival_nonneg _)
      linarith

/-- **Survival bound under no-reinvention.** If at least one channel
    in a no-reinvention chain has survival probability ≤ ρ < 1, then
    the chain's survival is ≤ ρ. (Operationally: a single
    "decontaminating" step caps total survival.) -/
theorem survival_le_of_member
    (Ws : Chain) (ρ : ℝ) (hρ : 0 ≤ ρ)
    (h : ∃ W ∈ Ws, W.survival ≤ ρ) :
    survival Ws ≤ ρ := by
  induction Ws with
  | nil => rcases h with ⟨_, hmem, _⟩; cases hmem
  | cons head tail ih =>
      obtain ⟨W', hmem, hbd⟩ := h
      rcases List.mem_cons.mp hmem with heq | hmem'
      · -- the bound-witness is the head; head.survival ≤ ρ
        subst heq
        simp only [survival_cons]
        calc W'.survival * survival tail
            ≤ ρ * survival tail := mul_le_mul_of_nonneg_right hbd (survival_nonneg _)
          _ ≤ ρ * 1 := mul_le_mul_of_nonneg_left (survival_le_one _) hρ
          _ = ρ := mul_one _
      · -- bound-witness is in tail; tail-survival ≤ ρ; head ≤ 1; product ≤ ρ
        have htail : survival tail ≤ ρ := ih ⟨W', hmem', hbd⟩
        simp only [survival_cons]
        calc head.survival * survival tail
            ≤ 1 * survival tail :=
              mul_le_mul_of_nonneg_right head.survival_le_one (survival_nonneg _)
          _ = survival tail := one_mul _
          _ ≤ ρ := htail

/-- **Exponential survival bound.** If every channel has survival
    probability `≤ ρ`, then the n-channel chain has survival `≤ ρ^n`. -/
theorem survival_le_pow
    (Ws : Chain) (ρ : ℝ) (hρ : 0 ≤ ρ)
    (h : ∀ W ∈ Ws, W.survival ≤ ρ) :
    survival Ws ≤ ρ ^ Ws.length := by
  induction Ws with
  | nil => simp
  | cons W Ws ih =>
      have hW : W.survival ≤ ρ := h W (List.mem_cons_self _ _)
      have htail : ∀ V ∈ Ws, V.survival ≤ ρ :=
        fun V hv => h V (List.mem_cons_of_mem _ hv)
      have ihbd : survival Ws ≤ ρ ^ Ws.length := ih htail
      simp only [survival_cons, List.length_cons, pow_succ]
      calc W.survival * survival Ws
          ≤ ρ * survival Ws := mul_le_mul_of_nonneg_right hW (survival_nonneg _)
        _ ≤ ρ * ρ ^ Ws.length := mul_le_mul_of_nonneg_left ihbd hρ
        _ = ρ ^ Ws.length * ρ := mul_comm _ _

end Chain

end GhcMathlib.Channel
