# GQT Student Portal — Concurrent Login & Session Isolation Guide

## 1. Overview and Purpose

This document details the multi-user authentication architecture, session isolation model, token renewal mechanisms, and security boundaries implemented in the GQT Student Portal. It guarantees that students, Training and Placement Officers (TPOs), and administrators can authenticate and navigate the portal simultaneously without session collisions, unwanted logouts, or data leakage.

---

## 2. Authentication Architecture & Token Lifecycle

### 2.1 Backend JWT Configuration (`backend/config/settings/base.py`)
```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}
```

- **Independent Token Issuance**: When a user logs in, SimpleJWT creates an independent pair of access and refresh tokens. Each login generates a distinct token pair.
- **Rotation with Blacklisting**: When a refresh token is exchanged at `POST /api/v1/auth/token/refresh/`, SimpleJWT creates a new refresh token and immediately blacklists the old refresh token to prevent replay attacks.
- **No Global Session Lock**: The portal does not enforce a single-session-per-account constraint. A student can log in from a mobile phone and laptop simultaneously; both sessions maintain independent token families.

---

## 3. Frontend Concurrency Protection: Single-Flight Refresh Queue

### 3.1 The Problem
In modern SPAs, complex pages (like the Student Dashboard) make multiple API requests concurrently (dashboard telemetry, notifications, courses, attendance). If the 15-minute access token expires, all in-flight requests encounter an HTTP 401 response at the same instant.

Without synchronization:
1. Request A and Request B receive 401.
2. Request A sends `POST /auth/token/refresh/` with `refresh_token_1`.
3. Request B sends `POST /auth/token/refresh/` with `refresh_token_1` simultaneously.
4. Request A succeeds: SimpleJWT rotates the token, issuing `refresh_token_2`, and blacklists `refresh_token_1`.
5. Request B arrives at Django with `refresh_token_1`, which is now blacklisted.
6. Request B fails with 401.
7. The Axios interceptor interprets this as a fatal session expiration, clears `localStorage`, and forces a logout.

### 3.2 The Single-Flight Promise Queue Solution (`frontend/src/api/client.ts`)
```typescript
let isRefreshing = false;
let refreshSubscribers: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  refreshSubscribers.forEach((subscriber) => {
    if (error) {
      subscriber.reject(error);
    } else if (token) {
      subscriber.resolve(token);
    }
  });
  refreshSubscribers = [];
};

// Interceptor logic
if (error.response?.status === 401 && !originalRequest._retry) {
  originalRequest._retry = true;

  if (isRefreshing) {
    // Queue concurrent requests until active refresh finishes
    return new Promise<string>((resolve, reject) => {
      refreshSubscribers.push({ resolve, reject });
    })
      .then((newAccessToken) => {
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        }
        return apiClient(originalRequest);
      })
      .catch((err) => Promise.reject(err));
  }

  isRefreshing = true;
  const refreshToken = localStorage.getItem("gqt_refresh_token");

  if (refreshToken) {
    try {
      const { data } = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
        refresh: refreshToken,
      });
      const newAccessToken = data.data.access;
      localStorage.setItem("gqt_access_token", newAccessToken);
      if (data.data.refresh) {
        localStorage.setItem("gqt_refresh_token", data.data.refresh);
      }
      processQueue(null, newAccessToken);
      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
      }
      return apiClient(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      // Clean up storage and redirect to login
      localStorage.removeItem("gqt_access_token");
      localStorage.removeItem("gqt_refresh_token");
      // ... redirect ...
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
}
```

---

## 4. Cross-User Data Isolation & IDOR Protections

### 4.1 Backend Scope Derivement
- Every protected endpoint derives user identity directly from `request.user`.
- No module-level, thread-local, or process-wide variables store current user state.
- **Student Scoping**: All student API endpoints filter by `student=request.user.student_profile` or `user=request.user`.
- **TPO Scoping**: TPO endpoints enforce assigned college isolation:
  ```python
  Q(college=assigned_college) | Q(college__isnull=True, college_name__iexact=assigned_college.name)
  ```
  Attempting to access a student record outside the TPO's assigned college returns `404 Not Found`.
- **Admin Endpoints**: Require `IsAdmin` permission (`request.user.role == "ADMIN"`).

### 4.2 Frontend Cache Clearing on Account Switching
In `frontend/src/store/authStore.ts`:
- Calling `setAuth()` and `clearAuth()` automatically executes:
  ```typescript
  queryClient.removeQueries({ queryKey: ["student"] });
  queryClient.clear();
  ```
- User queries are keyed with the user ID (`["student", "dashboard", user?.id]`), preventing cache reuse if an account switch occurs within the same browser tab without a full reload.

---

## 5. Automated Concurrency Tests

The test suite in `backend/apps/accounts/tests/test_concurrent_sessions_and_isolation.py` validates:
1. Two different students can log in at the same time and query their own profiles independently.
2. An Administrator, Student, and TPO can operate concurrently with correct permission scoping.
3. User A refreshing their token does not invalidate User B's tokens.
4. User A logging out blacklists User A's refresh token only; User B remains authenticated.
5. User A logging in from Device 2 receives a new token without invalidating Device 1.
6. TPO A cannot access Student B (College B), verifying IDOR protection.
