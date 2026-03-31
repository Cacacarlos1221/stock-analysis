"""Market-relative feature generation."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_market_features(
    df: pd.DataFrame,
    benchmark_df: pd.DataFrame | None = None,
    date_col: str = "trade_date",
    group_col: str = "symbol",
    close_col: str = "close",
    benchmark_symbol: str | None = None,
    regime_window: int = 20,
    bullish_threshold: float = 0.02,
    bearish_threshold: float = -0.02,
    volatility_threshold: float = 0.02,
) -> pd.DataFrame:
    result = df.copy()
    result[date_col] = pd.to_datetime(result[date_col])
    result = result.sort_values([group_col, date_col])
    result["return_1d"] = result.groupby(group_col, group_keys=False)[close_col].pct_change()

    benchmark_source = benchmark_df
    if benchmark_source is None and benchmark_symbol is not None:
        benchmark_source = result[result[group_col] == benchmark_symbol][[date_col, close_col]].copy()

    if benchmark_source is None:
        raise ValueError("benchmark_df or benchmark_symbol must be provided")

    benchmark = benchmark_source.copy()
    benchmark[date_col] = pd.to_datetime(benchmark[date_col])
    benchmark = benchmark.sort_values(date_col)
    benchmark["benchmark_return_1d"] = benchmark[close_col].pct_change()
    benchmark = benchmark[[date_col, "benchmark_return_1d"]].drop_duplicates(subset=[date_col], keep="last")

    result = result.merge(benchmark, on=date_col, how="left")
    result["relative_return_vs_benchmark"] = result["return_1d"] - result["benchmark_return_1d"]

    rolling_mean = benchmark["benchmark_return_1d"].rolling(
        window=regime_window,
        min_periods=regime_window,
    ).mean()
    rolling_vol = benchmark["benchmark_return_1d"].rolling(
        window=regime_window,
        min_periods=regime_window,
    ).std()

    regime = np.where(
        rolling_mean >= bullish_threshold,
        "bull",
        np.where(rolling_mean <= bearish_threshold, "bear", "sideways"),
    )
    regime = np.where(rolling_vol >= volatility_threshold, "high_vol", regime)

    benchmark_regime = benchmark.copy()
    benchmark_regime["market_regime"] = regime
    result = result.merge(
        benchmark_regime[[date_col, "market_regime"]],
        on=date_col,
        how="left",
    )
    return result
