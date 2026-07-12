import argparse
from datetime import date, timedelta
from scoring import generate_suggestions
from models import get_session, Suggestion, Asset

def list_suggestions(target_date: date, asset_type: str = None):
    session = get_session()
    query = session.query(Suggestion, Asset).join(Asset, Suggestion.asset_id == Asset.id)
    query = query.filter(Suggestion.date == target_date)
    if asset_type:
        query = query.filter(Asset.type == asset_type)
    suggestions = query.order_by(Suggestion.score.desc()).all()
    if not suggestions:
        print(f'No suggestions found for {target_date}. Generating now...')
        top = generate_suggestions(target_date)
        for sym, score, reason in top:
            print(f'{sym}: Score={score:.4f} | {reason}')
    else:
        for sug, asset in suggestions:
            print(f'{asset.symbol}: Score={sug.score:.4f} | {sug.reasoning}')
    session.close()

def main():
    parser = argparse.ArgumentParser(description='Indian Stock Tracker CLI')
    parser.add_argument(
        '--date',
        type=str,
        help='Date for suggestions in YYYY-MM-DD (default: yesterday)'
    )
    parser.add_argument(
        '--type',
        type=str,
        choices=['equity', 'mutual_fund', 'bond', 'derivative', 'commodity'],
        help='Filter suggestions by asset type'
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

    list_suggestions(target, args.type)

if __name__ == '__main__':
    main()