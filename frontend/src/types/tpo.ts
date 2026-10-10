import { College } from "./college";

export interface TPOProfile {
  id: string;
  email: string;
  mobile_number?: string | null;
  user_is_active?: boolean;
  user_onboarding_status?: string;
  role?: string;
  full_name: string;
  designation: string;
  department: string;
  phone_number?: string;
  bio?: string;
  avatar_url?: string;
  is_active: boolean;
  college?: College | null;
  assigned_by_email?: string | null;
  assigned_at?: string | null;
  revoked_by_email?: string | null;
  revoked_at?: string | null;
  user_id?: string;
  created_at: string;
  updated_at: string;
}

export interface RegisterTPOPayload {
  full_name: string;
  email: string;
  password: string;
  college_id?: string;
  college_name?: string;
  mobile_number?: string;
  designation?: string;
  department?: string;
  phone_number?: string;
  bio?: string;
}

export interface CreateTPOPayload {
  email: string;
  full_name: string;
  college_id: string;
  designation?: string;
  department?: string;
  phone_number?: string;
  bio?: string;
}

export interface ApproveTPOPayload {
  college_id?: string;
}

export interface UpdateTPOPayload {
  full_name?: string;
  designation?: string;
  department?: string;
  phone_number?: string;
  bio?: string;
  avatar_url?: string;
}

export interface ReassignCollegePayload {
  college_id: string;
}

export interface TPOAuditLog {
  id: string;
  action: string;
  actor_email: string;
  ip_address?: string | null;
  payload: Record<string, any>;
  created_at: string;
}

export interface TPOCollegeSummaryDistribution {
  name: string;
  count: number;
}

export interface TPOCollegeSummaryBatch {
  batch_code: string;
  count: number;
}

export interface TPOCollegeSummaryPerformer {
  id: string;
  student_id_number: string;
  full_name: string;
  total_points: number;
  batch_code: string;
  branch: string;
  attendance_percentage: number;
  avatar_url?: string;
}

export interface TPOCollegeSummary {
  college: College;
  total_students: number;
  active_students: number;
  inactive_students: number;
  average_attendance_percentage: number;
  students_above_75_attendance: number;
  total_submissions: number;
  accepted_submissions: number;
  technology_distribution: TPOCollegeSummaryDistribution[];
  branch_distribution: TPOCollegeSummaryDistribution[];
  batch_distribution: TPOCollegeSummaryBatch[];
  graduation_year_distribution?: { graduation_year: number; count: number }[];
  top_performers: TPOCollegeSummaryPerformer[];
}

export interface TPOStudentRosterItem {
  id: string;
  student_id_number: string;
  full_name: string;
  email: string;
  mobile_number?: string;
  batch_code: string;
  college_id?: string;
  college_name: string;
  branch: string;
  graduation_year?: number | null;
  course_opted: string;
  attendance_percentage: number;
  total_points: number;
  current_streak_days: number;
  highest_streak_days: number;
  avatar_url?: string;
  is_active: boolean;
  created_at: string;
}

export interface TPOStudentEnrollment {
  id: string;
  course_id: string;
  course_title: string;
  status: string;
  enrolled_at: string;
  completed_at?: string | null;
}

export interface TPOStudentSubmission {
  id: string;
  question_id?: string | null;
  question_title: string;
  language: string;
  status: string;
  score_awarded: number;
  passed_test_cases: number;
  total_test_cases: number;
  submitted_at: string;
}

export interface TPOStudentAttendanceRecord {
  id: string;
  date: string;
  session_title: string;
  technology: string;
  status: string;
  remarks?: string;
}

export interface TPOStudentDetail {
  id: string;
  user_id?: string | null;
  student_id_number: string;
  full_name: string;
  email: string;
  batch_code: string;
  college_id?: string | null;
  college_name: string;
  branch: string;
  graduation_year?: number | null;
  course_opted: string;
  bio?: string;
  github_url?: string;
  linkedin_url?: string;
  attendance_percentage: number;
  total_classes: number;
  attended_classes: number;
  current_streak_days: number;
  highest_streak_days: number;
  total_points: number;
  avatar_url?: string;
  is_active: boolean;
  created_at: string;
  enrollments: TPOStudentEnrollment[];
  recent_submissions: TPOStudentSubmission[];
  score_breakdown: Record<string, number>;
  recent_attendance: TPOStudentAttendanceRecord[];
}

// --- Phase 5 Analytics Interfaces ---

export interface TPOCourseProgressionSummary {
  course_id: string;
  course_title: string;
  enrolled_count: number;
  completed_count: number;
  in_progress_count: number;
}

export interface TPOModuleCompletionSummary {
  module_id: string;
  module_title: string;
  course_title: string;
  order_index: number;
  completed_count: number;
  in_progress_count: number;
}

