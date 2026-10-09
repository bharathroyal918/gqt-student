# GQT Student Portal — Security Audit & Threat Assessment

**Date:** 2026-10-09  
**Scope:** Full-stack codebase, API surface, Database access layer, Authentication/Authorization, and Deployment configurations.  

---

## 1. Secrets & Sensitive Data Exposure Audit

| Category | Assessment | Status | Notes |
| :--- | :--- | :--- | :--- |
| **Supabase Service Role Key** | Scanned all frontend and backend source files. | **CLEAN** | Key is strictly maintained in private environment variables and not exposed to the browser. |
| **Database Connection Strings** | Checked tracked git repositories. | **CLEAN** | Loaded exclusively through `DATABASE_URL` / `DJANGO_DATABASE_URL` in environment. |
| **JWT Signing Keys** | Verified token signing and validation secrets. | **CLEAN** | Sourced from `JWT_SIGNING_KEY` environment variable. |
| **Django Secret Key** | Verified production secret generation. | **CLEAN** | Production requires `DJANGO_SECRET_KEY` from environment, raising runtime error if missing. |
| **Client Bundles (`dist/`)** | Inspected Vite production build output. | **CLEAN** | No backend secrets or service-role keys bundled into frontend assets. |

---

## 2. Authentication & Authorization Controls

### 2.1 JWT Lifecycle & Token Management
- **Access Tokens**: Short-lived (15 minutes).
- **Refresh Tokens**: Long-lived (7 days).
- **Token Storage**: Access token managed in-memory / secure storage; automatic refresh performed via Axios interceptors on 401 challenge.
- **Revocation**: Blacklist and user-invalidation supported.

### 2.2 Role-Based Access Control (RBAC)
- **Role Hierarchy**: `ADMIN` (Staff/Instructors) vs `STUDENT` (Learners).
- **Enforcement Layer**: DRF permission classes (`IsAuthenticated`, `IsAdminRole`, `IsStudentRole`) applied on every view.
- **Negative Testing Verification**:
  - Direct student requests to `/api/v1/admin/*` endpoints return `HTTP 403 Forbidden`.
  - Direct unauthenticated requests return `HTTP 401 Unauthorized`.

### 2.3 Object-Level Permissions & IDOR Prevention
- Views filtering querysets explicitly restrict queries by `user=request.user` or `student=request.user.student_profile`.
- IDs passed via URL parameters (e.g., submission ID, application ID, certificate ID) cannot be queried across tenant boundaries without matching user ownership.

---

## 3. Data Integrity & Code Execution Security

### 3.1 Sandboxed Code Runner
- Student programming submissions are dispatched to an external isolated Judge service (`JUDGE_SERVICE_URL`).
- Code evaluation runs with restricted CPU, memory, timeout (e.g. 5s), and no privileged host filesystem or network access.
- Code execution is never evaluated within the main Django runtime process.

### 3.2 File Upload Security
- Resumes and project submissions are validated for allowed MIME types and file extension whitelisting.
- Uploaded files are handled with randomized UUID filenames to prevent path traversal (`../`) attacks.
- Download endpoints verify student ownership or admin authorization prior to streaming file contents.

---

## 4. Production Security Headers & Cookies

In `config/settings/production.py`:
- `DEBUG = False`
- `SECURE_BROWSER_XSS_FILTER = True`
- `SECURE_CONTENT_TYPE_NOSNIFF = True`
- `X_FRAME_OPTIONS = "DENY"`
- `SECURE_HSTS_SECONDS = 31536000` (1 Year)
- `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
- `SECURE_HSTS_PRELOAD = True`
- `SECURE_SSL_REDIRECT = True`
- `SESSION_COOKIE_SECURE = True`
- `CSRF_COOKIE_SECURE = True`
- `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`
