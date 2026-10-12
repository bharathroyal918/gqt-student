# GQT Student Portal — Production Reliability Fix Report

## 1. Executive Summary

- **Project:** GQT Student Portal
- **Baseline Git Commit:** `dbed397`
- **Target Environments:** Render (Backend Web Service) + Vercel (Frontend SPA) + Supabase (PostgreSQL Database)
- **Local Workspace:** `C:\Users\User\Documents\GQT Student Portal`
- **Final Status:** **CODE FIXED — LIVE VERIFICATION PENDING**

This comprehensive engineering initiative resolves critical production vulnerabilities, deployment instabilities, and session collisions in the GQT Student Portal:
1. **Health-Check Route Duplication:** Fixed the duplicated `/health/health/live/` route, established canonical `/health/live/` and `/health/ready/` routes, and preserved backward-compatible aliases.
2. **HTTP 429 Too Many Requests on Render Probes:** Exempted health checks from default anonymous rate limiting (`throttle_classes = []`), while keeping login and sensitive endpoints strictly throttled.
3. **Gunicorn Worker Shutdowns:** Resolved orchestrator `SIGTERM` restarts triggered by health check 429 failures, and enhanced Gunicorn configuration with graceful timeouts.
4. **Duplicate Frontend API Requests:** Deduplicated Student Dashboard and unread notification queries by aligning TanStack Query keys and disabling aggressive window focus refetching.
5. **Concurrent Multi-User Login & Session Isolation:** Added a single-flight token refresh promise queue in the Axios interceptor to prevent parallel 401 refresh collisions from triggering blacklisting and unwanted logouts.
6. **Data Scoping & IDOR Protections:** Verified student profile ownership and TPO assigned-college data isolation.
7. **Regression Prevention & CI Gates:** Added automated concurrency tests in backend pytest and created `.github/workflows/ci.yml`.

---

## 2. Confirmed Issues & Root Cause Analysis

### Issue 1: Duplicated Health Check Path (`/health/health/live/`)
- **Evidence:** Render service logs exhibited repeated polling of `GET /health/health/live/`.
- **Root Cause:** In `backend/config/urls.py`, the root URL configuration mounted `apps.common.urls` with `path("health/", include("apps.common.urls"))`. In `backend/apps/common/urls.py`, the health path was defined with `path("health/live/", ...)`. Concatenating these yielded `/health/health/live/`.
- **Fix:** In `backend/config/urls.py`, mounted canonical root routes directly (`/health/live/`, `/health/ready/`, `/health/`, etc.) and maintained `/health/health/*` legacy aliases for backward compatibility.

### Issue 2: HTTP 429 Rate-Limit Errors on Health Check Probes
- **Evidence:** Render logs showed `/health/health/live/` initially returning HTTP 200, followed by HTTP 429 Too Many Requests (`Too Many Requests: /health/health/live/`).
- **Root Cause:** In `backend/config/settings/base.py`, `DEFAULT_THROTTLE_CLASSES` includes `AnonRateThrottle` configured for `100/day`. The health check views in `apps/common/health.py` inherited this limit because they lacked explicit `throttle_classes = []`. Render's frequent polling exceeded 100 requests within ~10 minutes.
- **Fix:** Added `throttle_classes = []` and `permission_classes = [AllowAny]` to `LivenessCheckView`, `ReadinessCheckView`, `HealthCheckView`, `DatabaseHealthCheckView`, and `RedisHealthCheckView`.

### Issue 3: Gunicorn Master & Worker Process Shutdowns
- **Evidence:** Logs showed `Handling signal: term`, worker exit, master shutdown, and Gunicorn restart.
- **Root Cause:** 
  1. Render's container health monitor marks instances unhealthy when health probes fail (due to 429s). Following failed probes, Render sends `SIGTERM` (signal 15) to terminate and respawn the container.
  2. In `render.yaml`, `plan: free` causes inactive instances to spin down after 15 minutes of inactivity, also issuing `SIGTERM`.
