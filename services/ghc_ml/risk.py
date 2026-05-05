"""Supply-chain risk GNN.

A PyTorch message-passing GNN that consumes a `ProvenanceDag` and
emits a scalar risk score in `[0, 1]`. Operates on edge weights
plus per-node aggregates (degree-in, degree-out, total-incoming
weight, total-outgoing weight) — features that mirror the spectral
fingerprint substrate from `core/ghc-graph`.

We implement the message-passing layers from scratch (no
`torch_geometric` dependency) so CI stays light. The model is
deliberately small (~3k parameters) and converges on synthetic
data in seconds. Real-data fine-tuning on GDST traces is
Phase E+ work.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from ghc_graph.types import ProvenanceDag

NODE_FEATS = 4  # in_deg, out_deg, in_w, out_w


def dag_to_tensors(dag: ProvenanceDag) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Compute (node_features, edge_index, edge_weight) tensors for a
    DAG. Node ids are remapped to a contiguous 0..n-1 range."""
    nodes = sorted(dag.nodes()) or [0]
    idx = {n: i for i, n in enumerate(nodes)}
    n = len(nodes)
    in_deg = np.zeros(n, dtype=np.float32)
    out_deg = np.zeros(n, dtype=np.float32)
    in_w = np.zeros(n, dtype=np.float32)
    out_w = np.zeros(n, dtype=np.float32)
    src = []
    dst = []
    weights = []
    for e in dag.edges:
        s, t = idx[e.source], idx[e.target]
        out_deg[s] += 1.0
        in_deg[t] += 1.0
        out_w[s] += float(e.weight)
        in_w[t] += float(e.weight)
        src.append(s)
        dst.append(t)
        weights.append(float(e.weight))
    feats = np.stack([in_deg, out_deg, np.log1p(in_w), np.log1p(out_w)], axis=1)
    edge_index = (
        torch.tensor([src, dst], dtype=torch.long)
        if src
        else torch.zeros((2, 0), dtype=torch.long)
    )
    edge_w = (
        torch.tensor(weights, dtype=torch.float32)
        if weights
        else torch.zeros((0,), dtype=torch.float32)
    )
    return torch.from_numpy(feats), edge_index, edge_w


class MessagePassingLayer(nn.Module):
    """One layer of a weighted-edge GCN-style update."""

    def __init__(self, dim_in: int, dim_out: int) -> None:
        super().__init__()
        self.lin_self = nn.Linear(dim_in, dim_out)
        self.lin_msg = nn.Linear(dim_in, dim_out)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_weight: torch.Tensor,
    ) -> torch.Tensor:
        n = x.size(0)
        out = self.lin_self(x)
        if edge_index.size(1) == 0:
            return F.relu(out)
        src, dst = edge_index[0], edge_index[1]
        # Normalize edge weights so they don't dominate by scale.
        w = edge_weight / (edge_weight.max() + 1e-9)
        msgs = self.lin_msg(x[src]) * w.unsqueeze(-1)
        # Sum aggregation into destination nodes.
        agg = torch.zeros((n, msgs.size(-1)), dtype=msgs.dtype)
        agg.index_add_(0, dst, msgs)
        return F.relu(out + agg)


class SupplyChainRiskGNN(nn.Module):
    """Two message-passing layers + mean-pool readout + linear head."""

    def __init__(self, hidden: int = 16, layers: int = 2) -> None:
        super().__init__()
        dims = [NODE_FEATS] + [hidden] * layers
        self.mp = nn.ModuleList(
            [MessagePassingLayer(dims[i], dims[i + 1]) for i in range(layers)]
        )
        self.head = nn.Linear(hidden, 1)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_weight: torch.Tensor,
    ) -> torch.Tensor:
        h = x
        for layer in self.mp:
            h = layer(h, edge_index, edge_weight)
        pooled = h.mean(dim=0) if h.size(0) > 0 else h.new_zeros(h.size(-1))
        return torch.sigmoid(self.head(pooled)).squeeze(-1)


@dataclass
class RiskTrainStats:
    final_train_loss: float
    val_mae: float
    val_pr_auc: float


class RiskScorer:
    """High-level wrapper handling featurization, training, scoring."""

    def __init__(self, hidden: int = 16, layers: int = 2, seed: int = 0) -> None:
        torch.manual_seed(seed)
        self.net = SupplyChainRiskGNN(hidden=hidden, layers=layers)
        self.net.eval()

    def score(self, dag: ProvenanceDag) -> float:
        with torch.no_grad():
            x, ei, ew = dag_to_tensors(dag)
            return float(self.net(x, ei, ew).item())

    def train(
        self,
        samples: List[tuple[ProvenanceDag, float]],
        *,
        epochs: int = 80,
        lr: float = 5e-2,
        val_frac: float = 0.2,
        seed: int = 0,
    ) -> RiskTrainStats:
        rng = np.random.default_rng(seed)
        idx = rng.permutation(len(samples))
        n_val = max(1, int(len(samples) * val_frac))
        train = [samples[i] for i in idx[n_val:]]
        val = [samples[i] for i in idx[:n_val]]

        opt = torch.optim.Adam(self.net.parameters(), lr=lr)
        self.net.train()
        last_loss = float("nan")
        for _ in range(epochs):
            losses = []
            for dag, y in train:
                x, ei, ew = dag_to_tensors(dag)
                pred = self.net(x, ei, ew)
                target = torch.tensor(y, dtype=torch.float32)
                loss = F.mse_loss(pred, target)
                opt.zero_grad()
                loss.backward()
                opt.step()
                losses.append(float(loss.item()))
            last_loss = float(np.mean(losses)) if losses else float("nan")

        self.net.eval()
        with torch.no_grad():
            preds = np.array([self.score(d) for d, _ in val])
            ys = np.array([y for _, y in val])
        val_mae = float(np.mean(np.abs(preds - ys)))
        val_pr_auc = _binary_pr_auc(preds, (ys > 0.5).astype(int))
        return RiskTrainStats(
            final_train_loss=last_loss,
            val_mae=val_mae,
            val_pr_auc=val_pr_auc,
        )


def trained_default_scorer(seed: int = 0, n: int = 96) -> RiskScorer:
    from ghc_ml.data.synthetic import synthetic_dags

    samples = synthetic_dags(seed=seed, n=n)
    scorer = RiskScorer(seed=seed)
    scorer.train([(s.dag, s.risk) for s in samples])
    return scorer


# --- Metrics --------------------------------------------------------------


def _binary_pr_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Compute PR-AUC. If all labels are the same class, returns the
    base rate (which is the "no skill" line)."""
    if labels.sum() == 0 or labels.sum() == len(labels):
        return float(labels.mean())
    from sklearn.metrics import average_precision_score

    return float(average_precision_score(labels, scores))
