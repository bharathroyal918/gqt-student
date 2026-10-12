# GQT Student Portal — Health-Check Architecture & Rate-Limiting Policy

## 1. System Overview

This document specifies the health-check routes, rate-limiting rules, infrastructure probing architecture, and throttle management for the GQT Student Portal backend deployed on Render.

---

## 2. Health-Check Endpoints

### 2.1 Canonical Endpoints

| URL Path | View Class | Method | Purpose | Dependencies Checked | Throttling |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/health/live/` | `LivenessCheckView` | GET | Render container liveness probe | None (0 DB queries) | **Exempt** (`throttle_classes = []`) |
| `/health/ready/` | `ReadinessCheckView` | GET | Traffic readiness probe | PostgreSQL + Redis (if configured) | **Exempt** (`throttle_classes = []`) |
| `/health/` | `HealthCheckView` | GET | Comprehensive diagnostics | PostgreSQL, Redis, Cache, Storage | **Exempt** (`throttle_classes = []`) |
| `/health/database/`| `DatabaseHealthCheckView` | GET | Dedicated DB connectivity test | PostgreSQL (`SELECT 1`) | **Exempt** (`throttle_classes = []`) |
| `/health/redis/` | `RedisHealthCheckView` | GET | Dedicated Cache connectivity test | Redis ping | **Exempt** (`throttle_classes = []`) |

### 2.2 Backward-Compatibility & Versioned Endpoints

To maintain zero downtime for external monitoring, legacy configurations, and API consumers, the following aliases are fully supported:
- `/health/health/live/` (Legacy Render configuration alias)
- `/health/health/ready/` (Legacy readiness alias)
- `/health/health/` (Legacy root health alias)
- `/api/v1/health/live/` (Versioned API liveness probe)
- `/api/v1/health/ready/` (Versioned API readiness probe)

---

## 3. Rate-Limiting Policy

### 3.1 Django REST Framework Throttling Configuration

Configured in `backend/config/settings/base.py`:
```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
        "health": "120/minute",
        "otp": "5/minute",
        "submissions": "20/minute",
        "ai": "30/hour",
    },
}
```

### 3.2 Endpoint Protection Breakdown

| Endpoint Category | Throttle Policy | Key Derivation | Rationale |
| :--- | :--- | :--- | :--- |
| **Health Checks** (`/health/*`) | `throttle_classes = []` | None | Probing must never be blocked by app throttles. |
| **Login Endpoints** (`/auth/login/*`) | Burst & Sustained rate limit | Client IP | Protects against credential stuffing and brute-force attacks. |
| **OTP Request & Verification** | `5/minute` (`ScopedRateThrottle`) | Client IP / Phone | Prevents SMS/email bombing and verification brute forcing. |
| **Authenticated Business APIs** | `1000/day` (`UserRateThrottle`) | User ID (`request.user.pk`) | Campus NAT sharing does not block individual students. |
| **Code Submissions** | `20/minute` | User ID | Prevents execution engine queue saturation. |

---

## 4. Render Web Service Deployment Configuration

### 4.1 `render.yaml`
```yaml
services:
  - type: web
    name: gqt-student-portal-backend
    runtime: python
    rootDir: backend
    plan: free
    buildCommand: "./build.sh"
    startCommand: "gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 2 --timeout 60 --graceful-timeout 30 --keep-alive 5"
    healthCheckPath: /health/live/
```

### 4.2 Key Configuration Rules
1. **`healthCheckPath: /health/live/`**: Points directly to the canonical, zero-query liveness endpoint.
2. **`--graceful-timeout 30`**: Gives Gunicorn 30 seconds to finish serving in-flight requests when receiving `SIGTERM`.
3. **`--keep-alive 5`**: Keeps TCP connections open between Render's reverse proxy and Gunicorn for 5 seconds to reduce connection handshake overhead.
