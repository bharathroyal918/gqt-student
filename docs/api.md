# REST API Design & Complete Contract Specifications

## 1. API Architecture Principles

- **Base URI & Versioning:** All endpoints are strictly versioned under `/api/v1/`
- **Transport Security:** Strict HTTPS (TLS 1.3) with HSTS headers.
- **Content Type:** JSON payloads (`Content-Type: application/json; charset=utf-8`).
- **Authentication:** Dual bearer token format (`Authorization: Bearer <access_jwt>`).
- **Standardized Envelopes:** Every single endpoint response conforms to predictable JSON envelopes.
- **Server-Side Filtering & Pagination:** All data tables (Students, Assignments, Tasks, Certificates, Inquiries, Notifications) execute search, filtering, and pagination on the backend.

---

## 2. Standard Response Envelopes

### 2.1 Single Resource Envelope
```json
{
  "success": true,
  "data": {
    "id": "e6a2b37c-9b1c-4b52-bbf1-8a9d12345678",
    "title": "1. Data Types & Variables",
    "order_index": 1,
    "status": "UNLOCKED"
  },
  "meta": {
    "timestamp": "2026-10-03T09:40:00Z"
  }
}
```

### 2.2 Paginated List Envelope
```json
{
  "success": true,
  "data": [
    {
      "id": "d9812450-4d51-419b-a05e-85a228399581",
      "student_id_number": "GQT-2026-001",
      "full_name": "Rahul Sharma",
      "email": "rahul.sharma@example.com",
      "batch_code": "BATCH-2026-A",
      "institution_name": "National Institute of Technology",
      "total_points": "200.00",
      "enrolled_courses_count": 2,
      "status": "ACTIVE",
      "is_active": true
    }
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_records": 120,
      "total_pages": 6,
      "has_next": true,
      "has_prev": false
    },
    "timestamp": "2026-10-03T09:40:00Z"
  }
}
```

