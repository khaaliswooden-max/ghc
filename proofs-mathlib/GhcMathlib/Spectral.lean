/-
  GhcMathlib/Spectral.lean — Phase B+ spectral provenance invariants.

  Phase B+ extension of `Ghc/Spectral.lean`. Where the kernel proved
  combinatorial invariance of the edge-weight multiset under
  vertex-relabeling, we now prove the genuinely spectral statement:
  the characteristic polynomial — and therefore the multiset of
  eigenvalues — of any matrix-valued function of the graph (adjacency,
  Laplacian, normalized Laplacian, etc.) is invariant under vertex
  relabeling.

  The mathlib lemma `Matrix.charpoly_reindex` does the heavy lifting;
  we apply it to the case where the reindexing is a permutation
  (`Equiv (Fin n) (Fin n)`).
-/
import Mathlib.LinearAlgebra.Matrix.Charpoly.Basic
import Mathlib.LinearAlgebra.Matrix.Trace
import Mathlib.Data.Real.Basic

namespace GhcMathlib.Spectral

variable {n : ℕ}

open Matrix

/-- **Spectral fingerprint.** For any square matrix `M` over `ℝ` and
    any vertex-relabeling `σ : Equiv (Fin n) (Fin n)`, the
    characteristic polynomial of the relabeled matrix equals that of
    the original. This is the genuinely-spectral form of Whitepaper
    §6 Theorem (`σ(L_G)` invariance). -/
theorem charpoly_relabel
    (M : Matrix (Fin n) (Fin n) ℝ) (σ : Equiv (Fin n) (Fin n)) :
    (Matrix.reindex σ σ M).charpoly = M.charpoly :=
  charpoly_reindex σ M

/-- **Trace invariance** under vertex relabeling. -/
theorem trace_relabel
    (M : Matrix (Fin n) (Fin n) ℝ) (σ : Equiv (Fin n) (Fin n)) :
    (Matrix.reindex σ σ M).trace = M.trace := by
  -- reindex is the simultaneous row/column permutation; the diagonal
  -- entries are permuted, and trace is sum over the diagonal which is
  -- invariant under permutation.
  unfold Matrix.trace
  exact Fintype.sum_equiv σ.symm _ _ (fun i => by
    simp [Matrix.reindex, Matrix.submatrix])

/-- **Determinant invariance** under vertex relabeling. -/
theorem det_relabel
    (M : Matrix (Fin n) (Fin n) ℝ) (σ : Equiv (Fin n) (Fin n)) :
    (Matrix.reindex σ σ M).det = M.det :=
  Matrix.det_reindex_self σ M

end GhcMathlib.Spectral
