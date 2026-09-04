# Task History

## 2026-09-03: Fix Missing Columns in Legacy Databases - COMPLETED

**Type:** Bug Fix / Enhancement
**Status:** Completed

**Goal:** Fix `sqlalchemy.OperationalError: no such column: daily_prices.is_holiday` that occurs when merging with an old production database that lacks the `is_holiday` column, and implement systematic schema version tracking to prevent future occurrences.

**Problem:** The `_add_missing_columns()` function in `models.py` was designed to handle schema migrations, but it was only called from `init_db()`. Many code paths (like `cli.py` and `flask_app.py`) use `get_session()` directly without calling `init_db()` first, so the migration never happened when merging with old production databases.

**Fix Applied:**

1. **Modified `get_session()` in `models.py`** (line 142-151): Now automatically calls `Base.metadata.create_all(engine)` and `_add_missing_columns(engine)` before creating a session. This ensures the `is_holiday` column is added to `daily_prices` if missing, and all other expected columns are present.

2. **Modified `get_mutual_fund_session()` in `models.py`** (line 166-173): Now automatically calls `Base.metadata.create_all(engine)` and `_add_missing_mutual_fund_columns(engine)` before creating a session. This ensures the `latest_nav_date` column is added to `mutual_fund_assets` if missing.

3. **Added schema version tracking** (line 196-220): 
   - Added `_get_schema_version()` and `_set_schema_version()` functions
   - Modified `init_db(db_version='2.0')` to accept and track a schema version
   - The schema version is stored in a `schema_version` table in the database
   - `_set_schema_version()` uses INSERT/UPDATE logic to handle both new and existing (potentially empty) tables
   - Version number increments whenever model changes are made, providing a systematic way to track changes

4. **Updated callers to pass version:**
   - `run.py` line 29: Changed `init_db()` to `init_db(db_version='2.0')`
   - `run_daily.py` line 11: Changed `init_db()` to `init_db(db_version='2.0')`

5. **Auto-migration on every session**: The `get_session()` and `get_mutual_fund_session()` functions now automatically run migrations on every session creation, ensuring that:
   - New databases get the correct schema
   - Old/merged databases get missing columns added automatically
   - The schema version tracks what version the DB is at

**Files Changed:**
- `models.py` — Core fix: updated `get_session()`, `get_mutual_fund_session()`, added `_get_schema_version()`, `_set_schema_version()`, updated `init_db()`
- `run.py` — Updated to pass `db_version='2.0'` to `init_db()`
- `run_daily.py` — Updated to pass `db_version='2.0'` to `init_db()`

**Impact:** Any existing database (including those from merged old production projects) now automatically gets the required columns (`is_holiday` in `daily_prices`, `latest_nav_date` in `mutual_fund_assets`) without manual intervention. The schema version provides systematic tracking of model changes.

**Test:** Verified with a test that creates an old-style database without the `is_holiday` column, then calls `get_session()` — the column is automatically added and queries succeed. The schema version is correctly tracked and persists across sessions.

**Test:** Verified with a test that creates an old-style database without the `is_holiday` column, then calls `get_session()` — the column is automatically added and queries succeed.
# Task History

## 2026-08-30: Change Top 50 Mutual Funds to use mutual_funds.db - COMPLETED

**Type**: Feature (Data Source Change)
**Status**: Completed

**Goal**: Change the `/top-mutual-funds` Flask route to pull top 50 mutual funds from the dedicated `mutual_funds.db` database instead of the legacy `stocks.db` data source.

**Files Changed**:
- `flask_app.py` - Updated `top_mutual_funds()` route to use `get_mutual_fund_session()` and `MutualFundAsset`/`MutualFundSuggestion` models instead of `get_session()` and `Asset`/`Suggestion`
- `templates/top_mutual_funds.html` - Updated field mappings to use `scheme_name`, `scheme_code`, and `fund_house` instead of `name`, `symbol`, and `exchange`

**Key Changes**:
- Switched database from `stocks.db` to `mutual_funds.db` via `get_mutual_fund_session()`
- Changed models from `Asset`/`Suggestion` to `MutualFundAsset`/`MutualFundSuggestion`
- Changed freshness filter from `Suggestion.date` to `MutualFundAsset.latest_nav_date`
- Updated template field mappings to match `MutualFundAsset` model

**Results**:
- Top 50 funds now ranked globally across all categories (Debt, Large Cap, Mid Cap, Small Cap)
- Scores are based on category percentile rankings already stored in `mutual_funds.db`
- 154 funds available for selection; 50 returned by the query
- Route tested and returning HTTP 200 with correct fund names and scores

## 2026-08-30: Mutual Fund Dynamic Fetching from TigZig API - COMPLETED

**Type**: Feature (Major Redesign)
**Status**: Completed

**Goal**: Redesign mutual fund tracker to dynamically fetch 30+ unique funds per category (large cap, mid cap, small cap, debt) from the TigZig API, replacing the hardcoded list of ~50 scheme codes, and store the top funds per category in the SQLite database.

**Files Changed**:
- `mutual_fund_db.py` (major rework - completely rewritten for dynamic fetching)

