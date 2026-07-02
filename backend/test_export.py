import urllib.request
import urllib.parse
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

data = json.dumps({'username': 'admin', 'password': 'admin1234'}).encode('utf-8')
req = urllib.request.Request('http://localhost:8000/api/auth/login/', data=data, headers={'Content-Type': 'application/json'})
try:
    resp = urllib.request.urlopen(req, context=ctx)
    token = json.loads(resp.read())['access']
    print("Token obtained")
    
    url = 'http://localhost:8000/api/reports/export/?type=portfolio&export_format=csv'
    req2 = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + token})
    print(f"Requesting {url}")
    resp2 = urllib.request.urlopen(req2, context=ctx)
    print("Success")
    print(resp2.read().decode('utf-8')[:500])
except urllib.error.HTTPError as e:
    print(f'HTTP Error {e.code}: {e.read().decode("utf-8")}')
except Exception as e:
    print(f'Error: {e}')
