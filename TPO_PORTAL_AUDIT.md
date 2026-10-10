# GQT Student Portal — TPO Portal Integration Audit (Phase 1)

**Audit Date:** October 2026  
**Environment:** Production-Oriented React + TypeScript (Vite), Django 6.1.1 + DRF 3.15, Supabase (PostgreSQL) / SQLite (Dev)  
**Author:** AI Architecture & Security Review Team  
**Scope:** Phase 1 Comprehensive Baseline, Architectural Audit, College Relationship Mapping & Gap Analysis  

---

## 1. Executive Summary

The GQT Student Portal currently operates as a dual-portal platform (Administrator and Student) supporting student profile management, curriculum progression, sandboxed code execution, gamified scoring, streak tracking, attendance logging, and analytics reporting. 

To enable institutional partners (Training and Placement Officers — **TPO**) to monitor and support student performance, we conducted a comprehensive system audit. The purpose of this audit is to evaluate existing models, authentication mechanisms, authorization boundaries, database schemas, and frontend architectures to establish a safe, zero-leakage foundation for the **TPO Portal**.

---

## 2. Current Repository Architecture & Baseline

### 2.1 Backend Structure & Application Modules

The Django application is structured under `backend/apps/` with modular separation:

| Module / App | Primary Role | Key Models | Reusability for TPO |
| :--- | :--- | :--- | :--- |
| **`accounts`** | User identities, auth (JWT, OTP), profiles, audit trails | `User`, `AdminProfile`, `LoginActivity`, `OTPVerification`, `AuditLog` | **High**: Extend `User.RoleChoices` with `TPO`; add `TPOProfile`. |
| **`students`** | Student academic profiles, colleges, attendance | `College`, `StudentProfile`, `AttendanceRecord` | **High**: College canonical entity and student records exist here. |
| **`courses`** | Course catalog, enrollments, recorded classes | `Course`, `CourseEnrollment`, `RecordedClass`, `StudentRecordedClassProgress` | **High**: Reuse course progress queries scoped by college. |
| **`modules`** | Sequential syllabus modules, prerequisites, module progress | `Module`, `ModulePrerequisite`, `StudentModuleProgress` | **High**: Scoped curriculum completion metrics. |
| **`assignments`** | Algorithmic challenges, test cases, code submissions, progress | `CodingQuestion`, `TestCase`, `CodeSubmission`, `ExecutionResult`, `StudentQuestionProgress` | **High**: Read-only submission stats, pass rates, question progress. |
| **`scoring`** | Points ledger, audit logs, daily leaderboard snapshots | `ScoreRecord`, `ScoreEvent`, `LeaderboardSnapshot` | **High**: Verified score aggregation. |
| **`leaderboard`** | High-performance cached ranking service | *(Service-driven over `StudentProfile`)* | **High**: Adapt `LeaderboardService` for college-isolated rankings. |
| **`analytics`** | Aggregated telemetry, event logging, background export jobs | `ActivityEvent`, `DailyStudentAnalytics`, `ExportJob` | **High**: Export pipeline & metrics computation. |
| **`placements`** | Placement drives, job opportunities, applications | `PlacementDrive`, `PlacementApplication` | **High**: Read-only view for college student placement status. |
| **`notifications`**| System announcements, direct notifications | `Announcement`, `Notification` | **Medium**: Can deliver college-specific broadcast notices. |
| **`certificates`** | Student course completion certificates | `Certificate`, `CertificateVerification` | **Medium**: College student credential tracking. |
| **`common`** | Base models, permission classes, pagination, exception handling | `BaseModel`, `IsAdmin`, `IsStudent`, `IsOwnerOrAdmin` | **High**: Add `IsTPO`, `IsTPOOrAdmin`, college scoping utils. |

---

### 2.2 Baseline System Check & Test Execution Results

All baseline diagnostics were executed on the active codebase.

#### A. Django System Checks
- **Command:** `python manage.py check`
- **Result:** Code 0 with 2 system URL warnings:
  ```text
  WARNINGS:
  ?: (urls.W005) URL namespace 'api_v1:admin_students' isn't unique.
  ?: (urls.W005) URL namespace 'api_v1:students' isn't unique.
  ```
- **Root Cause:** In `backend/config/urls.py`, `apps.students.urls` and `apps.students.admin_urls` are included under both `colleges/` and `students/` prefixes, registering the same namespace twice.

#### B. Django Migrations Consistency
- **Command:** `python manage.py makemigrations --check --dry-run`
- **Result:** `No changes detected` (database schema is fully synchronized with migrations up to `0005_college_studentprofile_college`).

