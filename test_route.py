#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from flask_app import app

# Test the route directly
with app.test_client() as client:
    # Test the /stock/RELIANCE.NS route
    response = client.get('/stock/RELIANCE.NS')
    print('Status code:', response.status_code)
    print('Response data:')
    print(response.get_data(as_text=True)[:1000])

    # Test with another symbol
    response2 = client.get('/stock/ADANIENT.NS')
    print('\nStatus code for ADANIENT.NS:', response2.status_code)
    print('Response data:')
    print(response2.get_data(as_text=True)[:1000])
