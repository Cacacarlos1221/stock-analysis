#!/usr/bin/env python3
"""Generate predictions from the latest trained stock model."""

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
    apply_feature_schema,
    build_model_frame,
    ensure_data_directories,
    load_config,
    load_feature_frame,
    load_model_bundle,
    resolve_prediction_date,
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
        "--prediction-date",
        default="today",
        help="Requested prediction date in YYYY-MM-DD, or 'today'",
    )
    parser.add_argument(
        "--model-name",
        default=None,
        help="Optional model name override. Defaults to registry best_model.",
    )
    return parser.parse_args()


def main() -> None:
    try:
        args = parse_args()
        data_config = load_config(args.data_config, DEFAULT_DATA_CONFIG)
        feature_config = load_config(args.features_config, DEFAULT_FEATURE_CONFIG)
        paths = ensure_data_directories(data_config)

        registry_path = paths["models_dir"] / "registry.json"
        if not registry_path.exists():
            raise FileNotFoundError(f"Model registry not found: {registry_path}")

        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        model_name = args.model_name or registry["best_model"]
        bundle_path = Path(registry["models"][model_name]["bundle_path"])
        bundle = load_model_bundle(bundle_path)

        feature_path = Path(bundle["metadata"]["processed_input"])
        feature_df = load_feature_frame(feature_path)
        prediction_trade_date = resolve_prediction_date(feature_df, args.prediction_date)
        scoring_df = feature_df[feature_df["trade_date"] == prediction_trade_date].copy()
        if scoring_df.empty:
            raise ValueError(f"No rows available for prediction date {prediction_trade_date.date().isoformat()}")

        model_df, _ = build_model_frame(scoring_df, feature_config)
        x_score = apply_feature_schema(
            model_df,
            bundle["metadata"]["feature_columns"],
            bundle["metadata"]["fill_values"],
        )

        model = bundle["model"]
        task = bundle["metadata"]["task"]
        output = scoring_df[["trade_date", "symbol", "name", "close"]].copy()
        if task == "regression":
            output["predicted_return"] = model.predict(x_score)
        else:
            output["predicted_up"] = model.predict(x_score)
            if hasattr(model, "predict_proba"):
                output["probability_up"] = model.predict_proba(x_score)[:, 1]

        output = output.sort_values(["symbol"]).reset_index(drop=True)
        output_path = (
            paths["predictions_dir"] / f"predictions_{prediction_trade_date.strftime('%Y%m%d')}_{model_name}.csv"
        )
        output.to_csv(output_path, index=False)
    except (FileNotFoundError, KeyError, ValueError, ImportError) as exc:
        raise SystemExit(f"Prediction generation failed: {exc}") from exc

    print(f"Model: {model_name}")
    print(f"Prediction trade date: {prediction_trade_date.date().isoformat()}")
    print(f"Rows scored: {len(output)}")
    print(f"Prediction file: {output_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
