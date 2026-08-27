# Architecture Overview

## Layered Architecture

| Layer | Components | Responsibility |
|-------|------------|----------------|
| **Data Layer** | SQLAlchemy ORM models (`Asset`, `DailyPrice`, `Suggestion`, `MutualFundAsset`, `MutualFundSuggestion`) | Persist assets, daily OHLCV prices, and generated suggestions in SQLite. Separate database for mutual funds (`mutual_funds.db`). |
| **Service Layer** | `data_sources.py` – `DataSource` abstraction with implementations: `NSESource`, `YFinanceSource`, `MutualFundSource` | Fetch raw market data from external providers with automatic fallback. |
| **Business Logic** | `scoring2.py` – `calculate_score()`, `generate_suggestions()`, `calculate_mf_score()`, `generate_mf_suggestions()` | Compute composite scores (momentum, volume, RSI, MA, close strength, gap) and persist top‑N suggestions for both equities and mutual funds. |
| **Orchestration** | `data_fetcher.py` – `fetch_and_store()`; `run_daily.py` – end‑to‑end daily job | Coordinate fetch → store → score → output. |
| **CLI** | `cli.py` – `argparse` entry point | Query suggestions for a given date (default: latest available). |
| **Web UI** | `flask_app.py` + Jinja2 templates (`templates/*.html`) | Browse DB, filter/sort, JSON APIs (`/api/stocks`, `/api/prices`, `/mutual-funds`). |

---

## Mutual Fund Implementation

### Data Source
- **Source**: `MutualFundSource` in `data_sources.py`
- **API**: mfapi.in (free Indian mutual fund NAV API)
- **Data**: NAV (Net Asset Value) history for mutual fund schemes
- **Symbol Format**: mfapi.in scheme code (e.g., "0P0000XVTS")

### Database Schema
- **Separate Database**: `mutual_funds.db` (isolated from `stocks.db`)
- **Tables**:
  - `mutual_fund_assets`: scheme_code (PK), scheme_name, fund_house, type (category)
  - `mutual_fund_suggestions`: id, asset_id (FK), date, score, reasoning

### Scoring Methodology
- **Returns Calculated**: 1Y, 3Y, 5Y CAGR returns
- **Volatility**: Annualized standard deviation of daily returns
- **Score Formula**:
  - If 5Y data available: `score = score_1y * 0.30 + score_3y * 0.40 + score_5y * 0.30`
  - Otherwise: `score = score_1y * 0.40 + score_3y * 0.60`
- **Percentile Ranking**: Returns ranked within category

### Categories
- Large Cap Funds
- Mid Cap Funds
- Small Cap Funds
- Debt Funds

### Processing Pipeline
- `mutual_fund_db.py` main function:
  1. Fetch all schemes from mfapi.in
  2. Filter for Direct Growth funds
  3. Calculate returns and volatility
  4. Score funds within each category
  5. Store top 50 per category in database
  6. Export to CSV files (`top_large_cap_funds.csv`, etc.)

### Web UI Integration
- Route: `/mutual-funds`
- Category filtering via URL parameter: `/mutual-funds?category=large_cap`

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

## Extensibility

- **New data source**: Implement `DataSource` in `data_sources.py`; prepend to `SOURCES`.
- **New scoring factor**: Add function in `scoring2.py`; adjust `generate_suggestions()`.
- **New asset type**: Add `type` value in `DEFAULT_SYMBOLS`; ensure source supports it.
- **Additional API endpoint**: Add route in `flask_app.py`; create template if UI needed.
- **ML model**: Replace `calculate_momentum`/`calculate_volume_factor` with model inference.