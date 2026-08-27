# Known Issues

## 1. Dashboard Charts Not Displaying Data
**Description**: The dashboard overview charts (Top Gainers Bar Chart and Score Distribution Histogram) in `templates/index.html` reference JavaScript variables (`top_gainer_labels`, `top_gainer_values`, `score_labels`, `score_data`) that are not being passed from the Flask `index()` route in `flask_app.py`.

**Location**: 
- Template: `templates/index.html` lines 44-63 (chart containers) and lines 68-132 (JavaScript)
- Route: `flask_app.py` lines 66-81 (`index()` function)

**Impact**: Charts appear on the dashboard but display no data.

**Workaround**: None currently available - charts remain empty.

**Status**: Open

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

**Status**: Open

## 4. Mutual Fund Suggestion Testing Incomplete
**Description**: The mutual fund suggestion generation and display functionality has been implemented but not fully tested.

**Location**: 
- Mutual fund scoring: `mutual_fund_db.py` scoring logic
- Suggestion display: `/mutual-funds` route and template

**Impact**: Potential for incorrect scoring or display of mutual fund suggestions.

**Workaround**: Manual verification of mutual fund suggestion scores and rankings.

**Status**: Open

## 5. Search Functionality Cache May Serve Stale Data
**Description**: The in-memory cache for stock search history (`search_history_cache` in `flask_app.py`) uses a fixed TTL of 1 hour but doesn't invalidate when new data is fetched for the same symbol.

**Location**: `flask_app.py` lines 14-16 (cache definition) and lines 627-633 (cache usage)

**Impact**: Search results may show outdated price data for up to 1 hour after new data is available.

**Workaround**: None - data will refresh automatically after cache expiration.

**Status**: Open (considered low priority)