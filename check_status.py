import flask_app
import time
app = flask_app.app
app.config['TESTING'] = True
c = app.test_client()

# Test main route
start = time.time()
r = c.get('/')
elapsed = time.time() - start
html = r.data.decode()
print('Main route:', r.status_code, 'in', f'{elapsed:.3f}s')

# Test all API endpoints
endpoints = ['/api/dashboard/gainers', '/api/dashboard/losers', '/api/dashboard/chart-data', '/api/dashboard/sector-performance', '/api/dashboard/watchlist']
for ep in endpoints:
    r = c.get(ep)
    print(ep, '->', r.status_code)