"""
Real data service for the Indian Stock Tracker.

Provides a unified interface for fetching real-time market data from NSE India
and Yahoo Finance. Used to populate the dashboard's top gainers and top losers
sections with live data instead of demo data.

Caching: In-memory cache with TTL (5 minutes) to avoid excessive API calls.
"""

from __future__ import annotations

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GainerLoserStock:
    """Represents a single gainer or loser stock."""
    symbol: str
    name: str
    price: float
    change: float
    changePct: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'name': self.name,
            'price': self.price,
            'change': self.change,
            'changePct': self.changePct,
        }


@dataclass
class DashboardData:
    """Container for all dashboard data."""
    gainers: List[GainerLoserStock]
    losers: List[GainerLoserStock]

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        return {
            'gainers': [g.to_dict() for g in self.gainers],
            'losers': [l.to_dict() for l in self.losers],
        }


# In-memory cache for real-time data
_cache: Dict[str, tuple[Any, float]] = {}
CACHE_DURATION = 300  # 5 minutes


def _get_cached(key: str) -> Optional[Any]:
    """Get a value from cache if it exists and is fresh."""
    if key in _cache:
        value, timestamp = _cache[key]
        if time.time() - timestamp < CACHE_DURATION:
            return value
        del _cache[key]
    return None


def _set_cached(key: str, value: Any) -> None:
    """Set a value in the cache."""
    _cache[key] = (value, time.time())


def _safe_nse_call(func, *args, **kwargs) -> Optional[Any]:
    """Execute an NSE function with error handling."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"NSE API call failed: {e}")
        return None


def get_top_gainers_losers(limit: int = 10) -> Optional[DashboardData]:
    """
    Fetch real-time top gainers and top losers from NSE India.
    
    Args:
        limit: Maximum number of gainers/losers to return (default: 10)
        
    Returns:
        DashboardData with gainers and losers lists, or None if fetch fails
    """
    cached = _get_cached(f'gainers_losers_{limit}')
    if cached is not None:
        return cached

    gainers_list: List[GainerLoserStock] = []
    losers_list: List[GainerLoserStock] = []

    try:
        from nsetools import Nse
        nse = Nse()
        raw_gainers = _safe_nse_call(lambda: nse.get_top_gainers())
        raw_losers = _safe_nse_call(lambda: nse.get_top_losers())

        if not raw_gainers and not raw_losers:
            logger.warning("NSE returned no gainers or losers data")
            return None

        if raw_gainers:
            for stock in raw_gainers[:limit]:
                try:
                    symbol = stock.get('symbol', '')
                    price = float(stock.get('ltp', 0))
                    per_change = float(stock.get('perChange', 0))
                    net_change = float(stock.get('netPrice', 0))
                    name = stock.get('symbol', symbol)
                    gainers_list.append(GainerLoserStock(
                        symbol=symbol, name=name, price=price,
                        change=net_change, changePct=per_change
                    ))
                except (ValueError, TypeError) as e:
                    logger.debug(f"Skipping invalid gainer: {stock}, error: {e}")
                    continue

        if raw_losers:
            for stock in raw_losers[:limit]:
                try:
                    symbol = stock.get('symbol', '')
                    price = float(stock.get('ltp', 0))
                    per_change = float(stock.get('perChange', 0))
                    net_change = float(stock.get('netPrice', 0))
                    name = stock.get('symbol', symbol)
                    losers_list.append(GainerLoserStock(
                        symbol=symbol, name=name, price=price,
                        change=net_change, changePct=per_change
                    ))
                except (ValueError, TypeError) as e:
                    logger.debug(f"Skipping invalid loser: {stock}, error: {e}")
                    continue

        if gainers_list or losers_list:
            dashboard_data = DashboardData(gainers=gainers_list, losers=losers_list)
            _set_cached(f'gainers_losers_{limit}', dashboard_data)
            return dashboard_data

        return None

    except ImportError as e:
        logger.error(f"nsetools not available: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching gainers/losers: {e}")
        return None


def get_stock_name_from_yfinance(symbol: str) -> Optional[str]:
    """Get company name for a symbol from Yahoo Finance."""
    cached = _get_cached(f'name_{symbol}')
    if cached is not None:
        return cached
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info
        name = info.get('longName') or info.get('shortName')
        if name:
            _set_cached(f'name_{symbol}', name)
            return name
    except Exception as e:
        logger.debug(f"yfinance name lookup failed for {symbol}: {e}")
    return None


def enrich_stock_names(gainers: List[GainerLoserStock], losers: List[GainerLoserStock]) -> None:
    """Enrich gainers and losers with company names from Yahoo Finance."""
    stocks_needing_names = [s for s in gainers + losers if s.name == s.symbol or not s.name]
    for stock in stocks_needing_names:
        name = get_stock_name_from_yfinance(f"{stock.symbol}.NS")
        if not name:
            name = get_stock_name_from_yfinance(stock.symbol)
        if name:
            stock.name = name
        time.sleep(0.1)


def get_real_dashboard_data(limit: int = 10) -> Optional[Dict[str, List[Dict[str, Any]]]]:
    """Fetch real dashboard data, enriching with company names."""
    dashboard_data = get_top_gainers_losers(limit=limit)
    if dashboard_data is None:
        return None
    enrich_stock_names(dashboard_data.gainers, dashboard_data.losers)
    return dashboard_data.to_dict()


DEMO_DATA_FALLBACK = {
    "gainers": [
        {"symbol": "BAJFINANCE", "name": "Bajaj Finance", "price": 7248.15, "change": 156.80, "changePct": 2.21},
        {"symbol": "BHARTIARTL", "name": "Bharti Airtel", "price": 1623.45, "change": 32.15, "changePct": 2.02},
        {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical", "price": 1682.45, "change": 29.15, "changePct": 1.75}
    ],
    "losers": [
        {"symbol": "WIPRO", "name": "Wipro", "price": 547.80, "change": -8.20, "changePct": -1.47},
        {"symbol": "TATAMOTORS", "name": "Tata Motors", "price": 985.40, "change": -15.20, "changePct": -1.52},
        {"symbol": "BPCL", "name": "Bharat Petroleum", "price": 628.70, "change": -8.40, "changePct": -1.32}
    ]
}


def get_dashboard_data_with_fallback(limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch dashboard data with fallback to demo data if real data is unavailable."""
    real_data = get_real_dashboard_data(limit=limit)
    if real_data is not None:
        logger.info(f"Using real data: {len(real_data.get('gainers', []))} gainers, {len(real_data.get('losers', []))} losers")
        return real_data
    logger.warning("Real data unavailable, falling back to demo data")
    return DEMO_DATA_FALLBACK