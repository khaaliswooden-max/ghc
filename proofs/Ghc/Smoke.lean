/-
  Ghc/Smoke.lean — sanity checks. Every named theorem in the GHC kernel
  is referenced here so that `lake build` fails immediately if any of
  them is accidentally weakened or removed.
-/
import Ghc.Lattice
import Ghc.Category
import Ghc.Info
import Ghc.Spectral
import Ghc.Quantum
import Ghc.Convergence

namespace Ghc.Smoke

-- Lattice
#check @Verdict.meet_comm
#check @Verdict.meet_assoc
#check @Verdict.meet_idem
#check @Verdict.join_comm
#check @Verdict.join_assoc
#check @Verdict.absorb_meet_join
#check @Verdict.absorb_join_meet
#check @Verdict.meet_join_distrib
#check @Verdict.join_meet_distrib
#check @Verdict.halal_bot
#check @Verdict.haram_top

-- Halal-Closure Functor (kernel)
#check @Process.halalClosure_append
#check @Process.halalClosure_parallel
#check @Process.halalClosure_all_halal
#check @Process.halalClosure_haram_absorb

-- Contamination capacity (deterministic kernel)
#check @Info.chain_false_of_noinvent
#check @Info.chain_kills_under_no_invent

-- Spectral fingerprint (combinatorial kernel)
#check @Spectral.Graph.weightSeq_relabel
#check @Spectral.Graph.countWeight_relabel
#check @Spectral.Graph.totalWeight_relabel

-- Najis density matrix (discrete kernel)
#check @Quantum.Batch.verdict_append
#check @Quantum.Batch.verdict_mix
#check @Quantum.Batch.verdict_all_halal
#check @Quantum.Batch.verdict_haram_member
#check @Quantum.Batch.verdict_uniform

-- Compliance convergence (deterministic kernel)
#check @Convergence.count_le_length
#check @Convergence.count_unanimous
#check @Convergence.count_unanimous_other
#check @Convergence.plurality_unanimous

-- Deterministic-execution sanity: HCF on a beef supply chain.
example : Process.halalClosure
    [Verdict.halal, Verdict.halal, Verdict.haram, Verdict.halal]
    = Verdict.haram := by decide

example : Process.halalClosure
    [Verdict.halal, Verdict.halal, Verdict.halal] = Verdict.halal := by decide

example : Convergence.plurality
    [Verdict.halal, Verdict.halal, Verdict.halal] = Verdict.halal := by decide

example : Convergence.plurality
    [Verdict.haram, Verdict.haram, Verdict.halal] = Verdict.haram := by decide

end Ghc.Smoke
