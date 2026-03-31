#!/usr/bin/env python3
"""Train baseline and tree models on organized stock price data."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.features import add_market_features, add_seasonal_features, add_technical_features
from src.models import get_baseline_models, get_tree_models

DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "prices" / "stock_history.csv"

RAW_TO_CANONICAL = {
    "日期": "trade_date",
    "股票代码": "symbol",
    "股票名称": "name",
    "昨日收盘": "prev_close",
    "今日开盘": "open",
    "今日收盘": "close",
    "涨跌幅%": "pct_change",
    "最高价": "high",
    "最低价": "low",
    "成交量": "volume",
    "成交额": "turnover",
    "委买": "bid_volume",
    "委卖": "ask_volume",
    "换手率%": "turnover_rate",
    "振幅%": "amplitude",
    "量比": "volume_ratio",
    "市盈率": "pe_ratio",
    "总市值": "total_market_cap",
    "流通市值": "float_market_cap",
    "MA5": "ma_5_raw",
    "MA10": "ma_10_raw",
    "MA20": "ma_20_raw",
    "MACD": "macd_raw",
    "MACD信号": "macd_signal_raw",
    "KDJ-K": "kdj_k_raw",
    "KDJ-D": "kdj_d_raw",
    "KDJ-J": "kdj_j_raw",
    "RSI6": "rsi_6_raw",
    "RSI12": "rsi_12_raw",
    "主力净流入": "main_net_inflow",
    "所属板块": "sector_name",
    "板块涨幅%": "sector_pct_change",
    "涨跌家数比": "advance_decline_ratio",
    "大盘成交额": "market_turnover",
    "MA5量": "volume_ma_5",
    "MA10量": "volume_ma_10",
    "MA20量": "volume_ma_20",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input CSV path")
    parser.add_argument(
        "--task",
        choices=["regression", "classification"],
        default="classification",
        help="Training target type",
    )
    parser.add_argument(
        "--model-family",
        choices=["baseline", "tree", "all"],
        default="all",
        help="Which model family to train",
    )
    parser.add_argument(
        "--benchmark-symbol",
        default="000001",
        help="Benchmark symbol used for relative-return and market-regime features",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=1,
        help="Prediction horizon in trading days",
    )
    return parser.parse_args()


def load_raw_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    df = pd.read_csv(path)
    df = df.rename(columns={k: v for k, v in RAW_TO_CANONICAL.items() if k in df.columns})
    if "symbol" in df.columns:
        df["symbol"] = (
            df["symbol"]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.zfill(6)
        )
    df["trade_date"] = pd.to_datetime(df["trade_date"])

    for column in df.columns:
        if column in {"trade_date", "symbol", "name", "sector_name"}:
            continue
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df.sort_values(["symbol", "trade_date"]).reset_index(drop=True)


def build_feature_frame(
    df: pd.DataFrame,
    benchmark_symbol: str,
    horizon: int,
) -> pd.DataFrame:
    featured = add_technical_features(df)
    featured = add_seasonal_features(featured)
    featured = add_market_features(featured, benchmark_symbol=benchmark_symbol)

    grouped = featured.groupby("symbol", group_keys=False)
    featured["target_return"] = grouped["close"].shift(-horizon) / featured["close"] - 1
    featured["target_up"] = (featured["target_return"] > 0).astype(int)

    return featured


def build_model_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    excluded = {
        "trade_date",
        "symbol",
        "name",
        "sector_name",
        "target_return",
        "target_up",
        "close",
    }
    model_df = pd.get_dummies(
        df.drop(columns=[c for c in excluded if c in df.columns]),
        columns=[c for c in ["market_regime"] if c in df.columns],
        dummy_na=True,
    )
    model_df["trade_date"] = df["trade_date"].values
    model_df["target_return"] = df["target_return"].values
    model_df["target_up"] = df["target_up"].values
    return model_df, list(model_df.drop(columns=["trade_date", "target_return", "target_up"]).columns)


def prepare_training_frame(
    model_df: pd.DataFrame,
    feature_columns: list[str],
    min_non_null_ratio: float = 0.6,
) -> tuple[pd.DataFrame, list[str]]:
    usable_columns: list[str] = []
    for column in feature_columns:
        non_null_ratio = model_df[column].notna().mean()
        nunique = model_df[column].nunique(dropna=True)
        if non_null_ratio >= min_non_null_ratio and nunique > 1:
            usable_columns.append(column)

    prepared = model_df.copy()
    for column in usable_columns:
        prepared[column] = prepared[column].fillna(prepared[column].median())

    return prepared, usable_columns


def time_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    unique_dates = sorted(df["trade_date"].dropna().unique())
    if len(unique_dates) < 10:
        raise ValueError("Not enough unique dates for a train/validation/test split")

    train_cut = int(len(unique_dates) * 0.7)
    valid_cut = int(len(unique_dates) * 0.85)
    train_dates = set(unique_dates[:train_cut])
    valid_dates = set(unique_dates[train_cut:valid_cut])
    test_dates = set(unique_dates[valid_cut:])

    train_df = df[df["trade_date"].isin(train_dates)].copy()
    valid_df = df[df["trade_date"].isin(valid_dates)].copy()
    test_df = df[df["trade_date"].isin(test_dates)].copy()
    return train_df, valid_df, test_df


def evaluate_model(task: str, model, x_test: pd.DataFrame, y_test: pd.Series) -> dict[str, float]:
    if task == "regression":
        from sklearn.metrics import mean_absolute_error, mean_squared_error

        predictions = model.predict(x_test)
        return {
            "mae": float(mean_absolute_error(y_test, predictions)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, predictions))),
            "directional_accuracy": float((np.sign(predictions) == np.sign(y_test)).mean()),
        }

    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

    predictions = model.predict(x_test)
    return {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
        "f1": float(f1_score(y_test, predictions, zero_division=0)),
    }


def train_models(
    task: str,
    model_family: str,
    x_train: pd.DataFrame,
    y_train: pd.Series,
    x_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict[str, dict[str, float]]:
    factories: list[dict[str, object]] = []
    if model_family in {"baseline", "all"}:
        factories.append(get_baseline_models(task))
    if model_family in {"tree", "all"}:
        factories.append(get_tree_models(task))

    models: dict[str, object] = {}
    for family_models in factories:
        models.update(family_models)

    results: dict[str, dict[str, float]] = {}
    for name, model in models.items():
        model.fit(x_train, y_train)
        results[name] = evaluate_model(task, model, x_test, y_test)
    return results


def main() -> None:
    try:
        args = parse_args()
        raw_df = load_raw_data(args.input)
        featured = build_feature_frame(raw_df, args.benchmark_symbol, args.horizon)
        featured = featured.dropna(subset=["target_return"])
        model_df, feature_columns = build_model_frame(featured)
        model_df, feature_columns = prepare_training_frame(model_df, feature_columns)

        target_col = "target_return" if args.task == "regression" else "target_up"
        model_df = model_df.dropna(subset=feature_columns + [target_col]).copy()
        train_df, valid_df, test_df = time_split(model_df)

        x_train = pd.concat([train_df[feature_columns], valid_df[feature_columns]], axis=0)
        y_train = pd.concat([train_df[target_col], valid_df[target_col]], axis=0)
        x_test = test_df[feature_columns]
        y_test = test_df[target_col]

        results = train_models(args.task, args.model_family, x_train, y_train, x_test, y_test)
    except (FileNotFoundError, ValueError, ImportError) as exc:
        raise SystemExit(f"Training failed: {exc}") from exc

    print(f"Input: {args.input}")
    print(f"Task: {args.task}")
    print(f"Samples: train={len(x_train)} test={len(x_test)}")
    print("Results:")
    for model_name, metrics in results.items():
        metric_summary = ", ".join(f"{key}={value:.4f}" for key, value in metrics.items())
        print(f"  - {model_name}: {metric_summary}")


if __name__ == "__main__":
    main()
