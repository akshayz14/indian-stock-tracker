import argparse
from datetime import date, timedelta
from scoring import generate_suggestions
from models import get_session, Suggestion, Stock

def list_suggestions(target_date: date):
    session = get_session()
    suggestions = (
        session.query(Suggestion, Stock)
        .join(Stock, Suggestion.stock_id == Stock.id)
        .filter(Suggestion.date == target_date)
        .order_by(Suggestion.score.desc())
        .all()
    )
    if not suggestions:
        print(f'No suggestions found for {target_date}. Generating now...')
        top = generate_suggestions(target_date)
        for sym, score, reason in top:
            print(f'{sym}: Score={score:.4f} | {reason}')
    else:
        for sug, stock in suggestions:
            print(f'{stock.symbol}: Score={sug.score:.4f} | {sug.reasoning}')

def main():
    parser = argparse.ArgumentParser(description='Indian Stock Tracker CLI')
    parser.add_argument(
        '--date',
        type=str,
        help='Date for suggestions in YYYY-MM-DD (default: yesterday)'
    )
    args = parser.parse_args()
    if args.date:
        try:
            target = date.fromisoformat(args.date)
        except ValueError:
            print('Invalid date format. Use YYYY-MM-DD')
            return
    else:
        target = date.today() - timedelta(days=1)

    list_suggestions(target)

if __name__ == '__main__':
    main()