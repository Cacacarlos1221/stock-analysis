#!/usr/bin/env python3
"""Train stock prediction models from processed features and save artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import (
    DEFAULT_DATA_CONFIG,
    DEFAULT_FEATURE_CONFIG,
    DEFAULT_MODEL_CONFIG,
    apply_feature_schema,
    build_model_candidates,
    build_model_frame,
    choose_best_model,
    ensure_data_directories,
    evaluate_model,
    load_config,
    load_feature_frame,
    resolve_project_path,
    save_model_bundle,
    time_split,
    prepare_training_frame,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-config",
        type=Path,
        default=PROJECT_ROOT / "configs" / "data.yaml",
        help="Data config path",
    )
    parser.add_argument(
        "--features-config",
        type=Path,
        default=PROJECT_ROOT / "configs" / "features.yaml",
        help="Feature config path",
    )
    parser.add_argument(
        "--model-config",
        type=Path,
        default=PROJECT_ROOT / "configs" / "model_baseline.yaml",
        help="Model config path",
    )
    parser.add_argument("--input", type=Path, default=None, help="Optional processed feature CSV override")
    return parser.parse_args()


def main() -> None:
    try:
        args = parse_args()
        data_config = load_config(args.data_config, DEFAULT_DATA_CONFIG)
        feature_config = load_config(args.features_config, DEFAULT_FEATURE_CONFIG)
        model_config = load_config(args.model_config, DEFAULT_MODEL_CONFIG)
        paths = ensure_data_directories(data_config)

        input_path = args.input or resolve_project_path(data_config["paths"]["processed_features"])
        feature_df = load_feature_frame(input_path)
        feature_df = feature_df.dropna(subset=["target_return"]).copy()

        model_df, feature_columns = build_model_frame(feature_df, feature_config)
        model_df, feature_columns, fill_values = prepare_training_frame(
            model_df,
            feature_columns,
            float(model_config.get("min_non_null_ratio", 0.6)),
        )

        task = model_config.get("task", "classification")
        target_col = "target_return" if task == "regression" else "target_up"
        model_df = model_df.dropna(subset=feature_columns + [target_col]).copy()
        train_df, valid_df, test_df = time_split(model_df)

        x_train = pd.concat([train_df[feature_columns], valid_df[feature_columns]], axis=0)
        y_train = pd.concat([train_df[target_col], valid_df[target_col]], axis=0)
        x_test = apply_feature_schema(test_df, feature_columns, fill_values)
        y_test = test_df[target_col]

        candidates = build_model_candidates(model_config)
        results: dict[str, dict[str, float]] = {}
        bundles: dict[str, dict] = {}
        for model_name, model in candidates.items():
            model.fit(x_train, y_train)
            metrics = evaluate_model(task, model, x_test, y_test)
            results[model_name] = metrics
            bundles[model_name] = {
                "model": model,
                "metadata": {
                    "model_name": model_name,
                    "task": task,
                    "feature_columns": feature_columns,
                    "fill_values": fill_values,
                    "metrics": metrics,
                    "selection_metric": model_config.get("selection_metric", "f1"),
                    "target_col": target_col,
                    "train_rows": int(len(x_train)),
                    "test_rows": int(len(x_test)),
                    "processed_input": str(input_path),
                },
            }

        best_model_name = choose_best_model(
            results,
            task,
            str(model_config.get("selection_metric", "f1")),
        )

        registry = {
            "best_model": best_model_name,
            "results": results,
            "models": {},
        }
        for model_name, bundle in bundles.items():
            model_dir = paths["models_dir"] / model_name
            save_model_bundle(bundle, model_dir)
            registry["models"][model_name] = {
                "bundle_path": str((model_dir / "bundle.pkl").resolve()),
                "metrics": bundle["metadata"]["metrics"],
            }

        registry_path = paths["models_dir"] / "registry.json"
        registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
    except (FileNotFoundError, ValueError, ImportError) as exc:
        raise SystemExit(f"Training failed: {exc}") from exc

    print(f"Processed features: {input_path.relative_to(PROJECT_ROOT)}")
    print(f"Task: {task}")
    print(f"Samples: train={len(x_train)} test={len(x_test)}")
    print(f"Best model: {best_model_name}")
    for model_name, metrics in results.items():
        metric_summary = ", ".join(f"{key}={value:.4f}" for key, value in metrics.items())
        print(f"  - {model_name}: {metric_summary}")
    print(f"Model registry: {registry_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
