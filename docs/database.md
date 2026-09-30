# Database Architecture, Schema Specifications & Domain Layer

## 1. Overview & Source of Truth Architecture

The **GQT Student Learning and Coding Assessment Platform** uses **PostgreSQL 16** and the **Django ORM** as the authoritative relational persistence engine.

To prevent conflicting states, state drift, and split-brain scoring, the architecture establishes strict, non-redundant **Sources of Truth**:

| Business Domain | Authoritative Single Source of Truth | Mechanism & Aggregation Rule |
|---|---|---|
| **Assignment Score** | `apps.assignments.StudentQuestionProgress` & `apps.scoring.ScoreRecord` (`source_type="ASSIGNMENT"`) | The highest valid score achieved across non-redundant student submissions for that question. Recorded as an immutable `ScoreRecord`. |
| **Project Score** | `apps.projects.ProjectSubmission.score` & `apps.scoring.ScoreRecord` (`source_type="PROJECT"`) | The evaluated grade assigned by an administrative reviewer in `ProjectSubmission`, mirrored into `ScoreRecord`. |
| **Overall Student Score** | `apps.scoring.ScoreRecord` (with materialized cache in `apps.students.StudentProfile.total_points`) | The canonical sum of all verified `ScoreRecord` entries. `StudentProfile.total_points` serves as an indexed, materialized cache to allow sub-millisecond leaderboard ordering. |
| **Module Completion & Unlock** | `apps.modules.StudentModuleProgress` | Computed when a student achieves the module's `passing_percentage` (default 80%) across its questions, or via explicit administrative override. Unlocks module $N+1$. |
| **Leaderboard Rank** | Dynamic database query (and Redis Sorted Set cache), archived via `apps.scoring.LeaderboardSnapshot` | Calculated dynamically via `ORDER BY total_points DESC, current_streak_days DESC, updated_at ASC`. Frozen periodic daily point-in-time snapshots stored in `LeaderboardSnapshot`. |

---

## 2. Core Architectural Conventions

- **Primary Keys:** Every domain model inherits from `apps.common.models.UUIDModel`, generating cryptographically secure UUIDv4 identifiers (`uuid.uuid4`).
- **Timestamps:** Models inherit from `apps.common.models.TimeStampedModel`, providing indexed `created_at` and `updated_at`.
- **Soft Deletion:** Implemented selectively on entities where historical audit trails must survive administrative removal (e.g., `Course.is_deleted`, `CodingQuestion.is_active`, `Project.is_active`). Hard deletions are prevented where academic work has been submitted.
- **Precision Score Arithmetic:** All scoring, point totals, weights, and thresholds use `DecimalField(max_digits=..., decimal_places=2)` to prevent floating-point inaccuracy.
- **Explicit Choice Enums:** All workflow and state fields use `models.TextChoices`.

---

## 3. Entity Specifications by Domain

### 3.1 Authentication Domain (`apps/accounts`)

#### `User`
Primary identity model supporting both Email + Password and Mobile + OTP logins.
- `id`: UUID (PK)
- `email`: EmailField, unique, nullable, indexed
- `mobile_number`: CharField, unique, nullable, indexed
- `role`: TextChoices [`ADMIN`, `STUDENT`], indexed
- `onboarding_status`: TextChoices [`PENDING_ACTIVATION`, `ACTIVE`, `SUSPENDED`], indexed
- `is_active`: BooleanField, indexed
- `last_login_ip`: GenericIPAddressField, nullable
- **Indexes:** `[email, is_active]`, `[mobile_number, is_active]`, `[role, is_active]`
- **Validation:** Clean method enforces that either email or mobile number must be provided.

#### `Role`
Granular permission matrix for platform administrators.
- `name`: CharField(50), unique
- `permissions`: JSONField (default: dict)

#### `LoginActivity`
Immutable audit log of all authentication events.
- `user`: FK -> `User`, null=True, on_delete=SET_NULL
- `identifier`: CharField (email or mobile attempted)
- `login_type`: TextChoices [`EMAIL_PASSWORD`, `MOBILE_OTP`, `TOKEN_REFRESH`]
- `status`: TextChoices [`SUCCESS`, `FAILED_CREDENTIALS`, `FAILED_OTP`, `LOCKED`]
- `ip_address`: GenericIPAddressField, nullable, indexed
- `user_agent`: TextField
- `failure_reason`: CharField
- **Indexes:** `[user, created_at]`, `[ip_address, created_at]`, `[status, created_at]`

