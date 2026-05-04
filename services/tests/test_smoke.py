"""Smoke tests so CI has at least one green check from the services
package even before Phase D fills in real handlers."""

from fastapi.testclient import TestClient

from ghc_api.app import app


def test_healthz_returns_ok() -> None:
    client = TestClient(app)
    resp = client.get("/v1/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"]


def test_authorities_returns_list() -> None:
    client = TestClient(app)
    resp = client.get("/v1/authorities")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_attestation_issuance_is_not_implemented_yet() -> None:
    client = TestClient(app)
    resp = client.post(
        "/v1/attestations",
        json={"product_id": "urn:ghc:product:test", "authority_id": "urn:ghc:authority:test"},
    )
    assert resp.status_code == 501
