"""GHC FastAPI gateway.

Surfaces:
  POST /v1/attestations          issue a zk-Halal VC
  POST /v1/attestations/verify   verify a zk-Halal VC
  GET  /v1/authorities           list known Shariah authorities
  GET  /v1/healthz               liveness probe

Phase A ships only the surface; handlers return 501 until Phase D wires
in the real prover and registry adapters.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="GHC API",
    version="0.0.1",
    description="Global Halal Compliance reference gateway.",
)


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    version: str = "0.0.1"


class AttestationRequest(BaseModel):
    product_id: str = Field(..., description="URN of the product to attest.")
    authority_id: str = Field(..., description="URN of the issuing authority.")


class AttestationResponse(BaseModel):
    credential: dict


class VerifyRequest(BaseModel):
    credential: dict


class VerifyResponse(BaseModel):
    valid: bool
    reason: str | None = None


@app.get("/v1/healthz", response_model=HealthResponse, tags=["meta"])
async def healthz() -> HealthResponse:
    return HealthResponse()


@app.get("/v1/authorities", tags=["registry"])
async def list_authorities() -> list[dict]:
    # Phase D: pull from integrations/certifiers/.
    return []


@app.post(
    "/v1/attestations",
    response_model=AttestationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["attestation"],
)
async def issue_attestation(_req: AttestationRequest) -> AttestationResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="zk-Halal issuance lands in Phase C/D.",
    )


@app.post(
    "/v1/attestations/verify",
    response_model=VerifyResponse,
    tags=["attestation"],
)
async def verify_attestation(_req: VerifyRequest) -> VerifyResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="zk-Halal verification lands in Phase C/D.",
    )
