"""Python mirror of `core/ghc-graph` types.

Used by `ghc_ml.risk` (the GNN takes Python `ProvenanceDag` objects)
and the API gateway. The Rust crate remains the source of truth for
spectral fingerprint computation; this module carries only the
trivially-mirrored data types.
"""

from .types import Edge, ProvenanceDag

__all__ = ["Edge", "ProvenanceDag"]
