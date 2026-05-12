"""Sequence-aware ingredient classifier — Phase E+.

The v0.1 baseline (`ghc_ml.ingredient.IngredientClassifier`) uses a
bag-of-character-n-grams MLP. This module adds a **GRU-based
sequence model** that handles word order and multi-token ingredients
("rice flour" ≠ "rice" + "flour"), and ensembles it with the corpus
arm (which remains the deterministic ground truth on known tokens).

Architecture (~30k parameters):
* Word-level vocabulary: 1024 hashed slots.
* Embedding: 32 dims.
* Bidirectional GRU: 1 layer, hidden 32 (so 64 forward+backward).
* Linear head: 64 → 3.

Trains on the same synthetic corpus as the baseline; tests assert
val accuracy ≥ 0.95 (vs baseline's 0.90), demonstrating that the
sequence model captures structure the n-gram MLP misses.

Phase E++ swaps the GRU for a small pretrained transformer
(distilbert / xlm-roberta-base) once the labeled multilingual
corpus is licensed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import torch
import torch.nn as nn

from ghc_ml.data.corpus import keyword_verdict, lookup_e_number
from ghc_ml.ingredient import INDEX_VERDICT, VERDICT_INDEX
from ghc_traceability.types import Verdict

VOCAB_SIZE = 1024
PAD_IDX = 0


def _tokenize(text: str) -> List[int]:
    """Whitespace + comma tokenization with hashed indices.

    Token 0 is reserved for padding.
    """
    text = text.lower().replace(",", " ").replace(".", " ")
    tokens = [t for t in text.split() if t]
    return [(hash(t) % (VOCAB_SIZE - 1)) + 1 for t in tokens]


def _pad(seqs: List[List[int]]) -> torch.Tensor:
    max_len = max((len(s) for s in seqs), default=1)
    out = torch.zeros((len(seqs), max(max_len, 1)), dtype=torch.long)
    for i, s in enumerate(seqs):
        if s:
            out[i, : len(s)] = torch.tensor(s, dtype=torch.long)
    return out


class IngredientSeqNet(nn.Module):
    """Embedding + bi-GRU + linear head."""

    def __init__(self, vocab_size: int = VOCAB_SIZE, emb: int = 32, hidden: int = 32) -> None:
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb, padding_idx=PAD_IDX)
        self.gru = nn.GRU(emb, hidden, batch_first=True, bidirectional=True)
        self.head = nn.Linear(hidden * 2, 3)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        e = self.emb(x)
        out, h = self.gru(e)
        # Concatenate last hidden state of both directions.
        last = torch.cat([h[0], h[1]], dim=-1)
        return self.head(last)


@dataclass
class SeqTrainStats:
    final_train_loss: float
    final_train_accuracy: float
    val_accuracy: float


class IngredientSeqClassifier:
    """Corpus arm + GRU sequence model fallback."""

    def __init__(self, emb: int = 32, hidden: int = 32, seed: int = 0) -> None:
        torch.manual_seed(seed)
        self.net = IngredientSeqNet(emb=emb, hidden=hidden)
        self.net.eval()

    def classify(self, text: str) -> Tuple[Verdict, str]:
        # Corpus arm first (same as baseline).
        for token in text.replace(",", " ").split():
            v = lookup_e_number(token)
            if v is not None:
                return v, f"corpus:e_number:{token.upper()}"
        v = keyword_verdict(text)
        if v is not None:
            return v, "corpus:keyword"
        # Sequence model fallback.
        with torch.no_grad():
            x = _pad([_tokenize(text)])
            logits = self.net(x)
            idx = int(logits.argmax(dim=-1).item())
        return INDEX_VERDICT[idx], "sequence"

    def train(
        self,
        samples: List[Tuple[str, Verdict]],
        *,
        epochs: int = 30,
        lr: float = 5e-3,
        batch: int = 32,
        val_frac: float = 0.2,
        seed: int = 0,
    ) -> SeqTrainStats:
        rng = np.random.default_rng(seed)
        idx = rng.permutation(len(samples))
        n_val = max(1, int(len(samples) * val_frac))
        train = [samples[i] for i in idx[n_val:]]
        val = [samples[i] for i in idx[:n_val]]

        train_seqs = [_tokenize(t) for t, _ in train]
        train_y = torch.tensor([VERDICT_INDEX[v] for _, v in train], dtype=torch.long)
        val_seqs = [_tokenize(t) for t, _ in val]
        val_y = torch.tensor([VERDICT_INDEX[v] for _, v in val], dtype=torch.long)

        self.net.train()
        opt = torch.optim.Adam(self.net.parameters(), lr=lr)
        loss_fn = nn.CrossEntropyLoss()
        last_loss = float("nan")
        last_acc = 0.0

        for _ in range(epochs):
            perm = list(np.random.default_rng(seed).permutation(len(train_seqs)))
            for i in range(0, len(perm), batch):
                batch_idx = perm[i : i + batch]
                xb = _pad([train_seqs[j] for j in batch_idx])
                yb = train_y[batch_idx]
                opt.zero_grad()
                logits = self.net(xb)
                loss = loss_fn(logits, yb)
                loss.backward()
                opt.step()
                last_loss = float(loss.item())
            with torch.no_grad():
                logits = self.net(_pad(train_seqs))
                preds = logits.argmax(dim=-1)
                last_acc = float((preds == train_y).float().mean().item())

        self.net.eval()
        with torch.no_grad():
            logits = self.net(_pad(val_seqs))
            preds = logits.argmax(dim=-1)
            val_acc = float((preds == val_y).float().mean().item())
        return SeqTrainStats(
            final_train_loss=last_loss,
            final_train_accuracy=last_acc,
            val_accuracy=val_acc,
        )


def trained_default_seq_classifier(seed: int = 0, n: int = 256) -> IngredientSeqClassifier:
    from ghc_ml.data.synthetic import synthetic_ingredients

    clf = IngredientSeqClassifier(seed=seed)
    clf.train(synthetic_ingredients(seed=seed, n=n))
    return clf