export interface TPOStudentProgressItem {
  id: string;
  student_id_number: string;
  full_name: string;
  batch_code: string;
  branch: string;
  graduation_year?: number | null;
  course_opted: string;
  completed_modules: number;
  total_modules: number;
  progress_percentage: number;
  status: "COMPLETED" | "ON_TRACK" | "NOT_STARTED" | string;
}

export interface TPOLearningProgressResponse {
  total_students: number;
  total_courses: number;
  total_modules: number;
  course_progression: TPOCourseProgressionSummary[];
  module_completion: TPOModuleCompletionSummary[];
  student_progress: TPOStudentProgressItem[];
}

export interface TPOLanguageStat {
  language: string;
  total_submissions: number;
  accepted_submissions: number;
  pass_rate: number;
}

export interface TPORecentSubmissionTimelineItem {
  id: string;
  student_id: string;
  student_name: string;
  student_id_number: string;
  question_title: string;
  language: string;
  status: string;
  score_awarded: number;
  passed_test_cases: number;
  total_test_cases: number;
  submitted_at: string;
}

export interface TPOAssignmentsLabsResponse {
  total_students: number;
  participating_students: number;
  unattempted_students: number;
  total_attempts: number;
  unique_questions_attempted: number;
  accepted_submissions: number;
  rejected_submissions: number;
  pending_submissions: number;
  pass_rate_percentage: number;
  verdict_breakdown: Record<string, number>;
  language_stats: TPOLanguageStat[];
  recent_timeline: TPORecentSubmissionTimelineItem[];
}

export interface TPOAttendanceBandStat {
  count: number;
  percentage: number;
}

export interface TPOAttendanceDistributionBands {
  excellent_gte_85: TPOAttendanceBandStat;
  satisfactory_75_to_84: TPOAttendanceBandStat;
  critical_below_75: TPOAttendanceBandStat;
}

export interface TPOAttendanceBatchBreakdown {
  batch_code: string;
  student_count: number;
  average_attendance: number;
}

export interface TPOCriticalAttendanceStudent {
  id: string;
  student_id_number: string;
  full_name: string;
  batch_code: string;
  branch: string;
  graduation_year?: number | null;
  attendance_percentage: number;
  attended_classes: number;
  total_classes: number;
}

export interface TPOAttendanceAnalyticsResponse {
  total_students: number;
  college_average_attendance: number;
  policy_threshold_percentage: number;
  distribution_bands: TPOAttendanceDistributionBands;
  batch_breakdown: TPOAttendanceBatchBreakdown[];
  critical_students: TPOCriticalAttendanceStudent[];
  has_session_records: boolean;
}

export interface TPOMonthlyScoreTrend {
  period: string;
  total_points: number;
  awards_count: number;
}

export interface TPOMonthlySubmissionTrend {
  period: string;
  total_submissions: number;
  accepted_submissions: number;
  pass_rate: number;
}

export interface TPOPerformanceTrendsResponse {
  has_sufficient_history: boolean;
  unavailable_reason: string;
  monthly_score_trends: TPOMonthlyScoreTrend[];
  monthly_submission_trends: TPOMonthlySubmissionTrend[];
}

export interface TPOSupportReason {
  code: "LOW_ATTENDANCE" | "ZERO_SUBMISSIONS" | "HIGH_FAILURE_RATE" | "STALLED_PROGRESS" | string;
  label: string;
  severity: "HIGH" | "MEDIUM" | "LOW" | string;
  detail: string;
}

export interface TPOStudentNeedingSupport {
  id: string;
  student_id_number: string;
  full_name: string;
  batch_code: string;
  branch: string;
  graduation_year?: number | null;
  course_opted: string;
  attendance_percentage: number;
  total_points: number;
  submissions_count: number;
  accepted_submissions_count: number;
  reasons: TPOSupportReason[];
}

export interface TPOLeaderboardItem {
  rank: number;
  id: string;
  student_id_number: string;
  full_name: string;
  batch_code: string;
  branch: string;
  graduation_year?: number | null;
  course_opted: string;
  total_points: number;
  attendance_percentage: number;
  current_streak_days: number;
  avatar_url?: string;
}

export interface TPOReportType {
  id: string;
  name: string;
  description: string;
  supported_formats: string[];
  supported_filters: string[];
}

export interface TPOReportFilterPayload {
  batch_code?: string;
  graduation_year?: number | string;
  course_opted?: string;
  is_active?: boolean;
  risk_type?: string;
  date_from?: string;
  date_to?: string;
}

export interface TPOReportPreviewRequest {
  report_type: string;
  filters?: TPOReportFilterPayload;
}

export interface TPOReportPreviewResponse {
  report_type: string;
  report_name?: string;
  college?: {
    id: string;
    name: string;
    code: string;
  };
  college_id?: string;
  college_name?: string;
  total_rows: number;
  columns: string[];
  preview_rows: (string | number | boolean | null)[][];
  generated_at: string;
  is_truncated?: boolean;
  limitations?: string;
}

export interface TPOReportExportRequest {
  report_type: string;
  format: "csv" | "json";
  filters?: TPOReportFilterPayload;
}


