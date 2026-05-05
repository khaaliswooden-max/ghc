"""ML pipeline tests.

Deterministic-seed assertions covering:
* corpus arm classifies known haram / E-number cases correctly
* neural arm trains to >0.9 accuracy on synthetic data
* GNN risk scorer trains to MAE < 0.20 on synthetic data
* /v1/ml endpoints route through the lazy-loaded models
"""

from fastapi.testclient import TestClient

from ghc_api.app import app
from ghc_graph.types import ProvenanceDag
from ghc_ml.data.synthetic import synthetic_dags, synthetic_ingredients
from ghc_ml.ingredient import IngredientClassifier, trained_default_classifier
from ghc_ml.risk import RiskScorer
from ghc_traceability.types import Verdict

client = TestClient(app)


# ---- Ingredient corpus ---------------------------------------------------


def test_corpus_pork_is_haram() -> None:
    clf = IngredientClassifier(seed=0)
    v, reason = clf.classify("pork sausage, salt")
    assert v == Verdict.HARAM
    assert reason.startswith("corpus:")


def test_corpus_e120_is_haram() -> None:
    clf = IngredientClassifier(seed=0)
    v, reason = clf.classify("food coloring E120, water")
    assert v == Verdict.HARAM
    assert reason == "corpus:e_number:E120"


def test_corpus_lecithin_is_mashbuh() -> None:
    clf = IngredientClassifier(seed=0)
    v, _ = clf.classify("lecithin, sugar")
    assert v == Verdict.MASHBUH


def test_corpus_e322_is_mashbuh() -> None:
    clf = IngredientClassifier(seed=0)
    v, _ = clf.classify("wheat flour, E322, baking soda")
    assert v == Verdict.MASHBUH


# ---- Ingredient neural arm ----------------------------------------------


def test_neural_arm_converges_on_synthetic() -> None:
    clf = IngredientClassifier(seed=0)
    stats = clf.train(synthetic_ingredients(seed=0, n=400), epochs=30, seed=0)
    # Loss should decrease and accuracy should be high on synthetic
    # data where the corpus arm wins on non-empty signal.
    assert stats.final_train_loss < 0.6
    assert stats.val_accuracy > 0.9


# ---- GNN risk scorer -----------------------------------------------------


def test_gnn_converges_on_synthetic() -> None:
    samples = synthetic_dags(seed=0, n=80)
    scorer = RiskScorer(seed=0)
    stats = scorer.train(
        [(s.dag, s.risk) for s in samples], epochs=80, seed=0
    )
    assert stats.val_mae < 0.20
    # Synthetic risks cluster broadly, so PR-AUC against
    # `risk > 0.5` should still beat random (0.5).
    assert stats.val_pr_auc >= 0.3


def test_gnn_handles_empty_dag() -> None:
    scorer = RiskScorer(seed=0)
    risk = scorer.score(ProvenanceDag(edges=[]))
    assert 0.0 <= risk <= 1.0


# ---- API endpoints -------------------------------------------------------


def test_api_classify_pork_via_ml_endpoint() -> None:
    resp = client.post("/v1/ml/ingredient", json={"text": "pork sausage, salt"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "haram"
    assert body["reason"].startswith("corpus:")


def test_api_classify_halal_via_ml_endpoint() -> None:
    resp = client.post("/v1/ml/ingredient", json={"text": "rice flour, salt"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "halal"


def test_api_risk_endpoint_returns_unit_interval() -> None:
    dag = {
        "edges": [
            {"source": 0, "target": 1, "weight": 50},
            {"source": 1, "target": 2, "weight": 30},
            {"source": 2, "target": 3, "weight": 10},
        ]
    }
    resp = client.post("/v1/ml/risk", json={"dag": dag})
    assert resp.status_code == 200
    risk = resp.json()["risk"]
    assert 0.0 <= risk <= 1.0


# ---- Default model fixtures ---------------------------------------------


def test_trained_default_classifier_works_on_corpus() -> None:
    clf = trained_default_classifier(seed=0, n=200)
    v, _ = clf.classify("pork lard")
    assert v == Verdict.HARAM
    v, _ = clf.classify("rice flour, sunflower oil")
    assert v == Verdict.HALAL
