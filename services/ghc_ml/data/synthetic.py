"""Deterministic synthetic dataset generators.

Two generators ship in v0.0.x:

* `synthetic_ingredients(seed, n)` produces a list of
  `(text, ground_truth_verdict)` pairs combining halal-typical
  English and Malay/Arabic transliterations with known haram/mashbuh
  keywords and E-number patterns.

* `synthetic_dags(seed, n)` produces a list of
  `(ProvenanceDag, risk_score)` tuples where the risk score is
  derived deterministically from the DAG topology so the GNN has a
  computable ground truth to converge to.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Tuple

from ghc_graph.types import Edge, ProvenanceDag
from ghc_traceability.types import Verdict


# --- Ingredient synthesis -------------------------------------------------

# Halal-typical ingredients (no haram/mashbuh keywords).
_HALAL_BASE = [
    "wheat flour",
    "rice flour",
    "tapioca starch",
    "olive oil",
    "sunflower oil",
    "soybean oil",
    "tomato paste",
    "salt",
    "sugar",
    "baking soda",
    "yeast extract",
    "ascorbic acid",
    "citric acid",
    "lemon juice",
    "garlic powder",
    "black pepper",
    "turmeric",
    "paprika",
    "soy sauce",
    "carrots",
    "potatoes",
    "tomatoes",
    "onions",
    "kacang hijau",
    "santan kelapa",
]


def synthetic_ingredients(seed: int = 0, n: int = 256) -> List[Tuple[str, Verdict]]:
    """Generate a deterministic list of (text, verdict) training pairs."""
    rng = random.Random(seed)
    from ghc_ml.data.corpus import (
        E_NUMBER_LATTICE,
        HARAM_KEYWORDS,
        MASHBUH_KEYWORDS,
    )

    samples: List[Tuple[str, Verdict]] = []
    while len(samples) < n:
        kind = rng.choice(["halal", "mashbuh", "haram"])
        if kind == "halal":
            base = rng.sample(_HALAL_BASE, k=rng.randint(2, 4))
            samples.append((", ".join(base), Verdict.HALAL))
        elif kind == "mashbuh":
            choice = rng.choice(["keyword", "e"])
            if choice == "keyword":
                kw = rng.choice(MASHBUH_KEYWORDS)
                base = rng.sample(_HALAL_BASE, k=rng.randint(1, 3))
                ingredients = base + [kw.strip()]
                rng.shuffle(ingredients)
                samples.append((", ".join(ingredients), Verdict.MASHBUH))
            else:
                e = rng.choice(
                    [k for k, v in E_NUMBER_LATTICE.items() if v is Verdict.MASHBUH]
                )
                base = rng.sample(_HALAL_BASE, k=rng.randint(1, 3))
                ingredients = base + [e]
                rng.shuffle(ingredients)
                samples.append((", ".join(ingredients), Verdict.MASHBUH))
        else:  # haram
            choice = rng.choice(["keyword", "e"])
            if choice == "keyword":
                kw = rng.choice(HARAM_KEYWORDS).strip()
                base = rng.sample(_HALAL_BASE, k=rng.randint(1, 3))
                ingredients = base + [kw]
                rng.shuffle(ingredients)
                samples.append((", ".join(ingredients), Verdict.HARAM))
            else:
                e = rng.choice(
                    [k for k, v in E_NUMBER_LATTICE.items() if v is Verdict.HARAM]
                )
                base = rng.sample(_HALAL_BASE, k=rng.randint(1, 3))
                ingredients = base + [e]
                rng.shuffle(ingredients)
                samples.append((", ".join(ingredients), Verdict.HARAM))
    return samples


# --- Provenance DAG synthesis ---------------------------------------------


@dataclass
class DagSample:
    dag: ProvenanceDag
    risk: float
    """Ground-truth risk score in `[0, 1]`."""


def synthetic_dags(seed: int = 0, n: int = 64) -> List[DagSample]:
    """Generate a deterministic list of (dag, risk-score) pairs.

    Risk score is computed from the DAG's structural properties:
    higher when (a) total edge count is large, (b) the lowest-trust
    edge weight is small, and (c) the graph branches heavily.
    """
    rng = random.Random(seed)
    out: List[DagSample] = []
    for _ in range(n):
        n_nodes = rng.randint(3, 12)
        n_edges = rng.randint(n_nodes - 1, n_nodes * 2)
        edges = []
        for _ in range(n_edges):
            s = rng.randint(0, n_nodes - 2)
            t = rng.randint(s + 1, n_nodes - 1)
            w = rng.randint(1, 100)
            edges.append(Edge(source=s, target=t, weight=w))
        dag = ProvenanceDag(edges=edges)
        risk = _ground_truth_risk(dag)
        out.append(DagSample(dag=dag, risk=risk))
    return out


def _ground_truth_risk(dag: ProvenanceDag) -> float:
    if not dag.edges:
        return 0.0
    n_edges = len(dag.edges)
    weights = [e.weight for e in dag.edges]
    min_w = min(weights)
    avg_w = sum(weights) / n_edges
    # Scale: higher when more edges, lower-min weight, lower average.
    edge_pressure = min(1.0, n_edges / 24.0)
    weight_pressure = 1.0 - (avg_w / 100.0)
    min_pressure = 1.0 - (min_w / 100.0)
    risk = 0.4 * edge_pressure + 0.3 * weight_pressure + 0.3 * min_pressure
    return max(0.0, min(1.0, risk))
