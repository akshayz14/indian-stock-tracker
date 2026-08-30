"""
Backfill script: Generate suggestions for all historical dates that have
substantial price data (at least 20 stocks).

This script ensures that the Suggestion table is populated for all dates
that the user might want to filter by. After running once, subsequent
cron runs of run_daily.py will add suggestions for new dates automatically.
"""
import sys
from sqlalchemy import func
from models import get_session, DailyPrice, Suggestion
from scoring2 import generate_suggestions

# Minimum number of stocks needed for a date to be considered "substantial"
MIN_STOCKS_PER_DATE = 20

def backfill_suggestions():
    session = get_session()
    try:
        # Find all dates that have substantial price data
        dates_with_data = session.query(
            DailyPrice.date, func.count(DailyPrice.id).label('cnt')
        ).group_by(DailyPrice.date).having(
            func.count(DailyPrice.id) >= MIN_STOCKS_PER_DATE
        ).order_by(DailyPrice.date.desc()).all()
        
        print(f"Found {len(dates_with_data)} dates with substantial price data")
        
        total_generated = 0
        for i, (date, count) in enumerate(dates_with_data):
            # Check if suggestions already exist for this date
            existing_count = session.query(Suggestion).filter_by(date=date).count()
            if existing_count == 0:
                print(f"[{i+1}/{len(dates_with_data)}] Generating suggestions for {date} ({count} prices)...")
                try:
                    result = generate_suggestions(date)
                    total_generated += 1
                    print(f"  → Generated {len(result)} suggestions for {date}")
                except Exception as e:
                    print(f"  → Error generating for {date}: {e}")
            else:
                print(f"[{i+1}/{len(dates_with_data)}] Skipping {date} (already has {existing_count} suggestions)")
        
        print(f"\nBackfill complete. Generated suggestions for {total_generated} new dates.")
        
        # Summary
        total_suggestions = session.query(Suggestion).count()
        distinct_dates = session.query(Suggestion.date).distinct().count()
        print(f"Database now has {total_suggestions} suggestions across {distinct_dates} distinct dates")
    finally:
        session.close()

if __name__ == '__main__':
    backfill_suggestions()
