# Stock Prediction Project Specification

## 1. Project Overview and Goals

### 1.1 Background

This project extends the current stock monitoring and historical data collection repository into a full stock prediction system. The existing codebase already gathers A-share market data and provides monitoring utilities. The next stage is to build a reproducible pipeline that collects multi-source data, engineers predictive features, trains forecasting models, evaluates performance, and serves daily predictions for selected stocks and market benchmarks.

### 1.2 Project Vision

The system should support end-to-end stock analysis for short-term directional prediction and return forecasting. It should combine structured market data with event-driven signals such as news, seasonal patterns, and broader market indicators, then generate practical outputs for research and decision support.

### 1.3 Core Goals

1. Build a centralized dataset for stock prediction using historical prices, technical indicators, news-derived signals, calendar effects, and market-wide indicators.
2. Predict short-horizon outcomes such as next-day return, next-day direction, and short rolling trend probability.
3. Provide a repeatable workflow for data ingestion, feature generation, model training, backtesting, and inference.
4. Support experimentation with both baseline statistical models and more advanced machine learning models.
5. Keep the system modular so data sources, features, and models can be swapped without large refactors.

### 1.4 Non-Goals

1. High-frequency trading or intraday microsecond execution.
2. Fully automated live order execution in the initial version.
3. Guaranteed investment performance.
4. Prediction for all global markets in the first phase. The initial focus is A-shares, with optional future expansion.

### 1.5 Success Criteria

1. Daily prediction pipeline runs successfully from raw data to output report.
2. Historical backtests can be reproduced from saved datasets and configuration.
3. Baseline models outperform naive benchmarks such as zero-return prediction or previous-day direction.
4. Prediction outputs include confidence, feature provenance, and evaluation metrics.

## 2. Data Sources

The prediction system should merge multiple signal categories. Each category should be stored with timestamps and symbol mappings so features can be aligned without lookahead bias.

### 2.1 Historical Prices

Purpose:
Provide the core time series for returns, volatility, momentum, trend, and technical indicators.

Required fields:
1. Trade date
2. Symbol / stock code
3. Open
4. High
5. Low
6. Close
7. Previous close
8. Volume
9. Turnover / amount
10. Turnover rate if available
11. Adjusted price series if available

Candidate sources:
1. Existing local CSV files such as `stock_history.csv` and `daily_data.csv`
2. `akshare` for A-share historical quotes and index data
3. Current Tencent / Sina-based scripts already present in the repository

Derived features:
1. Daily return, log return, cumulative return
2. Rolling moving averages
3. Volatility windows
4. Price momentum over 3/5/10/20 days
5. MACD, RSI, KDJ, Bollinger Bands, ATR
6. Gap features between previous close and open

### 2.2 News and Event Data

Purpose:
Capture sentiment shifts, company events, sector catalysts, and macro narratives that may affect future price movement.

Required inputs:
1. News title
2. News body or summary
3. Publish timestamp
4. Source
5. Related stock code or sector tag
6. Event category if available

Candidate sources:
1. Existing `events.jsonl`
2. Financial news APIs or scrapers added in later phases
3. Exchange announcements, earnings releases, and policy news

Derived features:
1. Sentiment score per article
2. Daily aggregated sentiment by stock
3. News volume per symbol and sector
4. Event flags such as earnings, regulation, mergers, guidance, suspension, policy announcement
5. NLP embeddings for advanced models

Notes:
News features must be strictly aligned by publication time so only information known before prediction time is used.

### 2.3 Seasonal Factors

Purpose:
Capture recurring calendar patterns in market behavior.

Feature candidates:
1. Day of week
2. Week of month
3. Month of year
4. Quarter
5. Trading day before / after holiday
6. Month-end / quarter-end flag
7. Earnings season flag
8. Lunar New Year or major China market holiday proximity

Rationale:
Seasonality can influence liquidity, sentiment, institutional flows, and sector rotation. These features are low-cost and often useful for baseline models.

### 2.4 Market Indicators

Purpose:
Measure the broader market context influencing individual stock behavior.

Candidate indicators:
1. Major indices such as SSE Composite, CSI 300, ChiNext, sector indices
2. Market breadth: advancing vs declining stocks
3. Market turnover and liquidity
4. Sector strength and relative sector return
5. Northbound capital flow if available
6. Margin financing / securities lending metrics if available
7. Interest rate proxies or bond yield proxies if available
8. Commodity or FX proxies relevant to specific sectors
9. Volatility proxies

