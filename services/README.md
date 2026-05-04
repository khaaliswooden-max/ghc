# GHC Services

Python orchestration layer for GHC.

| Package | Purpose |
|---------|---------|
| `ghc_api`         | FastAPI gateway: VC issuance, attestation verification, federation. |
| `ghc_ml`          | PyTorch + HuggingFace pipelines (LayoutLMv3 OCR, GNN risk). |
| `ghc_traceability`| OpenEPCIS adapter; PROV-O / EPCIS 2.0 ↔ GHC mapping. |

## Install (dev)

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
```
