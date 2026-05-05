"""GHC FastAPI gateway.

Surfaces:
  GET  /v1/healthz                liveness probe
  GET  /v1/authorities            list known Shariah authorities
  GET  /v1/authorities/{id}/lookup?cert_id=...
                                  lookup a single certificate
  POST /v1/authorities/{id}/search
                                  search authority registry by query
  POST /v1/epcis/translate        EPCIS 2.0 → GHC document
  POST /v1/ghc/translate          GHC document → EPCIS 2.0 event
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

# Make `integrations.certifiers` importable from the services dir.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ghc_traceability.epcis import epcis_event_to_ghc, ghc_to_epcis_event  # noqa: E402
from ghc_traceability.types import AuthorityDescriptor, CertificateRecord  # noqa: E402
from integrations.certifiers import get_adapter, list_authorities  # noqa: E402

app = FastAPI(
    title="GHC API",
    version="0.0.1",
    description="Global Halal Compliance reference gateway.",
)


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.0.1"


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=25, ge=1, le=500)


class TranslateRequest(BaseModel):
    document: dict[str, Any]


class TranslateResponse(BaseModel):
    document: dict[str, Any]


@app.get("/v1/healthz", response_model=HealthResponse, tags=["meta"])
async def healthz() -> HealthResponse:
    return HealthResponse()


@app.get(
    "/v1/authorities",
    response_model=list[AuthorityDescriptor],
    tags=["registry"],
)
async def list_known_authorities() -> list[AuthorityDescriptor]:
    return list_authorities()


@app.get(
    "/v1/authorities/{authority_id}/lookup",
    response_model=Optional[CertificateRecord],
    tags=["registry"],
)
async def lookup(authority_id: str, cert_id: str = Query(..., min_length=1)):
    adapter = get_adapter(authority_id)
    if adapter is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"unknown authority: {authority_id}"
        )
    record = await adapter.lookup(cert_id)
    if record is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"no certificate {cert_id} at {authority_id}"
        )
    return record


@app.post(
    "/v1/authorities/{authority_id}/search",
    response_model=list[CertificateRecord],
    tags=["registry"],
)
async def search(authority_id: str, req: SearchRequest):
    adapter = get_adapter(authority_id)
    if adapter is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"unknown authority: {authority_id}"
        )
    return await adapter.search(req.query, limit=req.limit)


@app.post(
    "/v1/epcis/translate",
    response_model=TranslateResponse,
    tags=["epcis"],
)
async def translate_epcis_to_ghc(req: TranslateRequest) -> TranslateResponse:
    try:
        return TranslateResponse(document=epcis_event_to_ghc(req.document))
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@app.post(
    "/v1/ghc/translate",
    response_model=TranslateResponse,
    tags=["epcis"],
)
async def translate_ghc_to_epcis(req: TranslateRequest) -> TranslateResponse:
    try:
        return TranslateResponse(document=ghc_to_epcis_event(req.document))
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
