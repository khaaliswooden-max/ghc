# Certifier API Adapters

Query-on-demand adapters for the Shariah authorities GHC interoperates with.
Adapters MUST respect each registry's terms of service; bulk redistribution
is generally prohibited.

| Adapter | Authority | Region | Status |
|---------|-----------|--------|--------|
| `jakim/`  | Jabatan Kemajuan Islam Malaysia | Malaysia      | planned (Phase D) |
| `bpjph/`  | BPJPH (with MUI fatwa overlay)  | Indonesia     | planned (Phase D) |
| `hfa/`    | Halal Food Authority            | UK            | planned (Phase D) |
| `esma/`   | Emirates Authority for Standardization & Metrology | UAE | planned (Phase D) |
| `sfda/`   | Saudi Food and Drug Authority   | KSA           | planned (Phase D) |
| `smiic/`  | OIC/SMIIC                        | OIC global    | planned (Phase D) |

Each adapter exposes:

```python
class CertifierAdapter(Protocol):
    async def lookup(self, certificate_id: str) -> CertificateRecord | None: ...
    async def search(self, query: str, *, limit: int = 25) -> list[CertificateRecord]: ...
```

with `CertificateRecord` defined in `services/ghc_traceability/types.py`.
