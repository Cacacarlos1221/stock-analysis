# Data Column Mapping

This document records the current raw price datasets under `data/raw/prices/` and maps their source columns to a canonical feature vocabulary for downstream feature engineering and model training.

## Raw Datasets

### `stock_history.csv`

Observed shape during migration:
- Rows: 120
- Columns: 17

Source columns:

| Source Column | Canonical Name | Notes |
| --- | --- | --- |
| 日期 | `trade_date` | Trading date in `YYYY-MM-DD` format. |
| 股票代码 | `symbol` | A-share security code; some rows may parse as integers and should be zero-padded to 6 digits. |
| 股票名称 | `name` | Display name. |
| 昨日收盘 | `prev_close` | Previous close; missing in the earliest row of each symbol sample. |
| 今日开盘 | `open` | Session open price. |
| 今日收盘 | `close` | Session close price. |
| 涨跌幅% | `pct_change` | Percentage return in percent units, not decimal units. |
| 最高价 | `high` | Session high. |
| 最低价 | `low` | Session low. |
| 成交量 | `volume` | Trading volume. |
| 成交额 | `turnover` | Trading amount; currently sparsely populated. |
| MA5 | `ma_5` | 5-day moving average of close. |
| MA10 | `ma_10` | 10-day moving average of close. |
| MA20 | `ma_20` | 20-day moving average of close. |
| MA5量 | `volume_ma_5` | 5-day moving average of volume. |
| MA10量 | `volume_ma_10` | 10-day moving average of volume. |
| MA20量 | `volume_ma_20` | 20-day moving average of volume. |

### `daily_data.csv`

Observed shape during migration:
- Rows: 12
- Columns: 34

Source columns:

| Source Column | Canonical Name | Notes |
| --- | --- | --- |
| 日期 | `trade_date` | Trading date in `YYYY-MM-DD` format. |
| 股票代码 | `symbol` | A-share security code; normalize to 6 digits. |
| 股票名称 | `name` | Display name. |
| 昨日收盘 | `prev_close` | Previous close price. |
| 今日开盘 | `open` | Session open price. |
| 今日收盘 | `close` | Session close price. |
| 涨跌幅% | `pct_change` | Percentage return in percent units. |
| 最高价 | `high` | Session high. |
| 最低价 | `low` | Session low. |
| 成交量 | `volume` | Trading volume. |
| 成交额 | `turnover` | Trading amount. |
| 委买 | `bid_volume` | Aggregated bid-side queued volume from realtime snapshot. |
| 委卖 | `ask_volume` | Aggregated ask-side queued volume from realtime snapshot. |
| 换手率% | `turnover_rate` | Percentage value, not decimal unit. |
| 振幅% | `amplitude` | Intraday amplitude in percent. |
| 量比 | `volume_ratio` | Volume ratio. |
| 市盈率 | `pe_ratio` | Price-to-earnings ratio; may contain text such as `亏损`. |
| 总市值 | `total_market_cap` | Total market capitalization. |
| 流通市值 | `float_market_cap` | Free-float market capitalization. |
| MA5 | `ma_5` | 5-day moving average of close. |
| MA10 | `ma_10` | 10-day moving average of close. |
| MA20 | `ma_20` | 20-day moving average of close. |
| MACD | `macd` | MACD line. |
| MACD信号 | `macd_signal` | MACD signal line. |
| KDJ-K | `kdj_k` | KDJ K value. |
| KDJ-D | `kdj_d` | KDJ D value. |
| KDJ-J | `kdj_j` | KDJ J value. |
| RSI6 | `rsi_6` | 6-day RSI. |
| RSI12 | `rsi_12` | 12-day RSI. |
| 主力净流入 | `main_net_inflow` | Main capital net inflow. |
| 所属板块 | `sector_name` | Sector classification. |
| 板块涨幅% | `sector_pct_change` | Sector return in percent units. |
| 涨跌家数比 | `advance_decline_ratio` | Market breadth ratio. |
| 大盘成交额 | `market_turnover` | Broad market turnover. |

## Alignment Notes

- `stock_history.csv` contains the minimum OHLCV + moving average fields needed for price-based feature generation.
- `daily_data.csv` already contains several technical and market context fields, but the Phase 2 feature pipeline should recompute derived features from raw price columns where possible to keep training and inference consistent.
- Canonical names above use snake_case English fields so downstream code can stay stable even if raw CSV headers remain in Chinese.
