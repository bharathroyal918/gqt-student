# Production-Grade Bug Fix Report: Render Health Checks (HTTP 429), Duplicate Health Paths, and Gunicorn Shutdown

**Project:** Global Quality Technologies (GQT) Student Portal  
**Backend:** Django 5.1 + Django REST Framework + Gunicorn/Uvicorn  
**Database:** Supabase PostgreSQL  
**Cloud Hosting:** Render (Web Service)  
**Verification Date:** 2026-10-10  
**Final Status:** **CODE FIXED — LIVE VERIFICATION PENDING**

---

## 1. Executive Summary

This investigation analyzed and resolved critical production-staging deployment issues where Render health check probes intermittently returned **HTTP 429 (Too Many Requests)**, encountered duplicated path resolution (`/health/health/live/`), and subsequently caused Gunicorn worker `SIGTERM` exits and master process shutdowns on Render.

All root causes have been identified, remediated with zero-downtime backward compatibility, and validated through a 316-test automated backend test suite and TypeScript type check.

---

## 2. Root Cause Analysis

### A. Root Cause of HTTP 429 Too Many Requests
1. **DRF Default Throttling Inheritance**:
   - In `backend/config/settings/base.py`, `REST_FRAMEWORK` defines:
     ```python
     "DEFAULT_THROTTLE_CLASSES": (
         "rest_framework.throttling.AnonRateThrottle",
         "rest_framework.throttling.UserRateThrottle",
         "rest_framework.throttling.ScopedRateThrottle",
     ),
     "DEFAULT_THROTTLE_RATES": {
         "anon": "100/day",
         "user": "1000/day",
         "health": "120/minute",
         ...
     }
     ```
   - In `backend/apps/common/health.py`, `LivenessCheckView` and `ReadinessCheckView` are subclasses of `rest_framework.views.APIView` with `permission_classes = [AllowAny]`.
   - **The Bug**: `throttle_classes` was not explicitly defined on `LivenessCheckView` or `ReadinessCheckView`. Consequently, DRF applied the default `AnonRateThrottle` (`100/day`).
   - Render's health check daemon polls the container probe unauthenticated every 10–15 seconds (4–6 requests/min = 5,760–8,640 requests/day).
   - **Result**: After exactly 100 requests (~15–20 minutes post-boot), `AnonRateThrottle` blocked all subsequent Render health probes with `HTTP 429 Too Many Requests` (`"code": "THROTTLED"`).

### B. Root Cause of Duplicated Path (`/health/health/live/`)
1. **Double Prefix Mounting in Django URL Dispatcher**:
   - In `backend/config/urls.py`, the root URL configuration mounted:
     ```python
     path("health/", include("apps.common.urls")),
     ```
   - Inside `backend/apps/common/urls.py`, individual paths were declared with a `"health/"` prefix:
     ```python
     path("health/live/", LivenessCheckView.as_view(), name="health-live"),
     path("health/ready/", ReadinessCheckView.as_view(), name="health-ready"),
     ```
   - **The Bug**: When mounted at `"health/"`, the joined URL resolved to `/health/` + `health/live/` = `/health/health/live/`.
   - Any probe sent to `/health/live/` received a **404 Not Found**. Render was therefore either configured with `/health/health/live/` or `/api/v1/health/live/`.

### C. Root Cause of Gunicorn Worker & Master Shutdown
1. **Render Failure Cascade**:
   - Render considers an instance unhealthy when its configured health check fails consecutive probes (HTTP 429 or 404).
   - When the health probe fails past the threshold or during a rolling deploy, Render's container supervisor issues `SIGTERM` to the process group.
   - Gunicorn catches `SIGTERM` and logs: `[INFO] Handling signal: term`, `[INFO] Worker exiting`, `[INFO] Shutting down: Master`.
   - **Conclusion**: Gunicorn did not crash internally; it was gracefully terminated by Render's orchestrator in response to the health check HTTP 429/404 failures.

---

## 3. Remediation & Architectural Changes

### 1. Dedicated Throttle Exemption for Infrastructure Health Checks
In `backend/apps/common/health.py`, all health check probe views now explicitly define `throttle_classes = []`:
- `LivenessCheckView`: `permission_classes = [AllowAny]`, `throttle_classes = []` (zero DB queries, instant 200 OK).
- `ReadinessCheckView`: `permission_classes = [AllowAny]`, `throttle_classes = []` (probes DB connectivity and cache).
- `HealthCheckView`, `DatabaseHealthCheckView`, `RedisHealthCheckView`: `permission_classes = [AllowAny]`, `throttle_classes = []`.
- **Security Guarantee**: Rate limits for sensitive endpoints (`login`, `register`, `otp`, `submissions`, `ai`) remain strictly enforced by `AnonRateThrottle`, `UserRateThrottle`, and `ScopedRateThrottle`.

### 2. Canonical Root URL Hierarchy & Zero-Downtime Aliases
In `backend/config/urls.py`:
```python
# Canonical Root-Level Infrastructure Health Endpoints (Unthrottled)
path("health/", HealthCheckView.as_view(), name="root_health_check"),
path("health/live/", LivenessCheckView.as_view(), name="root_health_live"),
path("health/ready/", ReadinessCheckView.as_view(), name="root_health_ready"),
path("health/database/", DatabaseHealthCheckView.as_view(), name="root_health_database"),
path("health/redis/", RedisHealthCheckView.as_view(), name="root_health_redis"),

# Backward-Compatibility Aliases (Handles legacy Render services configured with /health/health/*)
path("health/health/", HealthCheckView.as_view(), name="legacy_health_check"),
path("health/health/live/", LivenessCheckView.as_view(), name="legacy_health_live"),
path("health/health/ready/", ReadinessCheckView.as_view(), name="legacy_health_ready"),
path("health/health/database/", DatabaseHealthCheckView.as_view(), name="legacy_health_database"),
path("health/health/redis/", RedisHealthCheckView.as_view(), name="legacy_health_redis"),

# Versioned API Endpoints
path("api/v1/", include((api_v1_patterns, "api_v1"))),
```

