"""Baseline model factories."""

from __future__ import annotations


def _require_sklearn():
    try:
        from sklearn.linear_model import LinearRegression, LogisticRegression
    except ImportError as exc:
        raise ImportError(
            "scikit-learn is required for baseline models. Install dependencies from requirements.txt."
        ) from exc
    return LinearRegression, LogisticRegression


def get_baseline_models(task_type: str) -> dict[str, object]:
    """Return baseline models for the requested task type."""
    LinearRegression, LogisticRegression = _require_sklearn()

    if task_type == "regression":
        return {
            "linear_regression": LinearRegression(),
        }

    if task_type == "classification":
        return {
            "logistic_regression": LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
            ),
        }

    raise ValueError(f"Unsupported task_type: {task_type}")
