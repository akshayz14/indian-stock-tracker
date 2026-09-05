# Architectural Decisions

## 2026-09-03: Schema Version Tracking with Auto-Migration

**Decision**: Add a `schema_version` table to track database schema versions and auto-migrate missing columns in `get_session()` and `get_mutual_fund_session()`.

**Context**: When merging with old production databases, missing columns (`is_holiday` in `daily_prices`, `latest_nav_date` in `mutual_fund_assets`) caused `sqlalchemy.OperationalError: no such column` errors. The existing `_add_missing_columns()` function was only called from `init_db()`, which wasn't invoked by `cli.py` or `flask_app.py`.

**Chosen Approach**:
- Added `schema_version` table (id, version, updated_at) to both databases
- Modified `get_session()` and `get_mutual_fund_session()` to automatically:
  1. Call `Base.metadata.create_all(engine)` to create missing tables
  2. Call `_add_missing_columns()` / `_add_missing_mutual_fund_columns()` to add missing columns
  3. Track schema version (currently v2.0)
- Schema version is set on first session if not present

**Trade-offs**:
- Slight performance overhead on every session creation (minimal, runs once per process)
- Schema version tracking requires future migrations to bump `db_version` parameter
- Existing databases get auto-migrated without manual intervention

**Files Changed**:
- `models.py` - added `_get_schema_version()`, `_set_schema_version()`, updated `init_db()` to accept `db_version` parameter
- `run.py`, `run_daily.py` - pass `db_version='2.0'` to `init_db()`

## 2026-09-03: Tailwind CSS v4 via CDN (No Build Step)

**Decision**: Use Tailwind CSS v4 via CDN instead of a build-step approach for the landing page redesign.

**Context**: The landing page redesign required a modern fintech look with comprehensive design tokens. Adding a Tailwind build step would have required additional tooling (npm, postcss, etc.).

**Alternatives Considered**:
1. Tailwind build step (postcss) - rejected due to added tooling complexity
2. Pure custom CSS with BEM - rejected as harder to maintain design system
3. Tailwind CDN with custom CSS variables - chosen for simplicity and explicit theming

**Chosen Approach**:
- Tailwind CSS v4 via CDN
- Custom CSS variables in `static/style.css` for theme tokens
- Lucide icons via CDN
- Chart.js via CDN
- Google Fonts: DM Sans, JetBrains Mono
- localStorage for theme persistence

**Trade-offs**:
- CDN slightly slower than build-time (acceptable for prototype)
- Limited to Tailwind utilities available in CDN version
- Theme flash on page load prevented by inline `<head>` script

## 2026-08-30: Mutual Fund Dynamic Scheme Discovery (TigZig API)

**Decision**: Replace hardcoded list of ~50 mutual fund scheme codes with dynamic discovery from TigZig API.

**Context**: The previous implementation used a hardcoded list of scheme codes, which limited fund coverage and became stale as new funds were added. Only ~24 funds in Small Cap category were available.

**Chosen Approach**:
- Use TigZig API's `search_schemes()` with pagination support
- Filter at API level: `plan="Direct"`, `option="Growth"`
- Expand debt funds to 18 sub-categories to reach 30+ funds
- Sequential processing to avoid 429 rate limits
- `REQUEST_DELAY = 0.3` seconds between requests
- Skip categories with ≥30 existing DB funds (incremental updates)

**Results**:
- Large Cap: 33 funds
- Mid Cap: 45 funds
- Small Cap: 31 funds
- Debt: 45 funds
- Total: 154 funds (vs ~50 with hardcoded list)

**Trade-offs**:
- Slower than hardcoded (sequential API calls)
- Requires rate-limit handling (exponential backoff retry)
- New funds require re-running `mutual_fund_db.py`

**Files Changed**:
- `mutual_fund_db.py` - completely rewritten with `search_schemes()`, `fetch_all_schemes_for_category()`, `fetch_and_filter_direct_growth()`, `DEBT_SUB_CATEGORIES`
- Added `DEBT_CATEGORY_MAPPING` for explicit debt category handling
- Added NaN score handling in `store_fund_in_db()`

## 2026-08-29: Mutual Fund Freshness Filtering

**Decision**: Filter out mutual funds that have no NAV updates within the last 2 years (730 days) AND no NAV data within the last 1 year (365 days).

**Context**: The `/mutual-funds` tab was showing discontinued funds like "Principal Emerging Bluechip Fund - Direct Plan - Growth Option" whose last NAV update was in 2013. These funds are wound up/merged/inactive and cannot be purchased by retail investors in 2026. The mfapi.in API still returns historical data for these funds, so filtering must be done client-side.

**Alternatives Considered**:
1. Filter only at web UI display time (single-layer defense) - rejected because existing data in `stocks.db` and `mutual_funds.db` would still include stale entries.
2. Filter at ingestion time only - rejected because existing databases contain old entries that wouldn't be cleaned.
3. Use 1-year threshold only - rejected because some funds legitimately publish data less frequently (e.g., quarterly for some debt funds) and we want a reasonable grace period.
4. Use current-year check only - rejected because it would incorrectly exclude funds that publish NAV but haven't had one in the current year yet (e.g., if processing on Jan 1).

**Chosen Approach**: Defense in depth with hybrid threshold:
- Ingestion filter in `mutual_fund_db.py process_fund()` using `is_fund_recent()`
- Display filter in Flask routes (`/mutual-funds` and `/top-mutual-funds`)
- Two-prong check: latest NAV must be within 2 years, AND there must be at least one NAV within 1 year
- Added `latest_nav_date` column to `MutualFundAsset` for fast filtering

**Trade-offs**:
- A fund that pauses NAV publication for >1 year but resumes will not appear until refreshed data is available.
- A 2-year grace period is generous to avoid false positives (e.g., funds in regulatory review).
- Storing `latest_nav_date` requires DB migration for existing `mutual_funds.db` instances.

**Files Changed**:
- `mutual_fund_db.py` - added `is_fund_recent()`, `MAX_FUND_AGE_DAYS`, `MAX_NO_RECENT_DATA_DAYS` constants; integrated check in `process_fund()` and `store_fund_in_db()`
- `models.py` - added `latest_nav_date` column to `MutualFundAsset` and `_add_missing_mutual_fund_columns()` migration function
- `flask_app.py` - added `MF_FRESHNESS_DAYS` constant; added freshness filter to `/mutual-funds` and `/top-mutual-funds` routes
- `migration.sql` - added ALTER TABLE for existing databases
- `tests/test_mutual_fund_freshness.py` - 12 tests covering edge cases and integration