#### `OTPVerification`
Manages cryptographically secure OTP lifecycles.
- `user`: FK -> `User`, null=True, on_delete=CASCADE
- `mobile_number`: CharField, indexed
- `otp_hash`: CharField(128) (secure hash of OTP code)
- `purpose`: TextChoices [`LOGIN`, `PASSWORD_RESET`, `PHONE_VERIFY`]
- `attempts`: PositiveSmallIntegerField (default: 0)
- `max_attempts`: PositiveSmallIntegerField (default: 5)
- `is_used`: BooleanField (default: False, indexed)
- `expires_at`: DateTimeField, indexed
- **Constraints:** `CheckConstraint(attempts <= max_attempts)`
- **Indexes:** `[mobile_number, is_used, expires_at]`

#### `PasswordResetRequest`
Tokenized password reset tracking.
- `user`: FK -> `User`, on_delete=CASCADE
- `token_hash`: CharField(128), unique, indexed
- `expires_at`: DateTimeField, indexed
- `is_used`: BooleanField (default: False, indexed)
- **Indexes:** `[token_hash, is_used]`, `[user, is_used]`

#### `AuditLog`
Compliance log of critical administrative actions.
- `actor`: FK -> `User`, null=True, on_delete=SET_NULL
- `action`: CharField(100), indexed
- `target_model`: CharField(100), indexed
- `target_id`: CharField(100), indexed
- `payload`: JSONField
- **Indexes:** `[actor, created_at]`, `[target_model, target_id]`

---

### 3.2 Student Domain (`apps/students`)

#### `StudentProfile`
Core academic and cohort profile.
- `user`: OneToOneField -> `User`, on_delete=CASCADE
- `student_id_number`: CharField(50), unique, indexed (e.g. `GQT-2026-001`)
- `full_name`: CharField(150)
- `batch_code`: CharField(50), indexed
- `college_name`: CharField(255), blank=True
- `graduation_year`: PositiveIntegerField, nullable
- `current_streak_days`: PositiveIntegerField (default: 0)
- `highest_streak_days`: PositiveIntegerField (default: 0)
- `total_points`: DecimalField(max_digits=10, decimal_places=2, default=0.00, db_index=True)
- **Constraints:** `CheckConstraint(total_points >= 0)`, `CheckConstraint(current_streak_days <= highest_streak_days)`
- **Indexes:** `[batch_code, -total_points]` (batch ranking), `[-total_points]` (global ranking), `[user, batch_code]`

---

### 3.3 Courses Domain (`apps/courses`)

#### `Course`
Top-level curriculum container.
- `title`: CharField(200)
- `slug`: SlugField(220), unique, indexed
- `description`: TextField
- `thumbnail_url`: URLField
- `is_published`: BooleanField, indexed
- `is_deleted`: BooleanField, indexed (soft deletion)
- `order`: PositiveIntegerField (default: 0)
- `created_by`: FK -> `User`, null=True, on_delete=SET_NULL
- **Indexes:** `[is_published, is_deleted]`

#### `CourseEnrollment`
Student course enrollment records.
- `student`: FK -> `StudentProfile`, on_delete=CASCADE
- `course`: FK -> `Course`, on_delete=CASCADE
- `status`: TextChoices [`ACTIVE`, `COMPLETED`, `REVOKED`, `SUSPENDED`], indexed
- `enrolled_at`: DateTimeField(auto_now_add=True, db_index=True)
- `completed_at`: DateTimeField, nullable
- **Constraints:** `UniqueConstraint(fields=[student, course])`
- **Indexes:** `[student, status]`, `[course, status]`

---

### 3.4 Modules Domain (`apps/modules`)

#### `Module`
Represents one of the **17 Sequential Learning Topics**.
- `course`: FK -> `Course`, on_delete=CASCADE
- `title`: CharField(150) (e.g., "1. Data Types", "2. If-Else", ...)
- `slug`: SlugField(180)
- `order_index`: PositiveSmallIntegerField, indexed (1 to 17)
- `summary`: TextField
- `lecture_content`: TextField
- `passing_percentage`: DecimalField(max_digits=5, decimal_places=2, default=80.00)
- `is_published`: BooleanField(default=True, db_index=True)
- **Constraints:** `UniqueConstraint([course, order_index])`, `UniqueConstraint([course, slug])`, `CheckConstraint(0 <= passing_percentage <= 100)`

