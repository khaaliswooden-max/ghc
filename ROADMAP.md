# GHC Roadmap

This is the externally-facing summary. The internal phase ledger
(weeks, file paths, commit hashes, blocking issues) lives in
[`docs/PLAN.md`](docs/PLAN.md); the per-release detail lives in
[`CHANGELOG.md`](CHANGELOG.md).

## Where we are: v0.1.0

* **Math kernel + mathlib extensions** — 46 theorems machine-checked
  in Lean 4 (36 pure-Lean kernel + 10 mathlib). Zero `sorry`s, zero
  unsafe axioms, CI-enforced.
* **Reference implementation** — Rust workspace (5 crates, 43
  tests), Python services + ML pipelines (30 tests), Go Fabric
  chaincode (9 tests), Circom + Solidity EVM verifier (3 end-to-end
  tests). The end-to-end zk-Halal demo proves and verifies in
  release build in ~110 ms with a 192-byte Groth16 proof over
  BLS12-381 and a parallel BN254 Solidity verifier.
* **Protocol spec** — frozen at v0.1.0 with a §0.7 changelog.
* **Whitepaper** — 15-page PDF, compiles cleanly under `latexmk`.

## What's next

The roadmap below is ordered by sequencing dependency, not by
priority. Multiple tracks run in parallel.

### v0.2 — security + maturation

| Track | Goal | Status |
|-------|------|--------|
| **Trusted-setup ceremony** | Multi-party Powers-of-Tau output replacing the v0.1 research Poseidon constants. Coordinated audit + public ceremony transcript. | open |
| **STARK round trip** (C+3a) | Move the all-halal constraint from the AIR into a Poseidon-hash equality computed inside the trace; close the winterfell degree-equality contract. Enable the three `#[ignore]`'d round-trip tests. | open |
| **PLONK** (C+3b) | Universal-setup variant. Either port `ark-marlin` to arkworks 0.4 or implement PLONK on `ark-poly-commit` 0.4. | open |
| **On-chain SNARK verification in Fabric** | Move SNARK verification from off-chain trust into the chaincode itself. | open |
| **Heavy mathlib** (C+) | Mutual-information `C_h` with the full Hoeffding survival bound; Hoeffding's lemma; Azuma-Hoeffding for martingales; spectral-theorem reduction connecting the diagonal-basis density-matrix purity bound to abstract Hermitian densities. | open |
| **Steward organization + governance** | Identify a foundation / consortium / standards body to take stewardship; ratify the v0.2 governance model in `GOVERNANCE.md`. | open |

### v0.3 — real-data ML

| Track | Goal | Status |
|-------|------|--------|
| **Image-based label OCR** (E++) | LayoutLMv3 + multilingual XLM-R for label OCR across Arabic, Malay, Urdu, Indonesian, English. Requires a licensed labeled multilingual image corpus. | open |
| **Real GDST evaluation** | Train the supply-chain risk GNN on real GDST traceability traces (replacing v0.1's synthetic-only data). Requires a redistribution-friendly license. | open |
| **Slaughter-video classification** | Phase E++ extension. | open |

### v1.0 — external review + standardization

| Track | Goal | Status |
|-------|------|--------|
| **Shariah-board review** (Phase G) | Engage AAOIFI, SMIIC, JAKIM, MUI/BPJPH for technical review. Encode dissents per §3.3 of the spec. | open |
| **arXiv preprint** | Submit the whitepaper. | open |
| **Standards-body submission** | OIC/SMIIC working-group submission; W3C VC schema annex; GS1 EPCIS halal-extension profile. | open |
| **Production deployment audits** | Third-party security audit of the cryptographic stack and the chaincode. | open |

## Things explicitly NOT on the roadmap

* **Adjudicating juristic questions.** GHC formalizes the
  propagation of compliance status; the underlying juristic
  questions remain the prerogative of recognized Shariah
  authorities. Encoding any one school of thought as canonical is
  not on any roadmap.
* **Surveillance / consumer profiling.** The point of zk-Halal is to
  prove compliance without exposing supplier identity, recipe, or
  audit history. Any feature that erodes those privacy properties
  is out of scope.
* **A consumer mobile app.** Out of scope for the protocol; a
  downstream community project would be welcome.

## How to influence the roadmap

* Open an issue with the `roadmap` label.
* For new tracks, attach a brief design sketch and the use case.
* For re-prioritization, link the dependencies you'd unblock.

The maintainers review roadmap issues monthly (cadence will be
ratified once a steward organization is named — see
[GOVERNANCE.md](GOVERNANCE.md)).
