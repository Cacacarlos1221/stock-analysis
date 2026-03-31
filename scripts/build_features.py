#!/usr/bin/env python3
"""Load raw stock data, build features, and save processed datasets."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import (
    DEFAULT_DATA_CONFIG,
    DEFAULT_FEATURE_CONFIG,
    ensure_data_directories,
    generate_feature_frame,
    load_config,
    load_raw_data,
    resolve_project_path,
    save_feature_frame,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=None, help="Optional raw CSV override")
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
    return parser.parse_args()


def main() -> None:
    try:
        args = parse_args()
        data_config = load_config(args.data_config, DEFAULT_DATA_CONFIG)
        feature_config = load_config(args.features_config, DEFAULT_FEATURE_CONFIG)
        paths = ensure_data_directories(data_config)

        raw_df = load_raw_data(data_config, args.input)
        feature_df = generate_feature_frame(raw_df, feature_config)
        output_path = resolve_project_path(data_config["paths"]["processed_features"])
        save_feature_frame(feature_df, output_path)
    except (FileNotFoundError, ValueError, ImportError) as exc:
        raise SystemExit(f"Feature build failed: {exc}") from exc

    latest_date = feature_df["trade_date"].max().date().isoformat()
    print(f"Raw rows: {len(raw_df)}")
    print(f"Feature rows: {len(feature_df)}")
    print(f"Latest trade date: {latest_date}")
    print(f"Processed feature file: {output_path.relative_to(PROJECT_ROOT)}")
    print(f"Processed directory: {paths['processed_dir'].relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
