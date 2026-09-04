# Deployment Documentation
## Indian Stock Tracker – Version 1.3

## Workflow Overview
This GitHub Actions workflow automatically updates stock data daily at midnight. It runs `run_daily.py` to fetch and store new market data in `stocks.db`, then commits changes only if the database was modified. Mutual fund data processing runs separately via `mutual_fund_db.py`.

## Manual Execution
To run manually:
1. Go to GitHub > Actions > "Update Stock Data" workflow
2. Click "Run workflow" and select "Run workflow"
3. Click "Run workflow" button

Or use the CLI:
```bash
gh workflow dispatch run-stock-data.yml
```

## Logs
View logs in GitHub Actions tab under the workflow run. Key steps to check:
- "Run daily update" - output from `run_daily.py`
- "Check for database changes" - whether data was updated
- "Commit and push database" - git operations if changes exist

## Database Update Process
1. Fetches data from NSE India CSV, Yahoo Finance (`yfinance`), and TigZig API (mutual funds)
2. Stores OHLCV data in SQLite database via SQLAlchemy ORM
3. Uses `git diff --quiet -- stocks.db` to detect changes
4. Commits and pushes only if data actually changed
5. No API keys or secrets required

## Mutual Fund Data Update
The workflow also runs `mutual_fund_db.py` to fetch and update mutual fund data from TigZig API. Updated CSV files are committed if they differ from existing files.

## Render Integration
The updated `stocks.db` and CSV files are automatically served by the Flask app on Render. Render detects the git push and redeploys the application.

## Failure Handling
If workflow fails:
- Check GitHub Actions logs for specific errors
- Verify dependencies in requirements.txt
- Ensure Python 3.10+ is available
- Check network connectivity to data sources (NSE, Yahoo Finance, TigZig API)

## Required GitHub Secrets
None. All data sources are public and require no authentication.

## Testing the Workflow
1. Make a small change to trigger a test run
2. Or manually dispatch via GitHub Actions UI
3. Monitor the "Check for database changes" step output
4. Verify the commit appears in the repository if data changed

## Recent Updates (2026-09-03)
- Added mutual fund data fetch step (`mutual_fund_db.py`)
- Added CSV export commit if files changed
- Updated schedule to 01:47 UTC (07:17 IST) for optimal market data freshness
- Added documentation for mutual fund deployment process</arg_value></tool_call>task_progress
- [x] Analyze run_daily.py and related scripts
- [x] Analyze data_fetcher.py
- [x] Analyze data_sources.py
- [x] Analyze scoring.py
- [x] Analyze scoring2.py
- [x] Check requirements.txt
- [x] Determine Python version compatibility (3.10+)
- [x] Create corrected GitHub Actions workflow
- [x] Update DEPLOYMENT.md
- [x] Explain workflow steps and testing
</task_progress>
</write_to_file></tool_call>