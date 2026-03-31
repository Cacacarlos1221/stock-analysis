"""Technical indicator feature generation."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd


def _ensure_sorted(
    df: pd.DataFrame,
    date_col: str,
    group_col: str | None,
) -> pd.DataFrame:
    sort_cols = [group_col, date_col] if group_col else [date_col]
    return df.sort_values(sort_cols).copy()


def _grouped_series(df: pd.DataFrame, group_col: str | None, column: str):
    if group_col:
        return df.groupby(group_col, group_keys=False)[column]
    return df[column]


def add_moving_averages(
    df: pd.DataFrame,
    close_col: str = "close",
    group_col: str | None = "symbol",
    windows: Sequence[int] = (5, 10, 20, 60),
) -> pd.DataFrame:
    result = df.copy()
    close_grouped = _grouped_series(result, group_col, close_col)

    for window in windows:
        result[f"ma_{window}"] = close_grouped.transform(
            lambda s, w=window: s.rolling(window=w, min_periods=w).mean()
        )
    return result


def add_macd(
    df: pd.DataFrame,
    close_col: str = "close",
    group_col: str | None = "symbol",
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    result = df.copy()
    close_grouped = _grouped_series(result, group_col, close_col)

    ema_fast = close_grouped.transform(
        lambda s: s.ewm(span=fast, adjust=False, min_periods=fast).mean()
    )
    ema_slow = close_grouped.transform(
        lambda s: s.ewm(span=slow, adjust=False, min_periods=slow).mean()
    )

    result["macd"] = ema_fast - ema_slow
    result["macd_signal"] = _grouped_series(result, group_col, "macd").transform(
        lambda s: s.ewm(span=signal, adjust=False, min_periods=signal).mean()
    )
    result["macd_hist"] = result["macd"] - result["macd_signal"]
    return result


def add_rsi(
    df: pd.DataFrame,
    close_col: str = "close",
    group_col: str | None = "symbol",
    periods: Sequence[int] = (6, 12, 14),
) -> pd.DataFrame:
    result = df.copy()

    def _calc_rsi(series: pd.Series, period: int) -> pd.Series:
        delta = series.diff()
        gain = delta.clip(lower=0.0)
        loss = -delta.clip(upper=0.0)
        avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
        rs = avg_gain / avg_loss.replace(0.0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(100).where(avg_loss.eq(0.0), rsi)

    grouped = _grouped_series(result, group_col, close_col)
    for period in periods:
        result[f"rsi_{period}"] = grouped.transform(lambda s, p=period: _calc_rsi(s, p))
    return result


def add_kdj(
    df: pd.DataFrame,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    group_col: str | None = "symbol",
    lookback: int = 9,
    smooth_k: int = 3,
    smooth_d: int = 3,
) -> pd.DataFrame:
    result = df.copy()

    if group_col:
        grouped = result.groupby(group_col, group_keys=False)
        low_min = grouped[low_col].transform(
            lambda s: s.rolling(window=lookback, min_periods=lookback).min()
        )
        high_max = grouped[high_col].transform(
            lambda s: s.rolling(window=lookback, min_periods=lookback).max()
        )
    else:
        low_min = result[low_col].rolling(window=lookback, min_periods=lookback).min()
        high_max = result[high_col].rolling(window=lookback, min_periods=lookback).max()

    denominator = (high_max - low_min).replace(0.0, np.nan)
    rsv = ((result[close_col] - low_min) / denominator) * 100
    result["_rsv"] = rsv

    if group_col:
        result["kdj_k"] = result.groupby(group_col, group_keys=False)["_rsv"].transform(
            lambda s: s.ewm(alpha=1 / smooth_k, adjust=False).mean()
        )
        result["kdj_d"] = result.groupby(group_col, group_keys=False)["kdj_k"].transform(
            lambda s: s.ewm(alpha=1 / smooth_d, adjust=False).mean()
        )
    else:
        result["kdj_k"] = rsv.ewm(alpha=1 / smooth_k, adjust=False).mean()
        result["kdj_d"] = result["kdj_k"].ewm(alpha=1 / smooth_d, adjust=False).mean()

    result["kdj_j"] = 3 * result["kdj_k"] - 2 * result["kdj_d"]
    result = result.drop(columns=["_rsv"])
    return result


def add_bollinger_bands(
    df: pd.DataFrame,
    close_col: str = "close",
    group_col: str | None = "symbol",
    window: int = 20,
    num_std: float = 2.0,
) -> pd.DataFrame:
    result = df.copy()
    grouped = _grouped_series(result, group_col, close_col)

    rolling_mean = grouped.transform(
        lambda s: s.rolling(window=window, min_periods=window).mean()
    )
    rolling_std = grouped.transform(
        lambda s: s.rolling(window=window, min_periods=window).std()
    )

    result["bollinger_mid"] = rolling_mean
    result["bollinger_upper"] = rolling_mean + num_std * rolling_std
    result["bollinger_lower"] = rolling_mean - num_std * rolling_std
    result["bollinger_bandwidth"] = (
        (result["bollinger_upper"] - result["bollinger_lower"]) / rolling_mean
    )
    return result


def add_atr(
    df: pd.DataFrame,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    group_col: str | None = "symbol",
    period: int = 14,
) -> pd.DataFrame:
    result = df.copy()
    if group_col:
        prev_close = result.groupby(group_col, group_keys=False)[close_col].shift(1)
    else:
        prev_close = result[close_col].shift(1)

    tr_components = pd.concat(
        [
            (result[high_col] - result[low_col]).abs(),
            (result[high_col] - prev_close).abs(),
            (result[low_col] - prev_close).abs(),
        ],
        axis=1,
    )
    result["true_range"] = tr_components.max(axis=1)
    result["atr"] = _grouped_series(result, group_col, "true_range").transform(
        lambda s: s.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    )
    return result


def add_technical_features(
    df: pd.DataFrame,
    date_col: str = "trade_date",
    group_col: str | None = "symbol",
    close_col: str = "close",
    high_col: str = "high",
    low_col: str = "low",
) -> pd.DataFrame:
    result = _ensure_sorted(df, date_col=date_col, group_col=group_col)
    result = add_moving_averages(result, close_col=close_col, group_col=group_col)
    result = add_macd(result, close_col=close_col, group_col=group_col)
    result = add_rsi(result, close_col=close_col, group_col=group_col)
    result = add_kdj(
        result,
        high_col=high_col,
        low_col=low_col,
        close_col=close_col,
        group_col=group_col,
    )
    result = add_bollinger_bands(result, close_col=close_col, group_col=group_col)
    result = add_atr(
        result,
        high_col=high_col,
        low_col=low_col,
        close_col=close_col,
        group_col=group_col,
    )
    return result
