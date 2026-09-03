# Architectural Decisions

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
