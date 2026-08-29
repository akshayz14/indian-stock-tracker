# Current State (as of 2026-08-30)

## Repository Status
- All core files present and tracked in Git.
- Virtual environment likely set up but not verified.
- Database files `stocks.db` and `mutual_funds.db` exist and are populated.
- Dependencies listed in `requirements.txt`; some may need installation.

## Codebase Structure
- **Models**: `models.py` defines SQLAlchemy ORM tables (`Asset`, `DailyPrice`, `Suggestion`, `MutualFundAsset`, `MutualFundSuggestion`) and session helpers.
- **Data Sources**: `data_sources.py` contains `DataSource` abstraction with implementations: `NSESource`, `YFinanceSource`, `MutualFundSource`.
- **Data Fetching**: `data_fetcher.py` orchestrates fetching and storing daily prices.
- **Scoring**: `scoring2.py` implements momentum, volume, RSI, MA, close-strength, and gap-up scoring, and `generate_suggestions()` / `generate_mf_suggestions()`.
- **Mutual Fund Processing**: `mutual_fund_db.py` fetches NAV data from TigZig API, scores funds, and stores in separate database.
- **Orchestration**: `run_daily.py` runs the full pipeline (fetch → store → score → print).
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

## Next Steps
- Verify `/mutual-funds` Flask route and template display correctly with the larger fund lists
- Run `python run_daily.py` to populate stock data
- Test CLI and Web UI functionality
- Verify mutual fund data appears in web UI at `/mutual-funds`