# Technical Requirements Document (TRD)
## Indian Stock Tracker – Version 1.0

---

### 1. Architecture Overview

| Layer | Components | Responsibility |
|-------|------------|----------------|
| **Data Layer** | SQLAlchemy ORM models (`Asset`, `DailyPrice`, `Suggestion`) | Persist assets, daily OHLCV prices, and generated suggestions in SQLite. |
| **Service Layer** | `data_sources.py` – `DataSource` abstraction with implementations: `NSESource`, `YFinanceSource`, `MutualFundSource` | Fetch raw market data from external providers with automatic fallback. |
| **Business Logic** | `scoring.py` – `calculate_momentum()`, `calculate_volume_factor()`, `generate_suggestions()` | Compute composite scores and persist top‑N suggestions. |
| **Orchestration** | `data_fetcher.py` – `fetch_and_store()`; `run_daily.py` – end‑to‑end daily job | Coordinate fetch → store → score → output. |
| **CLI** | `cli.py` – `argparse` entry point | Query suggestions for a given date (default: latest available). |
| **Web UI** | `flask_app.py` + Jinja2 templates (`templates/*.html`) | Browse DB, filter/sort, JSON APIs (`/api/stocks`, `/api/prices`). |

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

### 3. Data Model (SQLAlchemy)

| Table | Key Columns | Indexes |
|-------|-------------|---------|
| `assets` | `id` (PK), `symbol`, `name`, `type` | `symbol` (unique) |
| `daily_prices` | `id` (PK), `asset_id` (FK), `date`, `open`, `high`, `low`, `close`, `volume` | `(asset_id, date)` unique |
| `suggestions` | `id` (PK), `date`, `asset_id` (FK), `score`, `reasoning` | `(date, asset_id)` unique |

---

### 4. Dependencies (from `requirements.txt`)

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

### 5. Configuration

| File / Variable | Purpose |
|-----------------|---------|
| `data_fetcher.DEFAULT_SYMBOLS` | Dynamically generated list of `(symbol, type)` tuples, including Nifty 50 equities and mutual fund scheme codes. |
| `data_fetcher.SOURCES` | Ordered list of `DataSource` instances for fallback. |
| `scoring.MOMENTUM_WEIGHT`, `VOLUME_WEIGHT` | Scoring weights (default 0.7 / 0.3). |
| `flask_app.py` port | Default 8080 (avoid macOS AirPlay on 5000). |
| `.env` (optional) | Future API keys (Alpha Vantage, Finnhub). |

---

### 6. Security

- No secrets required; all data sources are public.
- SQLite file (`stocks.db`) stored locally; no network exposure.
- Flask binds to `0.0.0.0` on port 8080 in development mode; production deployment should use a reverse proxy (e.g., gunicorn + nginx) with restricted access.

---

### 7. Performance Targets

| Operation | Target |
|-----------|--------|
| Fetch single symbol (NSE) | ≤ 10 s |
| Fetch single symbol (Yahoo fallback) | ≤ 5 s |
| Scoring 200 symbols × 250 days | ≤ 3 s |
| CLI latency (query + print) | ≤ 5 s |
| Web UI page load (100k rows) | ≤ 2 s |

---

### 8. Testing Strategy

| Level | Scope | Tools |
|-------|-------|-------|
| Unit | `data_sources`, `scoring`, `data_fetcher` | `pytest`, `pytest-mock` |
| Integration | `run_daily.py` end‑to‑end (temp DB) | `pytest`, `sqlite3` in‑memory |
| Coverage Goal | ≥ 80 % | `pytest-cov` |

---

### 9. Deployment & Operations

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
   ```
3. **Scheduling (cron)**
   ```cron
   0 18 * * * /path/to/venv/bin/python /path/to/run_daily.py >> /path/to/logs/daily.log 2>&1
   ```
4. **Logs** – Write to `logs/` (create if missing); rotate weekly.

---

### 10. Extensibility Points

| Extension | Where to Modify |
|-----------|-----------------|
| New data source | Implement `DataSource` in `data_sources.py`; prepend to `SOURCES`. |
| New scoring factor | Add function in `scoring.py`; adjust `generate_suggestions()`. |
| New asset type | Add `type` value in `DEFAULT_SYMBOLS`; ensure source supports it. |
| Additional API endpoint | Add route in `flask_app.py`; create template if UI needed. |
| ML model | Replace `calculate_momentum`/`calculate_volume_factor` with model inference. |

---

### 11. Documentation

- **README.md** – Installation, usage, scheduling, configuration.
- **PRD.md** – Product requirements (this repo).
- **TRD.md** – Technical requirements (this document).
- Inline docstrings on all public functions/classes.

---

*Document Version: 1.1*  
*Last Updated: 2026-10-08*
