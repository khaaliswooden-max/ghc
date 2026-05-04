"""Supply-chain risk GNN — PyTorch Geometric.

Phase A stub: model class skeleton; trained checkpoints land in Phase E.
"""

from __future__ import annotations


class SupplyChainRiskGNN:
    """Placeholder for the heterogeneous-relational GNN risk model."""

    def __init__(self, hidden_dim: int = 128, num_layers: int = 3) -> None:
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

    def predict(self, _provenance_dag) -> float:  # noqa: ANN001
        """Return a [0,1] risk score for the given provenance DAG."""
        raise NotImplementedError("GNN training lands in Phase E.")
