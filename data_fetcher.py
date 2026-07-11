import datetime
from sqlalchemy.orm import Session
from models import Stock, DailyPrice, get_session
from data_sources import fetch_with_fallback, resolve_name, DEFAULT_SOURCES

# Default list of NSE symbols to track (major large/mid-cap stocks).
# Expand this list to increase the pool of candidates for suggestions.
DEFAULT_SYMBOLS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'HINDUNILVR.NS', 'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS',
    'LT.NS', 'AXISBANK.NS', 'ASIANPAINT.NS', 'MARUTI.NS', 'SUNPHARMA.NS',
    'TATAMOTORS.NS', 'BAJFINANCE.NS', 'WIPRO.NS', 'NTPC.NS', 'POWERGRID.NS',
    'ONGC.NS', 'TATASTEEL.NS', 'HCLTECH.NS', 'ULTRACEMCO.NS', 'TITAN.NS',
    'ADANIPORTS.NS', 'BAJAJFINSV.NS', 'DRREDDY.NS', 'GRASIM.NS', 'CIPLA.NS',
    'EICHERMOT.NS', 'COALINDIA.NS', 'JSWSTEEL.NS', 'BPCL.NS', 'IOC.NS',
    'DIVISLAB.NS', 'TECHM.NS', 'HEROMOTOCO.NS', 'HDFCLIFE.NS', 'SBILIFE.NS',
    'INDUSINDBK.NS', 'BRITANNIA.NS', 'APOLLOHOSP.NS', 'M&M.NS', 'NESTLEIND.NS',
    'UPL.NS', 'SHREECEM.NS', 'BAJAJ-AUTO.NS', 'TATACONSUM.NS', 'ADANIENT.NS',
]

# Ordered list of data sources used when fetching prices. yfinance is the
# primary source; NSE (via nsepy) is the fallback for resilience.
SOURCES = DEFAULT_SOURCES


# Helper to ensure a stock record exists
def get_or_create_stock(session: Session, symbol: str, name: str = None, exchange: str = None, sector: str = None):
    stock = session.query(Stock).filter_by(symbol=symbol).first()
    if not stock:
        stock = Stock(symbol=symbol, name=name or symbol, exchange=exchange or 'NSE', sector=sector)
        session.add(stock)
        session.commit()
    return stock


def fetch_and_store(symbols, sources=None):
    """
    Fetch daily price data for given symbols and store in SQLite DB.

    Symbols should be in Yahoo Finance format, e.g., 'RELIANCE.NS'. Data is
    pulled from the configured sources (yfinance first, then NSE as a
    fallback), so a failure in one provider does not drop the stock entirely.
    """
    sources = sources or SOURCES
    session = get_session()
    for sym in symbols:
        try:
            ohlcv = fetch_with_fallback(sym, sources)
            if ohlcv is None:
                print(f'No data for {sym} from any source')
                continue

            date = ohlcv.date

            # Resolve a friendly name, falling back across sources.
            name = resolve_name(sym, sources)
            stock = get_or_create_stock(session, sym, name=name, exchange='NSE')

            # Check if price for this date already exists
            exists = session.query(DailyPrice).filter_by(stock_id=stock.id, date=date).first()
            if exists:
                continue

            price = DailyPrice(
                stock_id=stock.id,
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
    # Example usage
    sample_symbols = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS']
    fetch_and_store(sample_symbols)