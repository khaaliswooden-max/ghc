/-
  GhcMathlib/Density.lean — Najis Density Matrix purity bounds.

  Phase B+ extension of `Ghc/Quantum.lean`. Proves the canonical
  inequalities

      1/n ≤ Tr(ρ²) ≤ 1

  for a density matrix ρ on an n-dimensional space.

  We work in the diagonal basis: by the spectral theorem, every
  Hermitian psd trace-1 operator is diagonalizable to a probability
  vector, and `Tr(ρ²) = Σ λᵢ²`. Both bounds are then real-analytic
  inequalities about probability vectors, fully provable from
  mathlib4. The connection to the abstract `Matrix` formulation is a
  one-line reduction via `Matrix.IsHermitian.spectralTheorem` and
  lives in `GhcMathlib.Density.Spectral` (Phase C+).
-/
import Mathlib.Algebra.BigOperators.Pi
import Mathlib.Algebra.Order.Chebyshev
import Mathlib.Data.Finset.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Linarith

namespace GhcMathlib.Density

open Finset

/-- Diagonal-basis density matrix: nonnegative weights summing to 1. -/
structure Diag (n : ℕ) where
  weights : Fin n → ℝ
  nonneg : ∀ i, 0 ≤ weights i
  sumOne : ∑ i, weights i = 1

namespace Diag

variable {n : ℕ}

/-- The purity Tr(ρ²) of a diagonal density. -/
def purity (ρ : Diag n) : ℝ := ∑ i, (ρ.weights i) ^ 2

/-- Each weight is bounded above by 1 (by sum constraint and nonneg). -/
lemma weight_le_one (ρ : Diag n) (i : Fin n) : ρ.weights i ≤ 1 := by
  have h := single_le_sum (f := ρ.weights) (s := (Finset.univ : Finset (Fin n)))
    (fun j _ => ρ.nonneg j) (mem_univ i)
  simpa [ρ.sumOne] using h

/-- **Upper bound:** `Tr(ρ²) ≤ 1`. Proof: `wᵢ² ≤ wᵢ` since
    `0 ≤ wᵢ ≤ 1`, then sum and use `Σ wᵢ = 1`. -/
theorem purity_le_one (ρ : Diag n) : ρ.purity ≤ 1 := by
  have hbd : ∀ i ∈ (univ : Finset (Fin n)), (ρ.weights i) ^ 2 ≤ ρ.weights i := by
    intro i _
    have h0 := ρ.nonneg i
    have h1 := ρ.weight_le_one i
    nlinarith [sq_nonneg (ρ.weights i)]
  have hsum := sum_le_sum hbd
  have : ρ.purity ≤ ∑ i, ρ.weights i := hsum
  rw [ρ.sumOne] at this
  exact this

/-- **Lower bound:** `1/n ≤ Tr(ρ²)`. Proof: by Cauchy–Schwarz
    (Chebyshev for `f = g`), `(Σ wᵢ)² ≤ n · Σ wᵢ²`. -/
theorem one_div_n_le_purity (ρ : Diag n) (hn : 0 < n) :
    (1 : ℝ) / n ≤ ρ.purity := by
  -- (Σ wᵢ)² ≤ #univ * Σ wᵢ²
  have key :
      (∑ i, ρ.weights i) ^ 2 ≤
      ((univ : Finset (Fin n)).card : ℝ) * ∑ i, (ρ.weights i) ^ 2 :=
    sq_sum_le_card_mul_sum_sq
  rw [ρ.sumOne] at key
  have hcard : ((univ : Finset (Fin n)).card : ℝ) = (n : ℝ) := by simp
  rw [hcard] at key
  have hnpos : (0 : ℝ) < n := by exact_mod_cast hn
  -- 1 ≤ n * purity ⇒ 1/n ≤ purity.
  have h1 : (1 : ℝ) ≤ n * ρ.purity := by simpa [purity] using key
  rw [div_le_iff₀ hnpos]
  linarith

/-- Combined bounds. -/
theorem purity_bounds (ρ : Diag n) (hn : 0 < n) :
    (1 : ℝ) / n ≤ ρ.purity ∧ ρ.purity ≤ 1 :=
  ⟨one_div_n_le_purity ρ hn, purity_le_one ρ⟩

end Diag

end GhcMathlib.Density
