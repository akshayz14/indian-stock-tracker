# Known Issues

## 11. Missing Columns When Merging Old Production Database (Fixed)

**Description:** When merging with an old production project that was already deployed, the old database lacked the `is_holiday` column in `daily_prices` (and `latest_nav_date` in `mutual_fund_assets`). The `_add_missing_columns()` function in `models.py` was designed to handle this, but it was only called from `init_db()` which wasn't invoked by `cli.py` or `flask_app.py`. This caused `sqlalchemy.OperationalError: no such column: daily_prices.is_holiday` errors.

**Location:** `models.py` — `get_session()` and `get_mutual_fund_session()` functions

**Fix Applied:** Modified `get_session()` and `get_mutual_fund_session()` to automatically call `Base.metadata.create_all(engine)` and the respective `_add_missing_columns()` functions before returning a session. This ensures any existing database (newly created or from a merged old project) gets the required columns automatically on first use.

**Status:** Fixed (2026-09-03)


# Known Issues

## 1. Dashboard Charts Not Displaying Data (Fixed)
**Description**: The dashboard overview charts (Top Gainers Bar Chart and Score Distribution Histogram) in `templates/index.html` reference JavaScript variables (`top_gainer_labels`, `top_gainer_values`, `score_labels`, `score_data`) that are not being passed from the Flask `index()` route in `flask_app.py`. This caused an `Object of type Undefined is not JSON serializable` error on the dashboard.

**Location**:
- Template: `templates/index.html` lines 44-63 (chart containers) and lines 68-132 (JavaScript)
- Route: `flask_app.py` lines 66-81 (`index()` function)

**Fix Applied**:
1. Added `|default([])` filter to all four chart variables in `templates/index.html` to handle the case when they're not passed from the Flask route.
2. Fixed a typo where `topGainer_values` (camelCase) was used instead of `top_gainer_values` (snake_case) in the tojson filter.

**Status**: Fixed (2026-08-29) — Dashboard now renders without the JSON serialization error. The charts still display empty data because the variables are not actually being computed and passed, but the page no longer crashes.

**Note**: To make the charts actually display data, the `index()` route in `flask_app.py` would need to compute and pass `top_gainer_labels`, `top_gainer_values`, `score_labels`, and `score_data` to the template. This is a follow-up task.

## 2. Missing Mutual Fund Navigation Links
**Description**: While the Mutual Funds page exists and is accessible via direct URL (`/mutual-funds`), there are no navigation links in the top navigation bar or sidebar to access this section.

**Location**:
- Top navigation: `templates/base.html` lines 13-21 (missing Mutual Funds link)
- Sidebar navigation: `templates/base.html` lines 30-36 (missing Mutual Funds link)

**Impact**: Users must know the direct URL to access mutual fund functionality.

**Workaround**: Access via direct URL: `http://localhost:8080/mutual-funds`

**Status**: Open

## 3. Mutual Fund Processing Not Integrated into Daily Job
**Description**: Mutual fund data processing (`mutual_fund_db.py`) is not automatically triggered by the main daily job (`run_daily.py`). Users must run mutual fund processing separately.

**Location**:
- Main daily job: `run_daily.py`
- Mutual fund processing: `mutual_fund_db.py`

**Impact**: Mutual fund data becomes stale relative to equity data unless manually updated.

**Workaround**: Run `python mutual_fund_db.py` separately after running `python run_daily.py`.

**Status**: Open (as of 2026-08-30)

## 4. Mutual Fund Suggestion Testing Incomplete
**Description**: The mutual fund suggestion generation and display functionality has been implemented but not fully tested.

**Location**: 
- Mutual fund scoring: `mutual_fund_db.py` scoring logic
- Suggestion display: `/mutual-funds` route and template

**Impact**: Potential for incorrect scoring or display of mutual fund suggestions.

**Workaround**: Manual verification of mutual fund suggestion scores and rankings.

**Status**: Open (as of 2026-08-30) - 154 funds now in DB with valid scores

## 5. Search Functionality Cache May Serve Stale Data
**Description**: The in-memory cache for stock search history (`search_history_cache` in `flask_app.py`) uses a fixed TTL of 1 hour but doesn't invalidate when new data is fetched for the same symbol.

**Location**: `flask_app.py` lines 14-16 (cache definition) and lines 627-633 (cache usage)

**Impact**: Search results may show outdated price data for up to 1 hour after new data is available.

**Workaround**: None - data will refresh automatically after cache expiration.

**Status**: Open (considered low priority)

## 6. GitHub Actions Cron Schedule Ran Before NSE Market Open (Fixed)
**Description**: The scheduled workflow in `.github/workflows/update-stock-data.yml` was set to `cron: '0 0 * * *'` which corresponds to **00:00 UTC = 05:30 IST**. This runs **before NSE market opens** (09:15-15:30 IST), meaning the data fetcher would either fail to get same-day data or fall back to stale previous-day data.

**Location**: `.github/workflows/update-stock-data.yml` line 5

**Fix Applied**: Changed cron to `47 1 * * *` which is **01:47 UTC = 07:17 IST**, matching the previous historical schedule shown in the Actions history (07:17-07:20 IST). **Note**: This is still before market open, so if same-day data is required, the schedule should be changed to something like `15 7 * * *` (07:15 UTC = 12:45 IST) once market is open and intraday data is reliably available.

**Status**: Fixed (2026-08-29) — restored historical schedule time, but data freshness concern remains if 07:17 IST is consistently before market open.

