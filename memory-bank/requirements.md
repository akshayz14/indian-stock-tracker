# Requirements

## Core Functional Requirements (from PRD)

1. **Data Fetching**
   - Pull OHLCV data for Nifty 50 equities from NSE India CSV with automatic fallback to Yahoo Finance (`yfinance`).
   - Fetch mutual fund NAV data from mfapi.in API for Direct Growth funds.

2. **Scoring Engine**
   - Compute a composite score (momentum × 0.7 + volume_factor × 0.3) for equities.
   - Compute CAGR returns with volatility adjustment for mutual funds.
   - Generate top-N suggestions per asset type (equities and mutual funds).

3. **Persistence**
   - Store stocks, daily prices, and suggestions in `stocks.db` via SQLAlchemy ORM.
   - Store mutual fund assets and suggestions in separate `mutual_funds.db` database.

4. **CLI**
   - `python cli.py [--date YYYY-MM-DD]` prints top suggestions for a given date.

5. **Automation**
   - `run_daily.py` fetches, scores, stores, and prints equity suggestions; intended for cr   - `run_daily.py` fetches, scores, stores, and prints equity sugg fetches NAV, calculates scores, stores in DB, and exports to CSV.

6. **Web DB Browser**
   - Flask UI (`http://localhost:8080`) for exploring stocks, prices, suggestions, mutual funds, and JSON APIs.
   - Interactive charts using Chart.js for market overview, score distributions, and fund NAV history.
   - Search functionality for non-Nifty 50 stocks with live data from Yahoo Finance.
   - Gainers/Losers tracking page with bar charts.
   - Mutual fund category filtering and detail pages.
   - Dashboard overview with charts for total stocks, price records, suggestions, and latest data date.

## Non-Functional Requirements

- **Performance**
   - Daily fetch success rate ≥ 99% (fallback works for equities).
   - CLI output latency ≤ 5 s.
   - Web UI response ≤ 2 s for 100k rows.
   - Cron job runs without manual intervention.
   - Mutual fund data refresh takes ≤ 5 minutes (API-dependent).

- **Constraints**
   - Must run on macOS/Linux/Windows with Python 3.10+.
   - No external paid APIs; only free public data sources (NSE CSV, yfinance, mfapi.in).
   - SQLite database size ≤ 200 MB for typical usage.
   - Separate databases for equities (`stocks.db`) and mutual funds (`mutual_funds.db`).

- **Data Integrity**
   - Mutual fund schemes filtered to Direct Growth category only.
   - NAV history minimum 60 records for return calculations.
   - Scoring percentile ranking within respective categories.

## Future Enhancements (may become requirements later)

- Add machine‑learning scoring models for both equities and mutual funds.
- Support additional data sources (Alpha Vantage, Finnhub) for equity data.
- Export suggestions to CSV/Excel format for both equities and mutual funds.
- Mobile‑friendly UI with responsive Chart.js charts.
- Add support for bond and derivative data sources.
