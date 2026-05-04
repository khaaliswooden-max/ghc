# GHC mathlib extensions (Phase B+)

Lean 4 + mathlib4 proofs that depend on real analysis, linear algebra
over `ℝ`, and probability theory.

This package is **separate from** the kernel (`../proofs/`) so that the
kernel CI stays fast and dependency-free. The mathlib package's CI job
warms a mathlib4 cache and builds the four contributions below.

## Theorems closed (no `sorry`, no extra axioms)

| File | Whitepaper | Statement |
|------|-----------|-----------|
| `GhcMathlib/Density.lean`     | §5 (`Tr(ρ²)` bounds)   | `1/n ≤ Tr(ρ²) ≤ 1` for diagonal density matrices over ℝ. |
| `GhcMathlib/Spectral.lean`    | §6 (fingerprint)       | `(reindex σ σ M).charpoly = M.charpoly`; trace and determinant invariance under vertex relabeling. |
| `GhcMathlib/Convergence.lean` | §8 (audit convergence) | Chebyshev concentration `μ{|X − E[X]| ≥ c} ≤ Var(X)/c²` for the audit RV; Chernoff upper-tail bound `μ{X ≥ ε} ≤ exp(−tε)·mgf`. |
| `GhcMathlib/Channel.lean`     | §4 (survival)          | For binary stochastic channels, survival ≤ ρ^n when each step has survival ≤ ρ; survival ≤ ρ when any one step has survival ≤ ρ. |

## Build

```bash
cd proofs-mathlib
lake update           # fetch mathlib4 + transitive deps
lake exe cache get    # download mathlib4 olean cache (fast)
lake build            # ~30s with cache, ~30min from source
```

## Phase C+ track

Statements that still need substantial new mathlib infrastructure:

- **Mutual-information `C_h` bound.** Mathlib does not yet ship a
  formalized mutual information; the bound `Pr ≤ 2^(C_h − nδ)` requires
  this development first. The `Channel.lean` exponential-decay bound
  is the operationally-decisive specialization for the no-reinvention
  channel class.
- **Hoeffding from MGF bound.** Mathlib has Chernoff (MGF-based) but
  not Hoeffding's lemma (sub-Gaussian MGF bound for bounded RVs);
  closing this delivers the full `O(1/√n)` rate.
- **Azuma-Hoeffding for martingales.** Mathlib has `Probability.Martingale`
  but no Azuma-Hoeffding inequality yet. Once Hoeffding's lemma lands,
  Azuma follows.
- **Spectral theorem reduction.** The `Density.lean` purity bound is
  proved on the diagonal-basis representation; the one-line reduction
  via `Matrix.IsHermitian.spectralTheorem` to the abstract Hermitian
  density matrix is straightforward and is queued for Phase C+.