**Key Changes**:
- Removed hardcoded `get_all_schemes()` function
- Added `search_schemes()` with `plan="Direct"` and `option="Growth"` query parameters
- Added `fetch_all_schemes_for_category()` with pagination support for all categories
- Added `fetch_and_filter_direct_growth()` to filter API results
- Added `DEBT_SUB_CATEGORIES` dict with 18 sub-categories for debt category expansion
- Added `DEBT_CATEGORY_MAPPING` for explicit debt category handling
- Updated `process_fund()` to accept cached metadata from `search_schemes()` calls
- Changed `TOP_N` from 40 to 45 to target 30+ funds per category
- Added rate-limit handling with exponential backoff and retry logic in `get_json()`
- Reduced `MAX_FUND_AGE_DAYS` to 365 and `MAX_NO_RECENT_DATA_DAYS` to 730 for small/mid cap leniency
- Relaxed `calculate_score()` to accept funds with only 1-year return data
- Added NaN score handling in `store_fund_in_db()` to prevent IntegrityError
- Changed from `ThreadPoolExecutor` to sequential `process_funds_for_category()` to avoid 429 errors
- Added skip logic: categories with ≥30 existing DB funds are skipped
- Updated `get_category()` to handle TigZig API response format

**Results**:
- Large Cap: 33 funds (vs 30+ target)
- Mid Cap: 45 funds (vs 30+ target)
- Small Cap: 31 funds (vs 30+ target)
- Debt: 45 funds (vs 30+ target)
- Total: 154 funds in `mutual_funds.db`
- Generated CSV files: `top_large_cap_funds.csv`, `top_mid_cap_funds.csv`, `top_small_cap_funds.csv`, `top_debt_funds.csv`

**Challenges**:
- Debt sub-categories initially yielded insufficient funds; expanded from 2 to 18 sub-categories
- Small Cap only had 24 funds with old hardcoded list; dynamic fetching yielded 31
- TigZig API rate limiting (429) required switching from parallel to sequential processing
- NaN scores caused IntegrityError; fixed by converting to `float()` with fallback

## 2026-08-29: Mutual Fund Freshness Filtering

**Type**: Feature
**Status**: Completed

**Files Changed**:
- `mutual_fund_db.py` - Added `is_fund_recent()` function and freshness thresholds
- `models.py` - Added `latest_nav_date` column to `MutualFundAsset`
- `flask_app.py` - Added freshness filtering to `/mutual-funds` and `/top-mutual-funds` routes
- `migration.sql` - Added ALTER TABLE for `latest_nav_date` column
- `tests/test_mutual_fund_freshness.py` - Created 12 tests for freshness logic

**What Was Done**:
1. Implemented `is_fund_recent()` function in `mutual_fund_db.py` that checks if a fund has at least one NAV within the last 2 years (730 days) AND at least one NAV within the last 1 year (365 days)
2. Added `MAX_FUND_AGE_DAYS = 730` and `MAX_NO_RECENT_DATA_DAYS = 365` thresholds
3. Integrated check in `process_fund()` to skip stale funds during ingestion
4. Added `latest_nav_date` column to `MutualFundAsset` model
5. Updated `store_fund_in_db()` to save `latest_nav_date`
6. Added freshness filtering in Flask routes:
   - `/mutual-funds`: Filters `MutualFundAsset.latest_nav_date >= today - 730 days`
   - `/top-mutual-funds`: Filters `Suggestion.date >= today - 730 days`
7. Added migration SQL to add `latest_nav_date` column to existing `mutual_funds.db`
8. Created 12 comprehensive tests in `tests/test_mutual_fund_freshness.py`

## 2026-08-30: Friendly Error Pages for API Failures - COMPLETED

**Type**: Bug Fix / UX Improvement
**Status**: Completed

**Goal**: Replace raw HTML error strings (e.g., `Error fetching mutual fund details: 502 Server Error: Bad Gateway for url: https://api.mfapi.in/mf/118479`) returned from API-failing routes with a styled, user-friendly error page that fits the app's design.

**Files Changed**:
- `flask_app.py` - Added `categorize_error()` helper; updated `/mutual-funds/<scheme_code>` route
- `templates/error.html` (new) - Reusable error page that extends `base.html`
- `tests/test_error_handling.py` (new) - 9 unit tests for `categorize_error()`
- `tests/test_error_route.py` (new) - 4 integration tests for the `/mutual-funds/<scheme_code>` error path

**Key Changes**:
- Added `categorize_error(error_message)` that maps raw `requests`/`HTTPError` strings to `(title, message, status_code)` tuples for 404, 500, 502, 503, 504, timeouts, and connection errors.
- Updated `/mutual-funds/<scheme_code>` to call `categorize_error()` on failure and render `templates/error.html` with the correct HTTP status code.
- Created reusable `templates/error.html` with: warning icon, friendly title, message, collapsible `<details>` for the raw error, and "Back" + "Dashboard" buttons.
- All styling uses existing CSS variables (`--card`, `--text`, `--muted`, `--border`, `--bg`) for visual consistency. Mobile responsive (≤480px).

**Coverage**:
- 502 Bad Gateway → "Service Temporarily Unavailable" (502)
- 503 Service Unavailable → "Service Temporarily Unavailable" (503)
- 504 Gateway Timeout → "Gateway Timeout" (504)
- Read timed out → "Request Timed Out" (504)
- Connection errors / Max retries exceeded → "Connection Error" (503)
- 404 → "Not Found" (404)
- 500 → "Service Error" (502)
- Unknown → "Unexpected Error" (502)

**Tests**: 13 total (9 unit + 4 integration), all passing.
