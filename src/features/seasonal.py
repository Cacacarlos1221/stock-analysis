"""Seasonal and calendar-based feature generation."""

from __future__ import annotations

import pandas as pd


def add_seasonal_features(
    df: pd.DataFrame,
    date_col: str = "trade_date",
) -> pd.DataFrame:
    result = df.copy()
    trade_dates = pd.to_datetime(result[date_col])
    unique_dates = pd.Series(sorted(trade_dates.dropna().unique()))

    prev_trade = unique_dates.shift(1)
    next_trade = unique_dates.shift(-1)
    calendar = pd.DataFrame(
        {
            "trade_date": unique_dates,
            "days_since_prev_trade": (unique_dates - prev_trade).dt.days,
            "days_until_next_trade": (next_trade - unique_dates).dt.days,
        }
    )

    calendar["is_pre_holiday"] = calendar["days_until_next_trade"].fillna(0).gt(3).astype(int)
    calendar["is_post_holiday"] = calendar["days_since_prev_trade"].fillna(0).gt(3).astype(int)

    result[date_col] = trade_dates
    result = result.merge(
        calendar.rename(columns={"trade_date": date_col}),
        on=date_col,
        how="left",
    )

    result["day_of_week"] = result[date_col].dt.dayofweek
    result["day_of_month"] = result[date_col].dt.day
    result["week_of_year"] = result[date_col].dt.isocalendar().week.astype(int)
    result["month"] = result[date_col].dt.month
    result["quarter"] = result[date_col].dt.quarter
    result["is_month_end"] = result[date_col].dt.is_month_end.astype(int)
    result["is_month_start"] = result[date_col].dt.is_month_start.astype(int)
    result["is_quarter_end"] = result[date_col].dt.is_quarter_end.astype(int)
    result["is_quarter_start"] = result[date_col].dt.is_quarter_start.astype(int)
    return result
