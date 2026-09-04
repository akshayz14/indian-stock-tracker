# Current State (as of 2026-09-09)

## Repository Status
- All core files present and tracked in Git.
- Virtual environment set up and active.
- Database files `stocks.db` and `mutual_funds.db` exist and are populated.
- Dependencies listed in `requirements.txt`; some may need installation.

## Recent Changes (2026-08-30 to 2026-09-09)
- **Dashboard Real-Data Integration (2026-09-09)** — `real_data_service.py` created to fetch real top gainers/losers from NSE India via `nsetools`.
  - New module `real_data_service.py` with `get_dashboard_data_with_fallback()`, `GainerLoserStock` and `DashboardData` dataclasses, in-memory caching (5 min TTL), and yfinance name enrichment.
  - `flask_app.py` updated to import `get_dashboard_data_with_fallback` and modified `inject_demo_data` context processor to replace `DEMO_DATA` gainers/losers with real data.
  - `/gainers-losers` route already uses live NSE data (unchanged).
  - Fallback to `DEMO_DATA_FALLBACK` if NSE API is unavailable.
- Dashboard renders successfully at `/` with all 15 UI component checks passing
  - Fixed index.html template slicing issue (changed `|slice(6,12)` to `demo_data.stocks[3:6]` for proper list slicing)
  - Dashboard renders successfully at `/` with all 15 UI component checks passing
  - Removed `if len(records) >= limit: break` check that stopped collection early
  - Added `return records[-limit:]` to take the most recent records
  - This allows `detect_and_store_holidays()` to correctly identify missing data instead of incorrectly marking recent weekdays as holidays
- Fixed `run_daily.py` to generate suggestions for ALL dates in the 60-day window, not just the most recent date
  - Now queries all distinct dates from the last 60 days and calls `generate_suggestions()` for each date
  - Collects top 50 suggestions per day and sorts by score globally to show the best opportunities across the entire window
  - Database now stores 2145+ suggestions across 43 trading dates (2026-07-01 to 2026-08-28)
- Updated `/top-mutual-funds` route in `flask_app.py` to query from `mutual_funds.db` instead of `stocks.db`
- Added friendly error pages for API failures (`categorize_error()` + `templates/error.html`)
- Added schema version tracking and auto-migration in `models.py` (v2.0)
- Added stock search route with yfinance fallback for non-Nifty 50 stocks
- Added `detect_and_store_holidays()` for market calendar awareness

## Implementation Summary
- Top 50 mutual funds now ranked globally across all categories (Large Cap, Mid Cap, Small Cap, Debt) from `mutual_funds.db`
- Removed mutual fund suggestion generation from `run_daily.py` (lines 28-32 and import)

## Codebase Structure
- **Models**: `models.py` defines SQLAlchemy ORM tables (`Asset`, `DailyPrice`, `Suggestion`, `MutualFundAsset`, `MutualFundSuggestion`) and session helpers.
- **Data Sources**: `data_sources.py` contains `DataSource` abstraction with implementations: `NSESource`, `YFinanceSource`, `MutualFundSource`.
- **Data Fetching**: `data_fetcher.py` orchestrates fetching and storing daily prices.
- **Scoring**: `scoring2.py` implements momentum, volume, RSI, MA, close-strength, and gap-up scoring, and `generate_suggestions()` / `generate_mf_suggestions()`.
- **Mutual Fund Processing**: `mutual_fund_db.py` fetches NAV data from TigZig API, scores funds, and stores in separate database.
- **Orchestration**: `run_daily.py` runs the full pipeline (fetch → store → score → print), generating suggestions for all 60 days of trading data.
- **CLI**: `cli.py` provides command-line interface for querying suggestions.
- **Web UI**: `flask_app.py` with Jinja2 templates provides browser UI and JSON APIs, including `/mutual-funds` endpoint.