#### `ModulePrerequisite`
Explicit graph-based prerequisite dependencies.
- `module`: FK -> `Module`, on_delete=CASCADE, related_name="prerequisites"
- `prerequisite_module`: FK -> `Module`, on_delete=CASCADE, related_name="dependent_modules"
- **Constraints:** `UniqueConstraint([module, prerequisite_module])`, `CheckConstraint(~Q(module=prerequisite_module))`
- **Validation:** Clean method ensures prerequisite order index precedes module order index.

#### `StudentModuleProgress`
Authoritative unlock and completion state for a student on a module.
- `student`: FK -> `StudentProfile`, on_delete=CASCADE
- `module`: FK -> `Module`, on_delete=CASCADE
- `status`: TextChoices [`LOCKED`, `UNLOCKED`, `IN_PROGRESS`, `COMPLETED`], indexed
- `score_percentage`: DecimalField(max_digits=5, decimal_places=2, default=0.00)
- `unlocked_at`: DateTimeField, nullable
- `completed_at`: DateTimeField, nullable
- `unlocked_by_override`: BooleanField(default=False)
- `override_admin`: FK -> `User`, null=True, on_delete=SET_NULL
- **Constraints:** `UniqueConstraint([student, module])`, `CheckConstraint(0 <= score_percentage <= 100)`
- **Indexes:** `[student, status]`, `[module, status]`

---

### 3.5 Assignments Domain (`apps/assignments`)

#### `CodingQuestion`
Algorithmic programming challenge belonging to a curriculum module.
- `module`: FK -> `Module`, on_delete=CASCADE
- `title`: CharField(255)
- `slug`: SlugField(280)
- `difficulty`: TextChoices [`EASY`, `MEDIUM`, `HARD`], indexed
- `problem_statement`: TextField (Markdown)
- `allowed_languages`: JSONField (e.g. `["python", "java", "c", "cpp", "javascript"]`)
- `starter_code`: JSONField (Boilerplate per language)
- `time_limit_seconds`: DecimalField(4, 2, default=2.00)
- `memory_limit_mb`: PositiveIntegerField(default=128)
- `points`: DecimalField(max_digits=7, decimal_places=2, default=100.00)
- `order`: PositiveIntegerField(default=0)
- `is_active`: BooleanField(default=True, db_index=True)
- **Constraints:** `UniqueConstraint([module, slug])`, `CheckConstraint(points > 0)`
- **Indexes:** `[module, difficulty]`, `[module, order]`

#### `TestCase`
Input/Output validation pairs for automated grading.
- `question`: FK -> `CodingQuestion`, on_delete=CASCADE
- `input_data`: TextField
- `expected_output`: TextField
- `is_visible`: BooleanField, indexed (True = public sample, False = hidden grading test)
- `weight`: DecimalField(max_digits=5, decimal_places=2, default=1.00)
- `order`: PositiveIntegerField(default=0)
- **Indexes:** `[question, is_visible]`

#### `CodeSubmission`
Immutable audit record of student code execution.
- `student`: FK -> `StudentProfile`, on_delete=CASCADE
- `question`: FK -> `CodingQuestion`, on_delete=CASCADE
- `language`: CharField(30), indexed
- `source_code`: TextField
- `status`: TextChoices [`PENDING`, `RUNNING`, `ACCEPTED`, `WRONG_ANSWER`, `TIME_LIMIT_EXCEEDED`, `MEMORY_LIMIT_EXCEEDED`, `COMPILATION_ERROR`, `RUNTIME_ERROR`], indexed
- `passed_test_cases`: PositiveIntegerField(default=0)
- `total_test_cases`: PositiveIntegerField(default=0)
- `execution_time_ms`: PositiveIntegerField, nullable
- `peak_memory_kb`: PositiveIntegerField, nullable
- `score_awarded`: DecimalField(max_digits=7, decimal_places=2, default=0.00)
- `scoring_policy`: TextChoices [`FULL`, `HALF`, `ZERO`]
- `submitted_at`: DateTimeField(auto_now_add=True, db_index=True)
- **Indexes:** `[student, question, -submitted_at]`, `[question, status]`, `[status, submitted_at]`

