import flask_app
import time
app = flask_app.app
app.config['TESTING'] = True
c = app.test_client()

print('Testing main route 3 times...')
for i in range(3):
    start = time.time()
    r = c.get('/')
    elapsed = time.time() - start
    print(f'  Request {i+1}: {r.status_code} in {elapsed:.3f}s')