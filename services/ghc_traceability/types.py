"""Common types shared across `ghc_api`, `ghc_ml`, `ghc_traceability`,
and `integrations/certifiers`.

These mirror the shape of `core/ghc-algebra::Verdict` and the JSON
artifacts the spec defines under `spec/schemas/`.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Verdict(str, Enum):
    """The compliance verdict lattice.

    Mirrors `Ghc.Verdict` (Lean) and `ghc_algebra::Verdict` (Rust).
    The `Ord` derivation in Rust matches the order here:
    `Halal < Mashbuh < Haram` (more restrictive comparison).
    """

    HALAL = "halal"
    MASHBUH = "mashbuh"
    HARAM = "haram"


class CertificateRecord(BaseModel):
    """A single record returned by a certifier registry."""

    model_config = ConfigDict(extra="allow")

    certificate_id: str = Field(..., description="Authority-issued ID.")
    authority_id: str = Field(..., description="GHC URN of the issuing authority.")
    subject_id: str = Field(..., description="The product/establishment certified.")
    subject_name: str = Field(..., description="Human-readable name.")
    verdict: Verdict = Field(default=Verdict.HALAL)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    raw: Optional[dict] = Field(
        default=None,
        description="Authority-specific raw record, kept for traceability.",
    )


class AuthorityDescriptor(BaseModel):
    """A Shariah authority known to the registry."""

    id: str
    name: str
    region: str
    scope: list[str]
    public_key: Optional[str] = None