#### `ExecutionResult`
Detailed per-testcase execution log produced by sandboxed judge.
- `submission`: FK -> `CodeSubmission`, on_delete=CASCADE
- `test_case`: FK -> `TestCase`, on_delete=CASCADE
- `status`: TextChoices [`PASSED`, `FAILED`, `TIME_LIMIT_EXCEEDED`, `MEMORY_LIMIT_EXCEEDED`, `RUNTIME_ERROR`, `COMPILATION_ERROR`], indexed
- `stdout`: TextField, blank=True
- `stderr`: TextField, blank=True
- `execution_time_seconds`: DecimalField(6, 4), nullable
- `memory_kb`: PositiveIntegerField, nullable
- `exit_code`: IntegerField, nullable
- **Constraints:** `UniqueConstraint([submission, test_case])`

#### `StudentQuestionProgress`
Authoritative highest score and completion tracking per question.
- `student`: FK -> `StudentProfile`, on_delete=CASCADE
- `question`: FK -> `CodingQuestion`, on_delete=CASCADE
- `is_solved`: BooleanField(default=False, db_index=True)
- `best_score`: DecimalField(max_digits=7, decimal_places=2, default=0.00, db_index=True)
- `best_submission`: FK -> `CodeSubmission`, null=True, on_delete=SET_NULL
- `attempts_count`: PositiveIntegerField(default=0)
- `first_solved_at`: DateTimeField, nullable
- `last_submitted_at`: DateTimeField(auto_now=True)
- **Constraints:** `UniqueConstraint([student, question])`, `CheckConstraint(best_score >= 0)`
- **Indexes:** `[student, is_solved]`

---

### 3.6 Scoring Domain (`apps/scoring`)

#### `ScoreRecord`
The authoritative single source of truth for points earned across any platform activity.
- `student`: FK -> `StudentProfile`, on_delete=CASCADE
- `source_type`: TextChoices [`ASSIGNMENT`, `DAILY_TASK`, `PROJECT`, `STREAK_BONUS`, `ADMIN_ADJUSTMENT`], indexed
- `source_id`: UUIDField, indexed (ID of QuestionSubmission, TaskCompletion, ProjectSubmission, etc.)
- `points`: DecimalField(max_digits=7, decimal_places=2)
- `policy_applied`: TextChoices [`FULL`, `HALF`, `ZERO`, `MANUAL`]
- `awarded_at`: DateTimeField(auto_now_add=True, db_index=True)
- `awarded_by`: FK -> `User`, null=True, on_delete=SET_NULL
- **Constraints:** `UniqueConstraint([student, source_type, source_id])`
- **Indexes:** `[student, source_type]`, `[source_type, source_id]`

#### `ScoreEvent`
Audit trail of point transactions, bonuses, deductions, or recalculations.
- `student`: FK -> `StudentProfile`, on_delete=CASCADE
- `score_record`: FK -> `ScoreRecord`, null=True, on_delete=CASCADE
- `event_type`: TextChoices [`SUBMISSION_EVALUATED`, `ADMIN_OVERRIDE`, `STREAK_BONUS_ADDED`, `DEDUCTION`, `RECALCULATION`], indexed
- `delta`: DecimalField(max_digits=7, decimal_places=2)
- `reason`: CharField(255)
- `created_by`: FK -> `User`, null=True, on_delete=SET_NULL
- **Indexes:** `[student, created_at]`

#### `LeaderboardSnapshot`
Frozen daily point-in-time leaderboard snapshot for historical ranking analysis.
- `snapshot_date`: DateField, indexed
- `student`: FK -> `StudentProfile`, on_delete=CASCADE
- `batch_code`: CharField(50), indexed
- `total_score`: DecimalField(max_digits=10, decimal_places=2)
- `global_rank`: PositiveIntegerField, indexed
- `batch_rank`: PositiveIntegerField, indexed
- `streak_days`: PositiveIntegerField(default=0)
- **Constraints:** `UniqueConstraint([snapshot_date, student])`
- **Indexes:** `[snapshot_date, batch_code, batch_rank]`, `[snapshot_date, global_rank]`

