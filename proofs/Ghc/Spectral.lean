/-
  Ghc/Spectral.lean — Spectral Provenance Invariants.

  Whitepaper §6: the normalized weighted Laplacian spectrum of a
  provenance DAG is invariant under the relabel/rename adversary class.
-/
import Mathlib.Combinatorics.SimpleGraph.Basic
import Mathlib.LinearAlgebra.Matrix.Spectrum

namespace Ghc.Spectral

/-- A provenance DAG with positive edge weights. -/
structure ProvenanceDAG (V : Type _) [Fintype V] [DecidableEq V] where
  edge   : V → V → ℝ
  edge_nonneg : ∀ u v, 0 ≤ edge u v

/-- The relabel/rename adversary: an arbitrary bijection of vertices. -/
def relabel {V : Type _} [Fintype V] [DecidableEq V]
    (σ : Equiv V V) (G : ProvenanceDAG V) : ProvenanceDAG V :=
  { edge := fun u v => G.edge (σ.symm u) (σ.symm v)
    edge_nonneg := by intro u v; exact G.edge_nonneg _ _ }

/-- Spectral fingerprint: the multiset of eigenvalues of the
    normalized weighted Laplacian. Returns a placeholder until the
    Phase B development of `mathlib`-backed weighted Laplacians lands. -/
noncomputable def fingerprint
    {V : Type _} [Fintype V] [DecidableEq V] (_G : ProvenanceDAG V) :
    Multiset ℝ := sorry

/-- Spectral fingerprint is invariant under relabel. -/
theorem spectralFingerprint
    {V : Type _} [Fintype V] [DecidableEq V]
    (G : ProvenanceDAG V) (σ : Equiv V V) :
    fingerprint (relabel σ G) = fingerprint G := by
  sorry

end Ghc.Spectral
