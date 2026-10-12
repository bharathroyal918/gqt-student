# GQT Student Portal — Phase 14: Concurrent Login Support, Session Isolation & Health-Check Rate-Limit Fix Report

## 1. Executive Summary

- **Project:** GQT Student Portal
- **Baseline Git Commit:** `dbed397` (derived from `71b411a`)
- **Backend Architecture:** Django 5.x + Django REST Framework + SimpleJWT + Supabase PostgreSQL
- **Frontend Architecture:** React 18 + TypeScript + Vite + Zustand + Axios
- **Hosting Targets:** Render (Backend Web Service) + Vercel (Frontend SPA)
- **Final Status:** **CODE FIXED — LIVE VERIFICATION PENDING**

This phase resolves critical multi-user session collisions, concurrent token-refresh race conditions, Render deployment health-check failures (HTTP 429), and route duplication while maintaining strict security boundaries (TPO college data isolation, IDOR protection, and rate-limiting on sensitive authentication endpoints).

---

## 2. Root Cause Analysis

### 2.1 Concurrent Login Race Condition & Forced Logout
- **Observed Behavior:** When multiple requests executed concurrently in the SPA frontend (e.g., student loading the dashboard which simultaneously fetches courses, assignments, attendance, and announcements), an expired access token triggered parallel 401 responses.
- **Root Cause:** In `frontend/src/api/client.ts`, each 401 response independently dispatched a `POST /api/v1/auth/token/refresh/` request using the stored refresh token. Because SimpleJWT rotates and blacklists refresh tokens upon use (`ROTATE_REFRESH_TOKENS = True`, `BLACKLIST_AFTER_ROTATION = True`), the first refresh request succeeded and blacklisted the token. The remaining parallel requests presented the newly blacklisted token, returned HTTP 401, wiped `localStorage`, and forced an unexpected user logout.
- **Secondary Session Isolation Check:** The backend architecture was audited for global mutable variables, shared session locks, or single-session-per-account database flags. Identity is derived strictly per-request from validated JWTs (`request.user`). No global session lock exists.

### 2.2 Health-Check HTTP 429 (Too Many Requests) on Render
- **Observed Behavior:** Render health checks to `/health/health/live/` or `/health/live/` returned HTTP 200 initially, followed by HTTP 429 Too Many Requests, causing Render to consider the service unhealthy and trigger Gunicorn worker shutdowns.
- **Root Cause:** In DRF settings (`config/settings/base.py`), `DEFAULT_THROTTLE_CLASSES` includes `AnonRateThrottle` (100 requests/day). The health-check views in `apps/common/health.py` inherited this default throttling because they did not explicitly specify `throttle_classes = []`. Render's continuous polling exhausted the anonymous quota in minutes.

### 2.3 Duplicated Health-Check URL Path (`/health/health/live/`)
- **Observed Behavior:** Render logs showed repeated polling of `/health/health/live/`.
- **Root Cause:** `config/urls.py` mounted `apps.common.urls` under `path("health/", include("apps.common.urls"))`, while `apps.common.urls` internally defined `path("health/live/", ...)`. Concatenating these prefixes resulted in `/health/health/live/`.

---

## 3. Implementation Details & Architecture Fixes

### 3.1 Single-Flight Token Refresh Promise Queue (Frontend)
In `frontend/src/api/client.ts`:
- Implemented an asynchronous mutex queue (`isRefreshing: boolean`, `refreshSubscribers: Array<(token: string) => void>`).
- When the first 401 response occurs, it acquires the refresh lock and initiates `api/v1/auth/token/refresh/`.
- Concurrent 401 requests are added to `refreshSubscribers` as suspended promises.
- Once the refreshed token is received, all queued requests are executed with the new token.
- If the refresh token is truly expired or invalid, all queued requests reject and the user is redirected cleanly to login.

```typescript
// Single-flight refresh lock in frontend/src/api/client.ts
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

const subscribeTokenRefresh = (callback: (token: string) => void) => {
  refreshSubscribers.push(callback);
};

const onRefreshed = (token: string) => {
  refreshSubscribers.forEach((callback) => callback(token));
  refreshSubscribers = [];
};
```

### 3.2 Health Check Throttle Exemption (Backend)
In `backend/apps/common/health.py`:
- Configured `throttle_classes = []` and `permission_classes = [AllowAny]` on:
  - `LivenessCheckView`
  - `ReadinessCheckView`
  - `HealthCheckView`
  - `DatabaseHealthCheckView`
  - `RedisHealthCheckView`
- Ensured `LivenessCheckView` executes zero database queries (`assertNumQueries(0)`) to remain lightweight and independent of database or cache state.

### 3.3 Zero-Downtime Canonical URL Routing & Aliases
In `backend/config/urls.py`:
- Mounted canonical root-level health paths:
  - `GET /health/live/` — Canonical Liveness probe
  - `GET /health/ready/` — Canonical Readiness probe
  - `GET /health/` — Canonical System health probe
  - `GET /health/database/` — Database probe
  - `GET /health/redis/` — Redis probe
- Preserved `/api/v1/health/*` paths for versioned API consumers.
- Maintained legacy aliases (`/health/health/live/`, `/health/health/ready/`, `/health/health/`) for zero-downtime backward compatibility with active Render configurations.
- Updated `render.yaml` to specify `healthCheckPath: /health/live/`.

---

## 4. Policy Comparison Matrix

### 4.1 Authentication & Session Handling

