# Supabase Data Platform & Relational Schema Specification

## 1. Overview & Data Platform Architecture

The **GQT Student Learning and Coding Assessment Platform** utilizes **Supabase** (PostgreSQL 16) as its exclusive, authoritative persistent data platform.

### Core Data Tenets:
1. **Single Source of Truth**: All academic records, verified points, code submissions, streaks, course enrollments, and support tickets reside exclusively in Supabase PostgreSQL tables.
2. **Backend Authority**: The Django REST Framework backend interacts with Supabase using direct connection pooling (`pgbouncer` on port 6543 or direct session port 5432) with service-role administrative credentials. All business logic, transaction boundaries, and state mutations execute in the backend service layer.
3. **Cryptographic Identity & UUIDs**: All primary keys are cryptographically random UUIDv4 identifiers generated via `uuid_generate_v4()`.
4. **Precision Scoring**: All point tallies, marks, and weighted scoring calculations use `NUMERIC(10, 2)` or `NUMERIC(7, 2)` to eliminate floating-point arithmetic errors.
5. **Multi-Tenant Isolation**: Batches/cohorts and individual student profiles are structurally partitioned through relational foreign keys and indexed columns.

---

## 2. Relational Schema by Domain

```mermaid
erDiagram
    User ||--o| StudentProfile : "has"
    User ||--o| AdminProfile : "has"
    User ||--o{ LoginActivity : "logs"
    User ||--o{ OTPVerification : "verifies"
    User ||--o{ AuditLog : "records"
    
    Institution ||--o{ StudentProfile : "affiliates"
    CohortBatch ||--o{ StudentProfile : "belongs_to"
    
    Course ||--o{ CourseEnrollment : "enrolls"
    StudentProfile ||--o{ CourseEnrollment : "has"
    
    Course ||--o{ Module : "contains"
    Module ||--o{ ModulePrerequisite : "requires"
    StudentProfile ||--o{ StudentModuleProgress : "tracks"
    Module ||--o{ StudentModuleProgress : "progress_for"
    
    Module ||--o{ CodingQuestion : "contains"
    CodingQuestion ||--o{ TestCase : "validates"
    StudentProfile ||--o{ CodeSubmission : "submits"
    CodingQuestion ||--o{ CodeSubmission : "receives"
    CodeSubmission ||--o{ ExecutionResult : "produces"
    StudentProfile ||--o{ StudentQuestionProgress : "achieves"
    CodingQuestion ||--o{ StudentQuestionProgress : "question_stats"
    
    StudentProfile ||--o{ ScoreRecord : "earns"
    StudentProfile ||--o{ ScoreEvent : "audits"
    StudentProfile ||--o{ LeaderboardSnapshot : "snapshots"
    
    Task ||--o{ StudentTask : "completes"
    StudentProfile ||--o{ StudentTask : "participates"
    
    Course ||--o{ Project : "assigns"
    Project ||--o{ ProjectSubmission : "receives"
    StudentProfile ||--o{ ProjectSubmission : "submits"
    ProjectSubmission ||--o{ ProjectFile : "attaches"
    ProjectSubmission ||--o{ ProjectFeedback : "evaluates"
    
    StudentProfile ||--o{ AIConversation : "initiates"
    AIConversation ||--o{ AIMessage : "contains"
    
    User ||--o{ Notification : "receives"
    CohortBatch ||--o{ Announcement : "targets"
    
    StudentProfile ||--o{ StudentBadge : "awards"
    Badge ||--o{ StudentBadge : "grants"
    StudentProfile ||--o{ Certificate : "issues"
    Course ||--o{ Certificate : "certifies"
    
    User ||--o{ ActivityEvent : "emits"
    StudentProfile ||--o{ DailyStudentAnalytics : "aggregates"
    
    User ||--o{ ContactInquiry : "submits"
```

---

## 3. Detailed Table Specifications

### 3.1 Authentication & RBAC Domain (`accounts_*`)

