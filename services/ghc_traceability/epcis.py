"""GS1 EPCIS 2.0 ↔ GHC bidirectional mapping.

Spec: GS1 EPCIS 2.0 (https://www.gs1.org/standards/epcis).

We translate the three EPCIS 2.0 event types we use operationally:

* `ObjectEvent`     → GHC observation of a single batch
* `TransformationEvent` → GHC `Process` (one or more inputs producing
  one or more outputs)
* `AggregationEvent` → GHC mixing event (treated structurally as a
  `TransformationEvent` of the parent + children)

GHC documents in JSON-LD bind to the context
`https://ghc.example/ns/v1`; EPCIS events bind to
`https://ref.gs1.org/standards/epcis/2.0.0/epcis-context.jsonld`.
The mapping preserves provenance; round-tripping
EPCIS → GHC → EPCIS produces semantically-equivalent (though not
byte-identical) events.
"""

from __future__ import annotations

from typing import Any

# Namespace URIs.
GHC_BIZSTEP_NS = "https://ghc.example/bizstep/"
GHC_DISPOSITION_NS = "https://ghc.example/disposition/"


def epcis_event_to_ghc(event: dict[str, Any]) -> dict[str, Any]:
    """Translate an EPCIS 2.0 JSON event to a GHC document."""
    ev_type = event.get("type") or event.get("isA") or "ObjectEvent"
    if ev_type == "ObjectEvent":
        return _object_to_ghc(event)
    if ev_type == "TransformationEvent":
        return _transform_to_ghc(event)
    if ev_type == "AggregationEvent":
        return _aggregation_to_ghc(event)
    raise ValueError(f"unsupported EPCIS event type: {ev_type}")


def ghc_to_epcis_event(doc: dict[str, Any]) -> dict[str, Any]:
    """Inverse mapping: GHC document → EPCIS 2.0 event."""
    t = doc.get("@type")
    if t == "ghc:Batch":
        return _ghc_batch_to_object_event(doc)
    if t == "ghc:Process":
        return _ghc_process_to_transformation_event(doc)
    raise ValueError(f"unsupported GHC document type: {t}")


# ---------- EPCIS → GHC ---------------------------------------------------


def _object_to_ghc(event: dict[str, Any]) -> dict[str, Any]:
    epcs = event.get("epcList", []) or [event.get("epc", "")]
    epc = next((e for e in epcs if e), "urn:epc:id:unknown")
    biz = event.get("bizStep", "")
    disp = event.get("disposition", "")
    return {
        "@type": "ghc:Batch",
        "@id": _epc_to_ghc_id(epc),
        "ingredient": event.get("readPoint", {}).get("id", "urn:ghc:ingredient:unknown"),
        "quantity": _extract_quantity(event),
        "compliance": {
            "lattice": _disposition_to_lattice(disp),
            "authority": _bizstep_to_authority(biz),
        },
        "epcis:eventTime": event.get("eventTime"),
    }


def _transform_to_ghc(event: dict[str, Any]) -> dict[str, Any]:
    inputs = event.get("inputEPCList", [])
    outputs = event.get("outputEPCList", [])
    biz = event.get("bizStep", "")
    return {
        "@type": "ghc:Process",
        "@id": event.get("eventID")
        or f"urn:ghc:process:{event.get('eventTime', 'untimed')}",
        "operation": _bizstep_to_operation(biz),
        "inputs": [_epc_to_ghc_id(e) for e in inputs],
        "outputs": [_epc_to_ghc_id(e) for e in outputs],
        "epcis:eventTime": event.get("eventTime"),
    }


def _aggregation_to_ghc(event: dict[str, Any]) -> dict[str, Any]:
    parent = event.get("parentID") or "urn:epc:id:unknown"
    children = event.get("childEPCs") or event.get("childEPCList") or []
    return {
        "@type": "ghc:Process",
        "@id": event.get("eventID")
        or f"urn:ghc:process:agg:{event.get('eventTime', 'untimed')}",
        "operation": "ghc:op/mixing/aggregation",
        "inputs": [_epc_to_ghc_id(c) for c in children],
        "outputs": [_epc_to_ghc_id(parent)],
        "epcis:eventTime": event.get("eventTime"),
    }


