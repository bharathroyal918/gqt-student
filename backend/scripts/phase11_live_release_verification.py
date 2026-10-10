"""
Phase 11: Live Staging Release & Security Verification Script
Target: Live Render Backend (https://gqt-student.onrender.com) & Vercel Frontend (https://gqt-student.vercel.app)
"""

import sys
import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error

BACKEND_URL = os.getenv("STAGING_BACKEND_URL", "https://gqt-student.onrender.com")
FRONTEND_URL = os.getenv("STAGING_FRONTEND_URL", "https://gqt-student.vercel.app")

results = []

def record(category, test_name, status, details, elapsed_ms=None):
    results.append({
        "category": category,
        "test": test_name,
        "status": status,
        "details": details,
        "elapsed_ms": elapsed_ms
    })
    badge = "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[WARN]" if status == "WARN" else "[INFO]"
    elapsed_str = f" ({elapsed_ms:.1f}ms)" if elapsed_ms is not None else ""
    print(f"{badge} {category} > {test_name}{elapsed_str}: {details}")

def http_req(path, method="GET", data=None, headers=None, base_url=BACKEND_URL, timeout=30):
    url = f"{base_url}{path}" if path.startswith("/") else f"{base_url}/{path}"
    req_headers = {"User-Agent": "Phase11LiveVerifier/1.0"}
    if headers:
        req_headers.update(headers)
    
    encoded_data = None
    if data is not None:
        if isinstance(data, dict):
            encoded_data = json.dumps(data).encode("utf-8")
            if "Content-Type" not in req_headers:
                req_headers["Content-Type"] = "application/json"
        elif isinstance(data, (bytes, str)):
            encoded_data = data if isinstance(data, bytes) else data.encode("utf-8")
            
    req = urllib.request.Request(url, data=encoded_data, headers=req_headers, method=method)
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = (time.time() - start) * 1000
            resp_body = resp.read()
            return resp.status, resp.headers, resp_body, elapsed
    except urllib.error.HTTPError as e:
        elapsed = (time.time() - start) * 1000
        resp_body = e.read()
        return e.code, e.headers, resp_body, elapsed
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return None, {}, str(e).encode("utf-8"), elapsed

def verify_live_endpoints():
    print("=" * 70)
    print("PHASE 11: LIVE RELEASE DEPLOYMENT & SECURITY VERIFICATION")
    print(f"Backend Target:  {BACKEND_URL}")
    print(f"Frontend Target: {FRONTEND_URL}")
    print("=" * 70)

    # 1. Live Backend Health
    status, hdrs, body, ms = http_req("/api/v1/health/live/")
    if status == 200:
        record("Backend Health", "Liveness Probe (/api/v1/health/live/)", "PASS", f"HTTP 200 OK: {body.decode('utf-8', 'ignore')[:100]}", ms)
    else:
        record("Backend Health", "Liveness Probe (/api/v1/health/live/)", "FAIL", f"HTTP {status}: {body.decode('utf-8', 'ignore')[:100]}", ms)

    # 2. Readiness Probe
    status, hdrs, body, ms = http_req("/api/v1/health/ready/")
    if status == 200:
        record("Backend Health", "Readiness Probe (/api/v1/health/ready/)", "PASS", f"HTTP 200 OK (DB connected): {body.decode('utf-8', 'ignore')[:100]}", ms)
    else:
        record("Backend Health", "Readiness Probe (/api/v1/health/ready/)", "WARN", f"HTTP {status}: {body.decode('utf-8', 'ignore')[:100]}", ms)

    # 3. TPO Report Types endpoint (Verifies commit 71b411a presence)
    status, hdrs, body, ms = http_req("/api/v1/tpo/reports/types/")
    if status in (200, 401): # 401 means endpoint exists and requires auth; 404 means old commit
        record("Deployment Version", "TPO Report Types Endpoint Presence", "PASS", f"HTTP {status} (Endpoint active & routing verified)", ms)
    elif status == 404:
        record("Deployment Version", "TPO Report Types Endpoint Presence", "FAIL", f"HTTP 404 Not Found (Old baseline build 720b4fa still running on Render)", ms)
    else:
        record("Deployment Version", "TPO Report Types Endpoint Presence", "WARN", f"HTTP {status}: {body.decode('utf-8', 'ignore')[:100]}", ms)

    # 4. Frontend Probe
    status, hdrs, body, ms = http_req("", base_url=FRONTEND_URL)
    if status == 200:
        record("Frontend Deployment", "Vercel Frontend Availability", "PASS", f"HTTP 200 OK ({len(body)} bytes returned)", ms)
    elif status == 404:
        record("Frontend Deployment", "Vercel Frontend Availability", "WARN", f"HTTP 404 DEPLOYMENT_NOT_FOUND (Vercel project unlinked or repository webhook pending)", ms)
    else:
        record("Frontend Deployment", "Vercel Frontend Availability", "FAIL", f"HTTP {status}: {body.decode('utf-8', 'ignore')[:100]}", ms)

if __name__ == "__main__":
    verify_live_endpoints()
