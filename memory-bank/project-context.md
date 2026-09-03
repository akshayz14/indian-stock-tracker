# Project Context

## Project Name
Indian Stock Tracker

## Purpose
A lightweight, automated system for Indian investors to fetch daily market data, score stocks using a momentum-plus-volume strategy, and expose the results via CLI and a web UI. Now includes mutual fund analysis with NAV-based scoring.

## Target Audience
- Individual retail investors
- Financial analysts
- Hobbyists who want quick, data-driven insights into NSE-listed equities, mutual funds, bonds, derivatives, and commodities

## Technology Stack
- **Language**: Python 3.10+
- **Database**: SQLite with SQLAlchemy ORM (separate databases: `stocks.db` for equities, `mutual_funds.db` for mutual funds)
- **Data Sources**: NSE India CSV (primary), Yahoo Finance/yfinance (fallback), mfapi.in (mutual fund NAV data)
- **Web Framework**: Flask
- **CLI**: argparse-based command-line interface
- **Scheduling**: APScheduler for automation

## Key Features
1. **Data Fetching**: Pull OHLCV data for Nifty 50 equities with automatic fallback to Yahoo Finance
2. **Mutual Fund Data**: Fetch NAV history from mfapi.in for Direct Growth funds
3. **Scoring Engine**: Composite score = momentum × 0.7 + volume_factor × 0.3 (equities); CAGR returns with volatility adjustment (mutual funds)
4. **Persistence**: SQLite database via SQLAlchemy
5. **CLI**: `python cli.py [--date dd-mm-yyyy]` for top suggestions
6. **Automation**: `run_daily.py` for cron scheduling (equities); `mutual_fund_db.py` for mutual fund processing
7. **Web UI**: Flask UI at http://localhost:8080 with `/mutual-funds` route for category-filtered fund listings
8. **Export**: CSV exports for top mutual funds by category (Large Cap, Mid Cap, Small Cap, Debt)

## Constraints
- Must run on macOS/Linux/Windows with Python 3.10+
- No external paid APIs; only free public data sources
- SQLite database size ≤ 200 MB for typical usage

## Document Version
- PRD.md: Version 1.2, Last Updated: 2026-08-21
- TRD.md: Version 1.2, Last Updated: 2026-08-21

- [x] Create project-context.md
- [x] Update PRD.md to version 1.2
- [x] Update architecture.md to include mutual fund implementation details
- [x] Create known-issues.md documenting project issues