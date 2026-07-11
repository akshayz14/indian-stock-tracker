# Indian Stock Tracker - Project Setup Checklist

## Initialization
- [ ] Create project directory: `mkdir indian_stock_tracker && cd indian_stock_tracker`
- [ ] Initialize git repository: `git init`
- [ ] Create virtual environment: `python -m venv venv`
- [ ] Activate virtual environment:
  - macOS/Linux: `source venv/bin/activate`
  - Windows: `venv\Scripts\activate`
- [ ] Upgrade pip: `pip install --upgrade pip`

## Dependencies
- [ ] Create requirements.txt (see below)
- [ ] Install dependencies: `pip install -r requirements.txt`

## Required Libraries (requirements.txt)
```
pandas
numpy
nsetools
nsepy
yfinance
requests
beautifulsoup4
python-dotenv
scikit-learn
flask
sqlalchemy
APScheduler
matplotlib
seaborn
plotly
```

## Database Setup
- [ ] Choose database backend (SQLite for MVP):
  - Create SQLite DB: `sqlite3 stocks.db`
- [ ] Design schema:
  - stocks (id, symbol, name, exchange, sector)
  - daily_prices (id, stock_id, date, open, high, low, close, volume, adj_close)
  - suggestions (id, date, stock_id, score, reasoning)
- [ ] Implement SQLAlchemy models in `models.py`

## API Integration
- [ ] Identify primary data source:
  - Option 1: nsepy (free, open-source)
  - Option 2: Alpha Vantage (requires API key)
  - Option 3: Finnhub (requires API key)
- [ ] Register for API keys (if needed)
- [ ] Create `.env` file for API credentials:
  ```
  NSE_API_KEY=your_key_here
  ALPHA_VANTAGE_KEY=your_key_here
  FINNHUB_KEY=your_key_here
  ```
- [ ] Implement data fetcher (`data_fetcher.py`) that:
  - Accepts stock symbols (e.g., RELIANCE.NS, TCS.NS)
  - Fetches daily price data
  - Handles rate limits and retries

## Project Structure
```
indian_stock_tracker/
├── data_fetcher.py
├── models.py
├── scoring.py
├── cli.py
├── run_daily.py
├── requirements.txt
├── .env
├── stocks.db (SQLite DB)
└── README.md
```

## Daily Automation
- [ ] Create master script `run_daily.py` that:
  1. Fetches latest market data
  2. Stores prices in database
  3. Runs scoring algorithm
  4. Generates top N suggestions
  5. Outputs results (CLI or file)
- [ ] Add cron job (Linux/macOS) to run after market close (6:00 PM IST):
  ```
  0 18 * * * /path/to/indian_stock_tracker/venv/bin/python /path/to/indian_stock_tracker/run_daily.py
  ```

## Next Steps
1. Execute the setup commands above
2. Implement the data fetcher for a few sample symbols (RELIANCE.NS, TCS.NS, HDFCBANK.NS)
3. Build the SQLite database and store initial data
4. Develop the scoring function (start with simple momentum + volume criteria)
5. Create CLI to display top 5 suggestions