"""Smoke + integration tests for the API gateway, EPCIS adapter, and
fixture-backed certifier registry."""

from fastapi.testclient import TestClient

from ghc_api.app import app
from ghc_traceability.epcis import epcis_event_to_ghc, ghc_to_epcis_event

client = TestClient(app)


# ---- meta ----------------------------------------------------------------


def test_healthz_returns_ok() -> None:
    resp = client.get("/v1/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"]


# ---- authority registry --------------------------------------------------


def test_authorities_returns_six_known() -> None:
    resp = client.get("/v1/authorities")
    assert resp.status_code == 200
    body = resp.json()
    ids = {a["id"] for a in body}
    assert ids == {
        "urn:ghc:authority:jakim",
        "urn:ghc:authority:mui",
        "urn:ghc:authority:hfa",
        "urn:ghc:authority:esma",
        "urn:ghc:authority:sfda",
        "urn:ghc:authority:smiic",
    }


def test_lookup_jakim_known_certificate() -> None:
    resp = client.get(
        "/v1/authorities/urn:ghc:authority:jakim/lookup",
        params={"cert_id": "JAKIM-MS1500-2026-00042"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["certificate_id"] == "JAKIM-MS1500-2026-00042"
    assert body["verdict"] == "halal"


def test_lookup_unknown_authority_returns_404() -> None:
    resp = client.get(
        "/v1/authorities/urn:ghc:authority:nope/lookup",
        params={"cert_id": "x"},
    )
    assert resp.status_code == 404


def test_lookup_unknown_certificate_returns_404() -> None:
    resp = client.get(
        "/v1/authorities/urn:ghc:authority:jakim/lookup",
        params={"cert_id": "DOES-NOT-EXIST"},
    )
    assert resp.status_code == 404


def test_search_jakim_substring() -> None:
    resp = client.post(
        "/v1/authorities/urn:ghc:authority:jakim/search",
        json={"query": "pelangi", "limit": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) >= 1
    assert all(
        "pelangi" in (r["subject_name"].lower() + str(r.get("raw", "")).lower())
        for r in body
    )


# ---- EPCIS adapter -------------------------------------------------------


def test_epcis_object_event_translates_to_batch() -> None:
    epcis = {
        "type": "ObjectEvent",
        "eventTime": "2026-05-04T12:00:00Z",
        "epcList": ["urn:epc:id:sgtin:beef-shoulder-batch-7c1a"],
        "action": "OBSERVE",
        "bizStep": "urn:epcglobal:cbv:bizstep:inspecting",
        "disposition": "https://ghc.example/disposition/halal",
    }
    ghc = epcis_event_to_ghc(epcis)
    assert ghc["@type"] == "ghc:Batch"
    assert ghc["compliance"]["lattice"] == "halal"


def test_epcis_transformation_event_translates_to_process() -> None:
    epcis = {
        "type": "TransformationEvent",
        "eventID": "urn:ghc:process:42b9",
        "eventTime": "2026-05-04T13:00:00Z",
        "inputEPCList": ["urn:epc:id:sgtin:input1"],
        "outputEPCList": ["urn:epc:id:sgtin:output1"],
        "bizStep": "https://ghc.example/bizstep/cleaning/CIP-3",
    }
    ghc = epcis_event_to_ghc(epcis)
    assert ghc["@type"] == "ghc:Process"
    assert ghc["operation"] == "ghc:op/cleaning/CIP-3"
    assert len(ghc["inputs"]) == 1
    assert len(ghc["outputs"]) == 1


def test_ghc_batch_to_epcis_object_event_roundtrip() -> None:
    ghc = {
        "@type": "ghc:Batch",
        "@id": "urn:ghc:batch:bf2e",
        "ingredient": "urn:ghc:ingredient:beef-shoulder",
        "quantity": {"value": 250.0, "unit": "kg"},
        "compliance": {
            "lattice": "halal",
            "authority": "urn:ghc:authority:jakim",
        },
        "epcis:eventTime": "2026-05-04T12:00:00Z",
    }
    epcis = ghc_to_epcis_event(ghc)
    assert epcis["type"] == "ObjectEvent"
    assert epcis["disposition"] == "https://ghc.example/disposition/halal"
    # Roundtrip lattice survives.
    back = epcis_event_to_ghc(epcis)
    assert back["compliance"]["lattice"] == "halal"


def test_ghc_process_to_epcis_transformation_event_roundtrip() -> None:
    ghc = {
        "@type": "ghc:Process",
        "@id": "urn:ghc:process:t1",
        "operation": "ghc:op/cleaning/CIP-3",
        "inputs": ["urn:ghc:batch:a"],
        "outputs": ["urn:ghc:batch:b"],
        "epcis:eventTime": "2026-05-04T14:00:00Z",
    }
    epcis = ghc_to_epcis_event(ghc)
    assert epcis["type"] == "TransformationEvent"
    assert epcis["bizStep"].endswith("cleaning/CIP-3")
    back = epcis_event_to_ghc(epcis)
    assert back["@type"] == "ghc:Process"
    assert back["operation"] == "ghc:op/cleaning/CIP-3"


# ---- API translate endpoints ---------------------------------------------


def test_api_epcis_translate_endpoint() -> None:
    resp = client.post(
        "/v1/epcis/translate",
        json={
            "document": {
                "type": "ObjectEvent",
                "eventTime": "2026-05-04T12:00:00Z",
                "epcList": ["urn:epc:id:sgtin:abc"],
                "action": "OBSERVE",
                "bizStep": "urn:epcglobal:cbv:bizstep:inspecting",
                "disposition": "https://ghc.example/disposition/mashbuh",
            }
        },
    )
    assert resp.status_code == 200
    out = resp.json()["document"]
    assert out["@type"] == "ghc:Batch"
    assert out["compliance"]["lattice"] == "mashbuh"
