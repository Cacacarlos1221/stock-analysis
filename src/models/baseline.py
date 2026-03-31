"""Baseline model factories."""

from __future__ import annotations


def _require_sklearn():
    try:
        from sklearn.linear_model import LinearRegression, LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:
        raise ImportError(
            "scikit-learn is required for baseline models. Install dependencies from requirements.txt."
        ) from exc
    return LinearRegression, LogisticRegression, Pipeline, StandardScaler


def get_baseline_models(task_type: str, overrides: dict[str, dict] | None = None) -> dict[str, object]:
    """Return baseline models for the requested task type."""
    LinearRegression, LogisticRegression, Pipeline, StandardScaler = _require_sklearn()
    overrides = overrides or {}

    if task_type == "regression":
        return {
            "linear_regression": Pipeline(
                [
                    ("scaler", StandardScaler()),
                    ("model", LinearRegression(**overrides.get("linear_regression", {}))),
                ]
            ),
        }

    if task_type == "classification":
        return {
            "logistic_regression": Pipeline(
                [
                    ("scaler", StandardScaler()),
                    (
                        "model",
                        LogisticRegression(
                            **{
                                "max_iter": 1000,
                                "class_weight": "balanced",
                                "solver": "liblinear",
                                **overrides.get("logistic_regression", {}),
                            }
                        ),
                    ),
                ]
            ),
        }

    raise ValueError(f"Unsupported task_type: {task_type}")
