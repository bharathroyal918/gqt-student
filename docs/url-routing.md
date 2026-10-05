# Canonical URL Routing & Endpoint Inventory — Phase 2

## 1. Overview & Architecture Standards

- **Canonical API Prefix:** `/api/v1/`
- **Root-Level Operational Endpoints:**
  - `GET /health/` — Top-level infrastructure health probe for reverse proxies and orchestrators.
  - `GET /certificates/verify/<identifier>/` — Public credential verification root entry point.
  - `GET /api/schema/`, `GET /api/docs/`, `GET /api/redoc/` — OpenAPI 3 interactive documentation.
- **Trailing Slash Policy:** Strictly enforced trailing slash (`/`) across all backend URL patterns, DRF views, Axios clients, and TanStack Query hooks.
- **Namespace Composition:** Predictable, non-colliding nested namespaces under `api_v1:<app_name>:<url_name>`.

---

## 2. Route Ownership & Application Namespace Table

| App Name | URL Prefix | URL Namespace (`api_v1:...`) | Domain Responsibility |
|---|---|---|---|
| `common` | `/api/v1/health/` | `api_v1` (Root) | Subsystem health checks (DB, Redis, Liveness, Readiness) |
| `accounts` | `/api/v1/auth/` | `api_v1:auth` | Login (Email/Mobile+OTP), Token refresh, Logout, Password recovery |
| `students` (Admin) | `/api/v1/admin/students/` | `api_v1:admin_students` | Admin student provisioning, status toggles, course assignments, rank/scores |
| `courses` (Admin) | `/api/v1/admin/courses/` | `api_v1:admin_courses` | Course catalog authoring and publication |
| `modules` (Admin) | `/api/v1/admin/modules/` | `api_v1:admin_modules` | 17 sequential topic reordering and publication |
| `assignments` (Admin) | `/api/v1/admin/assignments/` | `api_v1:admin_assignments`| Coding problem authoring, test case management (visible/hidden) |
| `tasks` (Admin) | `/api/v1/admin/tasks/` | `api_v1:admin_tasks` | Daily coding practice challenge scheduler |
| `projects` (Admin) | `/api/v1/admin/projects/` | `api_v1:admin_projects` | Capstone project authoring, submission grading, feedback remarks |
| `notifications` (Admin)| `/api/v1/admin/announcements/`| `api_v1:admin_announcements`| Broadcast announcement authoring and cohort targeting |
| `certificates` (Admin) | `/api/v1/admin/certificates/` | `api_v1:admin_certificates` | Certificate registry and revocation |
| `contact` (Admin) | `/api/v1/admin/contact/` | `api_v1:admin_contact` | Support desk inquiry resolution |
| `leaderboard` (Admin) | `/api/v1/admin/leaderboard/` | `api_v1:admin_leaderboard` | Cohort-wide and global leaderboard administrative queries |
| `analytics` (Admin) | `/api/v1/admin/` | `api_v1:admin_analytics` | Executive dashboards, domain reports, async CSV/PDF exports |
| `leaderboard` (Student)| `/api/v1/leaderboard/` | `api_v1:leaderboard` | Public/Cohort leaderboard ranking feeds and self rank |
| `contact` (Student) | `/api/v1/contact/` | `api_v1:contact` | Company info and student support inquiry ticket creation |
| `assignments` (Student)| `/api/v1/students/assignments/`| `api_v1:student_assignments`| Problem statements, Monaco Run (visible tests), Submit (hidden grading) |
| `tasks` (Student) | `/api/v1/students/tasks/` | `api_v1:student_tasks` | Daily challenge retrieval and completion lifecycle |
| `projects` (Student) | `/api/v1/students/projects/` | `api_v1:student_projects` | Capstone briefs, ZIP/GitHub submissions, file downloads |
| `ai_assistant` | `/api/v1/students/ai/` | `api_v1:ai_assistant` | Socratic AI tutor conversation threads, message exchange, retries |
| `notifications` (Student)| `/api/v1/students/notifications/`| `api_v1:notifications` | Categorized notifications feed, unread counters, mark-read |
| `certificates` (Student)| `/api/v1/students/` | `api_v1:certificates` | Student badge rack, certificate downloads, public verification |
| `students` (Student) | `/api/v1/students/` | `api_v1:students` | Student dashboard metrics, 17-topic roadmap, attendance, profile |

