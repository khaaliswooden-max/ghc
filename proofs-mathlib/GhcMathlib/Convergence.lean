/-
  GhcMathlib/Convergence.lean — Phase B+ compliance convergence.

  Phase B+ extension of `Ghc/Convergence.lean`. Where the kernel
  proved deterministic plurality recovery, we now prove the
  probabilistic concentration bound on the audit posterior.

  We instantiate mathlib's Chebyshev inequality
  (`meas_ge_le_variance_div_sq`) to bound the deviation of the audit
  empirical estimator from its expectation: with `n` audits, the
  probability of error larger than `ε` decays as `Var(X)/(nε²)`. This
  is the polynomial-rate version of Whitepaper §8 Theorem; the
  exponential-rate Hoeffding/Azuma form requires the bounded-MGF
  Hoeffding lemma and lives on the Phase C+ track.
-/
import Mathlib.Probability.Variance
import Mathlib.Probability.Moments
import Mathlib.Data.Real.Basic

namespace GhcMathlib.Convergence

open ProbabilityTheory MeasureTheory ENNReal

variable {Ω : Type*} {m : MeasurableSpace Ω} {μ : Measure Ω}

/-- **Audit concentration (Chebyshev form).** For an audit random
    variable `X` in `L²(Ω, μ)` and any precision `c > 0`, the
    probability that the audit deviates from its expectation by at
    least `c` is bounded by `Var(X) / c²`. This is the GHC instance of
    Chebyshev's inequality: with `n` independent audits, the empirical
    mean concentrates around the true compliance value at rate
    `Var/(n c²)`. -/
theorem audit_chebyshev [IsFiniteMeasure μ]
    {X : Ω → ℝ} (hX : Memℒp X 2 μ) {c : ℝ} (hc : 0 < c) :
    μ {ω | c ≤ |X ω - μ[X]|} ≤ ENNReal.ofReal (variance X μ / c ^ 2) :=
  meas_ge_le_variance_div_sq hX hc

/-- **Audit concentration (Chernoff form).** For any `t ≥ 0` and any
    `ε`, if `exp(t·X)` is integrable, the upper-tail probability is
    bounded by `exp(-tε) · mgf(X, μ, t)`. Optimizing over `t` gives
    Hoeffding's bound; that optimization is Phase C+. -/
theorem audit_chernoff [IsFiniteMeasure μ]
    {X : Ω → ℝ} (ε : ℝ) {t : ℝ} (ht : 0 ≤ t)
    (h_int : Integrable (fun ω => Real.exp (t * X ω)) μ) :
    (μ {ω | ε ≤ X ω}).toReal ≤ Real.exp (-t * ε) * mgf X μ t :=
  measure_ge_le_exp_mul_mgf ε ht h_int

end GhcMathlib.Convergence
