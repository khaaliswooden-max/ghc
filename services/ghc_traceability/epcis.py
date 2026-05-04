"""OpenEPCIS adapter — translates EPCIS 2.0 events ↔ GHC data model."""

from __future__ import annotations

from typing import Any


def epcis_event_to_ghc(_event: dict[str, Any]) -> dict[str, Any]:
    """Translate an EPCIS 2.0 event into a GHC `Process` document.

    Phase D: real translation. v0.0.1 stub returns the input unchanged
    so downstream tests can exercise the call path.
    """
    return dict(_event)


def ghc_process_to_epcis(_process: dict[str, Any]) -> dict[str, Any]:
    """Inverse translation."""
    return dict(_process)
