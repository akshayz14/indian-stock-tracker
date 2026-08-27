# Current State (as of 2026-08-21)

## Repository Status
- All core files present and tracked in Git.
- Virtual environment likely set up but not verified.
- Database files `stocks.db` and `mutual_funds.db` exist (may be empty or contain previous data).
- Dependencies listed in `requirements.txt`; no installation verification yet.

## Codebase Structure
- **Models**: `models.py` defines SQLAlchemy ORM tables (`Asset`, `DailyPrice`, `Suggestion`, `MutualFundAsset`, `MutualFundSuggestion`) and session helpers.
- **Data Sources**: `data_sources.py` contains `DataSource` abstraction with implementations: `NSESource`, `YFinanceSource`, `MutualFundSource`.
- **Data Fetching**: `data_fetcher.py` orchestrates fetching and storing daily prices.
- **Scoring**: `scoring2.py` implements momentum, volume, RSI, MA, close-strength, and gap-up scoring, and `generate_suggestions()` / `generate_mf_suggestions()`.
- **Mutual Fund Processing**: `mutual_fund_db.py` fetches NAV data from mfapi.in, scores funds, and stores in separate database.
- **Orchestration**: `run_daily.py` runs the full pipeline (fetch → store → score → print).
- **CLI**: `cli.py` provides command-line interface for querying suggestions.
- **Web UI**: `flask_app.py` with Jinja2 templates provides browser UI and JSON APIs, including `/mutual-funds` endpoint.

## Recent Changes
- Added mutual fund support with separate database (`mutual_funds.db`).
- Implemented `MutualFundSource` in `data_sources.py` for mfapi.in API.
- Added `MutualFundAsset` and `MutualFundSuggestion` models in `models.py`.
- Created `mutual_fund_db.py` for fetching and scoring mutual funds.
- Updated `flask_app.py` to include `/mutual-funds` route and template.
- Updated documentation (PRD.md, TRD.md) to reflect mutual fund functionality.
- Enhanced `/gainers-losers` route to display gainers/losers with date information (`for dd-mm-yyyy`).

## Running State
- `python run_daily.py` should fetch data, score, and store suggestions (assuming network connectivity).
- `python cli.py` should display suggestions for a given date.
- `python flask_app.py` should start web UI on port 8080.
- `python mutual_fund_db.py` should fetch and store mutual fund data.

## Dependencies
- `requirements.txt` includes pandas, numpy, yfinance, nsepy, requests, beautifulsoup4, python-dotenv, scikit-learn, flask, sqlalchemy, apscheduler, matplotlib, seaborn, plotly.
- No dependencies have been installed yet (virtual environment not activated).

## Known Issues
- Database may contain stale or incomplete data if previous runs failed.
- No verification of database schema initialization.
- No test suite executed yet.
- Mutual fund processing may take significant time due to API calls.

## Next Steps
- Activate virtual environment and install dependencies.
- Verify database schema with `init_db()`.
- Run `python run_daily.py` to populate stock data.
- Run `python mutual_fund_db.py` to populate mutual fund data.
- Test CLI and Web UI functionality.
- Verify mutual fund data appears in web UI at `/mutual-funds`.