### 2.3 Error Envelope
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "The provided payload failed schema validation.",
    "details": {
      "batch_code": ["Cohort batch 'BATCH-2026-Z' does not exist or is inactive."]
    },
    "request_id": "req-987abc-54321"
  },
  "meta": {
    "timestamp": "2026-10-03T09:40:00Z"
  }
}
```

---

## 3. Comprehensive Endpoint Specifications

### 3.1 Authentication & Session Context (`/api/v1/auth/`)

| Method | Endpoint | Description | Query / Body Parameters | Role Required |
|---|---|---|---|---|
| `POST` | `/api/v1/auth/login/email/` | Authenticate with Email & Password | Body: `{ email, password }` | None |
| `POST` | `/api/v1/auth/otp/send/` | Request 6-digit login OTP to mobile | Body: `{ mobile_number }` | None (Rate limit: 3/hr) |
| `POST` | `/api/v1/auth/otp/verify/` | Verify OTP code & receive JWT tokens | Body: `{ mobile_number, otp_code }` | None |
| `POST` | `/api/v1/auth/refresh/` | Exchange refresh token for fresh access token | Body: `{ refresh }` | None |
| `POST` | `/api/v1/auth/logout/` | Blacklist refresh token & terminate session | Body: `{ refresh }` | Bearer JWT |
| `GET` | `/api/v1/auth/me/` | Fetch authenticated user profile & role | Header: Bearer JWT | Authenticated |

---

### 3.2 Student Global Header & Summary (`/api/v1/students/`)

| Method | Endpoint | Description | Query / Response Summary | Role Required |
|---|---|---|---|---|
| `GET` | `/api/v1/students/summary/` | Authoritative header summary (Points, Streak, Batch, Notifications) | Returns: `{ student_id, full_name, avatar_url, batch_code, total_points: "200.00", current_streak_days: 5, unread_notifications: 3 }` | STUDENT |
| `GET` | `/api/v1/students/streak/` | Full streak statistics & calendar history | Returns: `{ current_streak: 5, highest_streak: 14, last_activity_date: "2026-10-02", active_today: true, history: [...] }` | STUDENT |
| `GET` | `/api/v1/students/me/` | Get student profile details (College, Batch, Graduation Year) | Returns full student profile DTO | STUDENT |
| `PATCH`| `/api/v1/students/me/` | Update editable student profile fields | Body: `{ avatar_url, graduation_year }` (Administrative fields locked) | STUDENT |

---

### 3.3 Admin Student Management & Provisioning (`/api/v1/admin/students/`)

| Method | Endpoint | Description | Query / Body Parameters | Role Required |
|---|---|---|---|---|
| `GET` | `/api/v1/admin/students/` | Server-paginated student table with search & filter | Query: `?page=1&page_size=20&search=Rahul&batch=BATCH-2026-A&status=ACTIVE&access_status=ACTIVE` | ADMIN |
| `POST` | `/api/v1/admin/students/onboard/` | Provision new student record | Body: `{ email, mobile_number, full_name, student_id_number, batch_id, institution_id, initial_course_id, send_invitation_email: true }` | ADMIN |
| `GET` | `/api/v1/admin/students/{id}/` | 360° student academic detail view | Returns full dossier: Profile, College, Batch, Courses, Module Progress, Scores, Submissions, Tasks, Certificates | ADMIN |
| `PATCH`| `/api/v1/admin/students/{id}/access/` | Toggle student portal access status | Body: `{ is_active: false, onboarding_status: "SUSPENDED", reason: "Tuition Hold" }` | ADMIN |
| `POST` | `/api/v1/admin/students/{id}/reset-password/` | Trigger secure password reset link | Body: `{ send_email: true }` | ADMIN |
| `GET` | `/api/v1/admin/batches/` | List all cohort batches for dropdowns | Returns: `[{ id, batch_code, name, academic_period, is_active }]` | ADMIN |
| `GET` | `/api/v1/admin/institutions/` | List all colleges / institutions for dropdowns | Returns: `[{ id, name, code, city, is_active }]` | ADMIN |

---

### 3.4 Courses, Roadmaps & Progression (`/api/v1/courses/`)

| Method | Endpoint | Description | Query / Response Summary | Role Required |
|---|---|---|---|---|
| `GET` | `/api/v1/courses/` | List all courses with student enrollment status | Returns: `[{ id, title, slug, description, thumbnail_url, enrollment_status: "ACTIVE", progress_percentage: 45.0, completed_modules: 7, total_modules: 17 }]` | STUDENT / ADMIN |
| `GET` | `/api/v1/courses/{id}/` | Get course syllabus & overview | Returns course detail and module list | Authenticated |
| `GET` | `/api/v1/courses/{id}/roadmap/` | 17 Sequential Modules with lock/completed states | Returns: `[{ id, order_index: 1, title: "1. Data Types", status: "COMPLETED", score: 95.0 }, { order_index: 2, status: "UNLOCKED" }, { order_index: 3, status: "LOCKED" }]` | STUDENT |
| `GET` | `/api/v1/courses/{id}/continue/` | Compute deep link to active learning location | Returns: `{ course_id, current_module_id, current_activity_type: "ASSIGNMENT", activity_id: "...", resume_route: "/courses/.../modules/..." }` | STUDENT |
| `POST` | `/api/v1/admin/modules/{id}/override-unlock/` | Administrative override to unlock a module | Body: `{ student_id, reason: "Prerequisite tested out" }` | ADMIN |

---

### 3.5 Algorithmic Coding & Sandboxed Assessment (`/api/v1/assignments/`)

| Method | Endpoint | Description | Query / Body Parameters | Role Required |
|---|---|---|---|---|
| `GET` | `/api/v1/assignments/` | List coding problems for module/course | Query: `?module_id=...&difficulty=MEDIUM` | Authenticated |
| `GET` | `/api/v1/assignments/{id}/` | Get problem brief, starter code & visible testcases | Returns question statement, languages, starter code, visible tests (Hidden tests hidden from student) | Authenticated |
| `POST` | `/api/v1/assignments/{id}/run/` | Execute code against visible sample testcases | Body: `{ language: "python", source_code: "..." }` -> Synchronous/Quick execution | STUDENT |
| `POST` | `/api/v1/assignments/{id}/submit/` | Submit final code for official grading | Body: `{ language: "python", source_code: "..." }` -> Returns 202 Accepted `{ submission_id, status: "PENDING" }` | STUDENT |
| `GET` | `/api/v1/assignments/submissions/{id}/` | Poll submission execution status & test results | Returns: `{ id, status: "ACCEPTED", passed_cases: 4, total_cases: 4, score_awarded: "100.00", visible_results: [...] }` | Authenticated (Owner / Admin) |
| `GET` | `/api/v1/admin/assignments/` | Admin coding problem table | Query: `?search=Array&difficulty=HARD&status=ACTIVE` | ADMIN |
| `POST` | `/api/v1/admin/assignments/` | Author new coding problem with testcases | Body: `{ title, module_id, difficulty, points, problem_statement, testcases: [{ input, output, is_visible, weight }] }` | ADMIN |
| `PATCH`| `/api/v1/admin/assignments/{id}/` | Edit problem metadata or archive | Body: `{ is_active: false, points: 150.00 }` | ADMIN |

---

### 3.6 Daily Tasks (`/api/v1/tasks/`)

| Method | Endpoint | Description | Query / Body Parameters | Role Required |
|---|---|---|---|---|
| `GET` | `/api/v1/tasks/` | List daily challenges with server-side filter | Query: `?filter=all` / `?filter=pending` / `?filter=completed` & `?search=String` | STUDENT |
| `GET` | `/api/v1/tasks/today/` | Fetch current date's active challenge | Returns: `{ id, title, description, points: 20.00, is_completed: false, question_id: "..." }` | STUDENT |
| `POST` | `/api/v1/tasks/{id}/complete/` | Complete daily task & trigger streak increment | Body: `{ submission_id: "..." }` (Atomic verification) | STUDENT |

---

### 3.7 Cohort Leaderboard (`/api/v1/leaderboard/`)

| Method | Endpoint | Description | Query / Response Summary | Role Required |
|---|---|---|---|---|
| `GET` | `/api/v1/leaderboard/cohort/` | Cohort-scoped leaderboard with Top-3 spotlight | Query: `?batch_code=BATCH-2026-A` Returns: `{ top_3: [...], current_student_rank: 4, current_student_points: "200.00", rankings: [{ rank: 1, name: "...", points: "250.00", is_current_user: false }, { rank: 4, name: "Rahul Sharma", is_current_user: true }] }` | Authenticated |
| `GET` | `/api/v1/leaderboard/global/` | Global platform-wide leaderboard | Query: `?page=1&page_size=50` | Authenticated |

---

### 3.8 Notification Center (`/api/v1/notifications/`)

| Method | Endpoint | Description | Query / Body Parameters | Role Required |
|---|---|---|---|---|
| `GET` | `/api/v1/notifications/` | Categorized notification feed | Query: `?category=ALL_ALERTS` / `ANNOUNCEMENTS` / `DEADLINES_TASKS` / `GRADES_PROJECTS` / `ACHIEVEMENTS` & `?unread_only=true` | STUDENT / ADMIN |
| `GET` | `/api/v1/notifications/unread-count/` | Lightweight unread badge counter | Returns: `{ unread_count: 3 }` | STUDENT / ADMIN |
| `POST` | `/api/v1/notifications/{id}/read/` | Mark specific notification as read | Returns 200 OK `{ id, is_read: true }` | Authenticated (Owner) |
| `POST` | `/api/v1/notifications/mark-all-read/`| Mark all notifications as read | Returns 200 OK `{ updated_count: 3 }` | Authenticated |
| `POST` | `/api/v1/admin/announcements/` | Publish targeted broadcast announcement | Body: `{ title, content, target_batch_id: "...", priority: "HIGH" }` | ADMIN |

---

### 3.9 Analytics & Score History (`/api/v1/analytics/`)

| Method | Endpoint | Description | Query / Response Summary | Role Required |
|---|---|---|---|---|
| `GET` | `/api/v1/analytics/score-history/` | 7-day timestamped score history & live trend | Returns: `{ live_points: 200.0, trend: [{ date: "2026-09-27", points: 40 }, ..., { date: "2026-10-03", points: 200 }] }` | STUDENT |
| `GET` | `/api/v1/analytics/skills-matrix/` | Multi-axis skills mastery matrix percentage | Returns: `{ skills: [{ name: "Data Structures", score: 85 }, { name: "Algorithms", score: 72 }, { name: "Java Full Stack", score: 90 }, { name: "Database Design", score: 65 }] }` | STUDENT |
| `GET` | `/api/v1/admin/analytics/overview/` | Platform-wide KPI aggregations | Query: `?batch=BATCH-2026-A&date_from=2026-09-01&date_to=2026-10-03` | ADMIN |
| `POST` | `/api/v1/admin/reports/export/` | Asynchronous CSV/PDF report generator | Body: `{ report_type: "COHORT_PERFORMANCE", batch_id: "...", format: "CSV" }` -> Returns 202 Accepted `{ job_id }` | ADMIN |

---

### 3.10 Certificates & Public Verification (`/api/v1/certificates/`)

| Method | Endpoint | Description | Query / Response Summary | Role Required |
|---|---|---|---|---|
| `GET` | `/api/v1/admin/certificates/` | Admin certificate search registry | Query: `?search=Rahul&status=ACTIVE&course_id=...` | ADMIN |
| `GET` | `/api/v1/certificates/my-certificates/` | Student earned certificate cards | Returns list of verified certificates with verification hashes | STUDENT |
| `GET` | `/api/v1/certificates/verify/{hash}/` | Public cryptographic certificate verification | Safe public response: `{ valid: true, certificate_id: "GQT-CERT-2026-A109", student_name: "Rahul S.****", course_title: "Java Full Stack", issue_date: "2026-10-01" }` | Public |

---

### 3.11 Support Inquiries & Tickets (`/api/v1/contact/`)

| Method | Endpoint | Description | Query / Body Parameters | Role Required |
|---|---|---|---|---|
| `GET` | `/api/v1/contact/inquiries/` | List student's submitted support tickets | Returns list of tickets with current status (`OPEN`, `IN_REVIEW`, `RESOLVED`, `CLOSED`) | STUDENT |
| `POST` | `/api/v1/contact/inquiries/` | Submit new support inquiry ticket | Body: `{ category: "COURSE_ENROLLMENT", subject: "Inquiry on Spring Framework", message: "..." }` (Student identity injected from JWT) | STUDENT |
| `GET` | `/api/v1/admin/contact/inquiries/` | Admin support desk ticket management | Query: `?status=OPEN&category=COURSE_ENROLLMENT` | ADMIN |
| `PATCH`| `/api/v1/admin/contact/inquiries/{id}/` | Update ticket status and resolution notes | Body: `{ status: "RESOLVED", admin_response: "Access unlocked." }` | ADMIN |
