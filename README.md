# Indian Stock Tracker

A Python application that tracks Indian stock market data, scores stocks using a momentum + volume strategy, and stores the results in a local SQLite database. It includes a command-line interface and a web-based database browser UI to explore the stored data.

## Features

- **Data fetching**: Pulls daily OHLCV (open, high, low, close, volume) data for NSE-listed stocks via Yahoo Finance (`yfinance`).
- **Scoring engine**: Computes a composite score per stock per day using price momentum and a relative volume factor.
- **Persistence**: Stores stocks, daily prices, and top suggestions in a SQLite database via SQLAlchemy ORM.
- **CLI**: Print the top suggestions for any date.
- **Daily automation**: A single script (`run_daily.py`) that fetches data, scores stocks, and stores suggestions — suitable for scheduling with cron.
- **Web DB Browser**: A Flask UI to browse the database like a DB explorer (dashboard, stocks, prices, suggestions, JSON APIs).

## Project Structure

```
indian_stock_tracker/
├── models.py          # SQLAlchemy models (Stock, DailyPrice, Suggestion) + DB session helpers
├── data_fetcher.py    # Fetches & stores daily price data from Yahoo Finance
├── scoring.py         # Scoring algorithm (momentum + volume) and suggestion generation
├── cli.py             # Command-line interface to print top suggestions
├── run_daily.py       # Master script: fetch -> score -> store -> print
├── flask_app.py       # Flask web app serving the DB browser UI
├── requirements.txt   # Python dependencies
├── stocks.db          # SQLite database (created at runtime)
├── templates/         # HTML templates for the web UI
│   ├── index.html        # Dashboard
│   ├── stocks.html        # Stocks list
│   ├── stock_detail.html  # Single stock detail
│   ├── prices.html        # Prices browser with filters
│   └── suggestions.html   # Suggestions browser with filters
└── README.md
```

## Database Schema

The SQLite database (`stocks.db`) contains three tables:

| Table | Columns |
|-------|---------|
| `stocks` | `id`, `symbol` (unique), `name`, `exchange`, `sector` |
| `daily_prices` | `id`, `stock_id` (FK), `date`, `open`, `high`, `low`, `close`, `adj_close`, `volume` |
| `suggestions` | `id`, `date`, `stock_id` (FK), `score`, `reasoning` |

## Installation

Requires Python 3.10+.

```bash
# 1. Clone / open the project directory
cd indian_stock_tracker

# 2. (Recommended) Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

> Dependencies include: `pandas`, `numpy`, `yfinance`, `requests`, `beautifulsoup4`, `python-dotenv`, `scikit-learn`, `flask`, `sqlalchemy`, `APScheduler`, `matplotlib`, `seaborn`, `plotly`.

## Usage

### 1. Populate the database (daily run)

Fetches the latest data for the configured symbols, scores them, and stores the top suggestions:

```bash
python run_daily.py
```

This will:
1. Ensure the DB and tables exist.
2. Fetch daily prices for the tracked symbols (e.g. `RELIANCE.NS`, `TCS.NS`, `HDFCBANK.NS`, `INFY.NS`, `ICICIBANK.NS`).
3. Generate and store the top-5 suggestions for yesterday.
4. Print the results to the console.

### 2. Command-line suggestions

Print suggestions for a specific date (defaults to yesterday):

```bash
python cli.py                 # yesterday's suggestions
python cli.py --date 2026-07-10   # specific date (YYYY-MM-DD)
```

If no suggestions exist for the date, the CLI generates them on the fly.

### 3. Web DB Browser UI

Launch the Flask web interface to browse the database in your browser:

```bash
python flask_app.py
```

Then open **http://localhost:8080** in your browser.

> Note: Port 5000 is often occupied by macOS AirPlay Receiver, so the app defaults to **8080**. To use a different port, edit the `port=` value in the `app.run(...)` call at the bottom of `flask_app.py`, or run with an environment override.

#### Web UI features
- **Dashboard (`/`)** — overview with total stocks, price records, suggestions, and latest data date.
- **Stocks (`/stocks`)** — paginated list of all tracked stocks; click a row to view its detail page.
- **Stock Detail (`/stocks/<id>`)** — recent prices and suggestions for a single stock.
- **Prices (`/prices`)** — daily price records, filterable by stock and date range, with pagination.
- **Suggestions (`/suggestions`)** — generated suggestions, filterable by stock and date range.
- **JSON APIs**:
  - `GET /api/stocks` — all stocks as JSON
  - `GET /api/prices?stock_id=<id>&days=<n>` — recent prices as JSON

## Scheduling (optional)

To run the tracker automatically after market close (≈ 6:00 PM IST), add a cron job:

```cron
0 18 * * * /path/to/indian_stock_tracker/venv/bin/python /path/to/indian_stock_tracker/run_daily.py
```

## Configuration Notes

- **Data source**: `data_fetcher.py` uses `yfinance` with Yahoo Finance symbol format (e.g. `RELIANCE.NS`). To track different stocks, edit the `symbols` list in `run_daily.py`.
- **Scoring**: Defined in `scoring.py` as `momentum * 0.7 + volume_factor * 0.3`. Tune the weights or add factors (e.g. from `scikit-learn`) as needed.
- **API keys**: The original design allowed for NSE/Alpha Vantage/Finnhub keys via a `.env` file, but the current implementation relies on `yfinance`, which needs no key.