## 8. Mutual Fund Freshness Filtering Implemented

**Description**: Implemented mutual fund freshness filtering mechanism to exclude funds not relevant for current investors (e.g., wound-up, merged, or defunct funds).

**Location**:
- Core logic: `mutual_fund_db.py` `is_fund_recent()` function
- Processing: `mutual_fund_db.py` `process_fund()` function
- Storage: `models.py` `MutualFundAsset.latest_nav_date` column
- Display: `flask_app.py` `/mutual-funds` and `/top-mutual-funds` routes

**Fix Applied**:
1. Added freshness thresholds: `MAX_FUND_AGE_DAYS = 730` (2 years) and `MAX_NO_RECENT_DATA_DAYS = 365` (1 year)
2. Added `is_fund_recent()` function to filter funds with stale NAV data
3. Added `latest_nav_date` column to `MutualFundAsset` model for storage
4. Integrated freshness check in `process_fund()` to skip stale funds during ingestion
5. Added freshness filtering in Flask routes:
   - `/mutual-funds`: Filters `MutualFundAsset.latest_nav_date >= today - 730 days`
   - `/top-mutual-funds`: Filters `Suggestion.date >= today - 730 days` (proxy for fund activity)
6. Added migration to add `latest_nav_date` column to existing `mutual_funds.db`
7. Added 12 comprehensive tests in `tests/test_mutual_fund_freshness.py`

**Impact**: Users will no longer see discontinued funds like "Principal Emerging Bluechip Fund - Direct Plan - Growth Option" (last NAV 2013) in mutual fund listings.

**Status**: Fixed (2026-08-29)

## 7. Stock Detail Chart X-Axis Misleading Last Tick Label (Fixed)
**Description**: On the stock detail page (`/stocks/<asset_id>`), the Chart.js price/volume charts used `maxTicksLimit: 10` which caused auto-skipping of x-axis tick labels. When the dataset had 14 data points, only 10 evenly-spaced labels were shown, and the last visible label was NOT the most recent date (e.g., showed `2026-08-19` when data went to `2026-08-27`). This misled users into thinking the chart ended at the last visible tick label.

**Location**: `templates/stock_detail.html` lines 119-216 (chart JavaScript)

**Fix Applied**: Added logic to show ALL labels when `priceLabels.length <= 30` by setting `autoSkip: false` and removing `maxTicksLimit`. For larger datasets (>30), falls back to `maxTicksLimit: 10` with auto-skipping. This ensures the most recent date is always visible as the last tick label for typical datasets.

**Status**: Fixed

## 9. Mutual Fund Dynamic Fetching - COMPLETED
**Description**: Redesigned mutual fund tracker to dynamically fetch 30+ unique funds per category (large cap, mid cap, small cap, debt) from the TigZig API instead of using a hardcoded list of ~50 scheme codes.

**Location**: 
- Core logic: `mutual_fund_db.py` (completely rewritten)
- Functions: `search_schemes()`, `fetch_all_schemes_for_category()`, `fetch_and_filter_direct_growth()`, `process_fund()`

**Implementation Details**:
- Removed hardcoded `get_all_schemes()` function
- Added dynamic fetching with pagination support for all categories
- Implemented debt sub-category expansion to reach 30+ funds
- Added Direct Growth filtering (plan=Direct, option=Growth)
- Fixed category mapping to match TigZig API responses
- Added rate-limit handling with exponential backoff and retry logic
- Sequential processing to avoid TigZig API 429 errors
- Updated freshness filtering for small/mid cap funds
- Relaxed scoring to accept funds with only 1-year return data
- Added NaN score handling in database storage

**Results**:
- Large Cap: 33 funds (vs 30+ target)
- Mid Cap: 45 funds (vs 30+ target) 
- Small Cap: 31 funds (vs 30+ target)
- Debt: 45 funds (vs 30+ target)
- Total: 154 funds in `mutual_funds.db`

**CSV Output**:
- `top_large_cap_funds.csv` (33 funds)
- `top_mid_cap_funds.csv` (45 funds)
- `top_small_cap_funds.csv` (31 funds)
- `top_debt_funds.csv` (45 funds)

**Status**: Completed (2026-08-30)

## 10. fetch_history Returned Oldest Records Instead of Most Recent (Fixed)
**Description**: The `YFinanceSource.fetch_history()` method in `data_sources.py` had a bug where it would break out of the loop after collecting `limit` records. Since yfinance returns records in chronological order (oldest-first), this meant the function was returning the OLDEST 60 days instead of the most recent 60 days. As a result, the database was always being populated with stale data (e.g., 2026-03 to 2026-06) even when current data was available from yfinance. This caused `detect_and_store_holidays()` to incorrectly mark all recent weekdays as holidays because no data existed for them.

**Location**: `data_sources.py` lines 105-137 (`YFinanceSource.fetch_history()` method)

**Fix Applied**:
1. Removed the `if len(records) >= limit: break` check that stopped collection at the first 60 records
2. Added `return records[-limit:]` at the end to take the LAST `limit` records (the most recent ones)

**Impact**: 
- Before fix: DB had 3000 trading rows (50×60 days) but only for old data range (2026-03-02 to 2026-06-01)
- After fix: DB has 3000 trading rows (50×60 days) for the current data range (2026-06-27 to 2026-08-28)
- 45 suggestions are now being generated correctly for the most recent date

**Status**: Fixed (2026-08-30)