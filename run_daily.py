import datetime
from data_fetcher import fetch_and_store, DEFAULT_SYMBOLS
from scoring import generate_suggestions
from models import init_db, get_session, DailyPrice

def main():
    # Ensure DB and tables exist
    init_db()

    # Define symbols to track (default list of ~50 NSE stocks)
    symbols = DEFAULT_SYMBOLS

    # Step 1: Fetch latest market data
    fetch_and_store(symbols)

    # Step 2: Generate suggestions for the latest date we actually have prices for
    session = get_session()
    latest = session.query(DailyPrice.date).order_by(DailyPrice.date.desc()).first()
    session.close()
    target_date = latest[0] if latest else (datetime.date.today() - datetime.timedelta(days=1))

    top = generate_suggestions(target_date)

    print('Top suggestions for', target_date)
    for sym, score, reason in top:
        print(f'{sym}: Score={score:.4f} | {reason}')

if __name__ == '__main__':
    main()