---

## 3. Comprehensive Route Inventory (All Endpoints)

### 3.1 Infrastructure & Operational Routes
| Method | Canonical Path | URL Name / Namespace | View Class | Auth Required | Permissions |
|---|---|---|---|---|---|
| `GET` | `/health/` | `health-check` | `HealthCheckView` | None | AllowAny |
| `GET` | `/health/live/` | `health-live` | `LivenessCheckView` | None | AllowAny |
| `GET` | `/health/ready/` | `health-ready` | `ReadinessCheckView` | None | AllowAny |
| `GET` | `/health/database/` | `health-database` | `DatabaseHealthCheckView` | None | AllowAny |
| `GET` | `/health/redis/` | `health-redis` | `RedisHealthCheckView` | None | AllowAny |
| `GET` | `/certificates/verify/<identifier>/` | `root_public_cert_verify` | `PublicCertificateVerifyView` | None | AllowAny |
| `GET` | `/api/v1/health/` | `api_v1:health-check` | `HealthCheckView` | None | AllowAny |
| `GET` | `/api/v1/health/live/` | `api_v1:health-live` | `LivenessCheckView` | None | AllowAny |
| `GET` | `/api/v1/health/ready/` | `api_v1:health-ready` | `ReadinessCheckView` | None | AllowAny |
| `GET` | `/api/v1/health/database/` | `api_v1:health-database` | `DatabaseHealthCheckView` | None | AllowAny |
| `GET` | `/api/v1/health/redis/` | `api_v1:health-redis` | `RedisHealthCheckView` | None | AllowAny |

---

### 3.2 Authentication & Session Lifecycle (`/api/v1/auth/`)
| Method | Canonical Path | URL Name / Namespace | View Class | Auth Required | Permissions |
|---|---|---|---|---|---|
| `POST` | `/api/v1/auth/register/` | `api_v1:auth:register` | `StudentRegisterView` | None | AllowAny |
| `POST` | `/api/v1/auth/login/student/` | `api_v1:auth:login_student` | `StudentLoginView` | None | AllowAny |
| `POST` | `/api/v1/auth/login/admin/` | `api_v1:auth:login_admin` | `AdminLoginView` | None | AllowAny |
| `POST` | `/api/v1/auth/login/email/` | `api_v1:auth:login_email` | `EmailLoginView` | None | AllowAny |
| `POST` | `/api/v1/auth/otp/request/` | `api_v1:auth:otp_request` | `RequestOTPView` | None | AllowAny (Rate Limited) |
| `POST` | `/api/v1/auth/otp/verify/` | `api_v1:auth:otp_verify` | `VerifyOTPView` | None | AllowAny |
| `POST` | `/api/v1/auth/token/refresh/` | `api_v1:auth:token_refresh` | `RefreshTokenView` | None | AllowAny |
| `POST` | `/api/v1/auth/logout/` | `api_v1:auth:logout` | `LogoutView` | Bearer JWT | IsAuthenticated |
| `GET` | `/api/v1/auth/me/` | `api_v1:auth:me` | `MeView` | Bearer JWT | IsAuthenticated |
| `POST` | `/api/v1/auth/password/forgot-otp/` | `api_v1:auth:password_forgot_otp`| `ForgotPasswordOTPRequestView` | None | AllowAny |
| `POST` | `/api/v1/auth/password/verify-reset-otp/`| `api_v1:auth:password_verify_reset_otp`| `ForgotPasswordOTPVerifyView` | None | AllowAny |
| `POST` | `/api/v1/auth/password/forgot/` | `api_v1:auth:password_forgot` | `ForgotPasswordView` | None | AllowAny |
| `POST` | `/api/v1/auth/password/reset/` | `api_v1:auth:password_reset` | `ResetPasswordView` | None | AllowAny |

