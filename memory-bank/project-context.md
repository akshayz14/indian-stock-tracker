# Project Context

## Project Name
Indian Stock Tracker

## Purpose
A lightweight, automated system for Indian investors to fetch daily market data, score stocks using a momentum-plus-volume strategy, and expose the results via CLI and a web UI.

## Target Audience
- Individual retail investors
- Financial analysts
- Hobbyists who want quick, data-driven insights into NSE-listed equities, mutual funds, bonds, derivatives, and commodities

## Technology Stack
- **Language**: Python 3.10+
- **Database**: SQLite with SQLAlchemy ORM
- **Data Sources**: NSE India CSV (primary), Yahoo Finance/yfinance (fallback)
- **Web Framework**: Flask
- **CLI**: argparse-based command-line interface
- **Scheduling**: APScheduler for automation

## Key Features
1. **Data Fetching**: Pull OHLCV data for Nifty 50 equities with automatic fallback to Yahoo Finance
2. **Scoring Engine**: Composite score = momentum × 0.7 + volume_factor × 0.3
3. **Persistence**: SQLite database via SQLAlchemy
4. **CLI**: `python cli.py [--date YYYY-MM-DD]` for top suggestions
5. **Automation**: `run_daily.py` for cron scheduling
6. **Web UI**: Flask UI at http://localhost:8080

## Constraints
- Must run on macOS/Linux/Windows with Python 3.10+
- No external paid APIs; only free public data sources
- SQLite database size ≤ 200 MB for typical usage

## Document Version
- PRD.md: Version 1.0, Last Updated: 2026-07-25
- TRD.md: Version 1.0, Last Updated: 2026-08-04

- [x] Create project-context.md