---

### 3.7 Tasks Domain (`apps/tasks`)

#### `Task` (Daily Coding Challenge)
- `title`: CharField(200)
- `description`: TextField
- `scheduled_date`: DateField, unique, indexed
- `question`: FK -> `CodingQuestion`, null=True, on_delete=SET_NULL
- `points`: DecimalField(5, 2, default=20.00)
- `is_active`: BooleanField(default=True, db_index=True)

#### `StudentTask`
- `student`: FK -> `StudentProfile`, on_delete=CASCADE
- `task`: FK -> `Task`, on_delete=CASCADE
- `is_completed`: BooleanField(default=True)
- `completed_at`: DateTimeField(auto_now_add=True, db_index=True)
- `score_awarded`: DecimalField(5, 2, default=20.00)
- **Constraints:** `UniqueConstraint([student, task])`
- **Indexes:** `[student, completed_at]`

---

### 3.8 Projects Domain (`apps/projects`)

#### `Project`
- `title`: CharField(200)
- `slug`: SlugField(220), unique, indexed
- `description`: TextField
- `deliverables_instructions`: TextField
- `course`: FK -> `Course`, null=True, on_delete=SET_NULL
- `max_score`: DecimalField(6, 2, default=100.00)
- `due_date`: DateTimeField, null=True, indexed
- `is_active`: BooleanField(default=True, db_index=True)

#### `ProjectSubmission`
- `project`: FK -> `Project`, on_delete=CASCADE
- `student`: FK -> `StudentProfile`, on_delete=CASCADE
- `github_repository_url`: URLField, blank=True
- `live_demo_url`: URLField, blank=True
- `status`: TextChoices [`SUBMITTED`, `UNDER_REVIEW`, `CHANGES_REQUESTED`, `APPROVED`, `REJECTED`], indexed
- `score`: DecimalField(6, 2, null=True, blank=True)
- `submitted_at`: DateTimeField(auto_now_add=True, db_index=True)
- `reviewed_at`: DateTimeField, null=True
- `reviewed_by`: FK -> `User`, null=True, on_delete=SET_NULL
- **Constraints:** `UniqueConstraint([project, student])`
- **Indexes:** `[project, status]`, `[student, status]`

#### `ProjectFile`
- `submission`: FK -> `ProjectSubmission`, on_delete=CASCADE
- `file`: FileField(upload_to="project_files/%Y/%m/")
- `file_name`: CharField(255)
- `file_size_bytes`: BigIntegerField
- `mime_type`: CharField(100)

#### `ProjectFeedback`
- `submission`: FK -> `ProjectSubmission`, on_delete=CASCADE
- `reviewer`: FK -> `User`, on_delete=CASCADE
- `feedback_text`: TextField
- `suggested_changes`: TextField, blank=True
- `rating`: PositiveSmallIntegerField(null=True)

---

### 3.9 AI Assistant Domain (`apps/ai_assistant`)

#### `AIConversation`
- `student`: FK -> `StudentProfile`, on_delete=CASCADE
- `context_question`: FK -> `CodingQuestion`, null=True, on_delete=SET_NULL
- `title`: CharField(200, default="New Consultation")
- `is_archived`: BooleanField(default=False, db_index=True)
- **Indexes:** `[student, -updated_at]`

#### `AIMessage`
- `conversation`: FK -> `AIConversation`, on_delete=CASCADE
- `sender`: TextChoices [`STUDENT`, `ASSISTANT`, `SYSTEM`], indexed
- `content`: TextField
- `tokens_used`: PositiveIntegerField(default=0)
- **Indexes:** `[conversation, created_at]`

---

### 3.10 Notifications & Announcements Domain (`apps/notifications`)

#### `Notification`
- `recipient`: FK -> `User`, on_delete=CASCADE
- `title`: CharField(200)
- `body`: TextField
- `notification_type`: TextChoices [`SUBMISSION_GRADED`, `MODULE_UNLOCKED`, `PROJECT_FEEDBACK`, `STREAK_ALERT`, `SYSTEM_NOTICE`]
- `is_read`: BooleanField(default=False, db_index=True)
- `read_at`: DateTimeField, null=True
- `action_url`: CharField(500, blank=True)
- **Indexes:** `[recipient, is_read, -created_at]`