Derived features:
1. Relative stock return vs benchmark
2. Beta-like rolling sensitivity
3. Market regime labels: bullish, bearish, sideways, high-volatility
4. Sector-relative momentum

### 2.5 Data Quality Requirements

1. All datasets must use a consistent symbol format.
2. Timestamps must be normalized to a single timezone.
3. Missing values must be explicitly handled and documented.
4. Corporate actions and suspended trading days should be accounted for where possible.
5. Each feature must be generated only from information available at or before prediction time.

## 3. Prediction Methodology

### 3.1 Prediction Targets

The project should support multiple supervised targets:

1. Regression target: next-day return
2. Binary classification target: next-day up/down direction
3. Optional multi-class target: strong up / flat / strong down
4. Optional horizon targets: 3-day and 5-day forward return

Initial recommendation:
Start with next-day direction classification and next-day return regression, since these are straightforward to evaluate and useful for downstream ranking.

### 3.2 Pipeline Stages

1. Data ingestion
2. Data cleaning and standardization
3. Feature engineering
4. Label generation
5. Train / validation / test split using time-based windows
6. Model training
7. Backtesting and performance evaluation
8. Daily inference and report generation

### 3.3 Feature Engineering Strategy

Feature groups:
1. Price-based features
2. Technical indicators
3. Volume and liquidity features
4. Market-relative features
5. News sentiment and event features
6. Seasonal and calendar features

Principles:
1. Use rolling windows to capture short-term and medium-term dynamics.
2. Avoid leakage by computing features only from past data.
3. Standardize feature generation so training and inference use the same logic.
4. Retain feature metadata for debugging and explainability.

### 3.4 Modeling Approach

Baseline models:
1. Naive persistence benchmark
2. Linear regression / logistic regression
3. Random forest
4. XGBoost or LightGBM

Advanced models:
1. LSTM / GRU for sequence modeling
2. Temporal CNN or Transformer-based time series models
3. Hybrid models that combine tabular features with text embeddings from news

Recommended phase rollout:
1. Phase 1: Baseline statistical and tree-based models
2. Phase 2: Sequence models on historical windows
3. Phase 3: Multimodal model combining price and text signals

Why this order:
Tree-based models are faster to iterate on, easier to debug, and strong baselines for structured financial features. Deep sequence models should only be added after the labeling, feature alignment, and evaluation pipeline are stable.

### 3.5 Training and Validation

1. Use chronological splits instead of random shuffling.
2. Prefer walk-forward validation for realistic evaluation.
3. Retrain on rolling windows if regime change sensitivity matters.
4. Record experiment parameters and metrics for comparison.

Example split:
1. Train: earliest 70%
2. Validation: next 15%
3. Test: latest 15%

Or:
Use rolling window backtests across multiple market periods.

### 3.6 Evaluation Metrics

Regression:
1. MAE
2. RMSE
3. Directional accuracy of predicted return sign
4. Information coefficient if ranking is used

Classification:
1. Accuracy
2. Precision / recall / F1
3. ROC-AUC
4. Confusion matrix
5. Balanced accuracy if class imbalance appears

Trading-oriented metrics:
1. Cumulative return from a simple strategy
2. Sharpe ratio
3. Maximum drawdown
4. Hit rate
5. Turnover

### 3.7 Backtesting Principles

1. Simulate predictions in chronological order.
2. Use realistic signal availability time.
3. Include transaction costs and slippage assumptions where possible.
4. Compare against benchmarks such as buy-and-hold and index returns.
5. Keep model evaluation separate from trading rule evaluation.

### 3.8 Inference Output

For each stock and prediction date, the system should output:
1. Predicted next-day return
2. Predicted direction probability
3. Confidence score
4. Top contributing features if explainability is enabled
5. Supporting market context summary

## 4. Tech Stack

### 4.1 Core Language

1. Python 3.11+ recommended

Reason:
The existing repository is Python-based, and Python has the strongest ecosystem for financial data processing, machine learning, and automation.

### 4.2 Data Processing

1. `pandas` for tabular processing
2. `numpy` for numerical operations
3. `pyarrow` for efficient local storage formats such as Parquet

### 4.3 Data Acquisition

1. `requests` for HTTP API calls
2. `akshare` for A-share market and macro data
3. Existing custom scripts for Tencent / Sina-compatible endpoints

