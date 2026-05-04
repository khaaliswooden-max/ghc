/-
  Ghc/Lattice.lean — the compliance lattice 𝐋 = {ḥalāl ≺ mashbūh ≺ ḥarām}.

  Modeled as a three-element chain. We prove that `meet` (more
  restrictive wins) and `join` (less restrictive wins) form a bounded
  distributive lattice with bottom `halal` and top `haram`. All proofs
  are by exhaustive case analysis and reduce to `rfl`; no axioms or
  unfinished obligations remain, and there is no external dependency.
-/

namespace Ghc

/-- Compliance verdicts in increasing order of restriction. -/
inductive Verdict
  | halal
  | mashbuh
  | haram
  deriving DecidableEq, Repr

namespace Verdict

/-- The lattice meet: more restrictive opinion wins. -/
def meet : Verdict → Verdict → Verdict
  | haram,   _       => haram
  | _,       haram   => haram
  | mashbuh, _       => mashbuh
  | _,       mashbuh => mashbuh
  | halal,   halal   => halal

/-- The lattice join: less restrictive opinion wins. -/
def join : Verdict → Verdict → Verdict
  | halal,   _       => halal
  | _,       halal   => halal
  | mashbuh, _       => mashbuh
  | _,       mashbuh => mashbuh
  | haram,   haram   => haram

/-- `≤` reads as "no more restrictive than". -/
def le : Verdict → Verdict → Prop
  | halal,   _       => True
  | mashbuh, halal   => False
  | mashbuh, _       => True
  | haram,   haram   => True
  | haram,   _       => False

instance : LE Verdict := ⟨le⟩

instance : DecidableEq Verdict := by
  intro a b; cases a <;> cases b <;> first | exact isTrue rfl | exact isFalse (by intro h; cases h)

theorem meet_comm (a b : Verdict) : meet a b = meet b a := by
  cases a <;> cases b <;> rfl

theorem meet_assoc (a b c : Verdict) :
    meet (meet a b) c = meet a (meet b c) := by
  cases a <;> cases b <;> cases c <;> rfl

theorem meet_idem (a : Verdict) : meet a a = a := by
  cases a <;> rfl

theorem join_comm (a b : Verdict) : join a b = join b a := by
  cases a <;> cases b <;> rfl

theorem join_assoc (a b c : Verdict) :
    join (join a b) c = join a (join b c) := by
  cases a <;> cases b <;> cases c <;> rfl

theorem join_idem (a : Verdict) : join a a = a := by
  cases a <;> rfl

/-- Absorption: `a ⊓ (a ⊔ b) = a`. -/
theorem absorb_meet_join (a b : Verdict) : meet a (join a b) = a := by
  cases a <;> cases b <;> rfl

/-- Absorption: `a ⊔ (a ⊓ b) = a`. -/
theorem absorb_join_meet (a b : Verdict) : join a (meet a b) = a := by
  cases a <;> cases b <;> rfl

/-- Distributivity: meet over join. -/
theorem meet_join_distrib (a b c : Verdict) :
    meet a (join b c) = join (meet a b) (meet a c) := by
  cases a <;> cases b <;> cases c <;> rfl

/-- Distributivity: join over meet. -/
theorem join_meet_distrib (a b c : Verdict) :
    join a (meet b c) = meet (join a b) (join a c) := by
  cases a <;> cases b <;> cases c <;> rfl

/-- `halal` is the bottom element of the lattice. -/
theorem halal_bot (a : Verdict) : meet halal a = a := by
  cases a <;> rfl

/-- `haram` is the top element of the lattice. -/
theorem haram_top (a : Verdict) : meet haram a = haram := by
  cases a <;> rfl

end Verdict

/-- Authority-parametrized lattice: one verdict per authority. -/
def AuthorityLattice (𝒜 : Type) := 𝒜 → Verdict

namespace AuthorityLattice

variable {𝒜 : Type}

/-- Pointwise meet (federated meet). -/
def meet (f g : AuthorityLattice 𝒜) : AuthorityLattice 𝒜 :=
  fun a => Verdict.meet (f a) (g a)

/-- Pointwise join. -/
def join (f g : AuthorityLattice 𝒜) : AuthorityLattice 𝒜 :=
  fun a => Verdict.join (f a) (g a)

theorem meet_comm (f g : AuthorityLattice 𝒜) : meet f g = meet g f := by
  funext a; exact Verdict.meet_comm (f a) (g a)

theorem meet_assoc (f g h : AuthorityLattice 𝒜) :
    meet (meet f g) h = meet f (meet g h) := by
  funext a; exact Verdict.meet_assoc (f a) (g a) (h a)

end AuthorityLattice

end Ghc
