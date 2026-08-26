import datetime
from sqlalchemy.orm import Session
from models import Asset, DailyPrice, Suggestion, get_session
from data_sources import fetch_with_fallback, resolve_name, DEFAULT_SOURCES, MutualFundSource

# Default list of symbols to track
# Each entry is a tuple: (symbol, type)
# 50 valid mfapi.in scheme codes (mutual funds) + Nifty 50 equities fetched from NSE
import requests
import io
import pandas as pd

MF_SCHEME_CODES = [
    119000, 119001, 119002, 119003, 119004, 119005, 119006, 119007, 119008, 119009,
    119010, 119011, 119012, 119013, 119014, 119015, 119016, 119017, 119018, 119019,
    119020, 119021, 119022, 119023, 119024, 119025, 119026, 119027, 119028, 119029,
    119030, 119031, 119032, 119033, 119034, 119035, 119036, 119037, 119038, 119039,
    119040, 119041, 119042, 119043, 119044, 119045, 119046, 119047, 119048, 119049,
]

def get_nifty50_symbols():
    """
    Fetch Nifty 50 symbols from NSE India.
    Returns a list of symbols (without .NS suffix).
    """
    print("Fetching Nifty 50 symbols from NSE...")
    url = 'https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv'
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
        nse_symbols = df['Symbol'].tolist()
        print(f"Successfully fetched {len(nse_symbols)} Nifty 50 symbols.")
        return nse_symbols
    except Exception as e:
        print(f"Failed to download Nifty 50 list from NSE: {e}")
        # Fallback: try to use NSESource if available
        try:
            from data_sources import NSESource
            # Note: NSESource.fetch_latest does not give us the list of symbols.
            # This is just to show we tried; we'll return empty list.
            print("NSESource available but cannot fetch constituent list; returning empty.")
            return []
        except ImportError:
            print("NSESource not available either.")
            return []

def get_default_symbols():
    """
    Get the complete list of default symbols to track.
    Combines Nifty 50 equities with mutual fund scheme codes.
    """
    # Get Nifty 50 symbols
    nifty50_symbols = get_nifty50_symbols()
    
    # Create equity symbols from Nifty 50 (append .NS suffix for yfinance)
    equity_symbols = [(f"{symbol}.NS", 'equity') for symbol in nifty50_symbols]
    
    # Add mutual fund symbols
    mutual_fund_symbols = [(str(code), 'mutual_fund') for code in MF_SCHEME_CODES]
    
    # Combine and return
    return equity_symbols + mutual_fund_symbols

# Get the default symbols
DEFAULT_SYMBOLS = get_default_symbols()

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
    For equities we store recent price history (last 60 days) for charting
    and analysis purposes.
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

            # For equities, fetch and store recent historical price data (last 60 days)
            # Use YFinanceSource directly to get history, as it's most reliable for historical data
            from data_sources import YFinanceSource
            yf_source = YFinanceSource()
            history_records = yf_source.fetch_history(sym, limit=60)
            # If we couldn't get history with the original symbol, try without suffix
            if not history_records and (sym.endswith('.NS') or sym.endswith('.BO')):
                base_symbol = sym.replace('.NS', '').replace('.BO', '')
                history_records = yf_source.fetch_history(base_symbol, limit=60)
            
            if not history_records:
                print(f'No historical data for {sym} from any source')
                # Fallback to storing just the latest price for backward compatibility
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
                print(f'Stored latest price data for {sym} on {date} (fallback)')
            else:
                # Store all historical price records
                name = resolve_name(sym, srcs)
                asset = get_or_create_asset(session, sym, name=name, asset_type=sym_type)
                stored = 0
                for ohlcv_record in history_records:
                    exists = session.query(DailyPrice).filter_by(asset_id=asset.id, date=ohlcv_record.date).first()
                    if exists:
                        continue
                    price = DailyPrice(
                        asset_id=asset.id,
                        date=ohlcv_record.date,
                        open=ohlcv_record.open,
                        high=ohlcv_record.high,
                        low=ohlcv_record.low,
                        close=ohlcv_record.close,
                        adj_close=ohlcv_record.adj_close,
                        volume=ohlcv_record.volume
                    )
                    session.add(price)
                    stored += 1
                session.commit()
                if stored:
                    print(f'Stored {stored} historical price records for {sym}')
        except Exception as e:
            print(f'Error fetching {sym}: {e}')
    session.close()

if __name__ == '__main__':
    fetch_and_store(DEFAULT_SYMBOLS)