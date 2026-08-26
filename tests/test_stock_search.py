"""Tests for stock search service integration."""
import sys
import os

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stock_search_service import StockSearchService


def test_search_stocks_reliance():
    """Test searching for Reliance stocks."""
    service = StockSearchService()
    results = service.search_stocks("reliance")
    assert len(results) > 0, "Should find at least one Reliance stock"
    # Check that results contain expected fields
    for result in results:
        assert "symbol" in result, "Result should have symbol"
        assert "name" in result, "Result should have name"
        assert "exchange" in result, "Result should have exchange"


def test_search_stocks_returns_indian_equities():
    """Test that search only returns Indian NSE/BSE equities."""
    service = StockSearchService()
    results = service.search_stocks("tata")
    for result in results:
        symbol = result["symbol"]
        # Should end with .NS or .BO
        assert symbol.endswith(".NS") or symbol.endswith(".BO"), \
            f"Symbol {symbol} should be NSE or BSE"


def test_search_stocks_empty_query():
    """Test search with empty query returns no results."""
    service = StockSearchService()
    results = service.search_stocks("")
    assert len(results) == 0, "Empty query should return no results"


def test_search_stocks_known_symbol():
    """Test searching for a known stock symbol."""
    service = StockSearchService()
    results = service.search_stocks("RELIANCE.NS")
    # Should find at least Reliance Industries
    assert len(results) > 0, "Should find Reliance Industries"
    # Check symbol matches
    symbols = [r["symbol"] for r in results]
    assert "RELIANCE.NS" in symbols or any("RELIANCE" in s["symbol"] for s in results)


if __name__ == "__main__":
    # Run tests manually since pytest not installed
    test_search_stocks_reliance()
    print("✓ test_search_stocks_reliance passed")
    
    test_search_stocks_returns_indian_equities()
    print("✓ test_search_stocks_returns_indian_equities passed")
    
    test_search_stocks_empty_query()
    print("✓ test_search_stocks_empty_query passed")
    
    test_search_stocks_known_symbol()
    print("✓ test_search_stocks_known_symbol passed")
    
    print("\nAll tests passed!")
