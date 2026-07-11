import datetime
from sqlalchemy.orm import Session
from models import Stock, DailyPrice, Suggestion, get_session

def calculate_score(price: DailyPrice) -> float:
    """
    Simple scoring:
    - Price momentum: (close - open) / open
    - Volume factor: volume / average volume over last 5 days (approx)
    Returns a composite score (higher is better).
    """
    momentum = (price.close - price.open) / price.open if price.open else 0

    # Compute average volume over last 5 days for the same stock
    session = get_session()
    five_days_ago = price.date - datetime.timedelta(days=5)
    recent_volumes = (
        session.query(DailyPrice.volume)
        .filter(DailyPrice.stock_id == price.stock_id, DailyPrice.date >= five_days_ago, DailyPrice.date < price.date)
        .all()
    )
    session.close()
    volumes = [v[0] for v in recent_volumes if v[0] is not None]
    avg_volume = sum(volumes) / len(volumes) if volumes else price.volume
    volume_factor = price.volume / avg_volume if avg_volume else 1

    # Composite score (weights can be tuned)
    return momentum * 0.7 + volume_factor * 0.3

def generate_suggestions(target_date: datetime.date = None, top_n: int = 5):
    """
    Generate top N suggestions for the given date (default: yesterday).
    Stores suggestions in the DB and returns a list of (symbol, score, reasoning).
    """
    session = get_session()
    if target_date is None:
        target_date = datetime.date.today() - datetime.timedelta(days=1)

    # Get all price records for the target date
    prices = session.query(DailyPrice).filter(DailyPrice.date == target_date).all()
    suggestions = []
    for price in prices:
        score = calculate_score(price)
        reasoning = f"Momentum: {(price.close - price.open) / price.open:.2%}, Volume factor: {price.volume / (price.volume or 1):.2f}"
        suggestions.append((price.stock.symbol, score, reasoning))

    # Sort and take top N
    suggestions.sort(key=lambda x: x[1], reverse=True)
    top = suggestions[:top_n]

    # Store in DB
    for symbol, score, reasoning in top:
        stock = session.query(Stock).filter_by(symbol=symbol).first()
        if stock:
            existing = (
                session.query(Suggestion)
                .filter_by(date=target_date, stock_id=stock.id)
                .first()
            )
            if not existing:
                sug = Suggestion(date=target_date, stock_id=stock.id, score=score, reasoning=reasoning)
                session.add(sug)
    session.commit()
    session.close()
    return top