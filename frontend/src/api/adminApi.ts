import { apiClient } from "./client";
import { ApiSuccessResponse, PaginatedResponse } from "../types/api";
import {
  StudentListItem,
  StudentDetail,
  StudentEnrollment,
  StudentProgressData,
  StudentScoresData,
  StudentRankData,
  CourseItem,
  ModuleItem,
  CodingQuestionListItem,
  CodingQuestionDetail,
  TestCaseItem,
  TaskItem,
  ProjectItem,
  ProjectSubmissionItem,
  AnnouncementItem,
  AnalyticsDashboardData,
  PerformanceReportData,
  CompletionReportData,
  AssignmentReportData,
  ProjectReportData,
  MonthlyActivityReportData,
  ExportJobItem,
} from "../types/admin";

export const adminApi = {
  // ==========================================
  // 1. STUDENTS
  // ==========================================
  getStudents: async (params?: Record<string, any>): Promise<PaginatedResponse<StudentListItem>> => {
    const { data } = await apiClient.get<PaginatedResponse<StudentListItem>>("/admin/students/", { params });
    return data;
  },

  getStudentDetail: async (id: string): Promise<StudentDetail> => {
    const { data } = await apiClient.get<ApiSuccessResponse<StudentDetail>>(`/admin/students/${id}/`);
    return data.data;
  },

  provisionStudent: async (payload: {
    full_name: string;
    student_id_number: string;
    batch_code: string;
    email?: string;
    mobile_number?: string;
    password?: string;
    college_name?: string;
    graduation_year?: number;
    onboarding_status?: string;
  }): Promise<StudentDetail> => {
    const { data } = await apiClient.post<ApiSuccessResponse<StudentDetail>>("/admin/students/", payload);
    return data.data;
  },

  updateStudent: async (id: string, payload: Partial<StudentDetail>): Promise<StudentDetail> => {
    const { data } = await apiClient.patch<ApiSuccessResponse<StudentDetail>>(`/admin/students/${id}/`, payload);
    return data.data;
  },

  assignCourses: async (studentId: string, courseIds: string[]): Promise<StudentEnrollment[]> => {
    const { data } = await apiClient.post<ApiSuccessResponse<StudentEnrollment[]>>(
      `/admin/students/${studentId}/courses/`,
      { course_ids: courseIds }
    );
    return data.data;
  },

  getStudentProgress: async (id: string): Promise<StudentProgressData> => {
    const { data } = await apiClient.get<ApiSuccessResponse<StudentProgressData>>(
      `/admin/students/${id}/progress/`
    );
    return data.data;
  },

  getStudentScores: async (id: string): Promise<StudentScoresData> => {
    const { data } = await apiClient.get<ApiSuccessResponse<StudentScoresData>>(
      `/admin/students/${id}/scores/`
    );
    return data.data;
  },

  getStudentRank: async (id: string): Promise<StudentRankData> => {
    const { data } = await apiClient.get<ApiSuccessResponse<StudentRankData>>(`/admin/students/${id}/rank/`);
    return data.data;
  },

  // ==========================================
  // 2. COURSES
  // ==========================================
  getCourses: async (params?: Record<string, any>): Promise<PaginatedResponse<CourseItem>> => {
    const { data } = await apiClient.get<PaginatedResponse<CourseItem>>("/admin/courses/", { params });
    return data;
  },

  getCourseDetail: async (id: string): Promise<CourseItem> => {
    const { data } = await apiClient.get<ApiSuccessResponse<CourseItem>>(`/admin/courses/${id}/`);
    return data.data;
  },

  createCourse: async (payload: {
    title: string;
    slug?: string;
    description?: string;
    thumbnail_url?: string;
    is_published?: boolean;
    order?: number;
  }): Promise<CourseItem> => {
    const { data } = await apiClient.post<ApiSuccessResponse<CourseItem>>("/admin/courses/", payload);
    return data.data;
  },

  updateCourse: async (id: string, payload: Partial<CourseItem>): Promise<CourseItem> => {
    const { data } = await apiClient.patch<ApiSuccessResponse<CourseItem>>(`/admin/courses/${id}/`, payload);
    return data.data;
  },

  archiveCourse: async (id: string): Promise<CourseItem> => {
    const { data } = await apiClient.delete<ApiSuccessResponse<CourseItem>>(`/admin/courses/${id}/`);
    return data.data;
  },

  publishCourse: async (id: string, is_published: boolean): Promise<CourseItem> => {
    const { data } = await apiClient.post<ApiSuccessResponse<CourseItem>>(`/admin/courses/${id}/publish/`, {
      is_published,
    });
    return data.data;
  },

  // ==========================================
  // 3. MODULES
  // ==========================================
  getModules: async (params?: Record<string, any>): Promise<PaginatedResponse<ModuleItem>> => {
    const { data } = await apiClient.get<PaginatedResponse<ModuleItem>>("/admin/modules/", { params });
    return data;
  },

  getModuleDetail: async (id: string): Promise<ModuleItem> => {
    const { data } = await apiClient.get<ApiSuccessResponse<ModuleItem>>(`/admin/modules/${id}/`);
    return data.data;
  },

  createModule: async (payload: {
    course_id: string;
    title: string;
    slug?: string;
    order_index?: number;
    summary?: string;
    lecture_content?: string;
    passing_percentage?: number;
    is_published?: boolean;
    prerequisite_ids?: string[];
  }): Promise<ModuleItem> => {
    const { data } = await apiClient.post<ApiSuccessResponse<ModuleItem>>("/admin/modules/", payload);
    return data.data;
  },

  updateModule: async (id: string, payload: Partial<ModuleItem> & { prerequisite_ids?: string[] }): Promise<ModuleItem> => {
    const { data } = await apiClient.patch<ApiSuccessResponse<ModuleItem>>(`/admin/modules/${id}/`, payload);
    return data.data;
  },

  reorderModules: async (courseId: string, orders: Array<{ id: string; order_index: number }>): Promise<ModuleItem[]> => {
    const { data } = await apiClient.post<ApiSuccessResponse<ModuleItem[]>>("/admin/modules/reorder/", {
      course_id: courseId,
      orders,
    });
    return data.data;
  },

  publishModule: async (id: string, is_published: boolean): Promise<ModuleItem> => {
    const { data } = await apiClient.post<ApiSuccessResponse<ModuleItem>>(`/admin/modules/${id}/publish/`, {
      is_published,
    });
    return data.data;
  },

  // ==========================================
  // 4. ASSIGNMENTS & TEST CASES
  // ==========================================
  getQuestions: async (params?: Record<string, any>): Promise<PaginatedResponse<CodingQuestionListItem>> => {
    const { data } = await apiClient.get<PaginatedResponse<CodingQuestionListItem>>(
      "/admin/assignments/questions/",
      { params }
    );
    return data;
  },

  getQuestionDetail: async (id: string): Promise<CodingQuestionDetail> => {
    const { data } = await apiClient.get<ApiSuccessResponse<CodingQuestionDetail>>(
      `/admin/assignments/questions/${id}/`
    );
    return data.data;
  },

  createQuestion: async (payload: {
    module_id: string;
    title: string;
    slug?: string;
    difficulty: "EASY" | "MEDIUM" | "HARD";
    problem_statement: string;
    allowed_languages?: string[];
    starter_code?: Record<string, string>;
    time_limit_seconds?: number;
    memory_limit_mb?: number;
    points?: number;
    order?: number;
    is_active?: boolean;
    test_cases?: Array<{
      input_data: string;
      expected_output: string;
      is_visible: boolean;
      weight?: number;
      order?: number;
    }>;
  }): Promise<CodingQuestionDetail> => {
    const { data } = await apiClient.post<ApiSuccessResponse<CodingQuestionDetail>>(
      "/admin/assignments/questions/",
      payload
    );
    return data.data;
  },

  updateQuestion: async (id: string, payload: Partial<CodingQuestionDetail>): Promise<CodingQuestionDetail> => {
    const { data } = await apiClient.patch<ApiSuccessResponse<CodingQuestionDetail>>(
      `/admin/assignments/questions/${id}/`,
      payload
    );
    return data.data;
  },

  archiveQuestion: async (id: string): Promise<CodingQuestionDetail> => {
    const { data } = await apiClient.delete<ApiSuccessResponse<CodingQuestionDetail>>(
      `/admin/assignments/questions/${id}/`
    );
    return data.data;
  },

  addTestCase: async (questionId: string, payload: {
    input_data: string;
    expected_output: string;
    is_visible: boolean;
    weight?: number;
    order?: number;
  }): Promise<TestCaseItem> => {
    const { data } = await apiClient.post<ApiSuccessResponse<TestCaseItem>>(
      `/admin/assignments/questions/${questionId}/testcases/`,
      payload
    );
    return data.data;
  },

  updateTestCase: async (testCaseId: string, payload: Partial<TestCaseItem>): Promise<TestCaseItem> => {
    const { data } = await apiClient.patch<ApiSuccessResponse<TestCaseItem>>(
      `/admin/assignments/testcases/${testCaseId}/`,
      payload
    );
    return data.data;
  },

  deleteTestCase: async (testCaseId: string): Promise<void> => {
    await apiClient.delete(`/admin/assignments/testcases/${testCaseId}/`);
  },

  // ==========================================
  // 5. DAILY TASKS
  // ==========================================
  getTasks: async (params?: Record<string, any>): Promise<PaginatedResponse<TaskItem>> => {
    const { data } = await apiClient.get<PaginatedResponse<TaskItem>>("/admin/tasks/", { params });
    return data;
  },

  getTaskDetail: async (id: string): Promise<TaskItem> => {
    const { data } = await apiClient.get<ApiSuccessResponse<TaskItem>>(`/admin/tasks/${id}/`);
    return data.data;
  },

  createTask: async (payload: {
    title: string;
    description: string;
    scheduled_date: string;
    question_id?: string | null;
    points?: number;
    is_active?: boolean;
  }): Promise<TaskItem> => {
    const { data } = await apiClient.post<ApiSuccessResponse<TaskItem>>("/admin/tasks/", payload);
    return data.data;
  },

  updateTask: async (id: string, payload: Partial<TaskItem>): Promise<TaskItem> => {
    const { data } = await apiClient.patch<ApiSuccessResponse<TaskItem>>(`/admin/tasks/${id}/`, payload);
    return data.data;
  },

  deleteTask: async (id: string): Promise<void> => {
    await apiClient.delete(`/admin/tasks/${id}/`);
  },

  // ==========================================
  // 6. CAPSTONE PROJECTS
  // ==========================================
  getProjects: async (params?: Record<string, any>): Promise<PaginatedResponse<ProjectItem>> => {
    const { data } = await apiClient.get<PaginatedResponse<ProjectItem>>("/admin/projects/", { params });
    return data;
  },

  getProjectDetail: async (id: string): Promise<ProjectItem> => {
    const { data } = await apiClient.get<ApiSuccessResponse<ProjectItem>>(`/admin/projects/${id}/`);
    return data.data;
  },

  createProject: async (payload: {
    title: string;
    slug?: string;
    description: string;
    deliverables_instructions: string;
    course_id?: string | null;
    max_score?: number;
    due_date?: string | null;
    is_active?: boolean;
  }): Promise<ProjectItem> => {
    const { data } = await apiClient.post<ApiSuccessResponse<ProjectItem>>("/admin/projects/", payload);
    return data.data;
  },

  updateProject: async (id: string, payload: Partial<ProjectItem>): Promise<ProjectItem> => {
    const { data } = await apiClient.patch<ApiSuccessResponse<ProjectItem>>(`/admin/projects/${id}/`, payload);
    return data.data;
  },

  getSubmissions: async (params?: Record<string, any>): Promise<PaginatedResponse<ProjectSubmissionItem>> => {
    const { data } = await apiClient.get<PaginatedResponse<ProjectSubmissionItem>>(
      "/admin/projects/submissions/",
      { params }
    );
    return data;
  },

  getSubmissionDetail: async (id: string): Promise<ProjectSubmissionItem> => {
    const { data } = await apiClient.get<ApiSuccessResponse<ProjectSubmissionItem>>(
      `/admin/projects/submissions/${id}/`
    );
    return data.data;
  },

  reviewSubmission: async (id: string, payload: {
    status: string;
    score?: number;
    feedback_text?: string;
    suggested_changes?: string;
    rating?: number;
  }): Promise<ProjectSubmissionItem> => {
    const { data } = await apiClient.post<ApiSuccessResponse<ProjectSubmissionItem>>(
      `/admin/projects/submissions/${id}/`,
      payload
    );
    return data.data;
  },

  // ==========================================
  // 7. ANNOUNCEMENTS
  // ==========================================
  getAnnouncements: async (params?: Record<string, any>): Promise<PaginatedResponse<AnnouncementItem>> => {
    const { data } = await apiClient.get<PaginatedResponse<AnnouncementItem>>("/admin/announcements/", {
      params,
    });
    return data;
  },

  getAnnouncementDetail: async (id: string): Promise<AnnouncementItem> => {
    const { data } = await apiClient.get<ApiSuccessResponse<AnnouncementItem>>(`/admin/announcements/${id}/`);
    return data.data;
  },

  createAnnouncement: async (payload: {
    title: string;
    content: string;
    target_batch?: string;
    priority?: string;
    expires_at?: string | null;
    is_active?: boolean;
  }): Promise<AnnouncementItem> => {
    const { data } = await apiClient.post<ApiSuccessResponse<AnnouncementItem>>(
      "/admin/announcements/",
      payload
    );
    return data.data;
  },

  updateAnnouncement: async (id: string, payload: Partial<AnnouncementItem>): Promise<AnnouncementItem> => {
    const { data } = await apiClient.patch<ApiSuccessResponse<AnnouncementItem>>(
      `/admin/announcements/${id}/`,
      payload
    );
    return data.data;
  },

  deleteAnnouncement: async (id: string): Promise<void> => {
    await apiClient.delete(`/admin/announcements/${id}/`);
  },

  // ==========================================
  // 8. ANALYTICS & REPORTS
  // ==========================================
  getAnalyticsDashboard: async (params?: {
    course_id?: string;
    batch_code?: string;
    days?: number;
  }): Promise<AnalyticsDashboardData> => {
    const { data } = await apiClient.get<ApiSuccessResponse<AnalyticsDashboardData>>(
      "/admin/analytics/dashboard/",
      { params }
    );
    return data.data;
  },

  getPerformanceReport: async (params?: {
    batch_code?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<PerformanceReportData> => {
    const { data } = await apiClient.get<ApiSuccessResponse<PerformanceReportData>>(
      "/admin/reports/performance/",
      { params }
    );
    return data.data;
  },

  getCompletionReport: async (params?: { course_id?: string }): Promise<CompletionReportData> => {
    const { data } = await apiClient.get<ApiSuccessResponse<CompletionReportData>>(
      "/admin/reports/completion/",
      { params }
    );
    return data.data;
  },

  getAssignmentReport: async (params?: {
    module_id?: string;
    course_id?: string;
  }): Promise<AssignmentReportData> => {
    const { data } = await apiClient.get<ApiSuccessResponse<AssignmentReportData>>(
      "/admin/reports/assignment/",
      { params }
    );
    return data.data;
  },

  getProjectReport: async (params?: { course_id?: string }): Promise<ProjectReportData> => {
    const { data } = await apiClient.get<ApiSuccessResponse<ProjectReportData>>(
      "/admin/reports/project/",
      { params }
    );
    return data.data;
  },

  getMonthlyActivityReport: async (days: number = 30): Promise<MonthlyActivityReportData> => {
    const { data } = await apiClient.get<ApiSuccessResponse<MonthlyActivityReportData>>(
      "/admin/reports/monthly-activity/",
      { params: { days } }
    );
    return data.data;
  },

  // ------------------------------------------
  // ASYNCHRONOUS EXPORT JOBS
  // ------------------------------------------
  createExportJob: async (payload: {
    report_type: string;
    format?: "CSV" | "JSON";
    filters?: Record<string, any>;
  }): Promise<ExportJobItem> => {
    const { data } = await apiClient.post<ApiSuccessResponse<ExportJobItem>>(
      "/admin/reports/export/",
      payload
    );
    return data.data;
  },

  getExportJobs: async (): Promise<{ jobs: ExportJobItem[]; count: number }> => {
    const { data } = await apiClient.get<
      ApiSuccessResponse<{ jobs: ExportJobItem[]; count: number }>
    >("/admin/reports/exports/");
    return data.data;
  },

  getExportJobDetail: async (jobId: string): Promise<ExportJobItem> => {
    const { data } = await apiClient.get<ApiSuccessResponse<ExportJobItem>>(
      `/admin/reports/exports/${jobId}/`
    );
    return data.data;
  },

  // ==========================================
  // 9. CERTIFICATES & CREDENTIALS
  // ==========================================
  getCertificates: async (params?: {
    search?: string;
    course_id?: string;
    is_revoked?: boolean;
  }): Promise<{ certificates: AdminCertificateItem[]; count: number }> => {
    const { data } = await apiClient.get<
      ApiSuccessResponse<{ certificates: AdminCertificateItem[]; count: number }>
    >("/admin/certificates/", { params });
    return data.data;
  },

  revokeCertificate: async (
    certificateId: string,
    reason: string
  ): Promise<AdminCertificateItem> => {
    const { data } = await apiClient.post<ApiSuccessResponse<AdminCertificateItem>>(
      `/admin/certificates/${certificateId}/revoke/`,
      { reason }
    );
    return data.data;
  },

  // ==========================================
  // 10. CONTACT INQUIRIES & SUPPORT TICKETS
  // ==========================================
  getContactInquiries: async (params?: {
    status?: string;
    category?: string;
    search?: string;
  }): Promise<{ inquiries: AdminContactInquiryItem[]; count: number }> => {
    const { data } = await apiClient.get<
      ApiSuccessResponse<{ inquiries: AdminContactInquiryItem[]; count: number }>
    >("/admin/contact/inquiries/", { params });
    return data.data;
  },

  getContactInquiryDetail: async (inquiryId: string): Promise<AdminContactInquiryItem> => {
    const { data } = await apiClient.get<ApiSuccessResponse<AdminContactInquiryItem>>(
      `/admin/contact/inquiries/${inquiryId}/`
    );
    return data.data;
  },

  updateContactInquiry: async (
    inquiryId: string,
    payload: { status: string; admin_notes?: string }
  ): Promise<AdminContactInquiryItem> => {
    const { data } = await apiClient.patch<ApiSuccessResponse<AdminContactInquiryItem>>(
      `/admin/contact/inquiries/${inquiryId}/`,
      payload
    );
    return data.data;
  },
};

export interface AdminContactInquiryItem {
  id: string;
  user: string | null;
  user_email?: string | null;
  name: string;
  email: string;
  subject: string;
  category: "TECHNICAL_SUPPORT" | "COURSE_DOUBT" | "ACCOUNT_ISSUE" | "GENERAL_FEEDBACK";
  message: string;
  status: "PENDING" | "INVESTIGATING" | "RESOLVED" | "CLOSED";
  admin_notes: string;
  ip_address?: string | null;
  user_agent?: string;
  resolved_by_email?: string | null;
  resolved_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminCertificateItem {
  id: string;
  certificate_id: string;
  title: string;
  student: {
    id: string;
    student_id_number: string;
    full_name: string;
    batch_code: string;
  };
  student_name: string;
  course: {
    id: string;
    title: string;
    slug: string;
  };
  course_title: string;
  verification_hash: string;
  pdf_file: string | null;
  issued_at: string;
  is_revoked: boolean;
  metadata: Record<string, any>;
}