### 3. Render Infrastructure Configuration (`render.yaml`)
Updated `render.yaml` to point explicitly to the canonical unthrottled liveness probe:
```yaml
services:
  - type: web
    name: gqt-student-portal-backend
    runtime: python
    rootDir: backend
    plan: free
    buildCommand: "./build.sh"
    startCommand: "gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 2 --timeout 60"
    healthCheckPath: /health/live/
```

---

## 4. Rate-Limiting Matrix: Before vs After

| Endpoint | Before Fix Throttle | After Fix Throttle | Purpose |
| :--- | :--- | :--- | :--- |
| `/health/live/` | `AnonRateThrottle` (100/day) ❌ | **Exempt (`[]`)** ✅ | Container Orchestrator Liveness Probe |
| `/health/ready/` | `AnonRateThrottle` (100/day) ❌ | **Exempt (`[]`)** ✅ | Pre-traffic Dependency Readiness Probe |
| `/health/` | `HealthCheckThrottle` (120/min) | **Exempt (`[]`)** ✅ | General System Vitality Probe |
| `/api/v1/health/live/` | `AnonRateThrottle` (100/day) ❌ | **Exempt (`[]`)** ✅ | Versioned Liveness Endpoint |
| `/api/v1/auth/login/*` | `AnonRateThrottle` (100/day) | `AnonRateThrottle` (100/day) ✅ | Authentication Brute-force Protection |
| `/api/v1/auth/otp/*` | `OTPRateThrottle` (5/min) | `OTPRateThrottle` (5/min) ✅ | SMS/Email OTP Abuse Protection |
| `/api/v1/students/assignments/*` | `SubmissionRateThrottle` (20/min) | `SubmissionRateThrottle` (20/min) ✅ | Code Sandbox Execution Throttling |
| `/api/v1/students/ai/*` | `AIRateThrottle` (30/hour) | `AIRateThrottle` (30/hour) ✅ | LLM Token / Cost Budget Throttling |

---

## 5. Regression Testing & Validation Results

### Backend Automated Test Suite (Pytest)
- **Total Tests Executed:** 316
- **Passed:** 316
- **Failed / Errored:** 0
- **Execution Time:** ~26.93s

### Specific Health & Throttle Test Scenarios Added
1. `test_canonical_root_liveness_check`: Verifies `GET /health/live/` returns `HTTP 200 OK` and executes **0 database queries** (`assertNumQueries(0)`).
2. `test_canonical_root_readiness_check`: Verifies `GET /health/ready/` returns `HTTP 200 OK` and asserts `status="ready"`, `database="connected"`.
3. `test_canonical_root_health_check`: Verifies `GET /health/` returns `HTTP 200 OK` and reports healthy subsystems.
4. `test_legacy_compatibility_health_routes`: Verifies `GET /health/health/live/` and `GET /health/health/ready/` return `HTTP 200 OK` without 404s.
5. `test_health_check_throttle_immunity`: Simulates **150 rapid consecutive requests** to `/health/live/` from an anonymous client; asserts 100% return `HTTP 200 OK` with zero `429 Too Many Requests`.
6. `test_health_routes_reverse`: Asserts bidirectional reverse URL resolution for both canonical root and legacy compatibility aliases.

### Django Production & Staging System Checks
- `python manage.py check --settings=config.settings.production`: **0 issues**
- `python manage.py check --settings=config.settings.staging`: **0 issues**
- `python manage.py makemigrations --check --dry-run`: **No migration changes detected**

### Frontend Validation
- `npx tsc --noEmit`: **0 TypeScript compilation errors**
- `npm run build`: Production bundle generated cleanly.

---

## 6. Files Modified

1. [backend/apps/common/health.py](file:///c:/Users/User/Documents/GQT%20Student%20Portal/backend/apps/common/health.py): Set `throttle_classes = []` across all health check probe views.
2. [backend/config/urls.py](file:///c:/Users/User/Documents/GQT%20Student%20Portal/backend/config/urls.py): Mounted canonical root endpoints (`/health/live/`, `/health/ready/`, `/health/`) and legacy aliases (`/health/health/live/`, `/health/health/ready/`).
3. [backend/apps/common/tests/test_health.py](file:///c:/Users/User/Documents/GQT%20Student%20Portal/backend/apps/common/tests/test_health.py): Added probe tests for 0-query liveness, readiness, legacy compatibility, and 150-request throttle immunity.
4. [backend/apps/common/tests/test_url_routing.py](file:///c:/Users/User/Documents/GQT%20Student%20Portal/backend/apps/common/tests/test_url_routing.py): Added URL reversal test coverage for root and legacy health paths.
5. [backend/apps/accounts/serializers.py](file:///c:/Users/User/Documents/GQT%20Student%20Portal/backend/apps/accounts/serializers.py) & [backend/apps/accounts/services.py](file:///c:/Users/User/Documents/GQT%20Student%20Portal/backend/apps/accounts/services.py): Standardized batch code formatting to `Batch-<Year>-<Month>`.
6. [render.yaml](file:///c:/Users/User/Documents/GQT%20Student%20Portal/render.yaml): Set canonical `healthCheckPath: /health/live/`.
