# Product Requirements Document (PRD)
## Indian Stock Tracker – Version 1.0

---

### 1. Purpose
Provide a lightweight, automated system for Indian investors to fetch daily market data, score stocks using a momentum‑plus‑volume strategy, and expose the results via CLI and a web UI.

### 2. Target Audience
- Individual retail investors
- Financial analysts
- Hobbyists who want quick, data‑driven insights into NSE‑listed equities, mutual funds, bonds, derivatives, and commodities

### 3. Core Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Data Fetching** | Pull OHLCV data for Nifty 50 equities fetched dynamically from NSE India CSV with automatic fallback to Yahoo Finance (`yfinance`). |
| 2 | **Scoring Engine** | Compute a composite score (momentum × 0.7 + volume_factor × 0.3) and generate top‑N suggestions. |
| 3 | **Persistence** | Store stocks, daily prices, and suggestions in a local SQLite database via SQLAlchemy. |
| 4 | **CLI** | `python cli.py [--date YYYY‑MM‑DD]` prints top suggestions for a given date. |
| 5 | **Automation** | `run_daily.py` fetches, scores, stores, and prints suggestions; intended for cron scheduling. |
| 6 | **Web DB Browser** | Flask UI (`http://localhost:8080`) for exploring stocks, prices, suggestions, and JSON APIs. |

### 4. User Stories
- **As a trader**, I want to see the top 50 stock suggestions for yesterday so I can decide which to research.
- **As a developer**, I want to schedule the tracker to run automatically after market close.
- **As a data analyst**, I want to browse historical prices and suggestions via a web UI.

### 5. Success Metrics
- Daily fetch success rate ≥ 99% (fallback works).
- CLI output latency ≤ 5 s.
- Web UI response ≤ 2 s for 100k rows.
- Cron job runs without manual intervention.

### 6. Constraints
- Must run on macOS/Linux/Windows with Python 3.10+.
- No external paid APIs; only free public data sources.
- SQLite database size ≤ 200 MB for typical usage.

### 7. Future Enhancements
- Add machine‑learning scoring models.
- Support additional data sources (Alpha Vantage, Finnhub).
- Export suggestions to CSV/Excel.
- Mobile‑friendly UI.

---

*Document Version: 1.0*  
*Last Updated: 2026-07-25*