# Technical Requirements Document (TRD)
## Indian Stock Tracker – Version 1.3

---

### 1. Architecture Overview

| Layer | Components | Responsibility |
|-------|------------|----------------|
| **Data Layer** | SQLAlchemy ORM models (Asset, DailyPrice, Suggestion, MutualFundAsset, MutualFundSuggestion, schema_version) | Persist assets, daily OHLCV prices, and generated suggestions in SQLite. Separate database for mutual funds (mutual_funds.db). Auto-migration with schema version tracking (v2.0). |
| **Service Layer** | data_sources.py - DataSource abstraction with: NSESource, YFinanceSource, MutualFundSource | Fetch raw market data from external providers with automatic fallback. |
| **Business Logic** | scoring2.py - calculate_score(), generate_suggestions(), calculate_mf_score(), generate_mf_suggestions() | Compute enhanced composite scores (momentum, volume, RSI, MA, close strength, gap) and persist top-N suggestions. |
| **Orchestration** | data_fetcher.py - fetch_and_store(); run_daily.py - end-to-end daily job; run.py - unified entry point | Coordinate fetch -> store -> score -> output. |
| **CLI** | cli.py - argparse entry point | Query suggestions for a given date (default: latest); auto-generates if missing. |
| **Web UI** | flask_app.py + Jinja2 templates + Tailwind CSS + Chart.js | Modern fintech UI with dark/light theme, browse DB, filter/sort, JSON APIs. |

---

### 2. Data Flow

1. **Daily Job** (run_daily.py -> run.py)
   - Calls data_fetcher.fetch_and_store() -> iterates DEFAULT_SYMBOLS, dynamically generated from NSE Nifty 50 and mutual fund codes.
   - For each symbol, tries SOURCES in order (NSESource -> YFinanceSource -> MutualFundSource).
   - Inserts/updates DailyPrice rows (last 60 trading days).
2. **Scoring** (scoring2.generate_suggestions())
   - Queries all distinct dates from the last 60 days in DailyPrice.
   - Computes enhanced scores: momentum (20-day ROC), volume factor, RSI, MA, close strength, gap signals.
   - Composite score = momentum * 0.7 + volume_factor * 0.3 (plus additional factors).
   - Inserts top 50 rows per date into Suggestion (2145+ suggestions across 43+ dates).
3. **Consumption**
   - CLI (cli.py) queries Suggestion for requested date; auto-generates if missing.
   - Web UI serves paginated tables, JSON endpoints, interactive charts.

---

### 3. Mutual Fund Implementation

#### 3.1 Data Source
- Source: MutualFundSource in data_sources.py
- API: TigZig API (scheme discovery + NAV data)
- Symbol Format: TigZig scheme code (numeric)
- Filtering: Direct Growth plans only (plan="Direct", option="Growth")

#### 3.2 Database Schema
- Separate Database: mutual_funds.db
- Tables:
  - mutual_fund_assets: scheme_code (PK), scheme_name, fund_house, type, latest_nav_date
  - mutual_fund_suggestions: id, asset_id (FK), date, score, reasoning
- Auto-Migration: _add_missing_mutual_fund_columns() runs on every get_mutual_fund_session()

#### 3.3 Scoring Methodology
- Returns: 1Y, 3Y, 5Y CAGR (1Y required; 3Y/5Y optional)
- Volatility: Annualized standard deviation of daily returns
- Score Formula:
  - If 5Y available: score = score_1y * 0.30 + score_3y * 0.40 + score_5y * 0.30
  - Otherwise: score = score_1y * 0.40 + score_3y * 0.60
- Percentile Ranking: Within category
- NaN Handling: Skip to prevent IntegrityError

#### 3.4 Categories
- Large Cap, Mid Cap, Small Cap, Debt (18 sub-categories)

#### 3.5 Processing Pipeline
- mutual_fund_db.py main function:
  1. Dynamic scheme discovery with pagination (fetch_all_schemes_for_category())
  2. Direct Growth filtering (plan="Direct", option="Growth")
  3. Sequential NAV fetching (avoid 429 rate limits)
  4. Freshness check (is_fund_recent()) - max 730 days old, at least 1 NAV in 365 days
  5. Returns & volatility calculation (1Y, 3Y, 5Y CAGR)
  6. Percentile ranking within category
  7. Store top 45 per category (target 30+)
  8. Export CSV files

#### 3.6 Rate Limit Handling
- Exponential backoff retry (max 3 retries, base 2s delay, max 60s)
- Sequential processing (no parallel threads)
- REQUEST_DELAY = 0.3 seconds between requests
- Skip logic: categories with >=30 existing DB funds skipped

#### 3.7 Freshness Filtering
- MAX_FUND_AGE_DAYS = 730 (2 years)
- MAX_NO_RECENT_DATA_DAYS = 365 (1 year)
- latest_nav_date column for fast display filtering

