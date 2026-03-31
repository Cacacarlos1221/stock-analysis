"""Tree-based model factories."""

from __future__ import annotations


def _require_sklearn():
    try:
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    except ImportError as exc:
        raise ImportError(
            "scikit-learn is required for tree models. Install dependencies from requirements.txt."
        ) from exc
    return RandomForestClassifier, RandomForestRegressor


def _load_xgboost():
    try:
        from xgboost import XGBClassifier, XGBRegressor
    except ImportError:
        return None, None
    return XGBClassifier, XGBRegressor


def get_tree_models(
    task_type: str,
    random_state: int = 42,
    overrides: dict[str, dict] | None = None,
) -> dict[str, object]:
    """Return RandomForest and, when available, XGBoost models."""
    RandomForestClassifier, RandomForestRegressor = _require_sklearn()
    XGBClassifier, XGBRegressor = _load_xgboost()
    overrides = overrides or {}

    if task_type == "regression":
        models: dict[str, object] = {
            "random_forest_regressor": RandomForestRegressor(
                **{
                    "n_estimators": 300,
                    "max_depth": 6,
                    "min_samples_leaf": 5,
                    "random_state": random_state,
                    "n_jobs": -1,
                    **overrides.get("random_forest_regressor", {}),
                }
            )
        }
        if XGBRegressor is not None:
            models["xgboost_regressor"] = XGBRegressor(
                **{
                    "n_estimators": 300,
                    "max_depth": 4,
                    "learning_rate": 0.05,
                    "subsample": 0.8,
                    "colsample_bytree": 0.8,
                    "objective": "reg:squarederror",
                    "random_state": random_state,
                    **overrides.get("xgboost_regressor", {}),
                }
            )
        return models

    if task_type == "classification":
        models = {
            "random_forest_classifier": RandomForestClassifier(
                **{
                    "n_estimators": 300,
                    "max_depth": 6,
                    "min_samples_leaf": 5,
                    "class_weight": "balanced_subsample",
                    "random_state": random_state,
                    "n_jobs": -1,
                    **overrides.get("random_forest_classifier", {}),
                }
            )
        }
        if XGBClassifier is not None:
            models["xgboost_classifier"] = XGBClassifier(
                **{
                    "n_estimators": 300,
                    "max_depth": 4,
                    "learning_rate": 0.05,
                    "subsample": 0.8,
                    "colsample_bytree": 0.8,
                    "eval_metric": "logloss",
                    "random_state": random_state,
                    **overrides.get("xgboost_classifier", {}),
                }
            )
        return models

    raise ValueError(f"Unsupported task_type: {task_type}")