- **Fix:** Fixed the 429 health probe failures; updated `render.yaml` startCommand to include `--graceful-timeout 30 --keep-alive 5`.

### Issue 4: Duplicate Dashboard Requests on Initial Mount
- **Evidence:** Frontend network telemetry displayed multiple simultaneous requests to `/api/v1/students/dashboard/` and `/students/notifications/unread-count/`.
- **Root Cause:** `StudentHeader.tsx` used `queryKey: ["student", "dashboard"]` while `StudentDashboardPage.tsx` used `queryKey: ["student", "dashboard", user?.id]`. Because query keys differed, TanStack Query could not share or deduplicate the in-flight requests. Additionally, `StudentDashboardPage.tsx` had `refetchOnWindowFocus: true`.
- **Fix:** Aligned `StudentHeader.tsx` to use `["student", "dashboard", user?.id]` with `staleTime: 30000`, added `staleTime: 30000` to `unreadCount`, and set `refetchOnWindowFocus: false` on `StudentDashboardPage.tsx`.

### Issue 5: Concurrent Multi-User Token Refresh Race Condition
- **Evidence:** When an access token expired on a busy page, parallel API requests triggered concurrent calls to `/api/v1/auth/token/refresh/`.
- **Root Cause:** SimpleJWT uses `ROTATE_REFRESH_TOKENS = True` and `BLACKLIST_AFTER_ROTATION = True`. The first refresh call succeeded and blacklisted the token; subsequent parallel calls failed with 401 because the token was now blacklisted, triggering an emergency storage purge and forced logout.
- **Fix:** Implemented an asynchronous mutex queue (`isRefreshing`, `refreshSubscribers`) in `frontend/src/api/client.ts`. All concurrent 401s pause and await the single in-flight refresh request.

---

## 3. Files Changed and Detailed Changes

| File | Nature of Change | Reason |
| :--- | :--- | :--- |
| `backend/config/urls.py` | Routing modification | Added canonical `/health/live/`, `/health/ready/`, `/health/`, and backward-compatible aliases for `/health/health/*`. |
| `backend/apps/common/health.py` | Throttling & permission update | Set `throttle_classes = []` and `permission_classes = [AllowAny]` on all health views. |
| `render.yaml` | Service deployment configuration | Updated `healthCheckPath: /health/live/` and added `--graceful-timeout 30 --keep-alive 5` to `startCommand`. |
| `frontend/src/api/client.ts` | Axios response interceptor | Implemented single-flight refresh queue (`isRefreshing`, `refreshSubscribers`). |
| `frontend/src/store/authStore.ts` | Auth state management | Verified storage cleanup and cache invalidation on login/logout. |
| `frontend/src/components/layout/StudentHeader.tsx` | Query deduplication | Aligned `queryKey` to `["student", "dashboard", user?.id]` and added `staleTime: 30000` to `unreadCount`. |
| `frontend/src/pages/student/StudentDashboardPage.tsx` | Query optimization | Set `refetchOnWindowFocus: false`. |
| `backend/apps/accounts/tests/test_concurrent_sessions_and_isolation.py` | New automated test suite | Added 7 comprehensive concurrency, multi-device, IDOR, and health rate-limit immunity tests. |
| `backend/apps/common/tests/test_health.py` | Test update | Updated assertions for canonical and legacy health endpoints. |
| `backend/apps/common/tests/test_url_routing.py` | Test update | Added URL resolution tests for canonical and alias routes. |
| `.github/workflows/ci.yml` | New CI workflow | Added GitHub Actions pipeline for backend and frontend release gates. |

---

## 4. Before and After Behavior Comparison

