# GQT Student Portal — Audit & Fix Checklist

**Status Legend:**
- **PASS**: Verified and working correctly in active codebase.
- **FIXED**: Defect identified, resolved with code change, and verified with tests.
- **BLOCKED**: Requires external action, hosting provider configuration, or live environment.
- **NOT APPLICABLE**: Not in the scope of this project.

---

## 1. Security & Secrets Management

| Item ID | Description | Status | Verification Notes |
| :--- | :--- | :--- | :--- |
| SEC-01 | No Supabase service-role keys in frontend code | **PASS** | Verified across all `frontend/src` files and Vite configs. |
| SEC-02 | No hardcoded database credentials in tracked git files | **PASS** | Evaluated via ripgrep; credentials loaded via `environ.Env()`. |
| SEC-03 | `.env` and `*_db.sqlite3` files excluded from git | **PASS** | Verified in root and backend `.gitignore`. |
| SEC-04 | Production settings enforce `DEBUG=False` | **PASS** | Confirmed in `config/settings/production.py`. |
| SEC-05 | Production settings enforce `SECURE_SSL_REDIRECT` | **PASS** | Configured in `config/settings/production.py`. |
| SEC-06 | Production settings enforce `SESSION_COOKIE_SECURE` | **PASS** | Configured in `config/settings/production.py`. |
| SEC-07 | Production settings enforce `CSRF_COOKIE_SECURE` | **PASS** | Configured in `config/settings/production.py`. |
| SEC-08 | Production settings enforce `SECURE_HSTS_SECONDS` | **PASS** | Configured with `31536000` (1 year). |
| SEC-09 | Secret keys loaded from environment variables | **PASS** | Configured via `django-environ`. |

---

## 2. Authentication, Authorization & Data Isolation

| Item ID | Description | Status | Verification Notes |
| :--- | :--- | :--- | :--- |
| AUTH-01 | JWT token generation and validation | **PASS** | Verified via Pytest auth suite. |
| AUTH-02 | Student cannot access another student's submission | **PASS** | Enforced by object-level permission & request filtering. |
| AUTH-03 | Student cannot access another student's certificates | **PASS** | Verified in `StudentCertificateDownloadView`. |
| AUTH-04 | Student cannot access another student's applications | **PASS** | Verified in `StudentMyApplicationsView`. |
| AUTH-05 | Admin endpoints strictly protected by `IsAdminRole` / `IsAdmin` | **PASS** | Verified across all `admin_views.py`. |
| AUTH-06 | Student QR code attendance token rotation & scanning | **PASS** | Verified in attendance security service. |
| AUTH-07 | Password reset workflow with time-limited OTP tokens | **PASS** | Tested and verified in `accounts/views.py`. |

---

## 3. Backend APIs & Business Logic

| Item ID | Description | Status | Verification Notes |
| :--- | :--- | :--- | :--- |
| BE-01 | System checks pass cleanly in production mode | **PASS** | `python manage.py check --settings=config.settings.production` (0 issues, 0 silenced). |
| BE-02 | Deployment check passes cleanly | **FIXED** | Fixed `manage.py` setting routing for `--deploy` checks while preserving explicit `--settings`. |
| BE-03 | OpenAPI schema generation and validation | **FIXED** | Removed global suppression flags (`DISABLE_ERRORS_AND_WARNINGS: False`, 0 silenced checks). Annotated all non-generic `APIView` endpoints with explicit serializers, request payloads, response structures, and enum name overrides. Validation passes with 0 errors and 0 warnings. |
| BE-04 | Database schema migrations up-to-date | **PASS** | `makemigrations --check --dry-run` reports no changes. |
| BE-05 | Supabase live connection | **PASS** | Verified live connection to Supabase PostgreSQL pooler (`aws-0-ap-northeast-1.pooler.supabase.com:6543`). |
| BE-06 | Sandboxed code execution isolation | **PASS** | Judge service connector handles remote sandboxed runner. |
| BE-07 | Course sequential module unlocking | **PASS** | Verified in `apps/modules/services.py`. |
| BE-08 | Placement drive eligibility calculation | **PASS** | Verified in `apps/placements/services.py`. |
| BE-09 | Pytest test suite execution | **PASS** | 236/236 passed in 30.25s. |

---

## 4. Frontend Application

| Item ID | Description | Status | Verification Notes |
| :--- | :--- | :--- | :--- |
| FE-01 | TypeScript static type checking | **PASS** | `npx tsc --noEmit` exited with 0 errors. |
| FE-02 | Production bundle build | **PASS** | `npm run build` generated production distribution in 12.53s. |
| FE-03 | Vitest frontend test suite | **PASS** | 12/12 test cases passing in 1.75s. |
| FE-04 | API client base URL configuration | **PASS** | Configured via `VITE_API_BASE_URL` with `/api/v1` fallback. |
| FE-05 | Role-based route guards (Admin vs Student) | **PASS** | Enforced by `ProtectedRoute` & `AuthContext`. |
| FE-06 | Token refresh and logout redirection | **PASS** | Axios response interceptor handles 401 & token renewal. |
| FE-07 | Responsive UI layouts | **PASS** | Vanilla CSS & Tailwind utility design tokens with mobile drawer and responsive grid. |
| FE-08 | QR Code Scanner component | **PASS** | Integrated with `html5-qrcode` camera handler. |

---

## 5. Deployment & Infrastructure

| Item ID | Description | Status | Verification Notes |
| :--- | :--- | :--- | :--- |
| DEP-01 | Render web service configuration (`render.yaml`) | **PASS** | Verified build script (`build.sh`) and gunicorn startup. |
| DEP-02 | Vercel frontend configuration (`vercel.json`) | **PASS** | Verified rewrite rules for SPA client-side routing. |
| DEP-03 | Static file collection (`collectstatic`) | **PASS** | Configured with WhiteNoise storage backend. |
| DEP-04 | Health check endpoints | **PASS** | `/api/v1/health/`, `/health/ready/`, `/health/live/` verified. |
