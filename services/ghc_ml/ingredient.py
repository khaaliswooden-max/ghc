"""Ingredient halal-status classifier.

Combines a curated haram-keyword + E-number corpus
(`ghc_ml.data.corpus`) with a character n-gram MLP trained on
synthetic data (`ghc_ml.data.synthetic.synthetic_ingredients`).

* The corpus arm is **deterministic**: any text matching a known
  haram or mashbuh keyword / E-number is classified by the corpus
  alone.
* The neural arm is **a fallback** that handles novel strings the
  corpus doesn't cover. Trained on synthetic data with seeded
  determinism so CI converges in seconds.

Phase E+ swaps the n-gram MLP for LayoutLMv3 + multilingual XLM-R
once a labeled image corpus is available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from ghc_ml.data.corpus import keyword_verdict, lookup_e_number
from ghc_traceability.types import Verdict

VERDICT_INDEX: dict[Verdict, int] = {
    Verdict.HALAL: 0,
    Verdict.MASHBUH: 1,
    Verdict.HARAM: 2,
}
INDEX_VERDICT: list[Verdict] = [Verdict.HALAL, Verdict.MASHBUH, Verdict.HARAM]


# --- Featurization --------------------------------------------------------


def _ngram_indices(text: str, n: int = 3, vocab_size: int = 4096) -> List[int]:
    """Hash character n-grams into a fixed-size vocabulary."""
    text = text.lower()
    out: List[int] = []
    for i in range(len(text) - n + 1):
        token = text[i : i + n]
        out.append(hash(token) % vocab_size)
    return out


def featurize(text: str, vocab_size: int = 4096) -> np.ndarray:
    """Bag-of-n-grams float32 vector."""
    vec = np.zeros(vocab_size, dtype=np.float32)
    for idx in _ngram_indices(text, vocab_size=vocab_size):
        vec[idx] += 1.0
    norm = vec.sum()
    if norm > 0:
        vec /= norm
    return vec


# --- Model ----------------------------------------------------------------


class IngredientNet(nn.Module):
    """Tiny MLP over hashed-character-n-gram features."""

    def __init__(self, vocab_size: int = 4096, hidden: int = 64) -> None:
        super().__init__()
        self.fc1 = nn.Linear(vocab_size, hidden)
        self.fc2 = nn.Linear(hidden, hidden)
        self.out = nn.Linear(hidden, 3)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = F.relu(self.fc1(x))
        h = F.relu(self.fc2(h))
        return self.out(h)


@dataclass
class TrainStats:
    final_train_loss: float
    final_train_accuracy: float
    val_accuracy: float


class IngredientClassifier:
    """The full classifier: corpus arm + neural fallback.

    Use `classify(text)` for inference and `train(samples)` to (re-)
    train the neural arm on `(text, verdict)` pairs.
    """

    def __init__(self, vocab_size: int = 4096, hidden: int = 64, seed: int = 0) -> None:
        self.vocab_size = vocab_size
        torch.manual_seed(seed)
        self.net = IngredientNet(vocab_size=vocab_size, hidden=hidden)
        self.net.eval()

    # Inference --------------------------------------------------------

    def classify(self, text: str) -> Tuple[Verdict, str]:
        """Return `(verdict, reason)`. `reason` is `corpus:<token>` if
        the corpus arm fired, else `neural`."""
        for token in text.replace(",", " ").split():
            v = lookup_e_number(token)
            if v is not None:
                return v, f"corpus:e_number:{token.upper()}"
        v = keyword_verdict(text)
        if v is not None:
            return v, "corpus:keyword"
        # Neural fallback.
        with torch.no_grad():
            x = torch.from_numpy(featurize(text, self.vocab_size)).unsqueeze(0)
            logits = self.net(x)
            idx = int(logits.argmax(dim=-1).item())
        return INDEX_VERDICT[idx], "neural"

    # Training ---------------------------------------------------------

    def train(
        self,
        samples: List[Tuple[str, Verdict]],
        *,
        epochs: int = 30,
        lr: float = 1e-2,
        batch: int = 32,
        val_frac: float = 0.2,
        seed: int = 0,
    ) -> TrainStats:
        rng = np.random.default_rng(seed)
        idx = rng.permutation(len(samples))
        n_val = max(1, int(len(samples) * val_frac))
        val_idx = idx[:n_val]
        train_idx = idx[n_val:]
        train = [samples[i] for i in train_idx]
        val = [samples[i] for i in val_idx]

        x_train = torch.from_numpy(
            np.stack([featurize(t, self.vocab_size) for t, _ in train])
        )
        y_train = torch.tensor([VERDICT_INDEX[v] for _, v in train], dtype=torch.long)
        x_val = torch.from_numpy(
            np.stack([featurize(t, self.vocab_size) for t, _ in val])
        )
        y_val = torch.tensor([VERDICT_INDEX[v] for _, v in val], dtype=torch.long)

        self.net.train()
        opt = torch.optim.Adam(self.net.parameters(), lr=lr)
        loss_fn = nn.CrossEntropyLoss()

        last_loss = float("nan")
        last_acc = 0.0
        for _ in range(epochs):
            perm = torch.randperm(x_train.size(0))
            x_train, y_train = x_train[perm], y_train[perm]
            for i in range(0, x_train.size(0), batch):
                xb = x_train[i : i + batch]
                yb = y_train[i : i + batch]
                opt.zero_grad()
                logits = self.net(xb)
                loss = loss_fn(logits, yb)
                loss.backward()
                opt.step()
                last_loss = float(loss.item())
            with torch.no_grad():
                preds = self.net(x_train).argmax(dim=-1)
                last_acc = float((preds == y_train).float().mean().item())

        self.net.eval()
        with torch.no_grad():
            preds = self.net(x_val).argmax(dim=-1)
            val_acc = float((preds == y_val).float().mean().item())

        return TrainStats(
            final_train_loss=last_loss,
            final_train_accuracy=last_acc,
            val_accuracy=val_acc,
        )


def trained_default_classifier(seed: int = 0, n: int = 256) -> IngredientClassifier:
    """Convenience: a seeded classifier trained on the synthetic corpus.

    Returned model converges to >0.9 val accuracy on the synthetic
    data; the corpus arm provides the ground truth on real label
    text, so the neural arm is exercised primarily as a fallback for
    novel strings.
    """
    from ghc_ml.data.synthetic import synthetic_ingredients

    clf = IngredientClassifier(seed=seed)
    clf.train(synthetic_ingredients(seed=seed, n=n))
    return clf
