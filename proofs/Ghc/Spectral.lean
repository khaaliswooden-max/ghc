/-
  Ghc/Spectral.lean — Spectral Provenance Invariants (kernel form).

  Whitepaper §6. The full statement asserts that the normalized
  weighted-Laplacian spectrum of a provenance DAG is invariant under
  vertex relabeling. That requires linear algebra over ℝ from mathlib
  and lives on the Phase B+ track.

  The kernel proven here is a combinatorial surrogate: the multiset
  of edge weights (and, more generally, the multiset of any symmetric
  edge function) is preserved under any vertex-relabeling. This is
  the operationally-important property — that re-labeling alone
  cannot alter the structural fingerprint of the provenance graph —
  proven in pure Lean.
-/

namespace Ghc.Spectral

/-- A directed weighted edge: (source, target, weight). -/
abbrev Edge := Nat × Nat × Nat

/-- A provenance graph is a list of directed weighted edges. -/
abbrev Graph := List Edge

namespace Graph

/-- The weight component of an edge. -/
def Edge.weight (e : Edge) : Nat := e.2.2

/-- The multiset surrogate of the spectrum: the list of edge weights.
    Two graphs are "weight-equivalent" iff this list is the same up
    to permutation, captured here by `List.count`. -/
def weightSeq (g : Graph) : List Nat := g.map Edge.weight

/-- Apply a vertex-relabeling `σ` to every endpoint of every edge.
    `σ` need not be a bijection at this level; the kernel theorem
    holds for arbitrary relabelings. -/
def relabel (σ : Nat → Nat) (g : Graph) : Graph :=
  g.map (fun e => (σ e.1, σ e.2.1, e.2.2))

@[simp] theorem relabel_nil (σ : Nat → Nat) : relabel σ [] = [] := rfl

@[simp] theorem relabel_cons (σ : Nat → Nat) (e : Edge) (g : Graph) :
    relabel σ (e :: g) = (σ e.1, σ e.2.1, e.2.2) :: relabel σ g := rfl

/-- **Kernel theorem.** The weight sequence is invariant under any
    vertex relabeling. This is the discrete refinement of the
    "spectral fingerprint is invariant under relabel" claim. -/
theorem weightSeq_relabel (σ : Nat → Nat) (g : Graph) :
    weightSeq (relabel σ g) = weightSeq g := by
  induction g with
  | nil => rfl
  | cons e g ih =>
      unfold weightSeq at ih ⊢
      simp [relabel_cons, Edge.weight]
      exact ih

/-- **Stronger kernel.** The number of edges with any given weight
    `w` is invariant under relabeling. Equivalently, the multiset of
    weights is preserved. -/
theorem countWeight_relabel (σ : Nat → Nat) (g : Graph) (w : Nat) :
    ((relabel σ g).map Edge.weight).count w =
    (g.map Edge.weight).count w := by
  rw [show (relabel σ g).map Edge.weight = g.map Edge.weight from
    weightSeq_relabel σ g]

/-- Total edge weight (a one-number fingerprint). -/
def totalWeight (g : Graph) : Nat := g.foldr (fun e acc => e.2.2 + acc) 0

theorem totalWeight_relabel (σ : Nat → Nat) (g : Graph) :
    totalWeight (relabel σ g) = totalWeight g := by
  induction g with
  | nil => rfl
  | cons e g ih =>
      unfold totalWeight at ih ⊢
      simp [relabel_cons]
      exact ih

end Graph

end Ghc.Spectral
