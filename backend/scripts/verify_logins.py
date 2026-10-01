import urllib.request
import json

base_url = 'http://127.0.0.1:8000/api/v1/auth/login/email/'

accounts = [
    ('Admin Account', 'admin@gqt.edu', 'AdminPassword@123'),
    ('Student Account', 'student@gqt.edu', 'StudentPassword@123'),
]

for name, email, pw in accounts:
    print(f"Testing {name} ({email})...", flush=True)
    payload = json.dumps({'email': email, 'password': pw}).encode('utf-8')
    req = urllib.request.Request(base_url, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            user = res_data['data']['user']
            tokens = res_data['data']['access']
            print(f"[{name}] Login: SUCCESS (HTTP {response.status})", flush=True)
            print(f"   Email:  {user.get('email')}", flush=True)
            print(f"   Role:   {user.get('role')}", flush=True)
            print(f"   Tokens: JWT Access Token Generated ({tokens[:30]}...)\n", flush=True)
    except Exception as e:
        print(f"[{name}] Login: FAILED - {e}\n", flush=True)