#### C. Backend Pytest Test Suite
- **Command:** `pytest`
- **Collected:** 236 test cases across 37 test modules.
- **Passed:** **234 passed**
- **Failed:** **2 failed** (0 errors)
- **Failure Details:**
  - `apps/common/tests/test_url_routing.py::URLRoutingAndNamespaceTests::test_admin_routes_reverse`
  - `apps/common/tests/test_url_routing.py::URLRoutingAndNamespaceTests::test_student_routes_reverse`
  - Both failures stem from the namespace collision documented above where `reverse("api_v1:students:student_dashboard")` resolved to `/api/v1/colleges/dashboard/` instead of `/api/v1/students/dashboard/`.

#### D. Frontend TypeScript Type Checking
- **Command:** `npx tsc --noEmit`
- **Result:** **Clean pass (0 errors)**.

#### E. Frontend Unit Test Suite
- **Command:** `npm test -- --run` (Vitest v1.6.1)
- **Result:** **12 passed across 3 test files** (`validation.test.ts`, `dashboard.test.ts`, `authStore.test.ts`).

#### F. Frontend Production Build
- **Command:** `npm run build` (`tsc && vite build`)
- **Result:** **Success (14.39s)**, all 65+ lazy-loaded route bundles compiled with zero bundle errors.

---

## 3. Existing College Data Mapping Findings

### 3.1 College Entities
- A `College` model exists in `apps/students/models.py` with fields: `id (UUID)`, `name`, `code`, `city`, `state`, `is_active`, `created_at`, `updated_at`.
- 20 institutional colleges are pre-seeded in the database (e.g., *Bangalore Institute of Technology (BIT)*, *BMS College of Engineering (BMSCE)*, *R.V. College of Engineering (RVCE)*, etc.).
- Admin CRUD endpoints exist at `/api/v1/admin/colleges/` (managed via `CollegeAdminListCreateView` and `CollegeAdminDetailUpdateDeleteView`).

### 3.2 Student-to-College Relationships in Active Database
- `StudentProfile` contains both:
  1. `college = ForeignKey(College, on_delete=SET_NULL, null=True, blank=True, related_name="students")`
  2. `college_name = CharField(max_length=255, blank=True, default="")` (legacy text field)
- **Data Audit of Current Database:**
  - Total student profiles: 7
  - Profiles with verified `college` ForeignKey: **0**
  - Profiles with non-empty `college_name` string: **5**
  - Profiles with missing/empty college data: **2**
- **Current Serialization Issue:** `StudentAdminSerializer` and `StudentProfileUpdateSerializer` write and read `college_name` text rather than linking `college_id`.

---

## 4. Security & Isolation Risk Analysis

| Risk Area | Threat / Vulnerability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Cross-College Student Exposure (IDOR)** | TPO manipulates `student_id` or query parameters to access students from another college. | High (Privacy violation) | Derive college scope strictly from `request.user.tpo_profile.college_id`. Never trust client-supplied college parameters. |
| **Ambiguous / Unassigned Students** | Students with `college=NULL` or legacy string `college_name` being accidentally returned or guessed. | Medium | Hard filter: TPO queries use `student__college_id=tpo_college_id`. Unlinked students are invisible to TPOs until verified by Admin. |
| **Privilege Escalation** | TPO attempting to access Admin endpoints or modify student grades/attendance. | High | Strict `IsTPO` permission class; TPO views are strictly read-only (`ReadOnlyModelViewSet` or `GET`-only APIViews). |
| **Cached Leaderboard Leakage** | Global leaderboard cache returning mixed college student data to a TPO. | Medium | Partition leaderboard cache keys by college ID: `leaderboard_top10_college_{college_id}`. |
| **Revocation Invalidation** | Deactivated TPO continues using valid JWT access token. | High | TPO permission class verifies `request.user.is_active` AND `request.user.tpo_profile.is_active` on **every** authenticated request. |
| **Direct DB Connection from Client** | Frontend connecting directly to Supabase with service keys. | Critical | Frontend communicates exclusively through Django REST API endpoints with JWT bearer authentication. |

---

## 5. Architectural Recommendations

1. **Canonical College ForeignKey:** Unify all student college associations around `StudentProfile.college_id`. Provide a safe, non-destructive migration script to link existing `college_name` strings to active `College` records.
2. **Dedicated TPO App / Module Structure:** Implement `TPOProfile` in `apps/accounts` and dedicated TPO endpoints under a dedicated URL namespace (`api_v1:tpo:*`).
3. **Dedicated TPO Frontend Portal:** Create a dedicated route prefix `/tpo/*` with `TPORouteGuard`, `TPOLayout`, and responsive role-specific dashboards.
4. **Fix Existing URL Namespace Collision:** Clean up `config/urls.py` routing definitions to eliminate the 2 baseline test failures.

---

## 6. Audit Conclusion & Phase 1 Completion Gate

Phase 1 audit is complete. All existing models, services, serializers, test baselines, and database records have been analyzed. The team is ready for Phase 2 once the design specifications are reviewed and approved.
