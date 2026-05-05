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
  POST /v1/ml/ingredient          classify an ingredient string
  POST /v1/ml/risk                score a provenance DAG
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

# Make `integrations.certifiers` importable from the services dir.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ghc_graph.types import ProvenanceDag  # noqa: E402
from ghc_ml.ingredient import IngredientClassifier, trained_default_classifier  # noqa: E402
from ghc_ml.risk import RiskScorer, trained_default_scorer  # noqa: E402
from ghc_traceability.epcis import epcis_event_to_ghc, ghc_to_epcis_event  # noqa: E402
from ghc_traceability.types import (  # noqa: E402
    AuthorityDescriptor,
    CertificateRecord,
    Verdict,
)
from integrations.certifiers import get_adapter, list_authorities  # noqa: E402

app = FastAPI(
    title="GHC API",
    version="0.1.0",
    description="Global Halal Compliance reference gateway.",
)


# --- Lazy ML model loaders --------------------------------------------------


_INGREDIENT_CLASSIFIER: IngredientClassifier | None = None
_RISK_SCORER: RiskScorer | None = None


def _ingredient_clf() -> IngredientClassifier:
    global _INGREDIENT_CLASSIFIER
    if _INGREDIENT_CLASSIFIER is None:
        _INGREDIENT_CLASSIFIER = trained_default_classifier(seed=0, n=256)
    return _INGREDIENT_CLASSIFIER


def _risk_scorer() -> RiskScorer:
    global _RISK_SCORER
    if _RISK_SCORER is None:
        _RISK_SCORER = trained_default_scorer(seed=0, n=96)
    return _RISK_SCORER


# --- Schemas ----------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=25, ge=1, le=500)


class TranslateRequest(BaseModel):
    document: dict[str, Any]


class TranslateResponse(BaseModel):
    document: dict[str, Any]


class IngredientRequest(BaseModel):
    text: str = Field(..., min_length=1)


class IngredientResponse(BaseModel):
    verdict: Verdict
    reason: str


class RiskRequest(BaseModel):
    dag: ProvenanceDag


class RiskResponse(BaseModel):
    risk: float = Field(..., ge=0.0, le=1.0)


# --- Endpoints --------------------------------------------------------------


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


@app.post(
    "/v1/ml/ingredient",
    response_model=IngredientResponse,
    tags=["ml"],
)
async def classify_ingredient(req: IngredientRequest) -> IngredientResponse:
    verdict, reason = _ingredient_clf().classify(req.text)
    return IngredientResponse(verdict=verdict, reason=reason)


@app.post(
    "/v1/ml/risk",
    response_model=RiskResponse,
    tags=["ml"],
)
async def score_risk(req: RiskRequest) -> RiskResponse:
    return RiskResponse(risk=_risk_scorer().score(req.dag))
