"""GHC ML pipelines.

Two trainable models ship in v0.0.x:

* `ingredient.IngredientClassifier` — text classifier over ingredient
  strings producing a `Verdict` (halal / mashbuh / haram). Combines a
  curated haram-keyword + E-number corpus with a small character n-gram
  MLP trained on synthetic data.

* `risk.SupplyChainRiskGNN` — provenance-DAG risk model. A custom
  PyTorch message-passing GNN that takes a `ProvenanceDag` (mirror of
  `core/ghc-graph::ProvenanceDag`) and outputs a `[0, 1]` risk score.
  Trained on the deterministic synthetic dataset under
  `ghc_ml.data.synthetic_dags`.

Both models are trainable on CPU in seconds on synthetic data so CI
keeps full coverage. Phase E+ swaps the n-gram MLP for LayoutLMv3 +
multilingual XLM-R for image-based label OCR.
"""

__version__ = "0.0.1"