#### `accounts_user`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Cryptographic User PK |
| `email` | `VARCHAR(255)` | `UNIQUE`, Nullable, Indexed | Student / Admin primary email |
| `mobile_number` | `VARCHAR(20)` | `UNIQUE`, Nullable, Indexed | International format mobile number |
| `password` | `VARCHAR(255)` | Not Null | Argon2id / PBKDF2 hashed password |
| `role` | `VARCHAR(20)` | Not Null, Default `'STUDENT'` | Enums: `'ADMIN'`, `'STUDENT'` |
| `onboarding_status` | `VARCHAR(30)` | Not Null, Default `'PENDING_ACTIVATION'` | Enums: `'PENDING_ACTIVATION'`, `'ACTIVE'`, `'SUSPENDED'`, `'REVOKED'` |
| `is_active` | `BOOLEAN` | Not Null, Default `TRUE`, Indexed | Account portal access toggle |
| `last_login` | `TIMESTAMPTZ` | Nullable | Timestamp of most recent authentication |
| `created_at` | `TIMESTAMPTZ` | Not Null, Default `NOW()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | Not Null, Default `NOW()` | Modification timestamp |

#### `accounts_loginactivity`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Audit PK |
| `user_id` | `UUID` | `FOREIGN KEY (accounts_user.id) ON DELETE SET NULL` | Target user |
| `identifier` | `VARCHAR(255)` | Not Null | Email / Mobile used in attempt |
| `login_type` | `VARCHAR(30)` | Not Null | Enums: `'EMAIL_PASSWORD'`, `'MOBILE_OTP'`, `'REFRESH'` |
| `status` | `VARCHAR(30)` | Not Null | Enums: `'SUCCESS'`, `'FAILED_CREDENTIALS'`, `'FAILED_OTP'`, `'LOCKED'` |
| `ip_address` | `INET` | Nullable, Indexed | Remote client IP |
| `user_agent` | `TEXT` | Blankable | Browser / Device user agent string |
| `created_at` | `TIMESTAMPTZ` | Not Null, Default `NOW()`, Indexed | Event timestamp |

#### `accounts_otpverification`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Verification record PK |
| `user_id` | `UUID` | `FOREIGN KEY (accounts_user.id) ON DELETE CASCADE` | Associated user |
| `mobile_number` | `VARCHAR(20)` | Not Null, Indexed | Target mobile |
| `otp_hash` | `VARCHAR(128)` | Not Null | SHA-256 hash of 6-digit OTP |
| `purpose` | `VARCHAR(30)` | Not Null | Enums: `'LOGIN'`, `'PASSWORD_RESET'`, `'PHONE_VERIFY'` |
| `attempts` | `SMALLINT` | Not Null, Default `0` | Attempt counter |
| `max_attempts` | `SMALLINT` | Not Null, Default `5` | Maximum allowed invalid attempts |
| `is_used` | `BOOLEAN` | Not Null, Default `FALSE`, Indexed | Consumption flag |
| `expires_at` | `TIMESTAMPTZ` | Not Null, Indexed | Expiration boundary (5 mins) |
| `created_at` | `TIMESTAMPTZ` | Not Null, Default `NOW()` | Dispatch timestamp |

---

### 3.2 Academic Institutions, Batches & Student Profiles (`students_*`)

#### `students_institution`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Institution PK |
| `name` | `VARCHAR(255)` | Not Null, `UNIQUE` | Full College / University name |
| `code` | `VARCHAR(50)` | Not Null, `UNIQUE`, Indexed | Short institutional identifier code |
| `city` | `VARCHAR(100)` | Blankable | Campus city location |
| `is_active` | `BOOLEAN` | Not Null, Default `TRUE` | Active status |

#### `students_cohortbatch`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Cohort Batch PK |
| `batch_code` | `VARCHAR(50)` | Not Null, `UNIQUE`, Indexed | Cohort code (e.g. `'BATCH-2026-A'`) |
| `name` | `VARCHAR(150)` | Not Null | Descriptive title |
| `academic_period` | `VARCHAR(50)` | Not Null | E.g. `'Spring 2026'`, `'Jan-Jun 2026'` |
| `start_date` | `DATE` | Not Null | Batch commencement date |
| `end_date` | `DATE` | Nullable | Expected completion date |
| `is_active` | `BOOLEAN` | Not Null, Default `TRUE`, Indexed | Active enrollment toggle |

#### `students_studentprofile`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Student Profile PK |
| `user_id` | `UUID` | `UNIQUE`, `FOREIGN KEY (accounts_user.id) ON DELETE CASCADE` | Core User account |
| `student_id_number` | `VARCHAR(50)` | Not Null, `UNIQUE`, Indexed | Academic ID (e.g. `'GQT-2026-001'`) |
| `full_name` | `VARCHAR(150)` | Not Null | Student legal full name |
| `avatar_url` | `TEXT` | Blankable | Supabase Storage avatar URL |
| `batch_id` | `UUID` | `FOREIGN KEY (students_cohortbatch.id) ON DELETE RESTRICT`, Indexed | Assigned Cohort Batch |
| `institution_id` | `UUID` | `FOREIGN KEY (students_institution.id) ON DELETE SET NULL`, Nullable | Affiliated College / Institution |
| `graduation_year` | `INTEGER` | Nullable | Target graduation year |
| `current_streak_days` | `INTEGER` | Not Null, Default `0`, Indexed | Authoritative active day streak |
| `highest_streak_days` | `INTEGER` | Not Null, Default `0` | All-time highest streak milestone |
| `last_activity_date` | `DATE` | Nullable, Indexed | Date of most recent qualifying activity |
| `total_points` | `NUMERIC(10, 2)` | Not Null, Default `0.00`, Indexed | Materialized sum of verified points |

---

### 3.3 Curriculum & Sequential Module Unlock Engine (`courses_*`, `modules_*`)

#### `courses_course`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Course PK |
| `title` | `VARCHAR(200)` | Not Null | Course title |
| `slug` | `VARCHAR(220)` | Not Null, `UNIQUE`, Indexed | URL slug identifier |
| `description` | `TEXT` | Not Null | Course syllabus & summary |
| `thumbnail_url` | `TEXT` | Blankable | Supabase Storage cover image |
| `is_published` | `BOOLEAN` | Not Null, Default `TRUE`, Indexed | Published status |
| `is_deleted` | `BOOLEAN` | Not Null, Default `FALSE`, Indexed | Soft delete flag |
| `order_index` | `INTEGER` | Not Null, Default `0` | Catalog display order |

#### `courses_courseenrollment`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Enrollment PK |
| `student_id` | `UUID` | `FOREIGN KEY (students_studentprofile.id) ON DELETE CASCADE` | Student |
| `course_id` | `UUID` | `FOREIGN KEY (courses_course.id) ON DELETE CASCADE` | Course |
| `status` | `VARCHAR(30)` | Not Null, Default `'ACTIVE'`, Indexed | Enums: `'ACTIVE'`, `'COMPLETED'`, `'SUSPENDED'`, `'REVOKED'` |
| `enrolled_at` | `TIMESTAMPTZ` | Not Null, Default `NOW()`, Indexed | Initial enrollment timestamp |
| `completed_at` | `TIMESTAMPTZ` | Nullable | Completion timestamp |
| `UNIQUE(student_id, course_id)` | Constraint | Prevents duplicate enrollments |

#### `modules_module`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Module PK |
| `course_id` | `UUID` | `FOREIGN KEY (courses_course.id) ON DELETE CASCADE` | Parent course |
| `title` | `VARCHAR(150)` | Not Null | Module title (e.g. `'1. Data Types'`) |
| `slug` | `VARCHAR(180)` | Not Null | URL slug |
| `order_index` | `SMALLINT` | Not Null, Indexed | Sequential order (1 to 17) |
| `summary` | `TEXT` | Not Null | Summary overview |
| `lecture_content` | `TEXT` | Not Null | Rich Markdown lecture body |
| `passing_percentage` | `NUMERIC(5, 2)` | Not Null, Default `80.00` | Minimum score % to unlock next module |
| `is_published` | `BOOLEAN` | Not Null, Default `TRUE`, Indexed | Publication state |
| `UNIQUE(course_id, order_index)` | Constraint | Enforces strict sequence |

#### `modules_studentmoduleprogress`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Progress PK |
| `student_id` | `UUID` | `FOREIGN KEY (students_studentprofile.id) ON DELETE CASCADE` | Student |
| `module_id` | `UUID` | `FOREIGN KEY (modules_module.id) ON DELETE CASCADE` | Target module |
| `status` | `VARCHAR(30)` | Not Null, Default `'LOCKED'`, Indexed | Enums: `'LOCKED'`, `'UNLOCKED'`, `'IN_PROGRESS'`, `'COMPLETED'` |
| `score_percentage` | `NUMERIC(5, 2)` | Not Null, Default `0.00` | Current earned module percentage |
| `unlocked_at` | `TIMESTAMPTZ` | Nullable | Unlock timestamp |
| `completed_at` | `TIMESTAMPTZ` | Nullable | Completion timestamp |
| `unlocked_by_override` | `BOOLEAN` | Not Null, Default `FALSE` | Flag for admin manual unlock |
| `override_admin_id` | `UUID` | `FOREIGN KEY (accounts_user.id) ON DELETE SET NULL`, Nullable | Admin user who granted override |
| `UNIQUE(student_id, module_id)` | Constraint | One progress record per module |

---

### 3.4 Assessment, Monaco Coding & Execution (`assignments_*`)

#### `assignments_codingquestion`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Problem PK |
| `module_id` | `UUID` | `FOREIGN KEY (modules_module.id) ON DELETE CASCADE` | Parent curriculum module |
| `title` | `VARCHAR(255)` | Not Null | Problem title |
| `slug` | `VARCHAR(280)` | Not Null, Indexed | Unique identifier slug |
| `difficulty` | `VARCHAR(20)` | Not Null, Default `'EASY'`, Indexed | Enums: `'EASY'`, `'MEDIUM'`, `'HARD'` |
| `problem_statement` | `TEXT` | Not Null | Markdown problem brief with constraints |
| `allowed_languages` | `JSONB` | Not Null, Default `'["python", "java", "c", "cpp", "javascript"]'` | Supported runtimes |
| `starter_code` | `JSONB` | Not Null, Default `'{}'` | Language boilerplate map |
| `time_limit_seconds` | `NUMERIC(4, 2)`| Not Null, Default `2.00` | Sandbox CPU limit |
| `memory_limit_mb` | `INTEGER` | Not Null, Default `128` | Sandbox memory ceiling |
| `points` | `NUMERIC(7, 2)` | Not Null, Default `100.00` | Max marks awarded for full pass |
| `order_index` | `INTEGER` | Not Null, Default `0` | Order within module |
| `is_active` | `BOOLEAN` | Not Null, Default `TRUE`, Indexed | Active / Archived status |

#### `assignments_testcase`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | TestCase PK |
| `question_id` | `UUID` | `FOREIGN KEY (assignments_codingquestion.id) ON DELETE CASCADE` | Parent problem |
| `input_data` | `TEXT` | Not Null | STDIN input data |
| `expected_output` | `TEXT` | Not Null | Expected STDOUT data |
| `is_visible` | `BOOLEAN` | Not Null, Default `FALSE`, Indexed | Public sample (True) vs Hidden grading test (False) |
| `weight` | `NUMERIC(5, 2)` | Not Null, Default `1.00` | Scoring weight |
| `order_index` | `INTEGER` | Not Null, Default `0` | Execution order |

#### `assignments_codesubmission`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Submission PK |
| `student_id` | `UUID` | `FOREIGN KEY (students_studentprofile.id) ON DELETE CASCADE` | Submitting student |
| `question_id` | `UUID` | `FOREIGN KEY (assignments_codingquestion.id) ON DELETE CASCADE` | Target problem |
| `language` | `VARCHAR(30)` | Not Null, Indexed | Execution runtime (e.g. `'python'`, `'java'`) |
| `source_code` | `TEXT` | Not Null | Student submitted source code |
| `status` | `VARCHAR(30)` | Not Null, Default `'PENDING'`, Indexed | Enums: `'PENDING'`, `'RUNNING'`, `'ACCEPTED'`, `'WRONG_ANSWER'`, `'TIME_LIMIT_EXCEEDED'`, `'MEMORY_LIMIT_EXCEEDED'`, `'COMPILATION_ERROR'`, `'RUNTIME_ERROR'` |
| `passed_test_cases` | `INTEGER` | Not Null, Default `0` | Number of testcases passed |
| `total_test_cases` | `INTEGER` | Not Null, Default `0` | Total testcases executed |
| `execution_time_ms` | `INTEGER` | Nullable | Sandbox wall-clock time |
| `peak_memory_kb` | `INTEGER` | Nullable | Sandbox peak memory usage |
| `score_awarded` | `NUMERIC(7, 2)` | Not Null, Default `0.00` | Calculated points earned |
| `scoring_policy` | `VARCHAR(20)` | Not Null, Default `'ZERO'` | Enums: `'FULL'`, `'HALF'`, `'ZERO'` |
| `submitted_at` | `TIMESTAMPTZ` | Not Null, Default `NOW()`, Indexed | Submission timestamp |

#### `assignments_executionresult`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Result PK |
| `submission_id` | `UUID` | `FOREIGN KEY (assignments_codesubmission.id) ON DELETE CASCADE` | Parent submission |
| `test_case_id` | `UUID` | `FOREIGN KEY (assignments_testcase.id) ON DELETE CASCADE` | Executed testcase |
| `status` | `VARCHAR(30)` | Not Null, Indexed | Enums: `'PASSED'`, `'FAILED'`, `'TIME_LIMIT_EXCEEDED'`, `'MEMORY_LIMIT_EXCEEDED'`, `'RUNTIME_ERROR'`, `'COMPILATION_ERROR'` |
| `stdout` | `TEXT` | Blankable | Output text (Sanitized) |
| `stderr` | `TEXT` | Blankable | Error text (Sanitized) |
| `execution_time_seconds` | `NUMERIC(6, 4)` | Nullable | Exact execution duration |
| `memory_kb` | `INTEGER` | Nullable | RAM consumed |
| `exit_code` | `INTEGER` | Nullable | Process exit code |

#### `assignments_studentquestionprogress`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Progress PK |
| `student_id` | `UUID` | `FOREIGN KEY (students_studentprofile.id) ON DELETE CASCADE` | Student |
| `question_id` | `UUID` | `FOREIGN KEY (assignments_codingquestion.id) ON DELETE CASCADE` | Problem |
| `is_solved` | `BOOLEAN` | Not Null, Default `FALSE`, Indexed | Solved indicator |
| `best_score` | `NUMERIC(7, 2)` | Not Null, Default `0.00`, Indexed | Maximum score achieved |
| `best_submission_id` | `UUID` | `FOREIGN KEY (assignments_codesubmission.id) ON DELETE SET NULL`, Nullable | FK to highest scoring submission |
| `attempts_count` | `INTEGER` | Not Null, Default `0` | Number of submission attempts |
| `first_solved_at` | `TIMESTAMPTZ` | Nullable | Timestamp of first accepted solution |
| `last_submitted_at`| `TIMESTAMPTZ` | Not Null, Default `NOW()` | Timestamp of last attempt |
| `UNIQUE(student_id, question_id)` | Constraint | Exactly one progress record per problem |

---

### 3.5 Scoring, Points & Leaderboard (`scoring_*`)

#### `scoring_scorerecord`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Immutable Score PK |
| `student_id` | `UUID` | `FOREIGN KEY (students_studentprofile.id) ON DELETE CASCADE` | Student recipient |
| `source_type` | `VARCHAR(30)` | Not Null, Indexed | Enums: `'ASSIGNMENT'`, `'DAILY_TASK'`, `'PROJECT'`, `'STREAK_BONUS'`, `'ADMIN_ADJUSTMENT'` |
| `source_id` | `UUID` | Not Null, Indexed | UUID of qualifying activity record |
| `points` | `NUMERIC(7, 2)` | Not Null | Verified Points awarded |
| `policy_applied` | `VARCHAR(20)` | Not Null | Enums: `'FULL'`, `'HALF'`, `'ZERO'`, `'MANUAL'` |
| `awarded_at` | `TIMESTAMPTZ` | Not Null, Default `NOW()`, Indexed | Award timestamp |
| `awarded_by_id` | `UUID` | `FOREIGN KEY (accounts_user.id) ON DELETE SET NULL`, Nullable | Admin user if manual adjustment |
| `UNIQUE(student_id, source_type, source_id)` | Constraint | Prevents duplicate point awards for same event |

#### `scoring_scoreevent`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Event PK |
| `student_id` | `UUID` | `FOREIGN KEY (students_studentprofile.id) ON DELETE CASCADE` | Student |
| `score_record_id` | `UUID` | `FOREIGN KEY (scoring_scorerecord.id) ON DELETE CASCADE`, Nullable | Associated score record |
| `event_type` | `VARCHAR(40)` | Not Null, Indexed | Enums: `'SUBMISSION_EVALUATED'`, `'ADMIN_OVERRIDE'`, `'STREAK_BONUS_ADDED'`, `'DEDUCTION'`, `'RECALCULATION'` |
| `delta` | `NUMERIC(7, 2)` | Not Null | Point delta (+ / -) |
| `reason` | `VARCHAR(255)` | Not Null | Audit explanation |
| `created_at` | `TIMESTAMPTZ` | Not Null, Default `NOW()`, Indexed | Event timestamp |

#### `scoring_leaderboardsnapshot`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Snapshot PK |
| `snapshot_date` | `DATE` | Not Null, Indexed | Snapshot calendar date |
| `student_id` | `UUID` | `FOREIGN KEY (students_studentprofile.id) ON DELETE CASCADE` | Student |
| `batch_id` | `UUID` | `FOREIGN KEY (students_cohortbatch.id) ON DELETE CASCADE`, Indexed | Student Cohort Batch |
| `total_points` | `NUMERIC(10, 2)`| Not Null | Snapshot total verified points |
| `global_rank` | `INTEGER` | Not Null, Indexed | Global standing |
| `batch_rank` | `INTEGER` | Not Null, Indexed | Batch standing |
| `streak_days` | `INTEGER` | Not Null, Default `0` | Active streak on snapshot date |
| `UNIQUE(snapshot_date, student_id)` | Constraint | Daily snapshot point-in-time record |

---

### 3.6 Daily Tasks Domain (`tasks_*`)

#### `tasks_task`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Daily Task PK |
| `title` | `VARCHAR(200)` | Not Null | Daily challenge title |
| `description` | `TEXT` | Not Null | Problem description |
| `scheduled_date`| `DATE` | Not Null, `UNIQUE`, Indexed | Calendar date of release |
| `question_id` | `UUID` | `FOREIGN KEY (assignments_codingquestion.id) ON DELETE SET NULL`, Nullable | Linked coding problem |
| `points` | `NUMERIC(5, 2)` | Not Null, Default `20.00` | Points awarded upon completion |
| `is_active` | `BOOLEAN` | Not Null, Default `TRUE`, Indexed | Active challenge flag |

#### `tasks_studenttask`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Participation PK |
| `student_id` | `UUID` | `FOREIGN KEY (students_studentprofile.id) ON DELETE CASCADE` | Participating student |
| `task_id` | `UUID` | `FOREIGN KEY (tasks_task.id) ON DELETE CASCADE` | Daily Task |
| `is_completed` | `BOOLEAN` | Not Null, Default `TRUE`, Indexed | Completion flag |
| `completed_at` | `TIMESTAMPTZ` | Not Null, Default `NOW()`, Indexed | Completion timestamp |
| `score_awarded` | `NUMERIC(5, 2)` | Not Null, Default `20.00` | Points awarded |
| `UNIQUE(student_id, task_id)` | Constraint | Prevents duplicate daily completions |

---

### 3.7 Capstone Projects Domain (`projects_*`)

#### `projects_project`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Project PK |
| `course_id` | `UUID` | `FOREIGN KEY (courses_course.id) ON DELETE SET NULL`, Nullable | Associated course |
| `title` | `VARCHAR(200)` | Not Null | Capstone project title |
| `slug` | `VARCHAR(220)` | Not Null, `UNIQUE`, Indexed | URL slug |
| `description` | `TEXT` | Not Null | Project specifications & rubric |
| `deliverables_instructions` | `TEXT` | Not Null | Submission guidelines |
| `max_score` | `NUMERIC(6, 2)` | Not Null, Default `100.00` | Maximum marks |
| `due_date` | `TIMESTAMPTZ` | Nullable, Indexed | Submission deadline |
| `is_active` | `BOOLEAN` | Not Null, Default `TRUE`, Indexed | Active status |

#### `projects_projectsubmission`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Submission PK |
| `project_id` | `UUID` | `FOREIGN KEY (projects_project.id) ON DELETE CASCADE` | Target project |
| `student_id` | `UUID` | `FOREIGN KEY (students_studentprofile.id) ON DELETE CASCADE` | Submitting student |
| `github_repository_url` | `TEXT` | Blankable | Public / Private GitHub link |
| `live_demo_url` | `TEXT` | Blankable | Hosted demo URL |
| `status` | `VARCHAR(30)` | Not Null, Default `'SUBMITTED'`, Indexed | Enums: `'SUBMITTED'`, `'UNDER_REVIEW'`, `'CHANGES_REQUESTED'`, `'APPROVED'`, `'REJECTED'` |
| `score` | `NUMERIC(6, 2)` | Nullable | Admin evaluated score |
| `submitted_at` | `TIMESTAMPTZ` | Not Null, Default `NOW()`, Indexed | Initial submission timestamp |
| `reviewed_at` | `TIMESTAMPTZ` | Nullable | Review completion timestamp |
| `reviewed_by_id` | `UUID` | `FOREIGN KEY (accounts_user.id) ON DELETE SET NULL`, Nullable | Admin reviewer |
| `UNIQUE(project_id, student_id)` | Constraint | One submission per student per project |

---

### 3.8 Notifications & Broadcasts Domain (`notifications_*`)

#### `notifications_notification`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Notification PK |
| `recipient_id` | `UUID` | `FOREIGN KEY (accounts_user.id) ON DELETE CASCADE`, Indexed | Target recipient user |
| `title` | `VARCHAR(200)` | Not Null | Alert headline |
| `body` | `TEXT` | Not Null | Notification details |
| `category` | `VARCHAR(40)` | Not Null, Default `'ALL_ALERTS'`, Indexed | Enums: `'ANNOUNCEMENTS'`, `'DEADLINES_TASKS'`, `'GRADES_PROJECTS'`, `'ACHIEVEMENTS'`, `'SYSTEM'` |
| `is_read` | `BOOLEAN` | Not Null, Default `FALSE`, Indexed | Read status flag |
| `read_at` | `TIMESTAMPTZ` | Nullable | Timestamp of user acknowledgement |
| `action_route` | `VARCHAR(255)` | Blankable | Controlled internal frontend route (e.g. `'/assignments/e6a2b37c'`) |
| `created_at` | `TIMESTAMPTZ` | Not Null, Default `NOW()`, Indexed | Dispatch timestamp |

#### `notifications_announcement`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Announcement PK |
| `title` | `VARCHAR(255)` | Not Null | Broadcast headline |
| `content` | `TEXT` | Not Null | Markdown body |
| `target_batch_id` | `UUID` | `FOREIGN KEY (students_cohortbatch.id) ON DELETE SET NULL`, Nullable, Indexed | Scoped batch or NULL for platform-wide |
| `priority` | `VARCHAR(20)` | Not Null, Default `'NORMAL'`, Indexed | Enums: `'LOW'`, `'NORMAL'`, `'HIGH'`, `'URGENT'` |
| `published_by_id` | `UUID` | `FOREIGN KEY (accounts_user.id) ON DELETE SET NULL`, Nullable | Authoring admin |
| `is_active` | `BOOLEAN` | Not Null, Default `TRUE`, Indexed | Active display toggle |
| `created_at` | `TIMESTAMPTZ` | Not Null, Default `NOW()`, Indexed | Publication timestamp |

---

### 3.9 Credentials & Verification Domain (`certificates_*`)

#### `certificates_certificate`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Certificate PK |
| `certificate_id` | `VARCHAR(64)` | Not Null, `UNIQUE`, Indexed | Display ID (e.g. `'GQT-CERT-2026-A109'`) |
| `student_id` | `UUID` | `FOREIGN KEY (students_studentprofile.id) ON DELETE CASCADE` | Recipient student |
| `course_id` | `UUID` | `FOREIGN KEY (courses_course.id) ON DELETE CASCADE` | Completed course |
| `verification_hash`| `VARCHAR(64)` | Not Null, `UNIQUE`, Indexed | Cryptographic SHA-256 validation token |
| `pdf_storage_path` | `TEXT` | Nullable | Supabase Storage path |
| `issue_date` | `DATE` | Not Null, Default `CURRENT_DATE` | Date issued |
| `is_revoked` | `BOOLEAN` | Not Null, Default `FALSE`, Indexed | Revocation toggle |
| `UNIQUE(student_id, course_id)` | Constraint | One certificate per completed course |

---

### 3.10 Support & Inquiry Domain (`contact_*`)

#### `contact_contactinquiry`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY`, Default `gen_random_uuid()` | Ticket PK |
| `student_id` | `UUID` | `FOREIGN KEY (students_studentprofile.id) ON DELETE CASCADE`, Indexed | Authenticated submitting student |
| `full_name` | `VARCHAR(150)` | Not Null | Student name (Auto-populated) |
| `email` | `VARCHAR(255)` | Not Null | Student email (Auto-populated) |
| `category` | `VARCHAR(40)` | Not Null, Indexed | Enums: `'COURSE_ENROLLMENT'`, `'TECHNICAL_SUPPORT'`, `'ASSIGNMENT_DOUBT'`, `'BILLING_ACCOUNT'`, `'GENERAL_INQUIRY'` |
| `subject` | `VARCHAR(200)` | Not Null | Inquiry subject |
| `message` | `TEXT` | Not Null | Inquiry details |
| `status` | `VARCHAR(30)` | Not Null, Default `'OPEN'`, Indexed | Enums: `'OPEN'`, `'IN_REVIEW'`, `'RESOLVED'`, `'CLOSED'` |
| `admin_response` | `TEXT` | Blankable | Support resolution notes |
| `assigned_to_id` | `UUID` | `FOREIGN KEY (accounts_user.id) ON DELETE SET NULL`, Nullable | Support engineer |
| `resolved_at` | `TIMESTAMPTZ` | Nullable | Resolution timestamp |
| `created_at` | `TIMESTAMPTZ` | Not Null, Default `NOW()`, Indexed | Submission timestamp |
| `updated_at` | `TIMESTAMPTZ` | Not Null, Default `NOW()` | Modification timestamp |