#### `Announcement`
- `title`: CharField(255)
- `content`: TextField
- `target_batch`: CharField(50, blank=True, db_index=True)
- `priority`: TextChoices [`LOW`, `NORMAL`, `HIGH`, `URGENT`], indexed
- `published_by`: FK -> `User`, null=True, on_delete=SET_NULL
- `is_active`: BooleanField(default=True, db_index=True)
- **Indexes:** `[is_active, target_batch, -created_at]`

---

### 3.11 Gamification & Credentials Domain (`apps/certificates`)

#### `Badge`
- `slug`: SlugField(60), unique, indexed
- `name`: CharField(100)
- `description`: TextField
- `icon_url`: URLField
- `criteria_type`: TextChoices [`STREAK_MILESTONE`, `QUESTIONS_SOLVED`, `MODULE_COMPLETION`, `LEADERBOARD_TOP`, `PROJECT_EXCELLENCE`]
- `criteria_threshold`: PositiveIntegerField(default=1)

#### `StudentBadge`
- `student`: FK -> `StudentProfile`, on_delete=CASCADE
- `badge`: FK -> `Badge`, on_delete=CASCADE
- **Constraints:** `UniqueConstraint([student, badge])`

#### `Certificate`
- `certificate_id`: CharField(64), unique, indexed (e.g. `GQT-CERT-2026-XXXX`)
- `student`: FK -> `StudentProfile`, on_delete=CASCADE
- `course`: FK -> `Course`, on_delete=CASCADE
- `verification_hash`: CharField(64), unique
- `pdf_file`: FileField, null=True
- `is_revoked`: BooleanField(default=False, db_index=True)
- **Constraints:** `UniqueConstraint([student, course])`

---

### 3.12 Analytics Domain (`apps/analytics`)

#### `ActivityEvent`
- `user`: FK -> `User`, null=True, on_delete=CASCADE
- `event_name`: CharField(100), indexed
- `entity_type`: CharField(50, blank=True)
- `entity_id`: CharField(64, blank=True)
- `properties`: JSONField
- **Indexes:** `[user, event_name, -created_at]`, `[event_name, -created_at]`

#### `DailyStudentAnalytics`
- `student`: FK -> `StudentProfile`, on_delete=CASCADE
- `date`: DateField, indexed
- `submissions_count`: PositiveIntegerField(default=0)
- `questions_solved_count`: PositiveIntegerField(default=0)
- `time_spent_minutes`: PositiveIntegerField(default=0)
- `score_earned`: DecimalField(max_digits=7, decimal_places=2, default=0.00)
- **Constraints:** `UniqueConstraint([student, date])`
- **Indexes:** `[date, -score_earned]`

---

### 3.13 Contact & Support Domain (`apps/contact`)

#### `ContactInquiry`
- `user`: FK -> `User`, null=True, on_delete=SET_NULL
- `name`: CharField(150)
- `email`: EmailField(255)
- `subject`: CharField(200)
- `category`: TextChoices [`TECHNICAL_SUPPORT`, `COURSE_DOUBT`, `ACCOUNT_ISSUE`, `GENERAL_FEEDBACK`], indexed
- `message`: TextField
- `status`: TextChoices [`PENDING`, `INVESTIGATING`, `RESOLVED`, `CLOSED`], indexed
- `admin_notes`: TextField(blank=True)
- `resolved_by`: FK -> `User`, null=True, on_delete=SET_NULL
- `resolved_at`: DateTimeField, null=True
- **Indexes:** `[status, -created_at]`, `[category, status]`

---

## 4. Ownership & Access Rules

1. **Student Isolation:** Students are only permitted to query their own `StudentProfile`, `StudentModuleProgress`, `CodeSubmission`, `ExecutionResult`, `ScoreRecord`, `StudentTask`, `ProjectSubmission`, and `AIConversation` records.
2. **Administrative Authority:** Users with role `ADMIN` hold platform-wide authority to onboard students, unlock module progress (`unlocked_by_override=True`), review and score project submissions, broadcast announcements, and audit all platform activity.
3. **Immutability of Evaluation Logs:** `CodeSubmission`, `ExecutionResult`, `ScoreRecord`, and `AuditLog` are strictly append-only; update operations are prohibited by domain services to preserve assessment integrity.
