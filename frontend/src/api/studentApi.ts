import { apiClient } from "./client";
import { ApiSuccessResponse } from "../types/api";

export interface DashboardProfile {
  id: string;
  student_id_number: string;
  full_name: string;
  email: string;
  avatar_url: string;
  course: string;
  course_id: string | null;
  batch_code: string;
  college_name: string;
  total_score: number;
  current_rank: number;
  total_students: number;
  completed_modules: number;
  total_modules: number;
  overall_progress: number;
  current_streak_days: number;
  highest_streak_days: number;
}

export interface LeaderboardEntry {
  rank: number;
  student_id: string;
  full_name: string;
  avatar_url: string;
  batch_code: string;
  total_points: number;
  is_current_student: boolean;
  is_in_top_10?: boolean;
}

export interface DashboardProgress {
  overall_progress: number;
  module_completion: {
    completed: number;
    total: number;
    percentage: number;
  };
  assignment_progress: {
    solved: number;
    total: number;
    percentage: number;
    total_points: number;
  };
  project_score: {
    submitted: number;
    approved: number;
    total_score: number;
  };
  task_progress: {
    completed: number;
    total_points: number;
  };
  chart_history: Array<{
    date: string;
    points: number;
    full_date: string;
  }>;
  skills_radar: Array<{
    skill: string;
    score: number;
    fullMark: number;
  }>;
}

export interface RecentSubmission {
  id: string;
  question_title: string;
  language: string;
  status: string;
  execution_time_ms: number | null;
  score_awarded: number;
  submitted_at: string;
}

export interface RecentTask {
  id: string;
  task_title: string;
  scheduled_date: string;
  is_completed: boolean;
  score_awarded: number;
  completed_at: string;
}

export interface RecentAchievement {
  id: string;
  badge_name: string;
  badge_description: string;
  icon_url: string;
  criteria_type: string;
  awarded_at: string;
}

export interface RecentNotification {
  id: string;
  title: string;
  body: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
}

export interface ActivityHeatmapRecord {
  date: string;
  day_name: string;
  month_name: string;
  month_index: number;
  day_of_week: number;
  count: number;
  points: number;
  level: number;
  is_today: boolean;
}

export interface ActivityHeatmapData {
  start_date: string;
  end_date: string;
  current_streak: number;
  longest_streak: number;
  total_active_days: number;
  total_submissions_year: number;
  solved_today: boolean;
  last_activity_date: string | null;
  records: ActivityHeatmapRecord[];
}

export interface StudentDashboardData {
  profile: DashboardProfile;
  leaderboard: {
    top_10: LeaderboardEntry[];
    current_student: LeaderboardEntry;
  };
  progress: DashboardProgress;
  activity: {
    recent_submissions: RecentSubmission[];
    recent_tasks: RecentTask[];
    recent_achievements: RecentAchievement[];
    notifications: RecentNotification[];
  };
  activity_heatmap?: ActivityHeatmapData;
}

export interface StudentCourseItem {
  id: string;
  title: string;
  slug: string;
  description: string;
  thumbnail_url: string;
  is_enrolled: boolean;
  enrollment_status: "ACTIVE" | "COMPLETED" | "REVOKED" | "SUSPENDED" | null;
  completed_modules: number;
  total_modules: number;
  progress_percentage: number;
  continue_module_id: string | null;
}

export interface StudentModuleItem {
  id: string;
  order_index: number;
  title: string;
  slug: string;
  summary: string;
  passing_percentage: number;
  status: "LOCKED" | "UNLOCKED" | "IN_PROGRESS" | "COMPLETED";
  is_accessible: boolean;
  score_percentage: number;
  completed_at: string | null;
}

export interface StudentCourseDetailData {
  course: {
    id: string;
    title: string;
    slug: string;
    description: string;
    thumbnail_url: string;
    total_modules: number;
    completed_modules: number;
    progress_percentage: number;
    continue_module_id: string | null;
  };
  modules: StudentModuleItem[];
}

