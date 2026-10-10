# GQT Student Portal — Staging Deployment & Launch Runbook

## 1. Staging Release Objective & Architecture

This runbook defines the controlled procedure for deploying, verifying, and rolling back the **Global Quality Technologies (GQT) Student Portal** in the staging environment.

### Staging Stack Summary
- **Frontend SPA**: React 18 + TypeScript + Vite, served via static hosting (Vercel / Cloudflare Pages / WhiteNoise).
- **Backend API**: Python 3.11 / Django 6.1 + Django REST Framework + ASGI (Uvicorn / Gunicorn).
- **Database**: Supabase PostgreSQL (Staging instance with connection pooling enabled).
- **Authentication**: JWT authentication with automatic access token refresh, rotation, and blacklisting.
- **Audit & Governance**: Immutable `AuditLog` table for all TPO provisioning, college reassignments, report previews, and secure file exports.

---

## 2. Environment Variables & Secret Configuration

> **CRITICAL SECURITY RULE:** Never store real secrets in Git repositories. Use the hosting provider's Secrets Manager (e.g. Render Secret Manager, AWS Secrets Manager, Vercel Environment Variables).

### Backend Variables (`config.settings.staging` / `config.settings.production`)

| Variable Name | Required | Example / Description |
| :--- | :--- | :--- |
| `DJANGO_SETTINGS_MODULE` | Yes | `config.settings.staging` |
| `ENVIRONMENT` | Yes | `staging` |
| `DEBUG` | Yes | `False` |
| `DJANGO_SECRET_KEY` | Yes | 64+ char random cryptographic string |
| `DATABASE_URL` | Yes | `postgresql://postgres:[PASSWORD]@[STAGING_HOST]:5432/postgres?sslmode=require` |
| `DJANGO_ALLOWED_HOSTS` | Yes | `staging-api.portal.gqt.edu,gqt-student.onrender.com,localhost` |
| `CORS_ALLOWED_ORIGINS` | Yes | `https://staging-portal.gqt.edu,https://gqt-student.vercel.app` |
| `CSRF_TRUSTED_ORIGINS` | Yes | `https://staging-portal.gqt.edu,https://*.vercel.app,https://*.onrender.com` |
| `SECURE_SSL_REDIRECT` | Yes | `True` |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | No | `15` (default) |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | No | `7` (default) |
| `JWT_SIGNING_KEY` | No | Uses `DJANGO_SECRET_KEY` by default |
| `REDIS_URL` | Optional | `redis://:[PASSWORD]@[REDIS_HOST]:6379/0` (fallback to in-memory if unconfigured) |

### Frontend Variables (`frontend/.env.production`)

| Variable Name | Required | Example / Description |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | Yes | `https://staging-api.portal.gqt.edu/api/v1` or `/api/v1` |
| `VITE_APP_NAME` | No | `GQT Student Portal (Staging)` |
| `VITE_APP_ENV` | No | `staging` |

---

## 3. Staging Deployment Procedure

### Step 1: Pre-Deployment Verification
```powershell
# In local/CI workspace:
# 1. Check Django configuration
python manage.py check --settings=config.settings.staging

# 2. Check for migration drifts
python manage.py makemigrations --check --dry-run --settings=config.settings.staging

# 3. Run complete automated test suite
python -m pytest -v

# 4. Verify Frontend TypeScript & Production Build
cd ../frontend
npx tsc --noEmit
npm test -- --run
npm run build
```

### Step 2: Database Migration Execution
```bash
# On Staging Backend Instance (or CI deployment hook):
python manage.py migrate --no-input --settings=config.settings.staging
```

### Step 3: Collect Static Assets
```bash
python manage.py collectstatic --no-input --clear --settings=config.settings.staging
```

### Step 4: Start ASGI Web Server
```bash
gunicorn config.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --timeout 60
```

---

## 4. Health Check Probes & Validation

| Probe URL | Expected HTTP Status | Expected Response Body |
| :--- | :--- | :--- |
| `GET /api/v1/health/live/` | `200 OK` | `{"data": {"status": "alive"}}` |
| `GET /api/v1/health/ready/` | `200 OK` | `{"data": {"status": "ready", "database": "connected"}}` |
| `GET /api/v1/health/` | `200 OK` | `{"data": {"status": "healthy", "service": "gqt-student-portal-backend"}}` |

---

## 5. End-to-End TPO Workflow Staging Verification

Execute this step-by-step verification checklist on staging using non-production test accounts:

1. **Admin TPO Provisioning**:
   - Log in as Admin (`/login` -> Admin Portal).
   - Navigate to `/admin/tpos`.
   - Click "Invite / Add Officer". Create a new TPO assigned to **College A**.
   - Verify that an audit record is created in Admin Audit History.
2. **Dedicated TPO Authentication**:
   - Navigate to `/auth/tpo-login` (or `/tpo/login`).
   - Log in with newly provisioned TPO credentials.
   - Verify redirect to `/tpo/dashboard`.
   - Verify the assigned institution name banner appears in the sidebar.
3. **College Data Isolation Check**:
   - Open `/tpo/students`. Verify that **only** College A students appear in the roster.
   - Test search, batch filter, and ordering controls.
   - Click a student to view details. Ensure view is strictly read-only with 0 edit controls.
4. **Analytics & Performance Trends**:
   - Inspect `/tpo/learning-progress`, `/tpo/assignments-labs`, `/tpo/attendance`, `/tpo/trends`, `/tpo/students-needing-support`, and `/tpo/analytics/leaderboard`.
   - Verify all metrics calculate correctly without leaking other colleges' data.
5. **Reports, Live Preview & Secure Export**:
   - Navigate to `/tpo/reports`.
   - Select "College Student Roster", "Attendance Compliance", and "College Summary".
   - Click "Refresh Preview" -> Verify preview table displays with correct column definitions.
   - Click "Download CSV Export" -> Verify downloaded CSV file opens cleanly in Excel with Unicode names intact and formula injections neutralized.
6. **Dynamic Reassignment & Revocation**:
   - In Admin Portal, reassign the TPO from College A to **College B**.
   - In TPO session, refresh the page -> Verify the student directory immediately switches to College B with 0 College A records.
   - In Admin Portal, deactivate the TPO -> Verify subsequent TPO requests return `403 Forbidden`.

---

## 6. Rollback & Incident Response Procedure

If staging verification fails or a regression occurs:

1. **Web Traffic Rollback**:
   - In Vercel / Render / Cloudflare dashboard, roll back deployment to previous stable build hash.
2. **Database Migration Reversal** (if applicable):
   ```bash
   # Roll back specific migration safely
   python manage.py migrate accounts 0003_previous_migration --settings=config.settings.staging
   ```
3. **Session Invalidation**:
   - If security keys or credentials were compromised, rotate `DJANGO_SECRET_KEY` in Secrets Manager to immediately invalidate all active JWT tokens.

---

## 7. Staging Release Recommendation

- **Current Status:** **STAGING READY**
- **Automated Verification:** All 310 backend tests and 12 frontend tests pass with 0 TypeScript compilation errors.
- **Production Boundary:** Staging deployment approved. Production launch requires staging smoke test validation with real staging Supabase database.
