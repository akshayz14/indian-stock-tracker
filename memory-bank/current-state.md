# Current State (as of 2026-08-04)

## Repository Status
- All core files present and tracked in Git.
- Virtual environment likely set up but not verified.
- Database file `stocks.db` exists (may be empty or contain previous data).
- Dependencies listed in `requirements.txt`; no installation verification yet.

## Codebase Structure
- **Models**: `models.py` defines SQLAlchemy ORM tables (`Stock`, `DailyPrice`, `Suggestion`) and session helpers.
- **Data Sources**: `data_sources.py` contains `DataSource` abstraction with `NSESource`, `YFinanceSource`, `MutualFundSource`.
- **Data Fetching**: `data_fetcher.py` orchestrates fetching and storing daily prices.
- **Scoring**: `scoring.py` implements momentum and volume factor calculations, and `generate_suggestions()`.
- **Orchestration**: `run_daily.py` runs the full pipeline (fetch → store → score → print).
- **CLI**: `cli.py` provides command-line interface for querying suggestions.
- **Web UI**: `flask_app.py` with Jinja2 templates provides browser UI and JSON APIs.

## Recent Changes
- Latest commit `fc0212ebc170c981eaedff16636c40023cebcfed` likely contains minor fixes.
- No breaking changes reported in recent commits.

## Running State
- `python run_daily.py` should fetch data, score, and store suggestions (assuming network connectivity).
- `python cli.py` should display suggestions for a given date.
- `python flask_app.py` should start web UI on port 8080.

## Dependencies
- `requirements.txt` includes pandas, numpy, yfinance, nsepy, requests, beautifulsoup4, python-dotenv, scikit-learn, flask, sqlalchemy, apscheduler, matplotlib, seaborn, plotly.
- No dependencies have been installed yet (virtual environment not activated).

## Known Issues
- Database may contain stale or incomplete data if previous runs failed.
- No verification of database schema initialization.
- No test suite executed yet.

## Next Steps
- Activate virtual environment and install dependencies.
- Verify database schema with `init_db()`.
- Run `python run_daily.py` to populate data.
- Test CLI and Web UI functionality.