export interface StudentModuleDetailData {
  id: string;
  course_id: string;
  course_title: string;
  order_index: number;
  title: string;
  slug: string;
  summary: string;
  lecture_content: string;
  passing_percentage: number;
  status: "LOCKED" | "UNLOCKED" | "IN_PROGRESS" | "COMPLETED";
  score_percentage: number;
  completed_at: string | null;
  prev_module_id: string | null;
  next_module_id: string | null;
  is_next_unlocked: boolean;
}

export interface ModuleCompletionResult {
  module_id: string;
  order_index: number;
  title: string;
  status: "COMPLETED";
  score_percentage: number;
  completed_at: string;
  course_id: string;
  course_progress_percentage: number;
  completed_modules_count: number;
  total_modules_count: number;
  next_module: {
    id: string;
    order_index: number;
    title: string;
    status: "UNLOCKED";
  } | null;
}

export interface ModuleProgressItem {
  module_id: string;
  order_index: number;
  title: string;
  total_questions: number;
  solved_questions: number;
  is_locked: boolean;
  is_completed: boolean;
  unlock_requirement: string | null;
}

export interface StudentQuestionItem {
  id: string;
  title: string;
  slug: string;
  difficulty: "EASY" | "MEDIUM" | "HARD";
  points: number;
  module_id: string;
  module_title: string;
  module_order: number;
  course_title: string;
  allowed_languages: string[];
  is_solved: boolean;
  best_score: number;
  attempts_count: number;
  is_module_locked?: boolean;
  module_unlock_requirement?: string | null;
}

export interface StudentTestCaseItem {
  id: string;
  input_data: string;
  expected_output: string;
  order: number;
}

export interface StudentQuestionDetailData {
  id: string;
  title: string;
  slug: string;
  difficulty: "EASY" | "MEDIUM" | "HARD";
  problem_statement: string;
  points: number;
  module_id: string;
  module_title: string;
  module_order: number;
  course_title: string;
  allowed_languages: string[];
  starter_code: Record<string, string>;
  time_limit_seconds: number;
  memory_limit_mb: number;
  visible_test_cases: StudentTestCaseItem[];
  is_solved: boolean;
  best_score: number;
  attempts_count: number;
  is_module_locked?: boolean;
  module_unlock_requirement?: string | null;
  last_submission_code?: string | null;
  last_submission_language?: string | null;
  submissions_by_language?: Record<string, string>;
}

export interface TestRunResultItem {
  order: number;
  input_data: string;
  expected_output: string;
  actual_output: string;
  status: string;
  stderr: string;
  execution_time_ms: number;
  memory_kb: number;
}

export interface CodeRunResponse {
  mode: "SAMPLE_TEST_CASES" | "CUSTOM_INPUT";
  overall_status?: string;
  status?: string;
  stdout?: string;
  stderr?: string;
  execution_time_ms?: number;
  peak_memory_kb?: number;
  exit_code?: number;
  test_results?: TestRunResultItem[];
}

export interface SubmissionTestResultItem {
  order: number;
  is_visible: boolean;
  status: "PASSED" | "FAILED";
  input_data?: string;
  expected_output?: string;
  actual_output?: string;
  stderr?: string;
  execution_time_ms: number;
  memory_kb?: number;
}

export interface CodeSubmitResponse {
  submission_id: string;
  status: string;
  passed_test_cases: number;
  total_test_cases: number;
  score_awarded: number;
  max_points: number;
  execution_time_ms: number;
  peak_memory_kb: number;
  is_solved: boolean;
  best_score: number;
  submitted_at: string;
  results: SubmissionTestResultItem[];
}

export interface QuestionSubmissionHistoryItem {
  id: string;
  question_id: string;
  question_title: string;
  language: string;
  status: string;
  passed_test_cases: number;
  total_test_cases: number;
  score_awarded: number;
  execution_time_ms: number;
  peak_memory_kb: number;
  submitted_at: string;
}

