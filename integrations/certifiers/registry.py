"""GHC's known-authority registry.

Each entry pairs an `AuthorityDescriptor` with a default
`CertifierAdapter`. v0.0.x ships fixture-backed adapters; production
deployments override `REGISTRY` with HTTP-backed adapters at startup.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ghc_traceability.types import AuthorityDescriptor

from .base import CertifierAdapter, FixtureCertifierAdapter

_FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _fixture(name: str, authority_id: str) -> CertifierAdapter:
    return FixtureCertifierAdapter(authority_id, _FIXTURES / f"{name}.json")


_AUTHORITIES: list[AuthorityDescriptor] = [
    AuthorityDescriptor(
        id="urn:ghc:authority:jakim",
        name="Jabatan Kemajuan Islam Malaysia (JAKIM)",
        region="Malaysia",
        scope=["food", "cosmetics", "pharma"],
    ),
    AuthorityDescriptor(
        id="urn:ghc:authority:mui",
        name="Lembaga Pengkajian Pangan Obat-obatan dan Kosmetika MUI (BPJPH/MUI)",
        region="Indonesia",
        scope=["food", "cosmetics", "pharma"],
    ),
    AuthorityDescriptor(
        id="urn:ghc:authority:hfa",
        name="Halal Food Authority",
        region="United Kingdom",
        scope=["food"],
    ),
    AuthorityDescriptor(
        id="urn:ghc:authority:esma",
        name="Emirates Authority for Standardization and Metrology",
        region="United Arab Emirates",
        scope=["food", "cosmetics"],
    ),
    AuthorityDescriptor(
        id="urn:ghc:authority:sfda",
        name="Saudi Food and Drug Authority",
        region="Saudi Arabia",
        scope=["food", "pharma"],
    ),
    AuthorityDescriptor(
        id="urn:ghc:authority:smiic",
        name="Standards and Metrology Institute for Islamic Countries",
        region="OIC global",
        scope=["food", "cosmetics", "pharma", "logistics"],
    ),
]


REGISTRY: dict[str, CertifierAdapter] = {
    "urn:ghc:authority:jakim": _fixture("jakim", "urn:ghc:authority:jakim"),
    "urn:ghc:authority:mui":   _fixture("mui",   "urn:ghc:authority:mui"),
    "urn:ghc:authority:hfa":   _fixture("hfa",   "urn:ghc:authority:hfa"),
    "urn:ghc:authority:esma":  _fixture("esma",  "urn:ghc:authority:esma"),
    "urn:ghc:authority:sfda":  _fixture("sfda",  "urn:ghc:authority:sfda"),
    "urn:ghc:authority:smiic": _fixture("smiic", "urn:ghc:authority:smiic"),
}


def list_authorities() -> list[AuthorityDescriptor]:
    return _AUTHORITIES


def get_adapter(authority_id: str) -> Optional[CertifierAdapter]:
    return REGISTRY.get(authority_id)
