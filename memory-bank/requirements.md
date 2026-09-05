# Requirements

## Core Functional Requirements (from PRD)

1. **Data Fetching**
    - Pull OHLCV data for Nifty 50 equities from NSE India CSV with automatic fallback to Yahoo Finance (`yfinance`).
    - Fetch mutual fund data from TigZig API with dynamic scheme discovery, pagination, and Direct Growth filtering.

2. **Enhanced Scoring Engine**
    - Compute composite score: `momentum × 0.7 + volume_factor × 0.3` (with RSI, MA, close strength, gap).
    - Mutual fund: 1Y/3Y/5Y CAGR returns ranked within category.
    - Auto-generation on-demand via CLI.

3. **Persistence**
    - `stocks.db` with SQLAlchemy ORM + auto-migration (schema v2.0).
    - `mutual_funds.db` separate database with auto-migration.

4. **CLI**
    - `python cli.py [--date dd-mm-yyyy]` auto-generates if missing.

5. **Automation**
    - `run_daily.py` - equities (60-day window), cron scheduling.
    - `mutual_fund_db.py` - TigZig API, CSV exports, rate-limit handling.

6. **Web DB Browser**
    - Flask UI at `http://localhost:8080`.
    - Chart.js for charts, Tailwind CSS v4, dark/light theme.
    - Search, gainers/losers, dashboard, mutual fund filtering.

## Non-Functional Requirements

- **Performance**: Daily fetch ≥99%, CLI ≤5s, Web UI ≤2s, MF refresh ≤5min.
- **Constraints**: Python 3.10+, free APIs only (NSE, yfinance, TigZig), SQLite ≤200MB.
- **Data Integrity**: Direct Growth only, freshness filter (730/365 days), NaN handling.

## Future Enhancements
- ML scoring models, additional data sources, CSV exports, mobile UI, bond/derivatives support.

## Dependencies
pandas>=2.0, numpy>=1.24, yfinance>=0.2, nsepy>=0.7, requests>=2.31, beautifulsoup4>=4.12, python-dotenv>=1.0, flask>=3.0, sqlalchemy>=2.0, apscheduler>=3.10, matplotlib>=3.7, seaborn>=0.12, plotly>=5.15, scikit-learn>=1.3
