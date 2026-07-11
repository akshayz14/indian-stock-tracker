"""
Data source abstraction for the Indian Stock Tracker.

This module defines a common interface for fetching daily OHLCV (open, high,
low, close, volume) data from multiple providers. The application currently
supports:

  * NSE India (``nsepy``)        — primary source (official exchange feed)
  * Yahoo Finance (``yfinance``) — secondary / fallback source

Relying on a single provider is fragile: rate limits, outages, or changes to a
provider's API can silently drop stocks from the database. By abstracting each
provider behind a common interface and falling back from one to the next, the
fetcher becomes far more resilient — if NSE is unavailable we can still
pull the same data from Yahoo Finance.
"""

from __future__ import annotations

import abc
import datetime
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class OHLCV:
    """Normalized daily price record returned by every data source."""
    date: datetime.date
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: float


def _strip_exchange_suffix(symbol: str) -> str:
    """
    Convert a Yahoo-style symbol (``RELIANCE.NS``) to a bare NSE/BSE ticker.

    NSE's official APIs expect bare tickers, so any ``.NS`` / ``.BO`` suffix
    is removed before the request is made.
    """
    return symbol.upper().replace('.NS', '').replace('.BO', '')


class DataSource(abc.ABC):
    """Abstract base class for all price data providers."""

    #: Human-readable name used for logging.
    name: str = "base"

    @abc.abstractmethod
    def fetch_latest(self, symbol: str) -> Optional[OHLCV]:
        """
        Fetch the most recent available trading day's OHLCV for ``symbol``.

        Returns ``None`` if no data could be retrieved (so the caller can fall
        back to the next source).
        """
        raise NotImplementedError

    def fetch_name(self, symbol: str) -> Optional[str]:
        """
        Best-effort lookup of a human-readable company name for ``symbol``.

        Returns ``None`` if the source cannot provide one; the caller will then
        try the next source or fall back to the raw symbol.
        """
        return None


class YFinanceSource(DataSource):
    """Yahoo Finance provider (wraps the ``yfinance`` library)."""

    name = "yfinance"

    def fetch_latest(self, symbol: str) -> Optional[OHLCV]:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        # Pull the last few sessions to guarantee we have a complete row even
        # if the very latest session is still being finalized.
        hist = ticker.history(period="5d")
        if hist is None or hist.empty:
            return None

        latest = hist.iloc[-1]
        row_date = latest.name.date() if isinstance(latest.name, datetime.datetime) else latest.name
        return OHLCV(
            date=row_date,
            open=float(latest["Open"]),
            high=float(latest["High"]),
            low=float(latest["Low"]),
            close=float(latest["Close"]),
            adj_close=float(latest.get("Adj Close", latest["Close"])),
            volume=float(latest["Volume"]),
        )

    def fetch_name(self, symbol: str) -> Optional[str]:
        try:
            import yfinance as yf

            return yf.Ticker(symbol).info.get("shortName")
        except Exception:
            return None


class NSESource(DataSource):
    """
    NSE India official data via ``nsepy``.

    NSE symbols are bare tickers (``RELIANCE``), so Yahoo-style suffixes such
    as ``.NS`` are stripped before the request. This is the primary source;
    Yahoo Finance is used as a fallback when NSE is unavailable.
    """

    name = "nse"

    def fetch_latest(self, symbol: str) -> Optional[OHLCV]:
        try:
            from nsepy import get_history
        except ImportError:
            return None

        nse_symbol = _strip_exchange_suffix(symbol)
        end = datetime.date.today()
        start = end - datetime.timedelta(days=7)
        try:
            hist = get_history(symbol=nse_symbol, start=start, end=end)
        except Exception:
            return None

        if hist is None or len(hist) == 0:
            return None

        latest = hist.iloc[-1]
        row_date = latest.name.date() if isinstance(latest.name, datetime.datetime) else latest.name
        # nsepy columns: Open, High, Low, Close, Volume (plus Last, VWAP, etc.)
        return OHLCV(
            date=row_date,
            open=float(latest["Open"]),
            high=float(latest["High"]),
            low=float(latest["Low"]),
            close=float(latest["Close"]),
            adj_close=float(latest["Close"]),
            volume=float(latest["Volume"]),
        )

    def fetch_name(self, symbol: str) -> Optional[str]:
        try:
            from nsepy import get_quote

            nse_symbol = _strip_exchange_suffix(symbol)
            quote = get_quote(nse_symbol)
            if isinstance(quote, dict):
                return quote.get("companyName") or quote.get("symbol")
        except Exception:
            return None
        return None


# Ordered list of sources tried by the fetcher. NSE is first (official
# exchange feed); yfinance is the fallback for resilience.
DEFAULT_SOURCES: List[DataSource] = [NSESource(), YFinanceSource()]


def fetch_with_fallback(symbol: str, sources: Optional[List[DataSource]] = None) -> Optional[OHLCV]:
    """
    Try each data source in order and return the first successful result.

    Returns ``None`` only if *every* source failed for ``symbol``.
    """
    sources = sources or DEFAULT_SOURCES
    last_error: Optional[Exception] = None
    for source in sources:
        try:
            result = source.fetch_latest(symbol)
            if result is not None:
                return result
        except Exception as exc:  # keep trying the next source
            last_error = exc
            continue
    if last_error:
        print(f"All data sources failed for {symbol}: {last_error}")
    return None


def resolve_name(symbol: str, sources: Optional[List[DataSource]] = None) -> Optional[str]:
    """
    Resolve a company name for ``symbol`` using the first source that can
    provide one. Returns ``None`` if no source succeeds.
    """
    sources = sources or DEFAULT_SOURCES
    for source in sources:
        try:
            name = source.fetch_name(symbol)
            if name:
                return name
        except Exception:
            continue
    return None