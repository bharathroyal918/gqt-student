# GQT Student Portal — TPO Module Production Readiness & Security Audit Report

## 1. Executive Summary & Readiness Assessment

This document provides the authoritative production-readiness, security audit, and verification report for the **Training & Placement Officer (TPO)** portal and management subsystem within the GQT Student Portal.

**Assessment:** **READY FOR PRODUCTION / STAGING DEPLOYMENT**  
- **Backend Test Suite:** 310 / 310 tests passing (100% pass rate).
- **Frontend Test Suite:** 12 / 12 tests passing.
- **TypeScript Static Verification:** 0 compilation errors (`tsc --noEmit`).
- **Production Build:** Vite production bundle generated successfully with 0 errors.
- **Django Health & Migrations:** 0 system check issues, 0 unapplied migrations.

---

## 2. Role & Permission Matrix

| Role | Access Scope | Allowed Operations | Guard Implementation |
| :--- | :--- | :--- | :--- |
| **Admin** | System-wide | Full CRUD on Colleges, TPO Provisioning, Reassignment, Deactivation, Audit Logs, Courses, Modules, Assessments. | `IsAdmin` (`apps.common.permissions`) |
| **TPO** | Assigned College Only | Read-only access to enrolled students, analytics, leaderboards, report previews, and secure CSV/JSON exports. Self-service profile editing. | `IsTPO` + `HasActiveTPOCollegeAssignment` |
| **Student** | Personal Record Only | Enrolled course learning, coding challenge submissions, attendance check-in, badges/achievements, profile updates. | `IsStudent` + `IsApprovedStudent` + `IsOwnerOrAdmin` |
| **Anonymous** | Public Endpoints Only | Login, Password Reset, Public Certificate Verification. | `AllowAny` |

---

## 3. TPO Endpoint Inventory

All TPO endpoints enforce strict JWT authentication, role verification, and active institutional assignment:

| Method | Endpoint Route | Permission Class | Authoritative Scoping / Logic |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/tpo/auth/login/` | `AllowAny` | Authenticates TPO identity and verifies active account status. |
| `GET` | `/api/v1/tpo/me/` | `IsTPO` | Returns current officer profile and assigned institution. |
| `PATCH` | `/api/v1/tpo/me/` | `IsTPO` | Self-service profile updates (name, phone, designation, bio, avatar). |
| `GET` | `/api/v1/tpo/college/` | `IsTPO` | Basic profile of the assigned institution. |
| `GET` | `/api/v1/tpo/college/summary/` | `IsTPO` | Real-time institutional telemetry (attendance, pass rate, active/inactive counts). |
| `GET` | `/api/v1/tpo/college/students/` | `IsTPO` | College-scoped paginated student directory with search, filtering, and sorting. |
| `GET` | `/api/v1/tpo/college/students/<uuid:pk>/` | `IsTPO` | Read-only student details and recent submission telemetry (cross-college IDOR returns 404). |
| `GET` | `/api/v1/tpo/analytics/learning-progress/` | `IsTPO` | Module progress metrics and syllabus completion status for assigned students. |
| `GET` | `/api/v1/tpo/analytics/assignments-labs/` | `IsTPO` | Lab submission telemetry, unique problem attempts, and evaluated pass rates. |
| `GET` | `/api/v1/tpo/analytics/attendance/` | `IsTPO` | Attendance compliance distributions and 75% policy threshold evaluations. |
| `GET` | `/api/v1/tpo/analytics/trends/` | `IsTPO` | Verified historical monthly score and submission trajectories. |
| `GET` | `/api/v1/tpo/analytics/students-needing-support/` | `IsTPO` | Rule-based academic risk indicators (`LOW_ATTENDANCE`, `ZERO_SUBMISSIONS`, `HIGH_FAILURE_RATE`, `STALLED_PROGRESS`). |
| `GET` | `/api/v1/tpo/analytics/leaderboard/` | `IsTPO` | College-isolated student rankings by score, attendance %, and active streak. |
| `GET` | `/api/v1/tpo/reports/types/` | `IsTPO` | Metadata registry of supported report templates, formats, and available filters. |
| `POST` | `/api/v1/tpo/reports/preview/` | `IsTPO` | Scoped preview schema with column definitions, total row count, sample preview rows. |
| `POST` | `/api/v1/tpo/reports/export/` | `IsTPO` | Streams injection-sanitized CSV (`utf-8-sig`) or formatted JSON export artifact. |

---

## 4. Multi-Tenant Scoping & Legacy Compatibility Rule

To prevent data leaks across institutional boundaries:
1. **Canonical Foreign Key Priority**:
   ```python
   Q(college=assigned_college) | Q(college__isnull=True, college_name__iexact=assigned_college.name)
   ```
2. **Conflicting Foreign Key Guard**:
   - If a student profile has `college = College B`, but legacy text `college_name = "College A"`, the explicit relational FK takes precedence and the record is **strictly excluded** from College A.
3. **Dynamic Reassignment**:
   - When an administrator reassigns a TPO officer to a new college, all subsequent requests immediately re-scope to the new college with zero cache contamination.

---

## 5. Report & Export Security Safeguards

1. **CSV Formula Injection Mitigation**:
   - All text cells starting with formula command triggers (`=`, `+`, `-`, `@`, `\t`, `\r`) are automatically escaped with a leading single quote (`'`).
2. **UTF-8 with BOM Encoding**:
   - CSV artifacts are encoded with `utf-8-sig` (`\xef\xbb\xbf`) to ensure native Unicode rendering in Microsoft Excel and LibreOffice.
3. **Compliance Audit Logging**:
   - Report preview (`TPO_REPORT_PREVIEW`) and file export (`TPO_REPORT_EXPORT`) events are immutably logged in `apps.accounts.models.AuditLog` with actor ID, college ID, timestamp, IP address, and payload parameters.

---

## 6. Environment & Deployment Instructions

### Backend Configuration Checklist
- `DEBUG=False` in production environments.
- Set `SECRET_KEY` and `DATABASE_URL` (Supabase / PostgreSQL connection string).
- Ensure `CONN_MAX_AGE=600` and `CONN_HEALTH_CHECKS=True` for persistent connection pooling.
- Configure `CORS_ALLOWED_ORIGINS` to include only trusted frontend domain names.
- Ensure `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`.

### Verification Commands
```powershell
# 1. Django System Checks
.venv\Scripts\python.exe manage.py check

# 2. Database Migration Consistency
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run

# 3. Backend Test Suite
.venv\Scripts\python.exe -m pytest -v

# 4. Frontend Type Checking
cd frontend && npx tsc --noEmit

# 5. Frontend Unit Tests
npm test -- --run

# 6. Production Frontend Build
npm run build
```
