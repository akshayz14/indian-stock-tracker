# Technical Requirements Document (TRD)
## Indian Stock Tracker – Version 1.2

---

### 1. Architecture Overview

| Layer | Components | Responsibility |
|-------|------------|----------------|
| **Data Layer** | SQLAlchemy ORM models (`Asset`, `DailyPrice`, `Suggestion`, `MutualFundAsset`, `MutualFundSuggestion`) | Persist assets, daily OHLCV prices, and generated suggestions in SQLite. Separate database for mutual funds (`mutual_funds.db`). |
| **Service Layer** | `data_sources.py` – `DataSource` abstraction with implementations: `NSESource`, `YFinanceSource`, `MutualFundSource` | Fetch raw market data from external providers with automatic fallback. |
| **Business Logic** | `scoring.py` – `calculate_momentum()`, `calculate_volume_factor()`, `generate_suggestions()` | Compute composite scores and persist top‑N suggestions. |
| **Orchestration** | `data_fetcher.py` – `fetch_and_store()`; `run_daily.py` – end‑to‑end daily job | Coordinate fetch → store → score → output. |
| **CLI** | `cli.py` – `argparse` entry point | Query suggestions for a given date (default: latest available). |
| **Web UI** | `flask_app.py` + Jinja2 templates (`templates/*.html`) | Browse DB, filter/sort, JSON APIs (`/api/stocks`, `/api/prices`, `/mutual-funds`). |

---

### 2. Data Flow

1. **Daily Job** (`run_daily.py`)
   - Calls `data_fetcher.fetch_and_store()` → iterates `DEFAULT_SYMBOLS`, dynamically generated from NSE Nifty 50 symbols and mutual fund codes.
   - For each symbol, tries `SOURCES` in order (`NSESource` → `YFinanceSource` → `MutualFundSource`).
   - Inserts/updates `DailyPrice` rows.
2. **Scoring** (`scoring.generate_suggestions()`)
   - Reads latest `DailyPrice.date`.
   - Computes momentum (e.g., 20‑day ROC) and volume factor (volume vs. 20‑day avg).
   - Composite score = `momentum * 0.7 + volume_factor * 0.3`.
   - Inserts top 50 rows into `Suggestion`.
3. **Consumption**
   - CLI (`cli.py`) queries `Suggestion` for requested date.
   - Web UI (`flask_app.py`) serves paginated tables and JSON endpoints.

---

### 3. Mutual Fund Implementation

#### 3.1 Data Source
- **Source**: `MutualFundSource` in `data_sources.py`
- **API**: mfapi.in (free Indian mutual fund NAV API)
- **Data**: NAV (Net Asset Value) history for mutual fund schemes
- **Symbol Format**: mfapi.in scheme code (e.g., "0P0000XVTS")

#### 3.2 Database Schema
- **Separate Database**: `mutual_funds.db` (isolated from `stocks.db`)
- **Tables**:
  - `mutual_fund_assets`: scheme_code (PK), scheme_name, fund_house, type (category)
  - `mutual_fund_suggestions`: id, asset_id (FK), date, score, reasoning

#### 3.3 Scoring Methodology
- **Returns Calculated**: 1Y, 3Y, 5Y CAGR returns
- **Volatility**: Annualized standard deviation of daily returns
- **Score Formula**:
  - If 5Y data available: `score = score_1y * 0.30 + score_3y * 0.40 + score_5y * 0.30`
  - Otherwise: `score = score_1y * 0.40 + score_3y * 0.60`
- **Percentile Ranking**: Returns ranked within category

#### 3.4 Categories
- Large Cap Funds
- Mid Cap Funds
- Small Cap Funds
- Debt Funds

#### 3.5 Processing Pipeline
- `mutual_fund_db.py` main function:
  1. Fetch all schemes from mfapi.in
  2. Filter for Direct Growth funds
  3. Calculate returns and volatility
  4. Score funds within each category
  5. Store top 50 per category in database
  6. Export to CSV files (`top_large_cap_funds.csv`, etc.)

#### 3.6 Web UI Integration
- Route: `/mutual-funds`
- Category filtering via URL parameter: `/mutual-funds?category=large_cap`
- Template: `templates/mutual_funds.html`

---

### 4. Data Model (SQLAlchemy)

