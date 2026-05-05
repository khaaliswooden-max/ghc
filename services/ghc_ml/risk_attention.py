"""Attention-based supply-chain risk GNN — Phase E+.

A multi-head attention GNN over provenance DAGs that improves on the
mean-pool baseline (`ghc_ml.risk.SupplyChainRiskGNN`) by:

* Replacing fixed-weight sum aggregation with learned attention
  scores per (source, target) pair (GAT-style, Veličković et al.
  2018).
* Replacing mean-pool readout with attention-weighted readout that
  identifies critical nodes (e.g., the lowest-trust step in the
  chain).

Architecture (per-batch, ~12k parameters at hidden=32):
* Input projection: 4 features → 32 dims.
* 2× MultiHeadAttentionLayer (4 heads, hidden=32).
* AttentionReadout pooling.
* Linear head + sigmoid → risk in [0, 1].

Trains on the same synthetic dataset (`ghc_ml.data.synthetic.synthetic_dags`)
as the baseline; tests assert MAE < 0.15 (vs baseline MAE < 0.20),
i.e., a measurable accuracy improvement of ≥ 25%.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from ghc_graph.types import ProvenanceDag
from ghc_ml.risk import dag_to_tensors

NODE_FEATS = 4


class MultiHeadAttentionLayer(nn.Module):
    """GAT-style multi-head attention over edges with learned scores."""

    def __init__(self, dim_in: int, dim_out: int, heads: int = 4) -> None:
        super().__init__()
        assert dim_out % heads == 0, "dim_out must be divisible by heads"
        self.heads = heads
        self.head_dim = dim_out // heads
        self.q = nn.Linear(dim_in, dim_out)
        self.k = nn.Linear(dim_in, dim_out)
        self.v = nn.Linear(dim_in, dim_out)
        self.edge_bias = nn.Linear(1, heads)
        self.out = nn.Linear(dim_out, dim_out)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_weight: torch.Tensor,
    ) -> torch.Tensor:
        n = x.size(0)
        if edge_index.size(1) == 0:
            return F.elu(self.q(x))

        q = self.q(x).view(n, self.heads, self.head_dim)
        k = self.k(x).view(n, self.heads, self.head_dim)
        v = self.v(x).view(n, self.heads, self.head_dim)

        src, dst = edge_index[0], edge_index[1]
        # Per-edge attention score: dot-product + edge-weight bias.
        scale = self.head_dim**-0.5
        e_scores = (q[dst] * k[src]).sum(dim=-1) * scale  # (E, heads)
        w_norm = edge_weight / (edge_weight.max() + 1e-9)
        e_scores = e_scores + self.edge_bias(w_norm.unsqueeze(-1))

        # Softmax over incoming edges per destination node.
        max_per_dst = torch.zeros((n, self.heads), dtype=e_scores.dtype)
        max_per_dst.scatter_reduce_(0, dst.unsqueeze(-1).expand_as(e_scores), e_scores, reduce="amax", include_self=False)
        e_scores = e_scores - max_per_dst[dst]
        e_exp = torch.exp(e_scores)
        denom = torch.zeros((n, self.heads), dtype=e_exp.dtype)
        denom.index_add_(0, dst, e_exp)
        attn = e_exp / (denom[dst] + 1e-12)

        # Weighted value aggregation.
        msgs = v[src] * attn.unsqueeze(-1)
        agg = torch.zeros((n, self.heads, self.head_dim), dtype=msgs.dtype)
        agg.index_add_(0, dst, msgs)
        agg = agg.reshape(n, -1)
        return F.elu(self.out(agg) + self.q(x))


class AttentionReadout(nn.Module):
    """Attention-weighted pooling: learns which nodes matter most."""

    def __init__(self, dim: int) -> None:
        super().__init__()
        self.score = nn.Linear(dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        scores = self.score(x).squeeze(-1)
        weights = F.softmax(scores, dim=0)
        return (x * weights.unsqueeze(-1)).sum(dim=0)


class AttentionRiskGNN(nn.Module):
    """Attention GNN with feature projection, 2 MHA layers, readout."""

    def __init__(self, hidden: int = 32, heads: int = 4) -> None:
        super().__init__()
        self.proj = nn.Linear(NODE_FEATS, hidden)
        self.mha1 = MultiHeadAttentionLayer(hidden, hidden, heads)
        self.mha2 = MultiHeadAttentionLayer(hidden, hidden, heads)
        self.readout = AttentionReadout(hidden)
        self.head = nn.Linear(hidden, 1)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_weight: torch.Tensor,
    ) -> torch.Tensor:
        h = F.elu(self.proj(x))
        h = self.mha1(h, edge_index, edge_weight)
        h = self.mha2(h, edge_index, edge_weight)
        if h.size(0) == 0:
            return torch.tensor(0.0)
        pooled = self.readout(h)
        return torch.sigmoid(self.head(pooled)).squeeze(-1)


@dataclass
class AttentionRiskTrainStats:
    final_train_loss: float
    val_mae: float
    val_pr_auc: float


class AttentionRiskScorer:
    """High-level wrapper for the attention-based risk model."""

    def __init__(self, hidden: int = 32, heads: int = 4, seed: int = 0) -> None:
        torch.manual_seed(seed)
        self.net = AttentionRiskGNN(hidden=hidden, heads=heads)
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
        lr: float = 5e-3,
        val_frac: float = 0.2,
        seed: int = 0,
    ) -> AttentionRiskTrainStats:
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
        return AttentionRiskTrainStats(
            final_train_loss=last_loss,
            val_mae=val_mae,
            val_pr_auc=val_pr_auc,
        )


def trained_default_attention_scorer(seed: int = 0, n: int = 96) -> AttentionRiskScorer:
    from ghc_ml.data.synthetic import synthetic_dags

    samples = synthetic_dags(seed=seed, n=n)
    scorer = AttentionRiskScorer(seed=seed)
    scorer.train([(s.dag, s.risk) for s in samples])
    return scorer


def _binary_pr_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    if labels.sum() == 0 or labels.sum() == len(labels):
        return float(labels.mean())
    from sklearn.metrics import average_precision_score

    return float(average_precision_score(labels, scores))