#### 3.8 Web UI Integration
- Routes: /mutual-funds, /mutual-funds/<scheme_code>, /top-mutual-funds
- Category filter: /mutual-funds?category=large_cap
- Freshness filter: latest_nav_date >= today - 730 days
- Error handling: categorize_error() maps API failures to friendly error pages

---

### 4. Schema Version Tracking

- Schema version table: schema_version (key, value) in both databases
- Current version: 2.0
- Functions: _get_schema_version(), _set_schema_version() in models.py
- Auto-migration: get_session() and get_mutual_fund_session() automatically create missing tables/columns

---

### 5. Enhanced Scoring Engine (scoring2.py)

Additional factors beyond momentum * 0.7 + volume_factor * 0.3:
- RSI: Relative Strength Index (overbought/oversold)
- Moving Average: Price vs. MA trend signal
- Close Strength: Position of close within daily range
- Gap-Up Detection: Significant overnight price gaps

---

### 6. Dependencies

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
matplotlib>=3.7
seaborn>=0.12
plotly>=5.15
scikit-learn>=1.3

Python >= 3.10 required.

---

### 7. Configuration

| File / Variable | Purpose |
|-----------------|---------|
| data_fetcher.DEFAULT_SYMBOLS | Dynamically generated (Nifty 50 + mutual fund codes) |
| data_fetcher.SOURCES | Ordered DataSource instances for fallback |
| scoring2.MOMENTUM_WEIGHT, VOLUME_WEIGHT | Scoring weights (default 0.7 / 0.3) |
| flask_app.py port | Default 8080 |
| mutual_fund_db.py TOP_N | 45 (target 30+ per category) |
| mutual_fund_db.py REQUEST_DELAY | 0.3 seconds |
| mutual_fund_db.py MAX_FUND_AGE_DAYS | 730 |
| mutual_fund_db.py MAX_NO_RECENT_DATA_DAYS | 365 |

---

### 8. Security

- No secrets required; all data sources are public.
- SQLite files stored locally; no network exposure.
- Flask in dev mode; production should use gunicorn + nginx with restricted access.

---

### 9. Performance Targets

| Operation | Target |
|-----------|--------|
| Fetch single symbol (NSE) | <= 10 s |
| Fetch single symbol (Yahoo fallback) | <= 5 s |
| Fetch mutual fund NAV (per fund) | <= 5 s |
| Score 200 symbols x 250 days | <= 3 s |
| Generate 60-day suggestions | <= 30 s |
| CLI latency | <= 5 s |
| Web UI page load (100k rows) | <= 2 s |
| Mutual fund refresh (154 funds) | <= 5 min |

---

### 10. Testing Strategy

| Level | Scope | Tools |
|-------|-------|-------|
| Unit | data_sources, scoring2, data_fetcher, error handling, freshness | pytest, pytest-mock |
| Integration | run_daily.py end-to-end | pytest, sqlite3 in-memory |
| Coverage Goal | >= 80 % | pytest-cov |

---

### 11. Deployment & Operations

1. **Setup**
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

2. **Manual Run**
python run.py, python run_daily.py, python mutual_fund_db.py, python cli.py, python flask_app.py

3. **Scheduling (cron)**
0 18 * * * /path/to/run_daily.py, 0 19 * * * /path/to/mutual_fund_db.py

4. **GitHub Actions**: .github/workflows/update-stock-data.yml runs daily at 01:47 UTC (07:17 IST)

---

### 12. Extensibility Points

| Extension | Where to Modify |
|-----------|-----------------|
| New data source | Implement DataSource in data_sources.py |
| New scoring factor | Add function in scoring2.py |
| New asset type | Add type in DEFAULT_SYMBOLS |
| Additional endpoint | Add route in flask_app.py |
| ML model | Replace scoring functions with model inference |
| New mutual fund category | Add to mutual_fund_db.py |
| New theme token | Add to CSS variables in static/style.css |
| Schema migration | Bump version in init_db() |

---

### 13. Web UI Architecture

- Base Template: templates/base.html - Tailwind CSS, Chart.js, Lucide icons, dark/light theme toggle
- Design System: CSS variables in static/style.css for light/dark tokens
- Pages: /, /stocks, /stocks/<id>, /mutual-funds, /mutual-funds/<scheme_code>, /top-mutual-funds, /prices, /suggestions, /search, /gainers-losers, /error
- JSON APIs: /api/stocks, /api/prices, /api/suggestions, /api/mutual-funds
- Demo Data: static/demo_data.js mirrors real API response shape

---

### 14. Documentation

- README.md - Installation, usage, scheduling
- PRD.md - Product requirements (this repo)
- TRD.md - Technical requirements (this document)
- DEPLOYMENT.md - GitHub Actions workflow
- IMPLEMENTATION_PLAN.md - Chart implementation plan
- memory-bank/ - Persistent context files
- docs/superpowers/specs/ - Design specs
- Inline docstrings on all public functions/classes

---

*Document Version: 1.3*
*Last Updated: 2026-09-03