## Recent Changes
- Updated `mutual_fund_db.py` to dynamically fetch 30+ funds per category from TigZig API instead of using hardcoded scheme codes
- Added pagination support (`fetch_all_schemes_for_category()`) for handling TigZig API pagination
- Added debt sub-category expansion (`DEBT_SUB_CATEGORIES` with 18 sub-categories) to reach 30+ funds
- Implemented `search_schemes()` with plan/option filters for Direct Growth funds
- Added `fetch_and_filter_direct_growth()` function to filter API results
- Updated `process_fund()` to accept cached metadata
- Changed `TOP_N` from 40 to 45 to target 30+ funds per category
- Added `DEBT_CATEGORY_MAPPING` for explicit debt category handling
- Fixed category mapping in `get_category()` to handle TigZig API format
- Added rate-limit handling with retry logic in `get_json()` (exponential backoff, 429 handling)
- Reduced `MAX_FUND_AGE_DAYS` to 365 and `MAX_NO_RECENT_DATA_DAYS` to 730 for small/mid cap leniency
- Relaxed `calculate_score()` to accept funds with only 1-year return data
- Added NaN score handling in `store_fund_in_db()` to prevent IntegrityError
- Sequential processing in `main()` to avoid TigZig API 429 rate limiting
- All categories now fetch 30+ funds dynamically: Large Cap (33), Mid Cap (45), Small Cap (31), Debt (45)
- Generated CSV files: `top_large_cap_funds.csv`, `top_mid_cap_funds.csv`, `top_small_cap_funds.csv`, `top_debt_funds.csv`
- Updated database schema and stored 154 funds in SQLite `mutual_funds.db`

## Running State
- `python mutual_fund_db.py` successfully fetches and stores 154 mutual funds across 4 categories (30+ per category)
- Generated CSV files for each category with top funds data
- Database populated in `mutual_funds.db` with `MutualFundAsset` and `MutualFundSuggestion` models
- `/mutual-funds` Flask route will now display dynamically fetched fund data

## Dependencies
- `requirements.txt` includes pandas, numpy, yfinance, nsepy, requests, beautifulsoup4, python-dotenv, scikit-learn, flask, sqlalchemy, apscheduler, matplotlib, seaborn, plotly.

## Known Issues
- TigZig API rate limiting (429) requires careful delay management - already handled with sequential processing and retry logic
- Small Cap funds (31) just barely exceeds the 30+ threshold; may need to increase buffer
- Database may contain stale or incomplete data if previous runs failed.
- No test suite executed yet.
- Demo data (DEMO_DATA) used for prototype UI - real data integration pending

## Next Steps
- Verify `/mutual-funds` Flask route and template display correctly with the larger fund lists
- Run `python run_daily.py` to populate stock data
- Test CLI and Web UI functionality end-to-end
- Verify mutual fund data appears in web UI at `/mutual-funds`
- Replace demo data with real stock API data integration
## Dashboard Real-Data Integration (2026-09-04)
- `index_data.py` module created: Yahoo Finance integration for 4 indices (NIFTY 50, NIFTY BANK, SENSEX, NIFTY IT) via `^NSEI`, `^NSEBANK`, `^BSESN`, `^CNXIT`.
- `INDEX_CONFIG` covers 4 indices × 3 constituent stocks each; `STOCK_SECTOR_MAP` static fallback (~50 stocks).
- 1-hour in-memory cache (`CACHE_DURATION = 3600`), keyed `index_{symbol}` and `sector_performance`.
- `flask_app.py` `index()` route calls `get_index_data_with_fallback()` / `get_sector_data_with_fallback()` with `_test_mode=False`, passing `indices_data` + `sectors_data` to template.
- `templates/index.html` "Top Stocks by Index" and "Sector Performance" sections now loop over real data.
- **Fixed (2026-09-04): all dashboard percentages showed 0.0%.** Root cause: `changePct` was hardcoded to `0.0` in both `_fetch_single_index_data` and `_fetch_stock_details`, and `YFinanceSource.fetch_latest()` returned only the latest row (no previous close). Fix: added optional `prev_close` field to `OHLCV` dataclass, populated by `YFinanceSource` from `hist.iloc[-2]["Close"]` when ≥2 rows exist, and added `_pct_change()` helper used in both index and stock dicts. Verified live: NIFTY 50 +0.31%, RELIANCE +2.13%, TCS -0.12%, HDFCBANK +1.20%, etc.
- **Remaining**: `Market Performance`, `Watch List`, `Top Gainers/Losers` still use `demo_data` (intentional, step-by-step). `_test_mode` flag still present but set to `False` in route; `TEST_*_DATA` constants retained for dev fallback.

- **UI: green up / red down arrows on percentage chips (2026-09-04)** — arrows are injected via CSS `::before` pseudo-elements on `.change-chip.up` (▲ U+25B2) and `.change-chip.down` (▼ U+25BC), `font-size:8px`, `gap:4px` flex layout. Same pattern applied to `.sector-chip`. Zero change now renders `neutral` (no arrow, muted color) instead of `up`. All four chip sites in `templates/index.html` (Watch List, index header, stock, sector) switched from `>= 0` to `> 0 / < 0 / else neutral`. Top Gainers `+` sign removed since the arrow replaces it.
- Add unit tests for dashboard rendering and UI components