---

### 3.3 Student Learning & Assessment Routes (`/api/v1/students/`)
| Method | Canonical Path | URL Name / Namespace | View Class | Auth Required | Permissions |
|---|---|---|---|---|---|
| `GET` | `/api/v1/students/dashboard/` | `api_v1:students:student_dashboard` | `StudentDashboardView` | Bearer JWT | IsStudentUser |
| `GET` | `/api/v1/students/leaderboard/` | `api_v1:students:student_leaderboard` | `StudentLeaderboardView` | Bearer JWT | IsStudentUser |
| `GET`, `PATCH` | `/api/v1/students/me/profile/` | `api_v1:students:student_profile_me` | `StudentProfileSelfUpdateView` | Bearer JWT | IsStudentUser |
| `GET` | `/api/v1/students/me/attendance/` | `api_v1:students:student_attendance_me` | `StudentAttendanceSelfView` | Bearer JWT | IsStudentUser |
| `GET` | `/api/v1/students/courses/` | `api_v1:students:student_courses` | `StudentCourseListView` | Bearer JWT | IsStudentUser |
| `GET` | `/api/v1/students/courses/<course_id>/` | `api_v1:students:student_course_detail` | `StudentCourseDetailView` | Bearer JWT | IsStudentUser |
| `GET` | `/api/v1/students/modules/<module_id>/` | `api_v1:students:student_module_detail` | `StudentModuleDetailView` | Bearer JWT | IsStudentUser (Prereq Gated) |
| `POST` | `/api/v1/students/modules/<module_id>/complete/`| `api_v1:students:student_module_complete`| `StudentModuleCompleteView` | Bearer JWT | IsStudentUser |
| `GET` | `/api/v1/students/assignments/questions/` | `api_v1:student_assignments:question_list` | `StudentQuestionListView` | Bearer JWT | IsStudentUser |
| `GET` | `/api/v1/students/assignments/questions/<id>/` | `api_v1:student_assignments:question_detail`| `StudentQuestionDetailView` | Bearer JWT | IsStudentUser |
| `POST` | `/api/v1/students/assignments/questions/<id>/run/` | `api_v1:student_assignments:code_run` | `StudentCodeRunView` | Bearer JWT | IsStudentUser |
| `POST` | `/api/v1/students/assignments/questions/<id>/submit/`| `api_v1:student_assignments:code_submit` | `StudentCodeSubmitView` | Bearer JWT | IsStudentUser |
| `GET` | `/api/v1/students/assignments/questions/<id>/submissions/`| `api_v1:student_assignments:submission_history`| `StudentSubmissionHistoryView`| Bearer JWT | IsStudentUser |
| `GET` | `/api/v1/students/assignments/submissions/<id>/` | `api_v1:student_assignments:submission_detail` | `StudentSubmissionDetailView` | Bearer JWT | IsStudentUser (Owner) |
| `GET` | `/api/v1/students/tasks/` | `api_v1:student_tasks:task_list` | `StudentTaskListView` | Bearer JWT | IsStudentUser |
| `GET` | `/api/v1/students/tasks/<id>/` | `api_v1:student_tasks:task_detail` | `StudentTaskDetailView` | Bearer JWT | IsStudentUser |
| `POST` | `/api/v1/students/tasks/<id>/complete/`| `api_v1:student_tasks:task_complete` | `StudentTaskCompleteView` | Bearer JWT | IsStudentUser |
| `GET` | `/api/v1/students/projects/` | `api_v1:student_projects:project_list` | `StudentProjectListView` | Bearer JWT | IsStudentUser |
| `GET` | `/api/v1/students/projects/<id>/` | `api_v1:student_projects:project_detail` | `StudentProjectDetailView` | Bearer JWT | IsStudentUser |
| `POST` | `/api/v1/students/projects/<id>/submit/` | `api_v1:student_projects:project_submit` | `StudentProjectSubmitView` | Bearer JWT | IsStudentUser |
| `GET` | `/api/v1/students/projects/files/<id>/download/`| `api_v1:student_projects:file_download` | `ProjectFileDownloadView` | Bearer JWT | IsAuthenticated |
| `GET`, `POST` | `/api/v1/students/ai/conversations/` | `api_v1:ai_assistant:conversation_list_create`| `StudentAIConversationListView`| Bearer JWT | IsStudentUser |
| `GET`, `DELETE`| `/api/v1/students/ai/conversations/<id>/` | `api_v1:ai_assistant:conversation_detail_archive`| `StudentAIConversationDetailView`| Bearer JWT | IsStudentUser (Owner) |
| `POST` | `/api/v1/students/ai/conversations/<id>/messages/`| `api_v1:ai_assistant:message_send` | `StudentAIMessageSendView` | Bearer JWT | IsStudentUser (Rate Limited) |
| `POST` | `/api/v1/students/ai/conversations/<id>/retry/` | `api_v1:ai_assistant:message_retry` | `StudentAIMessageRetryView` | Bearer JWT | IsStudentUser |
| `GET` | `/api/v1/students/notifications/` | `api_v1:notifications:notification_list`| `StudentNotificationListView` | Bearer JWT | IsStudentUser |
| `GET` | `/api/v1/students/notifications/unread-count/`| `api_v1:notifications:unread_count` | `StudentNotificationUnreadCountView`| Bearer JWT | IsStudentUser |
| `POST` | `/api/v1/students/notifications/<id>/read/`| `api_v1:notifications:mark_read` | `StudentNotificationMarkReadView`| Bearer JWT | IsStudentUser (Owner) |
| `POST` | `/api/v1/students/notifications/mark-all-read/`| `api_v1:notifications:mark_all_read` | `StudentNotificationMarkAllReadView`| Bearer JWT | IsStudentUser |
| `DELETE` | `/api/v1/students/notifications/<id>/` | `api_v1:notifications:delete_notification`| `StudentNotificationDeleteView`| Bearer JWT | IsStudentUser (Owner) |
| `GET` | `/api/v1/students/notifications/announcements/`| `api_v1:notifications:student_announcements`| `StudentAnnouncementListView` | Bearer JWT | IsStudentUser |
| `GET` | `/api/v1/students/achievements/` | `api_v1:certificates:student_badges` | `StudentBadgeListView` | Bearer JWT | IsStudentUser |
| `GET` | `/api/v1/students/certificates/` | `api_v1:certificates:student_certificates` | `StudentCertificateListView` | Bearer JWT | IsStudentUser |
| `GET` | `/api/v1/students/certificates/<id>/download/`| `api_v1:certificates:certificate_download`| `StudentCertificateDownloadView`| Bearer JWT | IsStudentUser (Owner) |
| `GET` | `/api/v1/students/verify/<identifier>/` | `api_v1:certificates:public_verify` | `PublicCertificateVerifyView` | None | AllowAny |

