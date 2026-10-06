/** Type definitions for Admin portal entities, reports, and API responses. */

export interface StudentListItem {
  id: string;
  student_id_number: string;
  full_name: string;
  batch_code: string;
  college_name: string;
  graduation_year: number | null;
  total_points: string;
  current_streak_days: number;
  email: string | null;
  mobile_number: string | null;
  is_active: boolean;
  onboarding_status: "ACTIVE" | "PENDING_ACTIVATION" | "SUSPENDED";
  enrolled_courses_count: number;
  avatar_url?: string;
  created_at: string;
}

export interface StudentEnrollment {
  id: string;
  course_id: string;
  course_title: string;
  status: "ACTIVE" | "COMPLETED" | "REVOKED" | "SUSPENDED";
  enrolled_at: string;
  completed_at: string | null;
}

export interface StudentDetail extends StudentListItem {
  avatar_url: string;
  enrollments: StudentEnrollment[];
}

export interface StudentProgressOverview {
  total_modules: number;
  completed_modules: number;
  module_completion_rate: number;
  total_questions: number;
  solved_questions: number;
  question_solve_rate: number;
}

export interface StudentProgressModule {
  module_id: string;
  module_title: string;
  course_title: string;
  status: "LOCKED" | "UNLOCKED" | "IN_PROGRESS" | "COMPLETED";
  score_percentage: string;
  completed_at: string | null;
}

export interface StudentProgressQuestion {
  question_id: string;
  question_title: string;
  module_title: string;
  is_solved: boolean;
  best_score: string;
  attempts_count: number;
  first_solved_at: string | null;
}

export interface StudentProgressData {
  student_id: string;
  student_id_number: string;
  full_name: string;
  overview: StudentProgressOverview;
  modules: StudentProgressModule[];
  questions: StudentProgressQuestion[];
}

export interface StudentScoreRecord {
  id: string;
  source_type: "ASSIGNMENT" | "DAILY_TASK" | "PROJECT" | "STREAK_BONUS" | "ADMIN_ADJUSTMENT";
  source_id: string;
  points: string;
  policy_applied: string;
  awarded_at: string;
}

export interface StudentScoresData {
  student_id: string;
  full_name: string;
  total_points: string;
  breakdown_by_source: Record<string, string>;
  records: StudentScoreRecord[];
}

export interface StudentRankData {
  student_id: string;
  full_name: string;
  batch_code: string;
  total_points: string;
  global_rank: number;
  total_students_global: number;
  batch_rank: number;
  total_students_batch: number;
  current_streak_days: number;
  highest_streak_days: number;
}

export interface CourseItem {
  id: string;
  title: string;
  slug: string;
  description: string;
  thumbnail_url: string;
  is_published: boolean;
  is_deleted: boolean;
  order: number;
  modules_count: number;
  enrolled_students_count: number;
  created_at: string;
  updated_at: string;
}

export interface ModulePrerequisiteItem {
  id: string;
  title: string;
  order_index: number;
}

export interface ModuleItem {
  id: string;
  course_id: string;
  course_title: string;
  title: string;
  slug: string;
  order_index: number;
  summary: string;
  lecture_content: string;
  passing_percentage: string;
  is_published: boolean;
  questions_count: number;
  prerequisites: ModulePrerequisiteItem[];
  created_at: string;
  updated_at: string;
}

export interface TestCaseItem {
  id: string;
  question_id?: string;
  input_data: string;
  expected_output: string;
  is_visible: boolean;
  weight: string;
  order: number;
  created_at: string;
  updated_at: string;
}

export interface CodingQuestionListItem {
  id: string;
  module_id: string;
  module_title: string;
  course_title: string;
  title: string;
  slug: string;
  difficulty: "EASY" | "MEDIUM" | "HARD";
  points: string;
  order: number;
  is_active: boolean;
  test_cases_count: number;
  created_at: string;
}

export interface CodingQuestionDetail extends CodingQuestionListItem {
  problem_statement: string;
  allowed_languages: string[];
  starter_code: Record<string, string>;
  time_limit_seconds: string;
  memory_limit_mb: number;
  test_cases: TestCaseItem[];
  updated_at: string;
}

