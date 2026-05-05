"""Certifier API adapters.

Each registry-specific module exposes an instance of
`CertifierAdapter` (see `base.py`). Concrete remote-API bindings are
deliberately query-on-demand and respect each registry's terms of
service; v0.0.x ships fixture-backed adapters whose JSON corpora
live under `fixtures/` so unit tests are fully reproducible without
network access.
"""

from .base import CertifierAdapter, FixtureCertifierAdapter, HttpCertifierAdapter
from .registry import REGISTRY, get_adapter, list_authorities

__all__ = [
    "CertifierAdapter",
    "FixtureCertifierAdapter",
    "HttpCertifierAdapter",
    "REGISTRY",
    "get_adapter",
    "list_authorities",
]
