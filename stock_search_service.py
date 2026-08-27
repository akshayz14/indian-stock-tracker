"""Service layer for stock search functionality."""
import requests
import json
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockSearchService:
    """Service for searching stocks via Yahoo Finance API."""
    
    YAHOO_SEARCH_URL = "https://query1.finance.yahoo.com/v1/finance/search"
    DEFAULT_SEARCH_LIMIT = 10
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def search_stocks(self, query: str, limit: int = DEFAULT_SEARCH_LIMIT) -> List[Dict[str, Any]]:
        """Search for stocks by query string."""
        if not query:
            return []
            
        params = {
            "q": query,
            "quotesCount": limit,
            "newsCount": 0
        }
        
        try:
            response = self.session.get(
                self.YAHOO_SEARCH_URL,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for quote in data.get("quotes", []):
                # Only equities
                if quote.get("quoteType") != "EQUITY":
                    continue
                
                symbol = quote.get("symbol", "")
                
                # Only Indian NSE/BSE stocks
                if not (symbol.endswith(".NS") or symbol.endswith(".BO")):
                    continue
                
                results.append({
                    "symbol": symbol,
                    "name": quote.get("longname") or quote.get("shortname") or "",
                    "exchange": quote.get("exchange"),
                    "type": quote.get("quoteType")
                })
            
            return results
            
        except requests.RequestException as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_stock_details(self, symbol: str) -> Dict[str, Any]:
        """Get detailed stock information for a symbol."""
        # This would be implemented with yfinance in the real implementation
        # For now, we'll return mock data based on the symbol
        ticker = f"{symbol.replace('.NS', '.NSE') if symbol.endswith('.NS') else symbol.replace('.BO', '.BSE')}"
        
        # Mock data based on symbol
        mock_data = {
            "symbol": symbol,
            "company_name": f"Mock {symbol}",
            "short_name": f"Mock {symbol.split('.')[0]}",
            "sector": "Energy" if "RELIANCE" in symbol else "Technology" if "TECH" in symbol else "Finance",
            "industry": "Conglomerate" if "RELIANCE" in symbol else "Banking" if "BANK" in symbol else "IT",
            "price": 1200.0 if "RELIANCE" in symbol else 800.0,
            "pe_ratio": 25.0 if "RELIANCE" in symbol else 30.0,
            "market_cap": 17565149560832 if "RELIANCE" in symbol else 50000000000,
            "beta": 1.2 if "RELIANCE" in symbol else 1.0,
            "dividend_yield": 1.5 if "RELIANCE" in symbol else 0.0,
            "book_value": 800.0 if "RELIANCE" in symbol else 400.0,
            "website": "https://www.reliance.com" if "RELIANCE" in symbol else "https://www.tcs.com",
            "country": "India",
            "currency": "INR"
        }
        
        return mock_data
    
    def get_stock_history(self, symbol: str, period: str = "3mo", days: int = 60) -> List[Dict[str, Any]]:
        """Get historical stock data from Yahoo Finance."""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            if hist is None or hist.empty:
                return []
            
            # Convert to list of dicts, take last 'days' records
            records = []
            for date, row in hist.iterrows():
                records.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "adjusted_close": float(row.get("Adj Close", row["Close"])),
                    "volume": float(row["Volume"])
                })
            return records[-days:]
        except Exception as e:
            logger.error(f"Error fetching history for {symbol}: {e}")
            return []