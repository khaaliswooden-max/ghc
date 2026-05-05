"""Python mirror of `core/ghc-graph::Edge` / `ProvenanceDag`.

The Rust crate is the source of truth (it ships the spectral
fingerprint computation). This module carries only the data
shapes so Python tooling (the GNN, the API gateway) can take and
return DAGs without a CFFI/PyO3 dependency.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class Edge(BaseModel):
    """Mirrors `ghc_graph::Edge`."""

    source: int = Field(..., ge=0)
    target: int = Field(..., ge=0)
    weight: int = Field(..., gt=0)


class ProvenanceDag(BaseModel):
    """Mirrors `ghc_graph::ProvenanceDag`."""

    edges: List[Edge] = Field(default_factory=list)

    def nodes(self) -> set[int]:
        out: set[int] = set()
        for e in self.edges:
            out.add(e.source)
            out.add(e.target)
        return out
