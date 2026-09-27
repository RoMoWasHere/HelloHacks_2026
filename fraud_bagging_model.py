"""Train and use the bagged decision-stump fraud model from Bagging.ipynb.

    from fraud_bagging_model import train_model, predict

    train_model()                      # trains on data.json, saves fraud_bagging_model.joblib
    predict({"title": ..., "description": ..., "price": 1300, ...})
    # -> {"fake": True, "votes": {"fake": 4, "real": 1},
    #     "consensus_rules": ["price <= 1500 (this listing: 1300)", ...],
    #     "trees": [{"tree": 1, "vote": "fake", "rule": [...]}, ...]}
"""

from functools import lru_cache
from pathlib import Path

import joblib
from sklearn.ensemble import BaggingClassifier
from sklearn.metrics import f1_score, make_scorer, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from fraud_model import (
    DATA_PATH,
    PROJECT_DIR,
    TARGET_COLUMN,
    build_preprocess,
    load_listings,
    parse_listing,
    prepare_features,
    transform_listing,
    tree_rule,
)

MODEL_PATH = PROJECT_DIR / "fraud_bagging_model.joblib"

RANDOM_STATE = 42
CV_FOLDS = 5
MAX_DEPTH = 1  # Each tree is a decision stump: one question
N_TREES = 5

SCORING = {
    "balanced_accuracy": "balanced_accuracy",
    "fake_precision": make_scorer(precision_score, pos_label=True, zero_division=0),
    "fake_recall": make_scorer(recall_score, pos_label=True, zero_division=0),
    "fake_f1": make_scorer(f1_score, pos_label=True, zero_division=0),
}


def build_model() -> Pipeline:
    """The bagging pipeline from Bagging.ipynb, untrained.

    Each stump sees a bootstrap sample of 80% of the listings and a random 80%
    of the features, so the trees ask different questions.
    """
    base_tree = DecisionTreeClassifier(
        max_depth=MAX_DEPTH, class_weight="balanced", random_state=RANDOM_STATE
    )
    ensemble = BaggingClassifier(
        estimator=base_tree, n_estimators=N_TREES, max_samples=0.8,
        bootstrap=True, max_features=0.8, bootstrap_features=False,
        random_state=RANDOM_STATE, n_jobs=-1,
    )
    return Pipeline([("preprocess", build_preprocess()), ("ensemble", ensemble)])


def train_model(data_path=DATA_PATH, model_path=MODEL_PATH) -> dict:
    """Create, evaluate and train the ensemble, then save it to ``model_path``.

    Reports five-fold cross-validated balanced accuracy and fake-class
    precision, recall and F1 (mean and standard deviation per metric), then
    fits on all listings and saves that model. Returns the metrics.
    """
    data = load_listings(data_path)
    X = prepare_features(data)
    y = data[TARGET_COLUMN].astype(bool)

    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_validate(build_model(), X, y, cv=cv, scoring=SCORING)
    metrics = {"rows": len(X)}
    for metric in SCORING:
        fold_scores = scores[f"test_{metric}"]
        metrics[metric] = {
            "folds": fold_scores.round(3).tolist(),
            "mean": round(float(fold_scores.mean()), 3),
            "std": round(float(fold_scores.std()), 3),
        }

    joblib.dump(build_model().fit(X, y), model_path)
    _load_model.cache_clear()
    metrics["model_path"] = str(model_path)
    return metrics


@lru_cache(maxsize=4)
def _load_model(model_path: str) -> Pipeline:
    return joblib.load(model_path)


def predict(listing, model_path=MODEL_PATH) -> dict:
    """Predict whether one listing is fake, using the ensemble saved by ``train_model``.

    ``listing`` is one JSON data point: a dict, or a JSON string of one, in the
    same format as data.json. Returns:

    - ``fake``: the ensemble's consensus (the average of the trees' probabilities,
      as ``BaggingClassifier.predict`` computes it)
    - ``votes``: how many trees voted fake and real
    - ``consensus_rules``: the rules of the trees that agree with the consensus
    - ``trees``: every tree's vote and the rule behind it
    """
    listing = parse_listing(listing)
    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"No trained model at {model_path}. Run train_model() first.")

    model = _load_model(str(model_path))
    features, names = transform_listing(model.named_steps["preprocess"], listing)
    ensemble = model.named_steps["ensemble"]

    trees = []
    for number, (tree, feature_indices) in enumerate(
        zip(ensemble.estimators_, ensemble.estimators_features_), start=1
    ):
        # Each tree was trained on its own subset of features.
        vote, rule = tree_rule(tree, features[feature_indices], names[feature_indices])
        trees.append({"tree": number, "vote": "fake" if vote else "real", "rule": rule})

    fake = bool(ensemble.predict(features.reshape(1, -1))[0])
    consensus_vote = "fake" if fake else "real"
    # Trees can ask the same question at slightly different thresholds;
    # keep one condition per question (the text before the numbers in brackets).
    consensus_rules = {}
    for tree in trees:
        if tree["vote"] == consensus_vote:
            for condition in tree["rule"]:
                consensus_rules.setdefault(condition.split(" (")[0], condition)
    fake_votes = sum(tree["vote"] == "fake" for tree in trees)
    return {
        "fake": fake,
        "votes": {"fake": fake_votes, "real": len(trees) - fake_votes},
        "consensus_rules": list(consensus_rules.values()),
        "trees": trees,
    }


if __name__ == "__main__":
    for name, value in train_model().items():
        print(f"{name}: {value}")