---

## 4. Supabase Storage Buckets

The platform utilizes three private Supabase Storage buckets with strict access policies:

| Bucket Name | Access Level | Max File Size | Allowed MIME Types | Usage |
|---|---|---|---|---|
| `project-deliverables` | Authenticated Only | 25 MB | `application/zip`, `application/x-tar`, `application/pdf` | Student capstone project source archives |
| `certificates-pdf` | Public (Signed / Verified) | 5 MB | `application/pdf` | Generated verifiable course completion PDFs |
| `profile-avatars` | Public Read / Authenticated Write | 2 MB | `image/png`, `image/jpeg`, `image/webp` | Student and Admin profile avatars |

---

## 5. Row-Level Security (RLS) & Security Policies

While Django acts as the authoritative application gateway using the Supabase Service Role key, Row-Level Security (RLS) policies are active as defense-in-depth:

```sql
-- Enable RLS across sensitive student tables
ALTER TABLE students_studentprofile ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignments_codesubmission ENABLE ROW LEVEL SECURITY;
ALTER TABLE scoring_scorerecord ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications_notification ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_contactinquiry ENABLE ROW LEVEL SECURITY;

-- Student Isolation Policy: Users can only select their own records
CREATE POLICY "Student Profile Self Read"
ON students_studentprofile FOR SELECT
USING (auth.uid() = user_id);

-- Code Submissions Isolation
CREATE POLICY "Student Submissions Self Read"
ON assignments_codesubmission FOR SELECT
USING (student_id IN (SELECT id FROM students_studentprofile WHERE user_id = auth.uid()));

-- Notifications Isolation
CREATE POLICY "Student Notifications Self Read"
ON notifications_notification FOR SELECT
USING (recipient_id = auth.uid());

-- Support Inquiries Isolation
CREATE POLICY "Student Inquiries Self Read"
ON contact_contactinquiry FOR SELECT
USING (student_id IN (SELECT id FROM students_studentprofile WHERE user_id = auth.uid()));

-- Service Role Policy: Backend Django Service Role has full bypass authority
CREATE POLICY "Service Role Full Access"
ON students_studentprofile FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
```

