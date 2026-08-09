# Requirements

## Core Functional Requirements (from PRD)

1. **Data Fetching**
   - Pull OHLCV data for Nifty 50 equities from NSE India CSV with automatic fallback to Yahoo Finance (`yfinance`).

2. **Scoring Engine**
   - Compute a composite score (momentum × 0.7 + volume_factor × 0.3) and generate top‑N suggestions.

3. **Persistence**
   - Store stocks, daily prices, and suggestions in a local SQLite database via SQLAlchemy.

4. **CLI**
   - `python cli.py [--date YYYY-MM-DD]` prints top suggestions for a given date.

5. **Automation**
   - `run_daily.py` fetches, scores, stores, and prints suggestions; intended for cron scheduling.

6. **Web DB Browser**
   - Flask UI (`http://localhost:8080`) for exploring stocks, prices, suggestions, and JSON APIs.

## Non-Functional Requirements

- **Performance**
  - Daily fetch success rate ≥ 99% (fallback works).
  - CLI output latency ≤ 5 s.
  - Web UI response ≤ 2 s for 100k rows.
  - Cron job runs without manual intervention.

- **Constraints**
  - Must run on macOS/Linux/Windows with Python 3.10+.
  - No external paid APIs; only free public data sources.
  - SQLite database size ≤ 200 MB for typical usage.

## Future Enhancements (may become requirements later)

- Add machine‑learning scoring models.
- Support additional data sources (Alpha Vantage, Finnhub).
- Export suggestions to CSV/Excel.
- Mobile‑friendly UI.</arg_value>
<task_progress>
- [x] Create project-context.md
- [x] Create architecture.md
- [x] Create requirements.md
</task_progress>
</write_to_file>