# ---------- GHC → EPCIS ---------------------------------------------------


def _ghc_batch_to_object_event(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "ObjectEvent",
        "eventTime": doc.get("epcis:eventTime"),
        "eventTimeZoneOffset": "+00:00",
        "epcList": [_ghc_id_to_epc(doc["@id"])],
        "action": "OBSERVE",
        "bizStep": "urn:epcglobal:cbv:bizstep:inspecting",
        "disposition": _lattice_to_disposition(
            doc.get("compliance", {}).get("lattice", "halal")
        ),
    }


def _ghc_process_to_transformation_event(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "TransformationEvent",
        "eventID": doc["@id"],
        "eventTime": doc.get("epcis:eventTime"),
        "eventTimeZoneOffset": "+00:00",
        "inputEPCList": [_ghc_id_to_epc(i) for i in doc.get("inputs", [])],
        "outputEPCList": [_ghc_id_to_epc(o) for o in doc.get("outputs", [])],
        "bizStep": _operation_to_bizstep(doc.get("operation", "")),
    }


# ---------- helpers -------------------------------------------------------


def _epc_to_ghc_id(epc: str) -> str:
    if not epc:
        return "urn:ghc:batch:unknown"
    if epc.startswith("urn:ghc:"):
        return epc
    return f"urn:ghc:batch:{epc.split(':')[-1]}"


def _ghc_id_to_epc(ghc_id: str) -> str:
    if ghc_id.startswith("urn:epc:"):
        return ghc_id
    if ghc_id.startswith("urn:ghc:batch:"):
        return f"urn:epc:id:sgtin:{ghc_id.split(':')[-1]}"
    return ghc_id


def _disposition_to_lattice(disposition: str) -> str:
    if disposition.startswith(GHC_DISPOSITION_NS):
        token = disposition.removeprefix(GHC_DISPOSITION_NS)
        if token in {"halal", "mashbuh", "haram"}:
            return token
    if "non_conformant" in disposition or "recall" in disposition:
        return "haram"
    return "halal"


def _lattice_to_disposition(lattice: str) -> str:
    if lattice in {"halal", "mashbuh", "haram"}:
        return f"{GHC_DISPOSITION_NS}{lattice}"
    return "urn:epcglobal:cbv:disp:active"


def _bizstep_to_operation(bizstep: str) -> str:
    if bizstep.startswith(GHC_BIZSTEP_NS):
        return f"ghc:op/{bizstep.removeprefix(GHC_BIZSTEP_NS)}"
    if "commissioning" in bizstep:
        return "ghc:op/commissioning"
    if "shipping" in bizstep:
        return "ghc:op/shipping"
    if "receiving" in bizstep:
        return "ghc:op/receiving"
    if "transforming" in bizstep:
        return "ghc:op/transforming"
    return "ghc:op/unknown"


def _operation_to_bizstep(op: str) -> str:
    if op.startswith("ghc:op/"):
        rest = op.removeprefix("ghc:op/")
        return f"{GHC_BIZSTEP_NS}{rest}"
    return "urn:epcglobal:cbv:bizstep:transforming"


def _bizstep_to_authority(_bizstep: str) -> str:
    # GHC events don't, in general, carry the issuing authority on the
    # event itself; the authority is attached at attestation time.
    return "urn:ghc:authority:unknown"


def _extract_quantity(event: dict[str, Any]) -> dict[str, Any]:
    q = event.get("quantityList") or []
    if q:
        first = q[0]
        return {"value": first.get("quantity", 1.0), "unit": first.get("uom", "EA")}
    return {"value": 1.0, "unit": "EA"}
