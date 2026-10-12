# GQT Student Portal — Production Reliability Audit

## 1. System Topology & Environment Baseline

| Layer | Technology | Hosting Provider | Observed Endpoint / Configuration |
| :--- | :--- | :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite, Zustand, TanStack Query v5 | Vercel | `https://gqt-student-uz53.vercel.app/` (`https://gqt-student.vercel.app/`) |
| **Backend** | Python 3.11, Django 5.x, Django REST Framework, SimpleJWT | Render | `https://gqt-student.onrender.com` (`render.yaml`) |
| **Database** | PostgreSQL (Supabase Cloud) | Supabase Cloud | PgBouncer / direct pooling via `DATABASE_URL` |
| **Cache / Broker** | Redis / in-memory fallback | Render / Upstash | `CACHES['default']` with `django_redis` fallback to `LocMemCache` |
| **Process Manager** | Gunicorn (ASGI with Uvicorn worker) | Render Web Service | `gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker` |

---

## 2. Priority 1 & 2 Audit: Health-Check Route Duplication & HTTP 429 Errors

### 2.1 Confirmed Root Causes

1. **Route Duplication (`/health/health/live/`)**:
   - In `backend/config/urls.py`, the URL resolver mounted common URLs with:
     ```python
     path("health/", include("apps.common.urls"))
     ```
   - In `backend/apps/common/urls.py`, the health routes were declared with:
     ```python
     path("health/live/", LivenessCheckView.as_view(), name="health-live")
     ```
   - Concatenating the prefix resulted in `/health/health/live/`.
   - Render's deployment health-check was configured to query this duplicated path, which worked initially but violated standard REST endpoint hierarchies.

2. **HTTP 429 Rate-Limit Exhaustion**:
   - In `backend/config/settings/base.py`, `REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"]` enforces:
     ```python
     "DEFAULT_THROTTLE_CLASSES": (
         "rest_framework.throttling.AnonRateThrottle",
         "rest_framework.throttling.UserRateThrottle",
         "rest_framework.throttling.ScopedRateThrottle",
     )
     ```
   - Default anonymous throttle rate was configured to `100/day`.
   - `LivenessCheckView` and other health views in `backend/apps/common/health.py` inherited `AnonRateThrottle` because they did not explicitly set `throttle_classes = []`.
   - Render polls health probes every 5 to 15 seconds. After ~10-15 minutes (reaching 100 requests), Django threw HTTP 429 Too Many Requests (`Too Many Requests: /health/health/live/`).

### 2.2 Implemented Architectural Fix

1. **Canonical Endpoint Standard**:
   - Canonical liveness endpoint established at `GET /health/live/`.
   - Canonical readiness endpoint established at `GET /health/ready/`.
   - Canonical root health endpoint established at `GET /health/`.
2. **Zero-Downtime Aliases**:
   - Mapped legacy routes (`/health/health/live/`, `/health/health/ready/`, `/health/health/`) and versioned routes (`/api/v1/health/*`) to ensure no in-flight Render deployments fail during transition.
3. **DRF Throttle Exemption**:
   - Configured `throttle_classes = []` and `permission_classes = [AllowAny]` on all health check views in `backend/apps/common/health.py`.
4. **Zero-Query Liveness Guarantee**:
   - `LivenessCheckView` executes 0 database queries (`assertNumQueries(0)`), guaranteeing that infrastructure health probes impose zero load on Supabase or Redis.

---

## 3. Priority 3 Audit: Gunicorn Restarts & Worker Exits

### 3.1 Observed Phenomenon
Render web service logs exhibited:
- `[INFO] Handling signal: term`
- `[INFO] Worker exiting (pid: ...)`
- `[INFO] Shutting down: Master`
- Worker respawn / restart.

### 3.2 Root Cause Analysis
1. **Health Check Failure Cascade**:
   - When Render's configured health check returned HTTP 429, Render marked the container unhealthy.
   - Render's container orchestrator sends `SIGTERM` (signal 15) to terminate failing containers.
   - Gunicorn received `SIGTERM`, triggering graceful worker exit and master process shutdown.
