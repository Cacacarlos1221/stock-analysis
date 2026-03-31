"""Config-driven data, feature, training, and prediction helpers."""

from __future__ import annotations

import json
import pickle
from copy import deepcopy
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from src.features.market import add_market_features
from src.features.seasonal import add_seasonal_features
from src.features.technical import (
    add_atr,
    add_bollinger_bands,
    add_kdj,
    add_macd,
    add_moving_averages,
    add_rsi,
)
from src.models import get_baseline_models, get_tree_models

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_DATA_CONFIG = {
    "paths": {
        "raw_data": "data/raw/prices/stock_history.csv",
        "processed_dir": "data/processed",
        "processed_features": "data/processed/featured_dataset.csv",
        "artifacts_dir": "data/artifacts",
        "models_dir": "data/artifacts/models",
        "predictions_dir": "data/artifacts/predictions",
    },
    "column_mapping": {
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
    },
    "categorical_columns": ["trade_date", "symbol", "name", "sector_name"],
    "symbol_length": 6,
}

DEFAULT_FEATURE_CONFIG = {
    "benchmark_symbol": "000001",
    "horizon": 1,
    "technical": {
        "moving_average_windows": [5, 10, 20, 60],
        "macd": {"fast": 12, "slow": 26, "signal": 9},
        "rsi_periods": [6, 12, 14],
        "kdj": {"lookback": 9, "smooth_k": 3, "smooth_d": 3},
        "bollinger": {"window": 20, "num_std": 2.0},
        "atr_period": 14,
    },
    "seasonal": {"enabled": True},
    "market": {
        "enabled": True,
        "regime_window": 20,
        "bullish_threshold": 0.02,
        "bearish_threshold": -0.02,
        "volatility_threshold": 0.02,
    },
    "excluded_model_columns": [
        "trade_date",
        "symbol",
        "name",
        "sector_name",
        "target_return",
        "target_up",
        "close",
    ],
    "one_hot_columns": ["market_regime"],
    "feature_columns": "auto",
}

