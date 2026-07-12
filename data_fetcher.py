import datetime
from sqlalchemy.orm import Session
from models import Asset, DailyPrice, Suggestion, get_session
from data_sources import fetch_with_fallback, resolve_name, DEFAULT_SOURCES, MutualFundSource

# Default list of symbols to track
# Each entry is a tuple: (symbol, type)
# 50 valid mfapi.in scheme codes (mutual funds) + a few equities for context.
MF_SCHEME_CODES = [
    119000, 119001, 119002, 119003, 119004, 119005, 119006, 119007, 119008, 119009,
    119010, 119011, 119012, 119013, 119014, 119015, 119016, 119017, 119018, 119019,
    119020, 119021, 119022, 119023, 119024, 119025, 119026, 119027, 119028, 119029,
    119030, 119031, 119032, 119033, 119034, 119035, 119036, 119037, 119038, 119039,
    119040, 119041, 119042, 119043, 119044, 119045, 119046, 119047, 119048, 119049,
]

DEFAULT_SYMBOLS = [
    ('RELIANCE.NS', 'equity'),
    ('TCS.NS', 'equity'),
    ('HDFCBANK.NS', 'equity'),
] + [(str(code), 'mutual_fund') for code in MF_SCHEME_CODES]

# Helper to ensure an asset record exists
def get_or_create_asset(session: Session, symbol: str, name: str = None, exchange: str = None, sector: str = None, asset_type: str = 'equity'):
    asset = session.query(Asset).filter_by(symbol=symbol).first()
    if not asset:
        asset = Asset(symbol=symbol, name=name or symbol, exchange=exchange or 'NSE', sector=sector, type=asset_type)
        session.add(asset)
        session.commit()
    return asset

def fetch_and_store(symbols, sources=None):
    """
    Fetch daily price data for given symbols and store in SQLite DB.
    Symbols should be tuples: (symbol, type).
    For mutual funds we store the recent NAV history (not just the latest
    NAV) so that scoring has prior NAVs to compute returns against.
    """
    session = get_session()
    for sym, sym_type in symbols:
        # Determine source list
        if sym_type == 'mutual_fund':
            srcs = [MutualFundSource()]
        else:
            srcs = DEFAULT_SOURCES

        try:
            if sym_type == 'mutual_fund':
                # Store recent NAV history for proper scoring
                history = MutualFundSource().fetch_history(sym, limit=60)
                if not history:
                    print(f'No data for {sym} from any source')
                    continue
                name = resolve_name(sym, srcs)
                asset = get_or_create_asset(session, sym, name=name, asset_type=sym_type)
                stored = 0
                for ohlcv in history:
                    exists = session.query(DailyPrice).filter_by(asset_id=asset.id, date=ohlcv.date).first()
                    if exists:
                        continue
                    price = DailyPrice(
                        asset_id=asset.id,
                        date=ohlcv.date,
                        open=ohlcv.open, high=ohlcv.high, low=ohlcv.low,
                        close=ohlcv.close, adj_close=ohlcv.adj_close,
                        volume=ohlcv.volume
                    )
                    session.add(price)
                    stored += 1
                session.commit()
                if stored:
                    print(f'Stored {stored} NAV records for {sym}')
                continue

            ohlcv = fetch_with_fallback(sym, srcs)
            if ohlcv is None:
                print(f'No data for {sym} from any source')
                continue

            date = ohlcv.date
            name = resolve_name(sym, srcs)
            asset = get_or_create_asset(session, sym, name=name, asset_type=sym_type)

            # Check if price for this date already exists
            exists = session.query(DailyPrice).filter_by(asset_id=asset.id, date=date).first()
            if exists:
                continue

            price = DailyPrice(
                asset_id=asset.id,
                date=date,
                open=ohlcv.open,
                high=ohlcv.high,
                low=ohlcv.low,
                close=ohlcv.close,
                adj_close=ohlcv.adj_close,
                volume=ohlcv.volume
            )
            session.add(price)
            session.commit()
            print(f'Stored data for {sym} on {date}')
        except Exception as e:
            print(f'Error fetching {sym}: {e}')
    session.close()

if __name__ == '__main__':
    fetch_and_store(DEFAULT_SYMBOLS)