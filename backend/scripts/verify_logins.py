import urllib.request
import json

base_url = 'http://127.0.0.1:8000/api/v1/auth/login/email/'

import os

admin_email = os.environ.get('TEST_ADMIN_EMAIL', 'admin@gqt.edu')
admin_pw = os.environ.get('TEST_ADMIN_PASSWORD', '')
student_email = os.environ.get('TEST_STUDENT_EMAIL', 'student@gqt.edu')
student_pw = os.environ.get('TEST_STUDENT_PASSWORD', '')

accounts = []
if admin_pw:
    accounts.append(('Admin Account', admin_email, admin_pw))
if student_pw:
    accounts.append(('Student Account', student_email, student_pw))

if not accounts:
    print("Please provide TEST_ADMIN_PASSWORD or TEST_STUDENT_PASSWORD in environment to run login verification.")

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
