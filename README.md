# Global Halal Compliance (GHC)

> A cross-domain unified protocol for halal compliance — food, pharma /
> cosmetics, Islamic finance, and logistics — backed by machine-checked
> proofs, information-theoretic contamination bounds, quantum-statistical
> provenance modeling, and zero-knowledge attestation.

**Status:** Phase A bootstrap. Empty‑repo seed.
The full plan lives in [`docs/PLAN.md`](docs/PLAN.md).

GHC is being developed as three coupled artifacts:

1. **Whitepaper** — `paper/` — academic monograph with formal proofs.
2. **Reference implementation** — `core/` (Rust), `services/` (Python),
   `proofs/` (Lean 4) — runs the pipeline end‑to‑end.
3. **Open protocol / spec** — `spec/` — versioned, schema‑backed standard
   that third parties can implement and certify against.

## Why deterministic?

Halal compliance today is largely qualitative ("reasonable precaution",
"trusted certifier"). GHC replaces qualitative judgments with a stack of
**verified, novel, quantitative** instruments:

| Layer | Instrument | Yields |
|------:|------------|--------|
| Semantics | Halal‑Closure Functor (category theory) | compositional ḥalāl/mashbūh/ḥarām status |
| Information | Contamination Channel Capacity `C_h` | bits/operation upper bound on haram‑signal survival |
| Physics | Najis Density Matrix `ρ_n` | scalar provenance‑purity score |
| Topology | Spectral provenance invariants | tamper‑evident DAG fingerprint |
| Crypto | zk‑Halal SNARK | privacy‑preserving compliance attestation |
| Statistics | Compliance Convergence Theorem | "how many audits are enough" with `O(1/√n)` rate |

Each instrument is mechanized in Lean 4 (`proofs/`), implemented in Rust
(`core/`) and Python (`services/`), and standardized in `spec/`.

## Layout

```
paper/         LaTeX whitepaper + bibliography
spec/          GHC Protocol — Markdown spec + JSON Schemas
proofs/        Lean 4 + mathlib4 formalization
core/          Rust workspace: algebra, ZK, graph spectra
services/      Python: API gateway, ML pipelines, EPCIS adapter
integrations/  Certifier APIs, GS1/EPCIS/GDST, DLT (Fabric / EVM)
datasets/      DVC manifests + license records
notebooks/     Reproducibility notebooks (papermill)
tools/         CI, release tooling, conformance suite
docs/          Project plan and design notes
vendor/        Vendored upstream references (git submodules)
```

## Getting started (when stubs are filled in)

```bash
make proofs    # lake build for Lean 4 theorems
make core      # cargo test --workspace
make services  # pytest in services/
make paper     # latexmk -pdf paper/main.tex
make spec      # validate JSON Schemas
make demo      # end-to-end traceability demo
```

## License

- Code (`core/`, `services/`, `proofs/`, `tools/`, `integrations/`):
  dual‑licensed **MIT OR Apache‑2.0**.
- Paper, spec, and notebooks: **CC‑BY‑4.0**.

See [`LICENSE`](LICENSE), [`LICENSE-MIT`](LICENSE-MIT),
[`LICENSE-APACHE`](LICENSE-APACHE), and per‑directory `LICENSE` files.

## Citation

See [`CITATION.cff`](CITATION.cff). When the v0.1 preprint lands, this
section will be updated with arXiv / DOI metadata.

## Contributing

GHC is research‑grade and pre‑v0.1. Issues and discussions are welcome;
substantive PRs should reference the relevant theorem / spec section. All
contributions are accepted under the dual MIT/Apache‑2.0 (code) or CC‑BY‑4.0
(prose) license.

## Vendored references

Reference implementations from Andrej Karpathy are pinned as git submodules
under `vendor/` for use by the ML pipelines in `services/` (and for general
study). Upstream history is preserved; we do not fork.

| Path | Upstream | Role |
| --- | --- | --- |
| `vendor/minGPT` | [karpathy/minGPT](https://github.com/karpathy/minGPT) | Clean PyTorch reference implementation; library-style `mingpt/` package with notebook demos. |
| `vendor/nanoGPT` | [karpathy/nanoGPT](https://github.com/karpathy/nanoGPT) | Single-file rewrite of minGPT; `train.py` reproduces GPT-2 on OpenWebText. |
| `vendor/build-nanogpt` | [karpathy/build-nanogpt](https://github.com/karpathy/build-nanogpt) | Companion to the "Let's reproduce GPT-2 (124M)" video; FineWeb prep + HellaSwag eval. |

After cloning:

```bash
git submodule update --init --recursive
# pull upstream updates:
git submodule update --remote vendor/nanoGPT
```