### 4.4 Machine Learning

1. `scikit-learn` for baseline models and preprocessing
2. `xgboost` or `lightgbm` for gradient boosting
3. `torch` for LSTM / Transformer models in advanced phases

### 4.5 NLP / News Processing

1. `jieba` or equivalent Chinese tokenization tooling if needed
2. `transformers` for sentiment or embedding extraction in advanced phases
3. Optional lightweight sentiment scoring in early versions

### 4.6 Experiment Tracking and Configuration

1. YAML or TOML config files for model and pipeline settings
2. `mlflow` optional for experiment tracking
3. `.env` for API keys and environment-specific configuration

### 4.7 Storage

1. CSV for raw compatibility and quick inspection
2. Parquet for feature datasets and training tables
3. Optional SQLite or DuckDB for local analytical querying

### 4.8 Visualization and Reporting

1. `matplotlib` / `seaborn` for research plots
2. `plotly` optional for interactive dashboards
3. Markdown or HTML report generation for daily prediction summaries

### 4.9 Orchestration and Scheduling

1. Existing shell entrypoint `run.sh`
2. Cron for scheduled daily jobs
3. Optional workflow manager later if the pipeline grows

## 5. File Structure

The repository currently contains monitoring and data collection scripts. The target structure below keeps those capabilities while organizing the code into clear modules for prediction work.

```text
stock-analysis/
├── SPEC.md
├── README.md
├── requirements.txt
├── run.sh
├── .env.example
├── configs/
│   ├── data.yaml
│   ├── features.yaml
│   ├── model_baseline.yaml
│   └── model_sequence.yaml
├── data/
│   ├── raw/
│   │   ├── prices/
│   │   ├── news/
│   │   ├── market/
│   │   └── events/
│   ├── processed/
│   │   ├── features/
│   │   ├── labels/
│   │   └── merged/
│   └── artifacts/
│       ├── models/
│       ├── metrics/
│       └── reports/
├── notebooks/
│   ├── exploratory_analysis.ipynb
│   └── model_research.ipynb
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── collectors.py
│   │   ├── loaders.py
│   │   ├── validators.py
│   │   └── news_ingestion.py
│   ├── features/
│   │   ├── technical.py
│   │   ├── seasonal.py
│   │   ├── market.py
│   │   └── sentiment.py
│   ├── models/
│   │   ├── baseline.py
│   │   ├── tree_models.py
│   │   ├── sequence_models.py
│   │   └── predict.py
│   ├── training/
│   │   ├── dataset.py
│   │   ├── train.py
│   │   ├── evaluate.py
│   │   └── backtest.py
│   ├── reporting/
│   │   ├── daily_report.py
│   │   └── plots.py
│   └── utils/
│       ├── io.py
│       ├── logging.py
│       └── dates.py
├── scripts/
│   ├── collect_data.py
│   ├── build_features.py
│   ├── train_model.py
│   ├── run_backtest.py
│   └── generate_predictions.py
├── legacy/
│   ├── stock_monitor.py
│   ├── stock_utils.py
│   ├── data_collector.py
│   └── fetch_history.py
└── tests/
    ├── test_collectors.py
    ├── test_features.py
    ├── test_training.py
    └── test_backtest.py
```

### 5.1 Structure Notes

1. `legacy/` preserves the current repository scripts during the transition.
2. `src/` contains the long-term maintainable application code.
3. `scripts/` contains task-oriented CLI entrypoints.
4. `data/raw/` stores source snapshots, while `data/processed/` stores cleaned and engineered datasets.
5. `data/artifacts/` stores model files, evaluation output, and prediction reports.
6. `configs/` keeps feature and model settings versioned outside code.

## Recommended Initial Milestones

1. Normalize existing CSV and script outputs into a `data/raw/` layout.
2. Build a feature pipeline from historical prices and market indicators.
3. Add baseline next-day direction and return models.
4. Add backtesting and benchmark comparison.
5. Add news ingestion and sentiment features.
6. Add daily prediction report generation.

## Final Deliverable Expectations

The first production-ready version of this project should be able to:

1. Collect and update daily market data automatically.
2. Build a training dataset with aligned historical, market, news, and seasonal features.
3. Train at least one regression model and one classification model.
4. Evaluate models with both ML metrics and trading-oriented metrics.
5. Generate a daily prediction output for tracked stocks in a reproducible way.