export interface TaskItem {
  id: string;
  title: string;
  description: string;
  scheduled_date: string;
  question_id: string | null;
  question_title: string | null;
  points: string;
  is_active: boolean;
  completions_count: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectItem {
  id: string;
  title: string;
  slug: string;
  description: string;
  deliverables_instructions: string;
  course_id: string | null;
  course_title: string | null;
  max_score: string;
  due_date: string | null;
  is_active: boolean;
  submissions_count: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectFileItem {
  id: string;
  file_name: string;
  file_size_bytes: number;
  mime_type: string;
  download_url: string;
  uploaded_at: string;
}

export interface ProjectFeedbackItem {
  id: string;
  reviewer_name: string;
  feedback_text: string;
  suggested_changes: string;
  rating: number | null;
  created_at: string;
}

export interface ProjectSubmissionItem {
  id: string;
  project_id: string;
  project_title: string;
  student_id: string;
  student_name: string;
  student_id_number: string;
  student_avatar_url?: string;
  status: "SUBMITTED" | "UNDER_REVIEW" | "CHANGES_REQUESTED" | "APPROVED" | "REJECTED";
  score: string | null;
  max_score: string;
  github_repository_url: string;
  live_demo_url: string;
  notes?: string;
  files?: ProjectFileItem[];
  feedbacks?: ProjectFeedbackItem[];
  reviewed_by_email?: string | null;
  submitted_at: string;
  reviewed_at: string | null;
}

export interface AnnouncementItem {
  id: string;
  title: string;
  content: string;
  target_batch: string;
  priority: "LOW" | "NORMAL" | "HIGH" | "URGENT";
  published_by_email: string | null;
  is_active: boolean;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AnalyticsDashboardData {
  total_students: number;
  active_students: number;
  module_completion_rate: number;
  total_modules: number;
  completed_modules_count: number;
  assignment_statistics: {
    total_submissions: number;
    accepted_submissions: number;
    acceptance_rate: number;
    unique_solved_count: number;
    difficulty_distribution: {
      easy: number;
      medium: number;
      hard: number;
    };
  };
  today_activity: {
    submissions_count: number;
    active_students_count: number;
  };
  project_statistics: {
    total_projects: number;
    total_submissions: number;
    approved_submissions: number;
    approval_rate: number;
    average_score: number;
  };
  score_distribution: Array<{
    bracket: string;
    count: number;
  }>;
  top_performers: Array<{
    id: string;
    full_name: string;
    student_id_number: string;
    batch_code: string;
    total_points: number;
    current_streak_days: number;
  }>;
  activity_timeline: Array<{
    date: string;
    label: string;
    submissions_count: number;
    active_students: number;
  }>;
  filters_applied?: {
    course_id?: string | null;
    batch_code?: string | null;
    days?: number;
  };
}

export interface ExportJobItem {
  id: string;
  user_email: string;
  report_type:
    | "STUDENT_PERFORMANCE"
    | "COURSE_STATISTICS"
    | "ASSIGNMENT_COMPLETION"
    | "PROJECT_PERFORMANCE"
    | "MONTHLY_ACTIVITY"
    | "FULL_EXECUTIVE";
  format: "CSV" | "JSON";
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  filters: Record<string, any>;
  file_name: string;
  file_size_bytes: number;
  row_count: number;
  error_message: string;
  created_at: string;
  completed_at: string | null;
  download_url: string;
}


export interface PerformanceReportData {
  batch_code: string;
  total_students: number;
  average_points: string;
  highest_points: string;
  average_streak_days: number;
  highest_streak_days: number;
  batch_breakdown: Array<{
    batch_code: string;
    student_count: number;
    average_points: string;
    total_points: string;
  }>;
}

export interface CompletionReportData {
  courses: Array<{
    course_id: string;
    course_title: string;
    active_enrollments: number;
    completed_enrollments: number;
    modules: Array<{
      module_id: string;
      module_title: string;
      order_index: number;
      completed_students: number;
      completion_rate: number;
    }>;
  }>;
}

export interface AssignmentReportData {
  questions: Array<{
    question_id: string;
    title: string;
    module_title: string;
    course_title: string;
    difficulty: string;
    points: string;
    total_submissions: number;
    accepted_submissions: number;
    pass_rate: number;
    unique_students_solved: number;
  }>;
}

export interface ProjectReportData {
  projects: Array<{
    project_id: string;
    title: string;
    course_title: string | null;
    max_score: string;
    total_submissions: number;
    approved_submissions: number;
    under_review_submissions: number;
    rejected_submissions: number;
    average_score: string;
  }>;
}

export interface MonthlyActivityReportData {
  days_analyzed: number;
  timeline: Array<{
    date: string;
    submissions_count: number;
    active_students: number;
  }>;
}