| Area | Baseline Behavior | Post-Fix Behavior |
| :--- | :--- | :--- |
| **Render Health Check Path** | `/health/health/live/` (duplicated segment) | `/health/live/` (canonical) + `/health/health/live/` (alias) |
| **Health Check Rate Limiting** | Throttled after 100 requests (HTTP 429) | Completely exempt (`throttle_classes = []`, HTTP 200 unlimited) |
| **Liveness DB Load** | None (View logic clean) | Explicitly verified 0 database queries (`assertNumQueries(0)`) |
| **Concurrent 401s on Frontend** | Parallel refresh calls -> token blacklisted -> forced logout | Single-flight promise queue -> seamless retry with new token |
| **Multi-Device Login** | Fully supported in SimpleJWT | Verified; independent token families per device |
| **Student Dashboard API Calls** | 2 simultaneous calls to `/students/dashboard/` | 1 single shared/deduplicated call via matching queryKey |
| **Window Refocus API Bursts** | Immediate refetch of dashboard on tab focus | Window focus refetch disabled; respects `staleTime` |
| **TPO College Scoping** | College foreign key with legacy name fallback | Enforced via `Q(college=assigned_college) \| ...`; IDOR returns 404 |
| **Gunicorn Process Termination** | Abrupt worker kill during 429 restarts | 429 eliminated; `--graceful-timeout 30` configured |

---

## 5. Verification & Test Totals

### 5.1 Backend Verification
- **Django System Check:**
  `python manage.py check` — **0 issues identified**
- **Migration Consistency:**
  `python manage.py makemigrations --check --dry-run` — **No changes detected**
- **Pytest Suite:**
  `pytest -q` — **323 passed in 27.42s** (100% pass rate)

### 5.2 Concurrency & Isolation Specific Tests (`test_concurrent_sessions_and_isolation.py`)
1. `test_concurrent_logins_for_multiple_students`: **PASSED**
2. `test_concurrent_student_admin_and_tpo_sessions`: **PASSED**
3. `test_token_refresh_isolation`: **PASSED**
4. `test_logout_isolation`: **PASSED**
5. `test_multi_device_login_for_same_user`: **PASSED**
6. `test_tpo_multi_college_data_isolation`: **PASSED**
7. `test_health_check_endpoints_throttle_immunity_high_load`: **PASSED** (250+ burst requests returned 200)

### 5.3 Frontend Verification
- **TypeScript Check:**
  `npx tsc --noEmit` — **0 errors** (Clean)
- **Vitest Unit Suite:**
  `npm test -- --run` — **12 passed across 3 test files**
- **Production Build:**
  `npm run build` — **Built successfully in 13.39s**

---

## 6. Deployment Configuration & Manual Actions

### 6.1 Render Web Service Settings (Render Dashboard)
1. **Health Check Path:** Ensure the web service configuration in the Render Dashboard specifies `/health/live/`.
2. **Environment Variables:** Verify that the following required variables are set:
   - `DJANGO_SETTINGS_MODULE`: `config.settings.production`
   - `DEBUG`: `False`
   - `DATABASE_URL`: Valid Supabase pooled PostgreSQL connection string
   - `ALLOWED_HOSTS`: `localhost,127.0.0.1,backend,.onrender.com,gqt-student.onrender.com`

### 6.2 Vercel Frontend Settings (Vercel Dashboard)
1. **Environment Variables:**
   - `VITE_API_BASE_URL`: `https://gqt-student.onrender.com/api/v1`

---

## 7. Rollback Plan

If an unexpected production regression occurs:
1. **Render Rollback:** In the Render Dashboard under **gqt-student-portal-backend** > **Deploys**, select the previous stable deployment and click **Rollback to this deploy**. Alternatively, execute `git revert HEAD` and push to master.
2. **Vercel Rollback:** In the Vercel Dashboard, select the previous working deployment and click **Instant Rollback**.

---

## 8. Final Status

**CODE FIXED — LIVE VERIFICATION PENDING**

All code fixes, single-flight refresh queues, rate-limiting exemptions, URL route canonicalization, query deduplication, and automated regression test suites are complete and passing with 100% test success across both backend and frontend suites. Staging and live deployment verification can proceed via normal deployment to Render and Vercel.
