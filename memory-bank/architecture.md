# Architecture Overview

## Layered Architecture

| Layer | Components | Responsibility |
|-------|------------|----------------|
| **Data Layer** | SQLAlchemy ORM models (`Asset`, `DailyPrice`, `Suggestion`, `MutualFundAsset`, `MutualFundSuggestion`, `schema_version`) | Persist assets, daily OHLCV prices, and generated suggestions in SQLite. Separate database for mutual funds (`mutual_funds.db`). Auto-migration with schema version tracking (v2.0). |
| **Service Layer** | `data_sources.py` – `DataSource` abstraction with implementations: `NSESource`, `YFinanceSource`, `MutualFundSource` | Fetch raw market data from external providers with automatic fallback. |
| **Business Logic** | `scoring2.py` – `calculate_score()`, `generate_suggestions()`, `calculate_mf_score()`, `generate_mf_suggestions()` | Compute enhanced composite scores (momentum, volume, RSI, MA, close strength, gap) and persist top‑N suggestions for both equities and mutual funds. |
| **Orchestration** | `data_fetcher.py` – `fetch_and_store()`; `run_daily.py` – end‑to‑end daily job; `run.py` – unified entry point | Coordinate fetch → store → score → output. |
| **CLI** | `cli.py` – `argparse` entry point | Query suggestions for a given date (default: latest available); auto-generates if missing. |
| **Web UI** | `flask_app.py` + Jinja2 templates (`templates/*.html`) + Tailwind CSS + Chart.js | Modern fintech UI with dark/light theme, browse DB, filter/sort, JSON APIs (`/api/stocks`, `/api/prices`, `/mutual-funds`). |

---

## Mutual Fund Implementation

### Data Source
- **Source**: `MutualFundSource` in `data_sources.py`
- **API**: TigZig API (primary source for scheme discovery and NAV data)
- **Data**: NAV (Net Asset Value) history for mutual fund schemes
- **Symbol Format**: TigZig scheme code (numeric)

### Database Schema
- **Separate Database**: `mutual_funds.db` (isolated from `stocks.db`)
- **Tables**:
  - `mutual_fund_assets`: scheme_code (PK), scheme_name, fund_house, type (category)
  - `mutual_fund_suggestions`: id, asset_id (FK), date, score, reasoning

### Scoring Methodology
- **Returns Calculated**: 1Y, 3Y, 5Y CAGR returns (3Y and 5Y optional - 1Y required minimum)
- **Volatility**: Annualized standard deviation of daily returns
- **Score Formula**:
  - If 5Y data available: `score = score_1y * 0.30 + score_3y * 0.40 + score_5y * 0.30`
  - Otherwise: `score = score_1y * 0.40 + score_3y * 0.60`
- **Percentile Ranking**: Returns ranked within category
- **Freshness Filter**: Funds must have NAV within 730 days (2 years) and at least one NAV within 365 days (1 year)

### Categories
- Large Cap Funds
- Mid Cap Funds
- Small Cap Funds
- Debt Funds (with 18 sub-categories: Liquid, Ultra Short Duration, Low Duration, Money Market, Short Duration, Medium Duration, Medium to Long Duration, Long Duration, Dynamic Bond, Corporate Bond, Credit Risk, Banking and PSU, Gilt, Gilt with 10 Year Constant Duration, Floater, Overnight, Arbitrage, Conservative Hybrid)

### Processing Pipeline
- `mutual_fund_db.py` main function:
  1. **Dynamic Scheme Discovery**: Search TigZig API with `plan="Direct"` and `option="Growth"` filters for each category
  2. **Pagination Handling**: Fetch all pages for each category/sub-category
  3. **Direct Growth Filtering**: Filter results for Direct Growth plan at API level
  4. **NAV Fetching**: Fetch NAV history for each fund (sequential processing to avoid rate limits)
  5. **Calculate Returns & Volatility**: 1Y, 3Y, 5Y CAGR returns and annualized volatility
  6. **Score Funds**: Within each category using percentile ranking
  7. **Store Top Funds**: Top 45 per category in database (target 30+ per category)
  8. **Export CSV**: `top_large_cap_funds.csv`, `top_mid_cap_funds.csv`, `top_small_cap_funds.csv`, `top_debt_funds.csv`

### Rate Limit Handling
- Exponential backoff retry logic in `get_json()` (max 3 retries, base delay 2s, max delay 60s)
- Sequential processing (no parallel threads) to avoid 429 errors
- `REQUEST_DELAY = 0.3` seconds between requests
- Skip logic: categories with ≥30 existing DB funds are skipped

### Web UI Integration
- Route: `/mutual-funds`
- Category filtering via URL parameter: `/mutual-funds?category=large_cap`
- Freshness filtering: Only shows funds with `latest_nav_date >= today - 730 days`

## Data Flow

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

## Configuration Points

- `data_fetcher.DEFAULT_SYMBOLS`: Dynamically generated list of `(symbol, type)` tuples, including Nifty 50 equities and mutual fund scheme codes.
- `data_fetcher.SOURCES`: Ordered list of `DataSource` instances for fallback.
- `scoring.MOMENTUM_WEIGHT`, `VOLUME_WEIGHT`: Scoring weights (default 0.7 / 0.3).
- `flask_app.py` port: Default 8080 (avoid macOS AirPlay on 5000).
- `.env` (optional): Future API keys (Alpha Vantage, Finnhub).
- **Mutual Fund Config** (in `mutual_fund_db.py`):
  - `TOP_N = 45` (target 30+ per category)
  - `REQUEST_DELAY = 0.3` seconds
  - `MAX_FUND_AGE_DAYS = 365` (relaxed for small/mid cap)
  - `MAX_NO_RECENT_DATA_DAYS = 730`

## Extensibility

- **New data source**: Implement `DataSource` in `data_sources.py`; prepend to `SOURCES`.
- **New scoring factor**: Add function in `scoring2.py`; adjust `generate_suggestions()`.
- **New asset type**: Add `type` value in `DEFAULT_SYMBOLS`; ensure source supports it.
- **Additional API endpoint**: Add route in `flask_app.py`; create template if UI needed.
- **ML model**: Replace `calculate_momentum`/`calculate_volume_factor` with model inference.
- **New mutual fund category**: Add to `DEBT_SUB_CATEGORIES` or new category in `mutual_fund_db.py`.