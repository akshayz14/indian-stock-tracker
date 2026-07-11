import os
import datetime
import yfinance as yf
from sqlalchemy.orm import Session
from models import Stock, DailyPrice, get_session

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

# Helper to ensure a stock record exists
def get_or_create_stock(session: Session, symbol: str, name: str = None, exchange: str = None, sector: str = None):
    stock = session.query(Stock).filter_by(symbol=symbol).first()
    if not stock:
        stock = Stock(symbol=symbol, name=name or symbol, exchange=exchange or 'NSE', sector=sector)
        session.add(stock)
        session.commit()
    return stock

def fetch_and_store(symbols):
    """
    Fetch daily price data for given symbols and store in SQLite DB.
    Symbols should be in Yahoo Finance format, e.g., 'RELIANCE.NS'
    """
    session = get_session()
    for sym in symbols:
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period='2d')  # get last 2 days to ensure we have yesterday's close
            if hist.empty:
                print(f'No data for {sym}')
                continue

            # Use the most recent row (yesterday's data)
            latest = hist.iloc[-1]
            date = latest.name.date() if isinstance(latest.name, datetime.datetime) else latest.name

            stock = get_or_create_stock(session, sym, name=ticker.info.get('shortName'), exchange='NSE')
            # Check if price for this date already exists
            exists = session.query(DailyPrice).filter_by(stock_id=stock.id, date=date).first()
            if exists:
                continue

            price = DailyPrice(
                stock_id=stock.id,
                date=date,
                open=latest['Open'],
                high=latest['High'],
                low=latest['Low'],
                close=latest['Close'],
                adj_close=latest.get('Adj Close', latest['Close']),
                volume=latest['Volume']
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