---

### 3.4 Admin Management Routes (`/api/v1/admin/`)
| Method | Canonical Path | URL Name / Namespace | View Class | Auth Required | Permissions |
|---|---|---|---|---|---|
| `GET`, `POST` | `/api/v1/admin/students/` | `api_v1:admin_students:list_create` | `StudentAdminListCreateView` | Bearer JWT | IsAdminUser |
| `POST` | `/api/v1/admin/students/provision/` | `api_v1:admin_students:provision` | `AdminStudentProvisionView` | Bearer JWT | IsAdminUser |
| `POST` | `/api/v1/admin/students/grant-access-by-email/`| `api_v1:admin_students:grant_access_by_email`| `StudentAdminGrantAccessByEmailView`| Bearer JWT | IsAdminUser |
| `GET`, `PATCH` | `/api/v1/admin/students/<id>/` | `api_v1:admin_students:detail_update` | `StudentAdminDetailUpdateView` | Bearer JWT | IsAdminUser |
| `PATCH` | `/api/v1/admin/students/<id>/status/` | `api_v1:admin_students:status` | `AdminStudentStatusView` | Bearer JWT | IsAdminUser |
| `POST` | `/api/v1/admin/students/<id>/grant-access/` | `api_v1:admin_students:grant_access` | `StudentAdminGrantAccessView` | Bearer JWT | IsAdminUser |
| `POST` | `/api/v1/admin/students/<id>/revoke-access/`| `api_v1:admin_students:revoke_access` | `StudentAdminRevokeAccessView` | Bearer JWT | IsAdminUser |
| `GET`, `POST` | `/api/v1/admin/students/<id>/attendance/`| `api_v1:admin_students:attendance` | `StudentAdminAttendanceView` | Bearer JWT | IsAdminUser |
| `GET`, `POST` | `/api/v1/admin/students/<id>/courses/` | `api_v1:admin_students:assign_courses` | `StudentAdminCoursesView` | Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/students/<id>/progress/` | `api_v1:admin_students:progress` | `StudentAdminProgressView` | Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/students/<id>/scores/` | `api_v1:admin_students:scores` | `StudentAdminScoresView` | Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/students/<id>/rank/` | `api_v1:admin_students:rank` | `StudentAdminRankView` | Bearer JWT | IsAdminUser |
| `GET`, `POST` | `/api/v1/admin/courses/` | `api_v1:admin_courses:list_create` | `CourseAdminListCreateView` | Bearer JWT | IsAdminUser |
| `GET`, `PATCH`, `DELETE`| `/api/v1/admin/courses/<id>/` | `api_v1:admin_courses:detail_update_delete`| `CourseAdminDetailUpdateDeleteView`| Bearer JWT | IsAdminUser |
| `POST` | `/api/v1/admin/courses/<id>/publish/` | `api_v1:admin_courses:publish` | `CourseAdminPublishView` | Bearer JWT | IsAdminUser |
| `GET`, `POST` | `/api/v1/admin/modules/` | `api_v1:admin_modules:list_create` | `ModuleAdminListCreateView` | Bearer JWT | IsAdminUser |
| `POST` | `/api/v1/admin/modules/reorder/` | `api_v1:admin_modules:reorder` | `ModuleAdminReorderView` | Bearer JWT | IsAdminUser |
| `GET`, `PATCH` | `/api/v1/admin/modules/<id>/` | `api_v1:admin_modules:detail_update` | `ModuleAdminDetailUpdateView` | Bearer JWT | IsAdminUser |
| `POST` | `/api/v1/admin/modules/<id>/publish/` | `api_v1:admin_modules:publish` | `ModuleAdminPublishView` | Bearer JWT | IsAdminUser |
| `GET`, `POST` | `/api/v1/admin/assignments/questions/` | `api_v1:admin_assignments:question_list_create`| `CodingQuestionAdminListCreateView`| Bearer JWT | IsAdminUser |
| `GET`, `PATCH`, `DELETE`| `/api/v1/admin/assignments/questions/<id>/`| `api_v1:admin_assignments:question_detail_update_delete`| `CodingQuestionAdminDetailUpdateDeleteView`| Bearer JWT | IsAdminUser |
| `POST` | `/api/v1/admin/assignments/questions/<id>/testcases/`| `api_v1:admin_assignments:testcase_create`| `TestCaseAdminCreateView` | Bearer JWT | IsAdminUser |
| `GET`, `PATCH`, `DELETE`| `/api/v1/admin/assignments/testcases/<id>/`| `api_v1:admin_assignments:testcase_detail_update_delete`| `TestCaseAdminDetailUpdateDeleteView`| Bearer JWT | IsAdminUser |
| `GET`, `POST` | `/api/v1/admin/tasks/` | `api_v1:admin_tasks:list_create` | `TaskAdminListCreateView` | Bearer JWT | IsAdminUser |
| `GET`, `PATCH`, `DELETE`| `/api/v1/admin/tasks/<id>/` | `api_v1:admin_tasks:detail_update_delete`| `TaskAdminDetailUpdateDeleteView` | Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/tasks/<id>/completions/` | `api_v1:admin_tasks:completions` | `TaskAdminCompletionsView` | Bearer JWT | IsAdminUser |
| `GET`, `POST` | `/api/v1/admin/projects/` | `api_v1:admin_projects:project_list_create`| `ProjectAdminListCreateView` | Bearer JWT | IsAdminUser |
| `GET`, `PATCH` | `/api/v1/admin/projects/<id>/` | `api_v1:admin_projects:project_detail_update`| `ProjectAdminDetailUpdateView` | Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/projects/submissions/` | `api_v1:admin_projects:submission_list` | `ProjectSubmissionAdminListView`| Bearer JWT | IsAdminUser |
| `GET`, `POST` | `/api/v1/admin/projects/submissions/<id>/`| `api_v1:admin_projects:submission_detail_review`| `ProjectSubmissionAdminDetailReviewView`| Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/projects/submissions/<id>/files/`| `api_v1:admin_projects:submission_files`| `ProjectSubmissionFilesView` | Bearer JWT | IsAdminUser |
| `GET`, `POST` | `/api/v1/admin/announcements/` | `api_v1:admin_announcements:list_create`| `AnnouncementAdminListCreateView`| Bearer JWT | IsAdminUser |
| `GET`, `PATCH`, `DELETE`| `/api/v1/admin/announcements/<id>/`| `api_v1:admin_announcements:detail_update_delete`| `AnnouncementAdminDetailUpdateDeleteView`| Bearer JWT | IsAdminUser |
| `POST` | `/api/v1/admin/announcements/<id>/publish/`| `api_v1:admin_announcements:publish` | `AnnouncementAdminPublishView` | Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/announcements/<id>/audit/`| `api_v1:admin_announcements:audit_history`| `AnnouncementAdminAuditHistoryView`| Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/certificates/` | `api_v1:admin_certificates:list` | `AdminCertificateListView` | Bearer JWT | IsAdminUser |
| `POST` | `/api/v1/admin/certificates/<id>/revoke/`| `api_v1:admin_certificates:revoke` | `AdminCertificateRevokeView` | Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/contact/inquiries/` | `api_v1:admin_contact:inquiry_list` | `AdminContactInquiryListView` | Bearer JWT | IsAdminUser |
| `GET`, `PATCH` | `/api/v1/admin/contact/inquiries/<id>/` | `api_v1:admin_contact:inquiry_detail` | `AdminContactInquiryDetailView` | Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/leaderboard/` | `api_v1:admin_leaderboard:admin_leaderboard_list`| `AdminLeaderboardListView` | Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/analytics/dashboard/` | `api_v1:admin_analytics:dashboard` | `AnalyticsDashboardView` | Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/reports/performance/` | `api_v1:admin_analytics:report_performance`| `ReportPerformanceView` | Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/reports/completion/` | `api_v1:admin_analytics:report_completion` | `ReportCompletionView` | Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/reports/assignment/` | `api_v1:admin_analytics:report_assignment` | `ReportAssignmentView` | Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/reports/project/` | `api_v1:admin_analytics:report_project` | `ReportProjectView` | Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/reports/monthly-activity/`| `api_v1:admin_analytics:report_monthly_activity`| `ReportMonthlyActivityView` | Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/reports/exports/` | `api_v1:admin_analytics:export_list` | `ReportExportListView` | Bearer JWT | IsAdminUser |
| `POST` | `/api/v1/admin/reports/export/` | `api_v1:admin_analytics:export_create` | `ReportExportCreateView` | Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/reports/exports/<job_id>/`| `api_v1:admin_analytics:export_detail` | `ReportExportDetailView` | Bearer JWT | IsAdminUser |
| `GET` | `/api/v1/admin/reports/exports/<job_id>/download/`| `api_v1:admin_analytics:export_download`| `ReportExportDownloadView` | Bearer JWT | IsAdminUser |
