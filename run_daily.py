import datetime
from data_fetcher import fetch_and_store
from scoring import generate_suggestions
from models import init_db

def main():
    # Ensure DB and tables exist
    init_db()

    # Define symbols to track (can be expanded later)
    symbols = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS']

    # Step 1: Fetch latest market data
    fetch_and_store(symbols)

    # Step 2: Generate suggestions for yesterday (or today if market closed)
    target_date = datetime.date.today() - datetime.timedelta(days=1)
    top = generate_suggestions(target_date)

    print('Top suggestions for', target_date)
    for sym, score, reason in top:
        print(f'{sym}: Score={score:.4f} | {reason}')

if __name__ == '__main__':
    main()