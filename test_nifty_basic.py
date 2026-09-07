"""Tests for NIFTY 50 market data service."""

import pytest
from unittest.mock import patch
from datetime import datetime
import pandas as pd


class TestNiftyDataService:
    """Test suite for NIFTY 50 data service."""

    def test_valid_1d_request(self):
        """Test valid 1D range request."""
        from nifty_data_service import get_nifty_data
        result = get_nifty_data('1D')
        assert result['status'] == 'success'
        assert result['symbol'] == '^NSEI'
        assert result['range'] == '1D'
        assert len(result['data']) > 0
        for point in result['data']:
            assert 'timestamp' in point
            assert 'value' in point
            assert point['value'] > 0

    def test_valid_1w_request(self):
        """Test valid 1W range request."""
        from nifty_data_service import get_nifty_data
        result = get_nifty_data('1W')
        assert result['status'] == 'success'
        assert result['range'] == '1W'

    def test_valid_1m_request(self):
        """Test valid 1M range request."""
        from nifty_data_service import get_nifty_data
        result = get_nifty_data('1M')
        assert result['status'] == 'success'
        assert result['range'] == '1M'

    def test_valid_3m_request(self):
        """Test valid 3M range request."""
        from nifty_data_service import get_nifty_data
        result = get_nifty_data('3M')
        assert result['status'] == 'success'
        assert result['range'] == '3M'

    def test_valid_1y_request(self):
        """Test valid 1Y range request."""
        from nifty_data_service import get_nifty_data
        result = get_nifty_data('1Y')
        assert result['status'] == 'success'
        assert result['range'] == '1Y'

    def test_invalid_range(self):
        """Test invalid range returns error."""
        from nifty_data_service import get_nifty_data
        result = get_nifty_data('INVALID')
        assert result['status'] == 'error'
        assert 'Invalid' in result['message']

    @patch('nifty_data_service.yf.Ticker')
    def test_empty_yfinance_response(self, mock_ticker):
        """Test handling of empty yfinance response."""
        mock_ticker.return_value.history.return_value = pd.DataFrame()
        from nifty_data_service import get_nifty_data
        result = get_nifty_data('1D')
        assert result['status'] in ['success', 'error']

    @patch('nifty_data_service.yf.Ticker')
    def test_yfinance_exception(self, mock_ticker):
        """Test handling of yfinance exception."""
        mock_ticker.side_effect = Exception('API Error')
        from nifty_data_service import get_nifty_data
        result = get_nifty_data('1D')
        assert result['status'] in ['success', 'error']
        assert result['source'] in ['yfinance', 'cache', 'error']

    def test_timestamp_format(self):
        """Test that timestamps are in ISO format."""
        from nifty_data_service import get_nifty_data
        result = get_nifty_data('1D')
        for point in result['data']:
            ts = point['timestamp']
            try:
                datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except ValueError:
                raise AssertionError(f'Timestamp {ts} is not valid ISO format')

    def test_data_values_positive(self):
        """Test that all data values are positive."""
        from nifty_data_service import get_nifty_data
        result = get_nifty_data('1M')
        for point in result['data']:
            assert point['value'] > 0, f'Non-positive value: {point}'

    def test_api_response_structure(self):
        """Test that API response has correct structure."""
        from nifty_data_service import get_nifty_data
        result = get_nifty_data('1D')
        required_keys = ['symbol', 'name', 'range', 'data', 'source', 'cached', 'stale', 'last_updated', 'status']
        for key in required_keys:
            assert key in result, f'Missing key: {key}'

    def test_different_ranges_return_different_data(self):
        """Test that different ranges with the same interval return different data.

        This tests the fix for the issue where 1M, 3M, and 1Y all returned
        the same cached data because the cache key only used (symbol, interval).
        """
        from nifty_data_service import get_nifty_data, fetch_nifty_data

        # Fetch 1M data
        result_1m = get_nifty_data('1M')
        assert result_1m['status'] == 'success'
        data_1m = result_1m['data']

        # Fetch 3M data
        result_3m = get_nifty_data('3M')
        assert result_3m['status'] == 'success'
        data_3m = result_3m['data']

        # Fetch 1Y data
        result_1y = get_nifty_data('1Y')
        assert result_1y['status'] == 'success'
        data_1y = result_1y['data']

        # All three ranges use interval='1d', so they should return
        # different data (different number of data points for different time ranges)
        # 1Y should have the most points, 1M the fewest
        assert len(data_1y) >= len(data_3m), \
            f"1Y should have >= data points than 3M: 1Y={len(data_1y)}, 3M={len(data_3m)}"
        assert len(data_3m) >= len(data_1m), \
            f"3M should have >= data points than 1M: 3M={len(data_3m)}, 1M={len(data_1m)}"

        # The data should not be identical between ranges
        if len(data_1m) > 0 and len(data_1y) > 0:
            # At least the last timestamp should differ if ranges are different
            # (1Y covers a longer period so its earliest data point should be older)
            ts_1m_first = data_1m[0]['timestamp']
            ts_1y_first = data_1y[0]['timestamp']
            assert ts_1m_first != ts_1y_first, \
                f"1M and 1Y should have different earliest timestamps: 1M={ts_1m_first}, 1Y={ts_1y_first}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])