export interface AttendanceRecordItem {
  id: string;
  date: string;
  status: "PRESENT" | "ABSENT" | "LATE" | "EXCUSED";
  session_title: string;
  remarks: string;
  marked_at: string;
}

export interface StudentAttendanceSummary {
  attendance_percentage: number;
  total_classes: number;
  attended_classes: number;
  records: AttendanceRecordItem[];
}

export interface StudentProfileUpdatePayload {
  dob?: string | null;
  avatar_url?: string;
  branch?: string;
  college_name?: string;
  graduation_year?: number | null;
  bio?: string;
  github_url?: string;
  linkedin_url?: string;
}

export const studentApi = {
  getDashboard: async (): Promise<StudentDashboardData> => {
    const { data } = await apiClient.get<ApiSuccessResponse<StudentDashboardData>>(
      "/students/dashboard/"
    );
    return data.data;
  },

  getAttendance: async (): Promise<StudentAttendanceSummary> => {
    const { data } = await apiClient.get<ApiSuccessResponse<StudentAttendanceSummary>>(
      "/students/me/attendance/"
    );
    return data.data;
  },

  getActivityHeatmap: async (): Promise<ActivityHeatmapData> => {
    const { data } = await apiClient.get<ApiSuccessResponse<ActivityHeatmapData>>(
      "/students/activity-heatmap/"
    );
    return data.data;
  },

  updateProfile: async (payload: StudentProfileUpdatePayload): Promise<any> => {
    const { data } = await apiClient.patch<ApiSuccessResponse<any>>(
      "/students/me/profile/",
      payload
    );
    return data.data;
  },

  uploadAvatar: async (file: File): Promise<{ avatar_url: string; relative_url?: string; user?: any; student_profile?: any }> => {
    const formData = new FormData();
    formData.append("avatar", file);
    const { data } = await apiClient.post<
      ApiSuccessResponse<{ avatar_url: string; relative_url?: string; user?: any; student_profile?: any }>
    >("/auth/avatar/upload/", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return data.data;
  },

  getLeaderboard: async (): Promise<{ top_10: LeaderboardEntry[]; current_student: LeaderboardEntry }> => {
    const { data } = await apiClient.get<
      ApiSuccessResponse<{ top_10: LeaderboardEntry[]; current_student: LeaderboardEntry }>
    >("/students/leaderboard/");
    return data.data;
  },

  getCourses: async (): Promise<StudentCourseItem[]> => {
    const { data } = await apiClient.get<ApiSuccessResponse<{ courses: StudentCourseItem[] }>>(
      "/students/courses/"
    );
    return data.data.courses;
  },

  getCourseDetail: async (courseId: string): Promise<StudentCourseDetailData> => {
    const { data } = await apiClient.get<ApiSuccessResponse<StudentCourseDetailData>>(
      `/students/courses/${courseId}/`
    );
    return data.data;
  },

  getModuleDetail: async (moduleId: string): Promise<StudentModuleDetailData> => {
    const { data } = await apiClient.get<ApiSuccessResponse<StudentModuleDetailData>>(
      `/students/modules/${moduleId}/`
    );
    return data.data;
  },

  completeModule: async (
    moduleId: string,
    scorePercentage?: number
  ): Promise<ModuleCompletionResult> => {
    const { data } = await apiClient.post<ApiSuccessResponse<ModuleCompletionResult>>(
      `/students/modules/${moduleId}/complete/`,
      { score_percentage: scorePercentage }
    );
    return data.data;
  },

  // --------------------------------------------------------------------------
  // CODING PRACTICE & AUTOMATED ASSESSMENT SANDBOX
  // --------------------------------------------------------------------------
  getQuestions: async (params?: {
    module_id?: string;
    difficulty?: string;
    search?: string;
  }): Promise<{ questions: StudentQuestionItem[]; modules_progress: ModuleProgressItem[] }> => {
    const { data } = await apiClient.get<
      ApiSuccessResponse<{
        questions: StudentQuestionItem[];
        modules_progress: ModuleProgressItem[];
      }>
    >("/students/assignments/questions/", { params });
    return data.data;
  },

  getQuestionDetail: async (questionId: string): Promise<StudentQuestionDetailData> => {
    const { data } = await apiClient.get<ApiSuccessResponse<StudentQuestionDetailData>>(
      `/students/assignments/questions/${questionId}/`
    );
    return data.data;
  },

  runCode: async (
    questionId: string,
    payload: { language: string; source_code: string; custom_input?: string }
  ): Promise<CodeRunResponse> => {
    const { data } = await apiClient.post<ApiSuccessResponse<CodeRunResponse>>(
      `/students/assignments/questions/${questionId}/run/`,
      payload
    );
    return data.data;
  },

  submitCode: async (
    questionId: string,
    payload: { language: string; source_code: string }
  ): Promise<CodeSubmitResponse> => {
    const { data } = await apiClient.post<ApiSuccessResponse<CodeSubmitResponse>>(
      `/students/assignments/questions/${questionId}/submit/`,
      payload
    );
    return data.data;
  },

  getQuestionSubmissions: async (
    questionId: string
  ): Promise<QuestionSubmissionHistoryItem[]> => {
    const { data } = await apiClient.get<
      ApiSuccessResponse<{ submissions: QuestionSubmissionHistoryItem[] }>
    >(`/students/assignments/questions/${questionId}/submissions/`);
    return data.data.submissions;
  },

  // --------------------------------------------------------------------------
  // AI LEARNING MENTOR & TUTOR CONSULTATIONS
  // --------------------------------------------------------------------------
  getAIConversations: async (): Promise<AIConversationItem[]> => {
    const { data } = await apiClient.get<
      ApiSuccessResponse<{ conversations: AIConversationItem[]; count: number }>
    >("/students/ai/conversations/");
    return data.data.conversations;
  },

  createAIConversation: async (payload?: {
    title?: string;
    context_question_id?: string;
    initial_message?: string;
  }): Promise<AIConversationDetail> => {
    const { data } = await apiClient.post<ApiSuccessResponse<AIConversationDetail>>(
      "/students/ai/conversations/",
      payload || {}
    );
    return data.data;
  },

  getAIConversationDetail: async (conversationId: string): Promise<AIConversationDetail> => {
    const { data } = await apiClient.get<ApiSuccessResponse<AIConversationDetail>>(
      `/students/ai/conversations/${conversationId}/`
    );
    return data.data;
  },

  sendAIMessage: async (
    conversationId: string,
    payload: { content: string }
  ): Promise<AIMessageItem> => {
    const { data } = await apiClient.post<ApiSuccessResponse<AIMessageItem>>(
      `/students/ai/conversations/${conversationId}/messages/`,
      payload
    );
    return data.data;
  },

  retryAIMessage: async (conversationId: string): Promise<AIMessageItem> => {
    const { data } = await apiClient.post<ApiSuccessResponse<AIMessageItem>>(
      `/students/ai/conversations/${conversationId}/retry/`
    );
    return data.data;
  },

  archiveAIConversation: async (conversationId: string): Promise<void> => {
    await apiClient.delete(`/students/ai/conversations/${conversationId}/`);
  },

  // --------------------------------------------------------------------------
  // DAILY PRACTICE TASKS
  // --------------------------------------------------------------------------
  getTasks: async (params?: {
    status?: string;
  }): Promise<{ tasks: StudentTaskItem[]; count: number }> => {
    const { data } = await apiClient.get<
      ApiSuccessResponse<{ tasks: StudentTaskItem[]; count: number }>
    >("/students/tasks/", { params });
    return data.data;
  },

  getTaskDetail: async (taskId: string): Promise<StudentTaskDetail> => {
    const { data } = await apiClient.get<ApiSuccessResponse<StudentTaskDetail>>(
      `/students/tasks/${taskId}/`
    );
    return data.data;
  },

  completeTask: async (
    taskId: string,
    payload?: { submission_notes?: string }
  ): Promise<StudentTaskCompletionResponse> => {
    const { data } = await apiClient.post<
      ApiSuccessResponse<StudentTaskCompletionResponse>
    >(`/students/tasks/${taskId}/complete/`, payload || {});
    return data.data;
  },

  // --------------------------------------------------------------------------
  // CAPSTONE PROJECTS
  // --------------------------------------------------------------------------
  getProjects: async (): Promise<{ projects: StudentProjectItem[]; count: number }> => {
    const { data } = await apiClient.get<
      ApiSuccessResponse<{ projects: StudentProjectItem[]; count: number }>
    >("/students/projects/");
    return data.data;
  },

  getProjectDetail: async (projectId: string): Promise<StudentProjectDetailData> => {
    const { data } = await apiClient.get<
      ApiSuccessResponse<StudentProjectDetailData>
    >(`/students/projects/${projectId}/`);
    return data.data;
  },

  submitProject: async (
    projectId: string,
    payload: StudentProjectSubmitPayload
  ): Promise<any> => {
    const { data } = await apiClient.post<ApiSuccessResponse<any>>(
      `/students/projects/${projectId}/submit/`,
      payload
    );
    return data.data;
  },

  // --------------------------------------------------------------------------
  // NOTIFICATIONS & ANNOUNCEMENTS
  // --------------------------------------------------------------------------
  getNotifications: async (params?: {
    is_read?: boolean;
    notification_type?: string;
  }): Promise<{ notifications: StudentNotificationItem[]; count: number; unread_count: number }> => {
    const { data } = await apiClient.get<
      ApiSuccessResponse<{
        notifications: StudentNotificationItem[];
        count: number;
        unread_count: number;
      }>
    >("/students/notifications/", { params });
    return data.data;
  },

  getUnreadNotificationsCount: async (): Promise<number> => {
    const { data } = await apiClient.get<ApiSuccessResponse<{ unread_count: number }>>(
      "/students/notifications/unread-count/"
    );
    return data.data.unread_count;
  },

  markNotificationAsRead: async (
    notificationId: string
  ): Promise<{ notification: StudentNotificationItem; unread_count: number }> => {
    const { data } = await apiClient.post<
      ApiSuccessResponse<{ notification: StudentNotificationItem; unread_count: number }>
    >(`/students/notifications/${notificationId}/read/`);
    return data.data;
  },

  markAllNotificationsAsRead: async (): Promise<{ updated_count: number; unread_count: number }> => {
    const { data } = await apiClient.post<
      ApiSuccessResponse<{ updated_count: number; unread_count: number }>
    >("/students/notifications/mark-all-read/");
    return data.data;
  },

  deleteNotification: async (notificationId: string): Promise<void> => {
    await apiClient.delete(`/students/notifications/${notificationId}/`);
  },

  getAnnouncements: async (): Promise<StudentAnnouncementItem[]> => {
    const { data } = await apiClient.get<
      ApiSuccessResponse<{ announcements: StudentAnnouncementItem[]; count: number }>
    >("/students/notifications/announcements/");
    return data.data.announcements;
  },

  // --------------------------------------------------------------------------
  // ACHIEVEMENTS, BADGES & VERIFIED CERTIFICATES
  // --------------------------------------------------------------------------
  getAchievements: async (): Promise<BadgeItem[]> => {
    const { data } = await apiClient.get<ApiSuccessResponse<{ badges: BadgeItem[]; count: number }>>(
      "/students/achievements/"
    );
    return data.data.badges;
  },

  getCertificates: async (): Promise<StudentCertificateItem[]> => {
    const { data } = await apiClient.get<
      ApiSuccessResponse<{ certificates: StudentCertificateItem[]; count: number }>
    >("/students/certificates/");
    return data.data.certificates;
  },

  verifyCertificate: async (identifier: string): Promise<CertificateVerificationResult> => {
    const { data } = await apiClient.get<ApiSuccessResponse<CertificateVerificationResult>>(
      `/certificates/verify/${identifier}/`
    );
    return data.data;
  },

  // --------------------------------------------------------------------------
  // QR ATTENDANCE & TELEMETRY
  // --------------------------------------------------------------------------
  getAttendanceTelemetry: async (): Promise<StudentAttendanceData> => {
    const { data } = await apiClient.get<ApiSuccessResponse<StudentAttendanceData>>(
      "/students/me/attendance/"
    );
    return data.data;
  },

  scanAttendanceQR: async (payload: {
    qr_data: string;
    session_code?: string;
  }): Promise<ScanAttendanceQRResponse> => {
    const { data } = await apiClient.post<ApiSuccessResponse<ScanAttendanceQRResponse>>(
      "/students/attendance/scan-qr/",
      payload
    );
    return data.data;
  },

  // --------------------------------------------------------------------------
  // CONTACT & INSTITUTIONAL SUPPORT
  // --------------------------------------------------------------------------
  getCompanyInfo: async (): Promise<CompanyInfoData> => {
    const { data } = await apiClient.get<ApiSuccessResponse<CompanyInfoData>>("/contact/info/");
    return data.data;
  },

  submitContactInquiry: async (payload: {
    name: string;
    email: string;
    subject: string;
    category?: string;
    message: string;
    website?: string;
  }): Promise<ContactInquiryResponse> => {
    const { data } = await apiClient.post<ApiSuccessResponse<ContactInquiryResponse>>(
      "/contact/inquiries/",
      payload
    );
    return data.data;
  },
};

export interface StudentAttendanceData {
  student: {
    full_name: string;
    student_id: string;
    batch_code: string;
    course_name: string;
    college_name: string;
    has_enrollments: boolean;
    enrolled_courses: string[];
  };
  student_qr_data: string;
  attendance_percentage: number;
  total_classes: number;
  attended_classes: number;
  missed_classes: number;
  current_streak_days: number;
  records: {
    id: string;
    date: string;
    session_title: string;
    status: "PRESENT" | "ABSENT" | "LATE" | "EXCUSED" | string;
    remarks: string;
    created_at: string;
  }[];
}

export interface ScanAttendanceQRResponse {
  success: boolean;
  message: string;
  is_already_marked: boolean;
  attendance: {
    id: string;
    date: string;
    session_title: string;
    status: string;
    remarks: string;
    timestamp: string;
  };
  student: {
    full_name: string;
    student_id: string;
    batch_code: string;
    course_name: string;
    college_name: string;
  };
  stats: {
    attendance_percentage: number;
    attended_classes: number;
    total_classes: number;
    streak_days: number;
  };
}

export interface CompanyInfoData {
  company_name: string;
  tagline: string;
  support_email: string;
  admissions_email: string;
  phone_primary: string;
  phone_support: string;
  office_address: {
    street: string;
    city: string;
    state: string;
    postal_code: string;
    country: string;
  };
  office_hours: string;
  social_links: {
    linkedin: string;
    github: string;
    youtube: string;
    twitter: string;
  };
}

export interface ContactInquiryResponse {
  id: string;
  name: string;
  email: string;
  subject: string;
  category: string;
  status: string;
  created_at: string;
}


export interface BadgeItem {
  id: string;
  slug: string;
  name: string;
  description: string;
  icon_url: string;
  criteria_type: string;
  criteria_threshold: number;
  points_reward: number;
  is_unlocked: boolean;
  awarded_at: string | null;
  progress_percentage: number;
}

export interface StudentCertificateItem {
  id: string;
  certificate_id: string;
  title: string;
  student_name: string;
  course_title: string;
  verification_hash: string;
  issued_at: string;
  pdf_file: string | null;
  is_revoked: boolean;
}

export interface CertificateVerificationResult {
  is_valid: boolean;
  status: "VERIFIED" | "REVOKED";
  certificate_id: string;
  title?: string;
  student_name?: string;
  student_id_number?: string;
  course_title?: string;
  issued_at?: string;
  verification_hash?: string;
  has_pdf?: boolean;
  download_url?: string;
  message?: string;
}

export interface AIMessageItem {
  id: string;
  sender: "STUDENT" | "ASSISTANT" | "SYSTEM";
  content: string;
  tokens_used: number;
  created_at: string;
}

export interface AIConversationItem {
  id: string;
  title: string;
  is_archived: boolean;
  messages_count: number;
  last_message_preview: string;
  created_at: string;
  updated_at: string;
}

export interface AIConversationDetail {
  id: string;
  title: string;
  context_question?: string | null;
  context_question_title?: string | null;
  is_archived: boolean;
  messages: AIMessageItem[];
  created_at: string;
  updated_at: string;
}

export interface StudentNotificationItem {
  id: string;
  title: string;
  body: string;
  notification_type:
    | "TASK_DEADLINE"
    | "PROJECT_MARKED"
    | "RANK_CHANGE"
    | "ADMIN_ANNOUNCEMENT"
    | "ACHIEVEMENT"
    | "CERTIFICATE"
    | "SUBMISSION_GRADED"
    | "MODULE_UNLOCKED"
    | "PROJECT_FEEDBACK"
    | "STREAK_ALERT"
    | "DEADLINE_REMINDER"
    | "TASK_COMPLETED"
    | "SYSTEM_NOTICE";
  notification_type_display: string;
  is_read: boolean;
  read_at: string | null;
  action_url: string;
  created_at: string;
  metadata?: Record<string, any>;
}

export interface StudentAnnouncementItem {
  id: string;
  title: string;
  content: string;
  priority: "LOW" | "NORMAL" | "HIGH" | "URGENT";
  published_by_name: string;
  published_at: string;
  created_at: string;
  expires_at: string | null;
}

export interface StudentTaskItem {
  id: string;
  title: string;
  description: string;
  scheduled_date: string | null;
  deadline: string | null;
  points: number;
  question_id: string | null;
  question_title: string | null;
  course_id: string | null;
  course_title: string | null;
  status: "PENDING" | "COMPLETED" | "OVERDUE" | "DUE_SOON" | string;
  deadline_status: string;
  is_completed: boolean;
  completed_at: string | null;
  score_awarded: number;
  submission_notes: string;
}

export interface StudentTaskDetail extends StudentTaskItem {}

export interface StudentTaskCompletionResponse {
  id: string;
  task_id: string;
  student_id: string;
  is_completed: boolean;
  score_awarded: number;
  completed_at: string;
  submission_notes: string;
  status: string;
}

export interface StudentProjectItem {
  id: string;
  title: string;
  slug: string;
  description: string;
  course_id: string | null;
  course_title: string | null;
  max_score: number;
  due_date: string | null;
  has_submitted: boolean;
  submission_id: string | null;
  status: "NOT_SUBMITTED" | "PENDING_REVIEW" | "APPROVED" | "CHANGES_REQUESTED" | "REJECTED" | string;
  score: number | null;
  submitted_at: string | null;
}

export interface ProjectFeedbackItem {
  id: string;
  reviewer_name: string;
  feedback_text: string;
  suggested_changes: string;
  rating: number | null;
  created_at: string;
}

export interface ProjectFileItem {
  id: string;
  file_name: string;
  file_size_bytes: number;
  mime_type: string;
  download_url: string;
  uploaded_at: string;
}

export interface StudentProjectSubmissionDetail {
  id: string;
  github_repository_url: string;
  live_demo_url: string;
  notes: string;
  status: string;
  score: number | null;
  submitted_at: string;
  reviewed_at: string | null;
  files: ProjectFileItem[];
  feedbacks: ProjectFeedbackItem[];
}

export interface StudentProjectDetailData extends StudentProjectItem {
  deliverables_instructions: string;
  submission_detail: StudentProjectSubmissionDetail | null;
}

export interface StudentProjectSubmitPayload {
  github_repository_url?: string;
  live_demo_url?: string;
  notes?: string;
}