DEFAULT_MODEL_CONFIG = {
    "task": "classification",
    "model_family": "baseline",
    "selection_metric": "f1",
    "min_non_null_ratio": 0.6,
    "random_state": 42,
    "baseline": {
        "logistic_regression": {
            "max_iter": 1000,
            "class_weight": "balanced",
            "solver": "liblinear",
        },
        "linear_regression": {},
    },
    "tree": {
        "random_forest_classifier": {
            "n_estimators": 300,
            "max_depth": 6,
            "min_samples_leaf": 5,
            "class_weight": "balanced_subsample",
        },
        "random_forest_regressor": {
            "n_estimators": 300,
            "max_depth": 6,
            "min_samples_leaf": 5,
        },
        "xgboost_classifier": {
            "n_estimators": 300,
            "max_depth": 4,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "eval_metric": "logloss",
        },
        "xgboost_regressor": {
            "n_estimators": 300,
            "max_depth": 4,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "objective": "reg:squarederror",
        },
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_yaml_like(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
    except ModuleNotFoundError:
        data = json.loads(text)

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Config file must contain a mapping: {path}")
    return data


def load_config(path: Path | None, default: dict) -> dict:
    if path is None or not path.exists():
        return deepcopy(default)
    return _deep_merge(default, _load_yaml_like(path))


def resolve_project_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def ensure_data_directories(data_config: dict) -> dict[str, Path]:
    paths = {name: resolve_project_path(value) for name, value in data_config["paths"].items()}
    for key in ("processed_dir", "artifacts_dir", "models_dir", "predictions_dir"):
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths


def load_raw_data(data_config: dict, input_path: Path | None = None) -> pd.DataFrame:
    source_path = input_path or resolve_project_path(data_config["paths"]["raw_data"])
    if not source_path.exists():
        raise FileNotFoundError(f"Input file not found: {source_path}")

    df = pd.read_csv(source_path)
    mapping = data_config.get("column_mapping", {})
    df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})

    if "trade_date" not in df.columns or "symbol" not in df.columns:
        raise ValueError("Raw data must include trade_date and symbol columns after mapping")

    symbol_length = int(data_config.get("symbol_length", 6))
    df["symbol"] = (
        df["symbol"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(symbol_length)
    )
    df["trade_date"] = pd.to_datetime(df["trade_date"])

    categorical = set(data_config.get("categorical_columns", []))
    for column in df.columns:
        if column in categorical:
            continue
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df.sort_values(["symbol", "trade_date"]).reset_index(drop=True)


def generate_feature_frame(df: pd.DataFrame, feature_config: dict) -> pd.DataFrame:
    result = df.sort_values(["symbol", "trade_date"]).copy()

    technical = feature_config.get("technical", {})
    result = add_moving_averages(
        result,
        windows=technical.get("moving_average_windows", [5, 10, 20, 60]),
    )

    macd = technical.get("macd", {})
    result = add_macd(
        result,
        fast=macd.get("fast", 12),
        slow=macd.get("slow", 26),
        signal=macd.get("signal", 9),
    )

    result = add_rsi(result, periods=technical.get("rsi_periods", [6, 12, 14]))

    kdj = technical.get("kdj", {})
    result = add_kdj(
        result,
        lookback=kdj.get("lookback", 9),
        smooth_k=kdj.get("smooth_k", 3),
        smooth_d=kdj.get("smooth_d", 3),
    )

    bollinger = technical.get("bollinger", {})
    result = add_bollinger_bands(
        result,
        window=bollinger.get("window", 20),
        num_std=bollinger.get("num_std", 2.0),
    )

    result = add_atr(result, period=technical.get("atr_period", 14))

    if feature_config.get("seasonal", {}).get("enabled", True):
        result = add_seasonal_features(result)

    market_cfg = feature_config.get("market", {})
    if market_cfg.get("enabled", True):
        result = add_market_features(
            result,
            benchmark_symbol=feature_config.get("benchmark_symbol", "000001"),
            regime_window=market_cfg.get("regime_window", 20),
            bullish_threshold=market_cfg.get("bullish_threshold", 0.02),
            bearish_threshold=market_cfg.get("bearish_threshold", -0.02),
            volatility_threshold=market_cfg.get("volatility_threshold", 0.02),
        )

    horizon = int(feature_config.get("horizon", 1))
    grouped = result.groupby("symbol", group_keys=False)
    result["target_return"] = grouped["close"].shift(-horizon) / result["close"] - 1
    result["target_up"] = (result["target_return"] > 0).astype(int)
    return result


def save_feature_frame(feature_df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    feature_df.to_csv(output_path, index=False)


def load_feature_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Processed feature file not found: {path}")
    df = pd.read_csv(path)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    return df.sort_values(["symbol", "trade_date"]).reset_index(drop=True)


def build_model_frame(feature_df: pd.DataFrame, feature_config: dict) -> tuple[pd.DataFrame, list[str]]:
    excluded = set(feature_config.get("excluded_model_columns", []))
    one_hot_columns = [
        column for column in feature_config.get("one_hot_columns", []) if column in feature_df.columns
    ]
    model_df = pd.get_dummies(
        feature_df.drop(columns=[column for column in excluded if column in feature_df.columns]),
        columns=one_hot_columns,
        dummy_na=True,
    )
    model_df["trade_date"] = feature_df["trade_date"].values
    model_df["symbol"] = feature_df["symbol"].values
    model_df["close"] = feature_df["close"].values
    model_df["target_return"] = feature_df["target_return"].values
    model_df["target_up"] = feature_df["target_up"].values

    configured_columns = feature_config.get("feature_columns", "auto")
    if configured_columns == "auto":
        feature_columns = [
            column
            for column in model_df.columns
            if column not in {"trade_date", "symbol", "close", "target_return", "target_up"}
        ]
    else:
        feature_columns = [column for column in configured_columns if column in model_df.columns]
    return model_df, feature_columns


def prepare_training_frame(
    model_df: pd.DataFrame,
    feature_columns: list[str],
    min_non_null_ratio: float = 0.6,
) -> tuple[pd.DataFrame, list[str], dict[str, float]]:
    usable_columns: list[str] = []
    fill_values: dict[str, float] = {}
    prepared = model_df.copy()

    for column in feature_columns:
        non_null_ratio = prepared[column].notna().mean()
        nunique = prepared[column].nunique(dropna=True)
        if non_null_ratio >= min_non_null_ratio and nunique > 1:
            usable_columns.append(column)
            median = prepared[column].median()
            fill_values[column] = 0.0 if pd.isna(median) else float(median)
            prepared[column] = prepared[column].fillna(fill_values[column])

    return prepared, usable_columns, fill_values


def apply_feature_schema(
    model_df: pd.DataFrame,
    feature_columns: list[str],
    fill_values: dict[str, float],
) -> pd.DataFrame:
    prepared = model_df.copy()
    for column in feature_columns:
        if column not in prepared.columns:
            prepared[column] = np.nan
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
        prepared[column] = prepared[column].fillna(fill_values.get(column, 0.0))
    return prepared[feature_columns]


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


def build_model_candidates(model_config: dict) -> dict[str, object]:
    task = model_config.get("task", "classification")
    family = model_config.get("model_family", "baseline")
    random_state = int(model_config.get("random_state", 42))

    models: dict[str, object] = {}
    if family in {"baseline", "all"}:
        models.update(get_baseline_models(task, model_config.get("baseline", {})))
    if family in {"tree", "all"}:
        models.update(get_tree_models(task, random_state, model_config.get("tree", {})))
    if not models:
        raise ValueError(f"No models available for family={family}")
    return models


def choose_best_model(results: dict[str, dict[str, float]], task: str, selection_metric: str) -> str:
    if selection_metric not in next(iter(results.values())):
        raise ValueError(f"Selection metric '{selection_metric}' not found in evaluation results")

    reverse = task != "regression" or selection_metric not in {"mae", "rmse"}
    return sorted(
        results,
        key=lambda name: results[name][selection_metric],
        reverse=reverse,
    )[0]


def save_model_bundle(bundle: dict, model_dir: Path) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)
    with (model_dir / "bundle.pkl").open("wb") as handle:
        pickle.dump(bundle, handle)


def load_model_bundle(bundle_path: Path) -> dict:
    with bundle_path.open("rb") as handle:
        return pickle.load(handle)


def resolve_prediction_date(feature_df: pd.DataFrame, requested_date: str | None) -> pd.Timestamp:
    available_dates = sorted(pd.to_datetime(feature_df["trade_date"]).dropna().unique())
    if not available_dates:
        raise ValueError("No trade dates available in processed features")

    if requested_date in {None, "today"}:
        target_date = pd.Timestamp(date.today())
    else:
        target_date = pd.Timestamp(requested_date)

    eligible_dates = [value for value in available_dates if value <= target_date]
    return eligible_dates[-1] if eligible_dates else available_dates[-1]
