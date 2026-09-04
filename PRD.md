# Product Requirements Document (PRD)
## Indian Stock Tracker – Version 1.3

### 1. Purpose
A lightweight, automated system for Indian investors to fetch daily market data, score stocks using an enhanced momentum-plus-volume strategy with additional technical indicators (RSI, MA, close strength, gap), and expose the results via CLI and a modern web UI. Now includes mutual fund analysis with NAV-based scoring from TigZig API with dynamic scheme discovery and freshness filtering.

### 2. Target Audience
- Individual retail investors
- Financial analysts
- Hobbyists who want quick, data-driven insights into NSE-listed equities, mutual funds, bonds, derivatives, and commodities

### 3. Technology Stack
- **Language**: Python 3.10+
- **Database**: SQLite with SQLAlchemy ORM (separate databases: `stocks.db` for equities, `mutual_funds.db` for mutual funds)
- **Data Sources**: 
  - Equities: NSE India CSV (primary), Yahoo Finance/yfinance (fallback)
  - Mutual Funds: TigZig API (Dynamic scheme discovery with pagination)
- **Web Framework**: Flask with Tailwind CSS v4 and custom design system
- **CLI**: argparse-based command-line interface
- **Scheduling**: APScheduler for automation
- **Charts**: Chart.js for interactive visualizations
- **Demo Data**: Structured demo data for UI development and testing

### 4. Key Features
1. **Enhanced Data Fetching**: 
   - Pull OHLCV data for Nifty 50 equities with automatic fallback to Yahoo Finance
   - Dynamic mutual fund scheme discovery from TigZig API with pagination support
   - Direct Growth fund filtering (plan=Direct, option=Growth)
2. **Mutual Fund Processing**:
   - Dynamic fetching of 30+ funds per category (Large Cap, Mid Cap, Small Cap, Debt)
   - Debt sub-category expansion (18 sub-categories) to ensure adequate fund coverage
   - Freshness filtering: Excludes funds with no NAV updates within 2 years AND no recent data within 1 year
   - Returns calculation: 1Y, 3Y, 5Y CAGR returns with volatility adjustment
   - Percentile ranking within categories for fair comparison
3. **Enhanced Scoring Engine**: 
   - Composite score = momentum × 0.7 + volume_factor × 0.3 (base)
   - Additional factors: RSI, Moving Average, Close Strength, Gap-Up signals
   - Mutual fund scoring: CAGR returns with volatility adjustment and percentile ranking
4. **Persistence**: SQLite database via SQLAlchemy with automatic schema migration
5. **CLI**: `python cli.py [--date dd-mm-yyyy]` for top suggestions (generates on-demand if missing)
6. **Automation**: 
   - `run_daily.py`: Fetches, scores, and stores suggestions for ALL dates in 60-day window
   - `mutual_fund_db.py`: Fetches and processes mutual fund data with rate-limit handling
   - `run.py`: Unified entry point for daily operations
7. **Modern Web UI**: 
   - Flask UI at http://localhost:8080 with professional fintech design
   - Dark/Light theme toggle with localStorage persistence
   - Interactive charts using Chart.js
   - Responsive layout with sidebar navigation
   - Demo data integration for development and testing
8. **Enhanced Features**:
   - Stock search with yfinance fallback for non-Nifty 50 stocks
   - CSV exports for top mutual funds by category
   - Schema version tracking for automatic database migrations
   - Friendly error pages for API failures
   - Holiday detection and storage for market calendar awareness

### 5. Constraints
- Must run on macOS/Linux/Windows with Python 3.10+
- No external paid APIs; only free public data sources (NSE CSV, yfinance, TigZig API)
- SQLite database size ≤ 200 MB for typical usage
- Separate databases for equities (`stocks.db`) and mutual funds (`mutual_funds.db`)

### 6. Document Version
- PRD.md: Version 1.3, Last Updated: 2026-09-03

- [x] Update PRD.md to reflect mutual fund TigZig API integration
- [x] Update PRD.md to reflect enhanced scoring engine (RSI, MA, close strength, gap)
- [x] Update PRD.md to reflect mutual fund freshness filtering
- [x] Update PRD.md to reflect modern web UI redesign with Tailwind CSS
- [x] Update PRD.md to reflect dynamic mutual fund scheme discovery
- [x] Update PRD.md to reflect enhanced automation (`run_daily.py` processes 60-day window)
- [x] Update PRD.md to reflect schema version tracking and auto-migration
- [x] Update PRD.md to reflect stock search functionality for non-Nifty 50 stocks