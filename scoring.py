import datetime
from sqlalchemy.orm import Session
from models import Asset, DailyPrice, Suggestion, get_session

def calculate_score(price: DailyPrice) -> float:
    """
    Simple scoring:
    - Price momentum: (close - open) / open
    - Volume factor: volume / average volume over last 5 days (approx)
    Returns a composite score (higher is better).
    """
    momentum = (price.close - price.open) / price.open if price.open else 0

    # Compute average volume over last 5 days for the same asset
    session = get_session()
    five_days_ago = price.date - datetime.timedelta(days=5)
    recent_volumes = (
        session.query(DailyPrice.volume)
        .filter(DailyPrice.asset_id == price.asset_id, DailyPrice.date >= five_days_ago, DailyPrice.date < price.date)
        .all()
    )
    session.close()
    volumes = [v[0] for v in recent_volumes if v[0] is not None]
    avg_volume = sum(volumes) / len(volumes) if volumes else price.volume
    volume_factor = price.volume / avg_volume if avg_volume else 1

    # Composite score (weights can be tuned)
    return momentum * 0.7 + volume_factor * 0.3

def generate_suggestions(target_date: datetime.date = None, top_n: int = 50):
    """
    Generate top N suggestions for the given date (default: yesterday).
    Stores suggestions in the DB and returns a list of (symbol, score, reasoning).
    """
    session = get_session()
    if target_date is None:
        target_date = datetime.date.today() - datetime.timedelta(days=1)

    # Get all price records for the target date (exclude mutual funds;
    # they are scored separately via generate_mf_suggestions)
    prices = (
        session.query(DailyPrice)
        .join(Asset, DailyPrice.asset_id == Asset.id)
        .filter(DailyPrice.date == target_date, Asset.type != 'mutual_fund')
        .all()
    )
    suggestions = []
    for price in prices:
        score = calculate_score(price)
        reasoning = f"Momentum: {(price.close - price.open) / price.open:.2%}, Volume factor: {price.volume / (price.volume or 1):.2f}"
        suggestions.append((price.asset.symbol, score, reasoning))

    # Sort and take top N
    suggestions.sort(key=lambda x: x[1], reverse=True)
    top = suggestions[:top_n]

    # Store in DB
    for symbol, score, reasoning in top:
        asset = session.query(Asset).filter_by(symbol=symbol).first()
        if asset:
            existing = (
                session.query(Suggestion)
                .filter_by(date=target_date, asset_id=asset.id)
                .first()
            )
            if not existing:
                sug = Suggestion(date=target_date, asset_id=asset.id, score=score, reasoning=reasoning)
                session.add(sug)
    session.commit()
    session.close()
    return top


def calculate_mf_score(price: DailyPrice) -> float:
    """
    Mutual-fund scoring based on NAV returns (since NAV has no intraday
    open/close or volume). We use a composite of:

      * Daily NAV return: (NAV_t - NAV_{t-1}) / NAV_{t-1}
      * Short-term momentum: (NAV_t - NAV_{t-20}) / NAV_{t-20}

    Both are scaled and combined. Higher is better.
    """
    session = get_session()
    try:
        # Previous NAV (most recent before this record)
        prev = (
            session.query(DailyPrice)
            .filter(DailyPrice.asset_id == price.asset_id, DailyPrice.date < price.date)
            .order_by(DailyPrice.date.desc())
            .first()
        )
        # NAV ~20 trading days ago (approx 1 month)
        month_ago = price.date - datetime.timedelta(days=30)
        month = (
            session.query(DailyPrice)
            .filter(DailyPrice.asset_id == price.asset_id, DailyPrice.date <= month_ago)
            .order_by(DailyPrice.date.desc())
            .first()
        )
    finally:
        session.close()

    daily_return = (price.close - prev.close) / prev.close if prev and prev.close else 0.0
    monthly_return = (price.close - month.close) / month.close if month and month.close else 0.0

    # Scale returns (e.g. 1% daily -> 0.7, 5% monthly -> 0.3) and clamp.
    score = daily_return * 70 + monthly_return * 6
    return max(score, 0.0)


def generate_mf_suggestions(target_date: datetime.date = None, top_n: int = 50):
    """
    Generate mutual-fund suggestions using NAV-based scoring. Each mutual fund
    is scored on its own most-recent NAV (so funds with different latest NAV
    dates are all included). The suggestion is stamped with that fund's latest
    NAV date. Returns a list of (symbol, score, reasoning).
    """
    session = get_session()

    mf_assets = session.query(Asset).filter(Asset.type == 'mutual_fund').all()
    suggestions = []
    for asset in mf_assets:
        latest = (
            session.query(DailyPrice)
            .filter(DailyPrice.asset_id == asset.id)
            .order_by(DailyPrice.date.desc())
            .first()
        )
        if not latest:
            continue
        score = calculate_mf_score(latest)
        reasoning = "NAV-based score (daily + monthly return)"
        suggestions.append((asset.symbol, score, reasoning, latest.date, asset.id))

    suggestions.sort(key=lambda x: x[1], reverse=True)
    top = suggestions[:top_n]

    for symbol, score, reasoning, sug_date, asset_id in top:
        existing = (
            session.query(Suggestion)
            .filter_by(date=sug_date, asset_id=asset_id)
            .first()
        )
        if not existing:
            sug = Suggestion(date=sug_date, asset_id=asset_id, score=score, reasoning=reasoning)
            session.add(sug)
    session.commit()
    session.close()
    return [(s[0], s[1], s[2]) for s in top]
