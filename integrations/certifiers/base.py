"""Certifier adapter abstractions.

The `CertifierAdapter` protocol defines the minimal surface every
registry binding must implement. Two concrete implementations are
provided:

* `FixtureCertifierAdapter`: loads records from a local JSON corpus.
  Used in CI and for offline development.
* `HttpCertifierAdapter`: a reusable scaffold for binding registries
  that expose a documented REST/JSON API. Concrete adapters subclass
  it and implement `_lookup_url` / `_search_url` / `_parse_record`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

import httpx

from ghc_traceability.types import CertificateRecord


@runtime_checkable
class CertifierAdapter(Protocol):
    """Protocol every certifier adapter must satisfy."""

    authority_id: str
    """GHC URN of the issuing authority (e.g. `urn:ghc:authority:jakim`)."""

    async def lookup(self, certificate_id: str) -> Optional[CertificateRecord]:
        """Look up a single certificate by its authority-issued ID."""
        ...

    async def search(self, query: str, *, limit: int = 25) -> list[CertificateRecord]:
        """Search by name / subject. Adapters MAY rate-limit."""
        ...


class FixtureCertifierAdapter:
    """Adapter backed by a JSON fixture file.

    The fixture format is a JSON array of objects matching
    `CertificateRecord` (with optional `searchable_text` for the
    search filter). All searches are case-insensitive substring matches
    against the certificate ID, subject ID, subject name, and the
    optional `searchable_text` field.
    """

    def __init__(self, authority_id: str, fixture_path: Path) -> None:
        self.authority_id = authority_id
        self._records = self._load(fixture_path)

    @staticmethod
    def _load(fixture_path: Path) -> list[CertificateRecord]:
        if not fixture_path.exists():
            return []
        with fixture_path.open() as f:
            data = json.load(f)
        return [CertificateRecord.model_validate(r) for r in data]

    async def lookup(self, certificate_id: str) -> Optional[CertificateRecord]:
        return next(
            (r for r in self._records if r.certificate_id == certificate_id),
            None,
        )

    async def search(self, query: str, *, limit: int = 25) -> list[CertificateRecord]:
        q = query.strip().lower()
        if not q:
            return []
        out: list[CertificateRecord] = []
        for r in self._records:
            haystack = " ".join(
                [
                    r.certificate_id,
                    r.subject_id,
                    r.subject_name,
                    str((r.raw or {}).get("searchable_text", "")),
                ]
            ).lower()
            if q in haystack:
                out.append(r)
                if len(out) >= limit:
                    break
        return out


class HttpCertifierAdapter:
    """Reusable scaffold for HTTP-backed registry bindings.

    Subclasses MUST implement:

    * `_lookup_url(certificate_id) -> URL`
    * `_search_url(query, limit) -> URL`
    * `_parse_record(json_dict) -> CertificateRecord`

    and SHOULD set `default_headers` (e.g. `User-Agent`, `Accept`)
    appropriate to the registry. The generic implementation does NOT
    bulk-cache; every call hits the upstream registry.
    """

    authority_id: str
    base_url: str
    default_headers: dict[str, str]

    def __init__(
        self,
        *,
        authority_id: str,
        base_url: str,
        default_headers: Optional[dict[str, str]] = None,
        timeout_s: float = 10.0,
    ) -> None:
        self.authority_id = authority_id
        self.base_url = base_url.rstrip("/")
        self.default_headers = default_headers or {
            "User-Agent": "ghc-services/0.0.1",
            "Accept": "application/json",
        }
        self._timeout = timeout_s

    # Subclass hooks -----------------------------------------------------

    def _lookup_url(self, certificate_id: str) -> str:
        raise NotImplementedError

    def _search_url(self, query: str, limit: int) -> str:
        raise NotImplementedError

    def _parse_record(self, payload: dict) -> CertificateRecord:
        raise NotImplementedError

    # Default protocol implementation -----------------------------------

    async def lookup(self, certificate_id: str) -> Optional[CertificateRecord]:
        url = self._lookup_url(certificate_id)
        async with httpx.AsyncClient(timeout=self._timeout) as c:
            resp = await c.get(url, headers=self.default_headers)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return self._parse_record(resp.json())

    async def search(self, query: str, *, limit: int = 25) -> list[CertificateRecord]:
        url = self._search_url(query, limit)
        async with httpx.AsyncClient(timeout=self._timeout) as c:
            resp = await c.get(url, headers=self.default_headers)
        resp.raise_for_status()
        payload = resp.json()
        records = payload.get("records", payload) if isinstance(payload, dict) else payload
        return [self._parse_record(r) for r in records[:limit]]