2. **Render Free Tier Spin-Down**:
   - On the Free tier (`plan: free` in `render.yaml`), Render terminates inactive web services after 15 minutes of inactivity. When spinning down, Render issues `SIGTERM`.
3. **Process Configuration Tuning**:
   - Start command updated in `render.yaml` to include:
     `--graceful-timeout 30 --keep-alive 5`
   - This guarantees that in-flight API requests are given 30 seconds to finish processing before process termination during rolling deployments.

---

## 4. Priority 4 Audit: Frontend Duplicate Requests & Telemetry Fetching

### 4.1 Identified Request Duplication
1. **Student Dashboard Fetch Collision**:
   - In `StudentHeader.tsx`, dashboard query was keyed as `["student", "dashboard"]`.
   - In `StudentDashboardPage.tsx`, dashboard query was keyed as `["student", "dashboard", user?.id]`.
   - Because the query keys differed, TanStack Query did not share the cache or deduplicate in-flight requests. On mounting `/dashboard`, the frontend fired two concurrent requests to `/api/v1/students/dashboard/`.
2. **Window Focus Telemetry Bursts**:
   - In `StudentDashboardPage.tsx`, `refetchOnWindowFocus` was set to `true`, causing unsolicited API bursts each time a user clicked into the portal window.
3. **Unread Notifications Polling**:
   - In `StudentHeader.tsx`, `unreadCount` used `refetchInterval: 30000` without `staleTime`, resulting in repeated fetches on every route navigation.

### 4.2 Implemented Fix
- Aligned `StudentHeader.tsx` to use `["student", "dashboard", user?.id]` with `staleTime: 30000`, matching `StudentDashboardPage.tsx`.
- Changed `refetchOnWindowFocus: false` on `StudentDashboardPage.tsx`.
- Added `staleTime: 30000` to `unreadCount` query.

---

## 5. Priority 5 & 6 Audit: Concurrent Logins & Session Isolation

### 5.1 Race Conditions in Token Renewal
- When multiple requests failed with 401 simultaneously on an expired access token, parallel calls were made to `/api/v1/auth/token/refresh/`.
- SimpleJWT with `ROTATE_REFRESH_TOKENS = True` and `BLACKLIST_AFTER_ROTATION = True` blacklisted the token on the first refresh. Subsequent parallel refresh calls failed with 401, triggering immediate storage wipe and forced logout.
- **Resolution**: Implemented single-flight refresh lock (`isRefreshing`) and subscriber promise queue in `frontend/src/api/client.ts`.

### 5.2 Multi-User & Multi-Device Isolation
- Backend derives identity exclusively from validated Bearer JWT (`request.user`). No mutable process-wide variables or single-session locks exist.
- Multi-device login is preserved: each device acquires an independent refresh token. Logging out device A blacklists device A's token only; device B remains fully operational.
- Cross-user data isolation verified: Student private data is scoped to `request.user.student_profile`.
- TPO college data isolation is strictly enforced via `Q(college=assigned_college) | Q(college__isnull=True, college_name__iexact=assigned_college.name)`, with IDOR attempts returning 404 Not Found.

---

## 6. Audit Conclusion & Risk Rating

| Domain | Initial Risk | Post-Fix Risk | Mitigation |
| :--- | :--- | :--- | :--- |
| **Health Probes** | High (Downtime/429) | Negligible | Exempted from throttling; 0-query liveness probe |
| **Concurrent Sessions** | High (Random logouts) | Negligible | Single-flight refresh queue; multi-session isolation |
| **Data Leakage (IDOR)** | Medium | Negligible | Dual-predicate TPO query; user ownership checks |
| **Frontend Request Load**| Medium (Double fetches)| Low | QueryKey alignment; window focus refetch disabled |
| **Gunicorn Restarts** | High (Container kill) | Low | 429 resolved; graceful-timeout configured |