| Table | Key Columns | Indexes |
|-------|-------------|---------|
| `assets` | `id` (PK), `symbol`, `name`, `type` | `symbol` (unique) |
| `daily_prices` | `id` (PK), `asset_id` (FK), `date`, `open`, `high`, `low`, `close`, `volume` | `(asset_id, date)` unique |
| `suggestions` | `id` (PK), `date`, `asset_id` (FK), `score`, `reasoning` | `(date, asset_id)` unique |
| `mutual_fund_assets` | `id` (PK), `scheme_code`, `scheme_name`, `fund_house`, `type` | `scheme_code` (unique) |
| `mutual_fund_suggestions` | `id` (PK), `asset_id` (FK), `date`, `score`, `reasoning` | `(date, asset_id)` unique |

---

### 5. Dependencies (from `requirements.txt`)

```
pandas>=2.0
numpy>=1.24
yfinance>=0.2
nsepy>=0.7
requests>=2.31
beautifulsoup4>=4.12
python-dotenv>=1.0
flask>=3.0
sqlalchemy>=2.0
apscheduler>=3.10
```

Python ≥ 3.10 required.

---

### 6. Configuration

| File / Variable | Purpose |
|-----------------|---------|
| `data_fetcher.DEFAULT_SYMBOLS` | Dynamically generated list of `(symbol, type)` tuples, including Nifty 50 equities and mutual fund scheme codes. |
| `data_fetcher.SOURCES` | Ordered list of `DataSource` instances for fallback. |
| `scoring.MOMENTUM_WEIGHT`, `VOLUME_WEIGHT` | Scoring weights (default 0.7 / 0.3). |
| `flask_app.py` port | Default 8080 (avoid macOS AirPlay on 5000). |
| `.env` (optional) | Future API keys (Alpha Vantage, Finnhub). |

---

### 7. Security

- No secrets required; all data sources are public.
- SQLite file (`stocks.db`) stored locally; no network exposure.
- Mutual funds database (`mutual_funds.db`) stored locally; no network exposure.
- Flask binds to `0.0.0.0` on port 8080 in development mode; production deployment should use a reverse proxy (e.g., gunicorn + nginx) with restricted access.

---

### 8. Performance Targets

| Operation | Target |
|-----------|--------|
| Fetch single symbol (NSE) | ≤ 10 s |
| Fetch single symbol (Yahoo fallback) | ≤ 5 s |
| Fetch mutual fund NAV | ≤ 5 s |
| Scoring 200 symbols × 250 days | ≤ 3 s |
| CLI latency (query + print) | ≤ 5 s |
| Web UI page load (100k rows) | ≤ 2 s |

---

### 9. Testing Strategy

| Level | Scope | Tools |
|-------|-------|-------|
| Unit | `data_sources`, `scoring`, `data_fetcher` | `pytest`, `pytest-mock` |
| Integration | `run_daily.py` end‑to‑end (temp DB) | `pytest`, `sqlite3` in‑memory |
| Coverage Goal | ≥ 80 % | `pytest-cov` |

---

### 10. Deployment & Operations

1. **Setup**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Manual Run**
   ```bash
   python run_daily.py
   python cli.py            # or python cli.py --date 2026-07-24
   python flask_app.py      # open http://localhost:8080
   python mutual_fund_db.py  # fetch and store mutual fund data
   ```
3. **Scheduling (cron)**
   ```cron
   0 18 * * * /path/to/venv/bin/python /path/to/run_daily.py >> /path/to/logs/daily.log 2>&1
   0 19 * * * /path/to/venv/bin/python /path/to/mutual_fund_db.py >> /path/to/logs/mf_daily.log 2>&1
   ```
4. **Logs** – Write to `logs/` (create if missing); rotate weekly.

---

### 11. Extensibility Points

| Extension | Where to Modify |
|-----------|-----------------|
| New data source | Implement `DataSource` in `data_sources.py`; prepend to `SOURCES`. |
| New scoring factor | Add function in `scoring.py`; adjust `generate_suggestions()`. |
| New asset type | Add `type` value in `DEFAULT_SYMBOLS`; ensure source supports it. |
| Additional API endpoint | Add route in `flask_app.py`; create template if UI needed. |
| ML model | Replace `calculate_momentum`/`calculate_volume_factor` with model inference. |

---

### 12. Documentation

- **README.md** – Installation, usage, scheduling, configuration.
- **PRD.md** – Product requirements (this repo).
- **TRD.md** – Technical requirements (this document).
- Inline docstrings on all public functions/classes.

---

*Document Version: 1.2*  
*Last Updated: 2026-08-21*