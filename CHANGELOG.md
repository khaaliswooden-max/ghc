# Changelog

All notable changes to GHC are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-05-05

First public release. The repository contains the full
substrate for Global Halal Compliance: machine-checked Lean 4
proofs (kernel + mathlib extensions), a Rust reference
implementation with zk-Halal Groth16 over BLS12-381, a Circom +
Solidity EVM verifier over BN254, real EPCIS 2.0 ↔ GHC
translation, six fixture-backed certifier adapters
(JAKIM, MUI/BPJPH, HFA, ESMA, SFDA, SMIIC), a Hyperledger Fabric
chaincode, and two trainable PyTorch ML pipelines (ingredient
classifier + supply-chain risk GNN). The whitepaper compiles
cleanly under `latexmk`.

### Phase summary

| Phase | Status | Highlights |
|------:|:-------|:-----------|
| A. Literature & corpus | done | `paper/bib/ghc.bib` seeded with halal-standards, category-theory, info-theory, quantum-statistical, graph-spectral, ZK, ML, and traceability sources. |
| B. Math kernel (Lean 4) | done | 36 theorems machine-checked in pure Lean 4: lattice laws, Halal-Closure Functor compositionality, deterministic survival, discrete najis closure, combinatorial spectral fingerprint, plurality recovery. |
| B+. Mathlib extensions | done | 10 theorems on top of mathlib4: density-matrix purity bounds `1/n ≤ Tr(ρ²) ≤ 1`, charpoly invariance under relabel, Chebyshev + Chernoff audit concentration, exponential survival under no-reinvention. |
| C. Rust core | done | `ghc-algebra` (29 tests), `ghc-graph` (5 tests), `ghc-zk` (8 tests, Groth16 over BLS12-381), `ghc-cli` (`ghc demo` end-to-end). |
| C+1. Poseidon commitment | done | Replace base-4 linear commitment with Poseidon-on-BLS12-381; `native_and_circuit_poseidon_agree` test guarantees byte-identity. |
| C+2. EVM verifier | done | Circom port over BN254; snarkjs-generated Solidity Groth16 verifier; `scripts/test.sh` asserts halal-only round trip + haram rejection + Solidity calldata export. |
| C+3. PLONK / STARK | open | Universal trusted setup + post-quantum variants. |
| D. Integrations | done | Six certifier adapters, real EPCIS 2.0 ↔ GHC mapping (3 event types), FastAPI gateway, Hyperledger Fabric chaincode (Go, 9 tests). |
| E. ML & datasets | done | `IngredientClassifier` (corpus + n-gram MLP, >0.9 val accuracy on synthetic data) + `SupplyChainRiskGNN` (custom message-passing, MAE < 0.20 + PR-AUC > 0.30 on synthetic data). |
| E+. Heavy ML | open | LayoutLMv3 + multilingual XLM-R for image-based label OCR; PyTorch-Geometric on real GDST traces. |
| F. Whitepaper + spec freeze | done | Paper compiles cleanly to PDF; spec marked v0.1.0; release packaged. |
| G. External review | open | Shariah-board review (AAOIFI / SMIIC consult); arXiv preprint; standards-body submission. |

### Numbers

* **Runtime tests passing.** 82 across all layers (Rust 53, Python 22,
  Go 9, Solidity/Circom 3 end-to-end + 5 Rust ZK proper).
* **Theorems machine-checked.** 46 (36 pure-Lean kernel + 10 mathlib
  extensions); zero `sorry`s, zero unsafe `axiom`s, both
  CI-enforced.
* **zk-Halal benchmarks** (release build, `n = 3`):
  * Off-chain (BLS12-381): setup 57 ms, prove 54 ms, verify 2.3 ms,
    proof 192 bytes.
  * On-chain (BN254): generated Solidity verifier; `scripts/test.sh`
    halal-only round trip succeeds, haram rejected at witness gen.

### Repository layout (frozen)

```
paper/         LaTeX whitepaper + bibliography (compiles to PDF)
spec/          GHC Protocol v0.1 — Markdown spec + JSON Schemas
proofs/        Lean 4 + mathlib4 formalization (kernel)
proofs-mathlib/  Phase B+ mathlib-backed extensions
core/          Rust workspace: algebra, ZK, graph spectra, CLI
services/      Python: API gateway, ML pipelines, EPCIS adapter
integrations/  Certifier adapters, GS1/EPCIS, DLT (Fabric + EVM)
datasets/      DVC manifests + license records
notebooks/     Reproducibility notebooks (papermill)
tools/         CI, release tooling, conformance suite
docs/          Project plan and design notes
vendor/        Vendored upstream references (git submodules)
```

### Breaking changes vs v0.0.x prereleases

* `ghc:scheme` enum tightened: `groth16-bls12-381` is now
  `groth16-bls12-381-poseidon`; `plonk-bn254` is now
  `plonk-bn254-poseidon`. v0.0.x clients MUST update their scheme
  tags or be rejected by the v0.1 verifier.
* Linear base-4 commitment replaced by Poseidon hash; v0.0.x proof
  artifacts are NOT compatible with v0.1 verifiers.
* `services/ghc_ml/{ocr,risk_gnn}.py` placeholder stubs removed in
  favour of the real `ingredient.py` and `risk.py`.

### Known gaps tracked for v0.2 / v0.3

* The Poseidon parameter set is sourced from arkworks'
  `bls381-fr` research constants; v0.2 will swap in parameters from
  a multi-party GHC trusted-setup ceremony.
* Mutual-information `C_h` (full Hoeffding bound `Pr ≤ 2^(C_h − nδ)`)
  needs a mutual-information formalization that mathlib does not
  yet ship.
* On-chain SNARK verification inside the Fabric chaincode (currently
  the chaincode validates the scheme tag and trusts off-chain
  verification by the issuer's public key signature).

[0.1.0]: https://github.com/khaaliswooden-max/ghc/releases/tag/v0.1.0
