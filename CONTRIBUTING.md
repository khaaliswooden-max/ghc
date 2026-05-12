# Contributing to GHC

Thanks for your interest in Global Halal Compliance. This document
covers how to submit changes, the conventions the project follows,
and what to expect from a review.

By participating in this project you agree to abide by the
[Code of Conduct](CODE_OF_CONDUCT.md).

---

## Quick start

```bash
# Lean kernel (~20s, no dependencies beyond elan)
cd proofs && lake build

# Rust workspace (5 crates, 43 tests)
cd core && cargo test --workspace

# Python services + ML (30 tests)
cd services && python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest

# Hyperledger Fabric chaincode (9 tests)
cd integrations/dlt/fabric/chaincode && go test ./...

# Circom + Solidity EVM verifier (3 end-to-end tests)
cd integrations/dlt/evm && npm install
bash scripts/build.sh halal_n3 && bash scripts/test.sh

# Mathlib extensions (Phase B+, ~5 min cache-warmed)
cd proofs-mathlib && lake exe cache get && lake build

# Whitepaper
cd paper && latexmk -pdf main.tex
```

## What kinds of contributions are welcome

| Track | What's appreciated |
|---|---|
| **Theorems** | Closing `sorry`s; porting Phase B+ statements to mathlib; new lemmas tied to spec §X.Y. |
| **Crypto** | Phase C+ work — Poseidon parameter ceremony, PLONK on arkworks 0.4, STARK Poseidon-AIR. |
| **Spec** | Clarifications, schema fixes, conformance test cases. PRs must include a `spec/00-overview.md` §0.7 changelog entry. |
| **Adapters** | New certifier-API bindings (subject to each registry's ToS). |
| **ML** | Improved model architectures with measurable accuracy delta vs the v0.1 baseline on the synthetic test set, or evaluations on a redistribution-friendly real-data corpus. |
| **Bugs** | Always — file an issue or open a PR. |

## What kinds of contributions are NOT in scope

* **Juristic adjudication.** GHC formalizes the *propagation* of
  compliance status; the underlying juristic questions (e.g. the
  status of a particular E-number) are the prerogative of recognized
  Shariah authorities. PRs that argue jurisprudence are out of scope;
  PRs that codify an *authority's* documented position are welcome.
* **Vulnerability reports.** These go to the disclosure process in
  [SECURITY.md](SECURITY.md), not public issues.

## Conventions

### Branching

* Trunk: `main`.
* Feature branches: `<your-handle>/<short-topic>`.
* Don't push directly to `main`; open a PR.

### Commits

* Imperative-mood subject ≤ 72 chars; body wrapped at 72.
* Reference issues / theorem labels / spec sections where applicable.
* Include the trailer

  ```
  Signed-off-by: Your Name <you@example.com>
  ```

  (`git commit -s`) to certify the [DCO](https://developercertificate.org/).

### Code style

* **Rust**: `cargo fmt --all` + `cargo clippy --workspace --all-targets
  -- -D warnings` are CI-mandatory.
* **Python**: `ruff check .` is CI-mandatory. Use type hints; we run
  `mypy` in `dev` extras locally.
* **Go**: `gofmt` + `go vet` for the Fabric chaincode.
* **Lean 4**: 4-space indent; `lake build` is CI-mandatory; no
  `sorry`s in the kernel tree.
* **LaTeX**: paper must compile cleanly under `latexmk -pdf`.

### Spec changes

Any change to `spec/` that affects on-the-wire format, scheme tags,
verifier behavior, or normative language MUST:

1. Update the relevant section.
2. Add an entry to `spec/00-overview.md` §0.7 (Spec changelog).
3. Update affected JSON Schemas in `spec/schemas/`.
4. Update `CHANGELOG.md` under the next pending release.

### Tests

* New behavior comes with a test in the appropriate layer.
* Lean kernel additions require a `Smoke.lean` `#check`.
* Rust public functions: at least one unit or `proptest`.
* Python: pytest under `services/tests/`.
* Go: `_test.go` co-located.
* The runtime ↔ Lean correspondence is *intentional*: when adding a
  proven Lean theorem, mirror it as a Rust proptest if it applies at
  runtime.

## PR review process

1. Open the PR against `main`.
2. CI must pass: `rust`, `python`, `fabric`, `spec`, `lean-kernel`,
   `lean-mathlib`, `paper`, `evm`.
3. A maintainer (see [MAINTAINERS.md](MAINTAINERS.md)) reviews.
4. For changes touching `spec/`, the change goes through a public
   discussion period of **at least 7 days** before merge (see
   [GOVERNANCE.md](GOVERNANCE.md)).
5. Merge is by squash with a clean commit message.

## Filing issues

See the issue templates under `.github/ISSUE_TEMPLATE/`.
For runtime help (not bug reports), check [SUPPORT.md](SUPPORT.md).

## Licensing of contributions

Contributions to code are accepted under the dual **MIT OR
Apache-2.0**; contributions to the paper, spec, and notebooks under
**CC-BY-4.0**. Including a DCO sign-off (`git commit -s`) is sufficient
to certify the contribution under these terms.

---

Thank you. GHC is research-grade and the most valuable contribution
right now is sharp, specific feedback on the existing constructions
— especially from Shariah scholars, regulators, and ZK-pipeline
implementers.