---

## 6. Connection Modes & Supavisor Pooler Architecture

Supabase provides two distinct PostgreSQL connection endpoints:

| Connection Mode | Port | Target Use Case | `CONN_MAX_AGE` Setting | SSL Requirement |
|---|---|---|---|---|
| **Direct Session Connection** | `5432` | Schema migrations (`migrate`), local development, long-running Celery worker tasks requiring session state. | `600` (Persistent) | `sslmode=require` |
| **Supavisor Transaction Pooler** | `6543` | Production high-concurrency stateless web APIs, Serverless workers. | `0` (Zero persistent connections) | `sslmode=require` |

### Django Driver Compatibility:
- **Driver:** `psycopg[binary] >= 3.1.18` (psycopg 3) with full support for Django 5.x connection pooling, SSL negotiation, and server-side cursors.
- **Connection Health Probes:** `CONN_HEALTH_CHECKS = True` automatically validates socket health before reusing connection handles.

---

## 7. Backup, Disaster Recovery & Data Safety Runbook

1. **Continuous WAL Archiving & Daily Backups:**
   - Managed automatically by Supabase Point-in-Time Recovery (PITR).
2. **Scheduled Logical Dump Exports:**
   ```bash
   pg_dump -Fc --no-acl --no-owner "postgresql://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require" > /backups/gqt_db_$(date +%Y%m%d_%H%M%S).dump
   ```
3. **Restoration Runbook:**
   ```bash
   pg_restore --clean --if-exists --no-acl --no-owner -d "postgresql://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require" /backups/gqt_db_YYYYMMDD_HHMMSS.dump
   ```
4. **Zero Data Loss Invariant:** Schema migrations must **never** execute destructive drops (`DROP TABLE`, `DROP COLUMN`) on live production academic records or score ledgers.
