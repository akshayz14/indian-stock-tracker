# Architecture Overview

## Layered Architecture

| Layer | Components | Responsibility |
|-------|------------|----------------|
| **Data Layer** | SQLAlchemy ORM models (`Asset`, `DailyPrice`, `Suggestion`) | Persist assets, daily OHLCV prices, and generated suggestions in SQLite. |
| **Service Layer** | `data_sources.py` – `DataSource` abstraction with implementations: `NSESource`, `YFinanceSource`, `MutualFundSource` | Fetch raw market data from external providers with automatic fallback. |
| **Business Logic** | `scoring.py` – `calculate_momentum()`, `calculate_volume_factor()`, `generate_suggestions()` | Compute composite scores and persist top‑N suggestions. |
| **Orchestration** | `data_fetcher.py` – `fetch_and_store()`; `run_daily.py` – end‑to‑end daily job | Coordinate fetch → store → score → output. |
| **CLI** | `cli.py` – `argparse` entry point | Query suggestions for a given date (default: latest available). |
| **Web UI** | `flask_app.py` + Jinja2 templates (`templates/*.html`) | Browse DB, filter/sort, JSON APIs (`/api/stocks`, `/api/prices`). |

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
- **New scoring factor**: Add function in `scoring.py`; adjust `generate_suggestions()`.
- **New asset type**: Add `type` value in `DEFAULT_SYMBOLS`; ensure source supports it.
- **Additional API endpoint**: Add route in `flask_app.py`; create template if UI needed.
- **ML model**: Replace `calculate_momentum`/`calculate_volume_factor` with model inference.