| Feature | Baseline Behavior | Post-Fix Behavior |
| :--- | :--- | :--- |
| **Concurrent API Requests (401)** | Multiple simultaneous refresh calls; token collision; forced logout | Single-flight refresh queue; 1 refresh call per renewal; requests replay seamlessly |
| **Multi-Device Login** | Fully supported in JWT; no single-session lock | Verified & preserved; independent refresh tokens per device |
| **Cross-User Session Interference** | Tokens stored in isolated browser storage | Verified; no global token variables; requests authenticated strictly via Bearer headers |
| **Logout Scope** | Blacklists specific refresh token | Verified; blacklists only the initiating device's refresh token without affecting other users or devices |

### 4.2 Rate-Limiting & Health Probes

| Endpoint | Baseline Rate-Limiting | Post-Fix Rate-Limiting |
| :--- | :--- | :--- |
| **Liveness (`/health/live/`)** | Anonymous 100/day (Failed after ~10 min) | **Exempt (`throttle_classes = []`)**; unlimited continuous polling |
| **Readiness (`/health/ready/`)** | Anonymous 100/day | **Exempt (`throttle_classes = []`)** |
| **Legacy Health (`/health/health/live/`)**| Anonymous 100/day | **Exempt (`throttle_classes = []`)** |
| **Login (`/auth/login/*`)** | Burst + Sustained Throttling active | **Protected (Unchanged)** |
| **OTP Request / Verify** | Strict Abuse-Prevention Throttling | **Protected (Unchanged)** |
| **Authenticated APIs** | User-scoped DRF throttling | **Protected (Unchanged)**; Scoped by User ID |

---

## 5. Automated Concurrency & Security Test Suite

A comprehensive test suite was implemented in `backend/apps/accounts/tests/test_concurrent_sessions_and_isolation.py`:

| Test Method | Objective | Result |
| :--- | :--- | :--- |
| `test_concurrent_logins_for_multiple_students` | Student A and Student B log in concurrently, receive distinct tokens, and retrieve isolated profiles. | **PASSED** |
| `test_concurrent_student_admin_and_tpo_sessions` | Admin, Student, and TPO authenticate concurrently; verify role separation and permissions. | **PASSED** |
| `test_token_refresh_isolation` | Rotating User A's token does not invalidate User B's active refresh or access tokens. | **PASSED** |
| `test_logout_isolation` | Logging out User A blacklists User A's refresh token only; User B remains authenticated. | **PASSED** |
| `test_multi_device_login_for_same_user` | User logging in on Device 2 does not terminate Device 1; logging out Device 1 preserves Device 2. | **PASSED** |
| `test_tpo_multi_college_data_isolation` | TPO A (College A) and TPO B (College B) receive strictly scoped student rosters; IDOR check returns 404. | **PASSED** |
| `test_health_check_endpoints_throttle_immunity_high_load` | High-frequency burst of 250+ consecutive health checks across all routes returns 200 with zero 429s. | **PASSED** |

---

## 6. Verification & Test Totals

### 6.1 Backend Test Results
```text
pytest backend/
============================== 323 passed in 27.42s ==============================
```
- All 323 backend unit, integration, authentication, and isolation tests passed with 0 failures and 0 errors.

### 6.2 Frontend Test Results
```text
npm test -- --run (Vitest)
 Test Files  3 passed (3)
      Tests  12 passed (12)
   Duration  3.74s
```
- All 12 frontend unit tests passed cleanly.

### 6.3 Frontend Type Check & Production Build
```text
npx tsc --noEmit
Exit code: 0 (Zero type errors)

npm run build (Vite v5.4.21)
✓ 2910 modules transformed.
✓ built in 13.39s
```
- Frontend production bundle built successfully without errors or warnings.

---

## 7. Files Changed

1. `frontend/src/api/client.ts`: Single-flight refresh mutex and subscriber queue.
2. `frontend/src/store/authStore.ts`: Session storage isolation and auth state integrity.
3. `backend/apps/common/health.py`: Added `throttle_classes = []` and `permission_classes = [AllowAny]` to all health probe views.
4. `backend/config/urls.py`: Canonicalized `/health/*` routes, added backward-compatible aliases for `/health/health/*`.
5. `backend/apps/accounts/views.py`: Verified `MeView` and authentication views.
6. `render.yaml`: Updated backend `healthCheckPath` to `/health/live/`.
7. `backend/apps/accounts/tests/test_concurrent_sessions_and_isolation.py`: New comprehensive test suite for multi-user concurrency, token refresh isolation, multi-device sessions, TPO IDOR isolation, and health check rate-limit immunity.
8. `backend/apps/common/tests/test_health.py`: Updated health probe unit tests for canonical and legacy paths.
9. `backend/apps/common/tests/test_url_routing.py`: Verified URL routing contracts for health endpoints.

---

## 8. Staging Deployment Verification Guide

When deploying to the Render staging web service and Vercel frontend:
1. **Render Health Check Configuration:**
   - Verify that the Web Service health check path is set to `/health/live/`.
   - Confirm that the Render deploy log registers healthy HTTP 200 responses immediately without any HTTP 429 warnings.
2. **Concurrent Multi-User Staging Test:**
   - Open three separate private browser windows (Window 1: Student, Window 2: TPO, Window 3: Admin).
   - Log into all three accounts simultaneously.
   - Refresh dashboards concurrently and verify each user retains their independent role, identity, and data.
   - Log out from Window 1; verify that Windows 2 and 3 remain fully authenticated.
3. **Sensitive Endpoint Protection:**
   - Attempt 15 rapid invalid login attempts to verify that authentication rate limits remain active on sensitive endpoints.

---

## 9. Final Status

**CODE FIXED — LIVE VERIFICATION PENDING**

All code fixes, single-flight refresh queues, rate-limiting exemptions, URL route aliases, batch naming standards, and automated concurrency test suites are complete and passing. Staging verification can be executed upon git deployment to Render and Vercel.
