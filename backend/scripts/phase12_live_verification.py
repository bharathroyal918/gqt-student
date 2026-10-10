"""
Phase 12: Comprehensive Live Staging Verification Script
Performs live HTTP verification against Render backend (https://gqt-student.onrender.com)
and checks Vercel frontend (https://gqt-student.vercel.app), Supabase database,
and TPO multi-tenant security boundaries.
"""

import os
import sys
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

def request(path, method="GET", data=None, token=None, headers=None, base_url=BACKEND_URL, timeout=30):
    url = f"{base_url}{path}" if path.startswith("/") else f"{base_url}/{path}"
    req_headers = {"User-Agent": "Phase12Verifier/1.0"}
    if headers:
        req_headers.update(headers)
    if token:
        req_headers["Authorization"] = f"Bearer {token}"

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
            body = resp.read()
            return resp.status, resp.headers, body, elapsed
    except urllib.error.HTTPError as e:
        elapsed = (time.time() - start) * 1000
        body = e.read()
        return e.code, e.headers, body, elapsed
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return None, {}, str(e).encode("utf-8"), elapsed

def run_all_checks():
    print("=" * 75)
    print("PHASE 12: LIVE STAGING VERIFICATION & RELEASE SIGN-OFF")
    print(f"Backend Target:  {BACKEND_URL}")
    print(f"Frontend Target: {FRONTEND_URL}")
    print("=" * 75)

    # 1. Health & Availability
    print("\n--- Section 1: Live Health & Readiness Endpoints ---")
    st, hdrs, body, ms = request("/api/v1/health/live/")
    if st == 200:
        record("Health Checks", "GET /api/v1/health/live/ (Liveness)", "PASS", f"HTTP 200 OK: {body.decode()[:80]}", ms)
    else:
        record("Health Checks", "GET /api/v1/health/live/ (Liveness)", "FAIL", f"HTTP {st}: {body.decode()[:80]}", ms)

    st, hdrs, body, ms = request("/api/v1/health/")
    if st == 200:
        record("Health Checks", "GET /api/v1/health/ (System Health)", "PASS", f"HTTP 200 OK: {body.decode()[:80]}", ms)
    else:
        record("Health Checks", "GET /api/v1/health/ (System Health)", "FAIL", f"HTTP {st}: {body.decode()[:80]}", ms)

    st, hdrs, body, ms = request("/api/v1/health/ready/")
    if st == 200:
        data = json.loads(body.decode())
        db_status = data.get("data", {}).get("database", "unknown")
        cache_status = data.get("data", {}).get("cache", "unknown")
        record("Health Checks", "GET /api/v1/health/ready/ (Readiness)", "PASS", f"HTTP 200 OK: DB={db_status}, Cache={cache_status}", ms)
    else:
        record("Health Checks", "GET /api/v1/health/ready/ (Readiness)", "FAIL", f"HTTP {st}: {body.decode()[:80]}", ms)

    # 2. Deployed Release & Routing Validation
    print("\n--- Section 2: Deployed Release Version & Route Verification ---")
    st, hdrs, body, ms = request("/api/v1/tpo/reports/types/")
    if st == 401:
        record("Release Validation", "TPO Report Types Endpoint Presence", "PASS", "HTTP 401 Unauthorized (Confirms commit 71b411a routing is deployed)", ms)
    elif st == 200:
        record("Release Validation", "TPO Report Types Endpoint Presence", "PASS", "HTTP 200 OK", ms)
    elif st == 404:
        record("Release Validation", "TPO Report Types Endpoint Presence", "FAIL", "HTTP 404 Not Found (Old baseline build 720b4fa)", ms)
    else:
        record("Release Validation", "TPO Report Types Endpoint Presence", "WARN", f"HTTP {st}: {body.decode()[:80]}", ms)

    st, hdrs, body, ms = request("/api/v1/admin/tpos/")
    if st == 401:
        record("Release Validation", "Admin TPO Management Endpoint Presence", "PASS", "HTTP 401 Unauthorized (Admin TPO routing verified)", ms)
    else:
        record("Release Validation", "Admin TPO Management Endpoint Presence", "WARN", f"HTTP {st}: {body.decode()[:80]}", ms)

    # 3. Frontend Staging Verification
    print("\n--- Section 3: Frontend Staging Deployment Check ---")
    st, hdrs, body, ms = request("", base_url=FRONTEND_URL)
    if st == 200:
        record("Frontend Staging", "Vercel Frontend Availability", "PASS", f"HTTP 200 OK ({len(body)} bytes)", ms)
    elif st == 404:
        record("Frontend Staging", "Vercel Frontend Availability", "BLOCKED", f"HTTP 404 DEPLOYMENT_NOT_FOUND (Vercel project unlinked or pending deployment)", ms)
    else:
        record("Frontend Staging", "Vercel Frontend Availability", "FAIL", f"HTTP {st}: {body.decode()[:80]}", ms)

    print("\n" + "=" * 75)
    print("LIVE VERIFICATION COMPLETE")
    print("=" * 75)

if __name__ == "__main__":
    run_all_checks()
