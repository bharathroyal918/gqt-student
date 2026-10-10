import { apiClient } from "./client";
import { College } from "../types/college";
import {
  TPOAssignmentsLabsResponse,
  TPOAttendanceAnalyticsResponse,
  TPOCollegeSummary,
  TPOLeaderboardItem,
  TPOLearningProgressResponse,
  TPOPerformanceTrendsResponse,
  TPOProfile,
  TPOReportExportRequest,
  TPOReportPreviewRequest,
  TPOReportPreviewResponse,
  TPOReportType,
  TPOStudentDetail,
  TPOStudentNeedingSupport,
  TPOStudentRosterItem,
  UpdateTPOPayload,
} from "../types/tpo";

export interface GetCollegeStudentsParams {
  search?: string;
  batch_code?: string;
  graduation_year?: number | string;
  course_opted?: string;
  is_active?: boolean;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export interface PaginatedStudentRosterResponse {
  data: TPOStudentRosterItem[];
  meta?: {
    pagination?: {
      page: number;
      page_size: number;
      total_records: number;
      total_pages: number;
      has_next: boolean;
      has_prev: boolean;
    };
  };
}

export const tpoApi = {
  getMe: async (): Promise<TPOProfile> => {
    const response = await apiClient.get<{ data: TPOProfile }>("/tpo/me/");
    return response.data.data;
  },

  updateMe: async (payload: UpdateTPOPayload): Promise<TPOProfile> => {
    const response = await apiClient.patch<{ data: TPOProfile }>("/tpo/me/", payload);
    return response.data.data;
  },

  getAssignedCollege: async (): Promise<College> => {
    const response = await apiClient.get<{ data: College }>("/tpo/college/");
    return response.data.data;
  },

  getCollegeSummary: async (): Promise<TPOCollegeSummary> => {
    const response = await apiClient.get<{ data: TPOCollegeSummary }>("/tpo/college/summary/");
    return response.data.data;
  },

  getCollegeStudents: async (
    params?: GetCollegeStudentsParams
  ): Promise<PaginatedStudentRosterResponse> => {
    const response = await apiClient.get<PaginatedStudentRosterResponse>(
      "/tpo/college/students/",
      {
        params,
      }
    );
    return response.data;
  },

  getStudentDetail: async (studentId: string): Promise<TPOStudentDetail> => {
    const response = await apiClient.get<{ data: TPOStudentDetail }>(
      `/tpo/college/students/${studentId}/`
    );
    return response.data.data;
  },

  // --- Phase 5 Analytics API Methods ---

  getLearningProgress: async (courseId?: string): Promise<TPOLearningProgressResponse> => {
    const response = await apiClient.get<{ data: TPOLearningProgressResponse }>(
      "/tpo/analytics/learning-progress/",
      {
        params: courseId ? { course_id: courseId } : undefined,
      }
    );
    return response.data.data;
  },

  getAssignmentsLabs: async (dateFrom?: string, dateTo?: string): Promise<TPOAssignmentsLabsResponse> => {
    const response = await apiClient.get<{ data: TPOAssignmentsLabsResponse }>(
      "/tpo/analytics/assignments-labs/",
      {
        params: {
          ...(dateFrom ? { date_from: dateFrom } : {}),
          ...(dateTo ? { date_to: dateTo } : {}),
        },
      }
    );
    return response.data.data;
  },

  getAttendanceAnalytics: async (batchCode?: string): Promise<TPOAttendanceAnalyticsResponse> => {
    const response = await apiClient.get<{ data: TPOAttendanceAnalyticsResponse }>(
      "/tpo/analytics/attendance/",
      {
        params: batchCode && batchCode !== "ALL" ? { batch_code: batchCode } : undefined,
      }
    );
    return response.data.data;
  },

  getPerformanceTrends: async (): Promise<TPOPerformanceTrendsResponse> => {
    const response = await apiClient.get<{ data: TPOPerformanceTrendsResponse }>(
      "/tpo/analytics/trends/"
    );
    return response.data.data;
  },

  getStudentsNeedingSupport: async (riskType?: string): Promise<TPOStudentNeedingSupport[]> => {
    const response = await apiClient.get<{ data: TPOStudentNeedingSupport[] }>(
      "/tpo/analytics/students-needing-support/",
      {
        params: riskType && riskType !== "ALL" ? { risk_type: riskType } : undefined,
      }
    );
    return response.data.data;
  },

  getLeaderboard: async (limit?: number): Promise<TPOLeaderboardItem[]> => {
    const response = await apiClient.get<{ data: TPOLeaderboardItem[] }>(
      "/tpo/analytics/leaderboard/",
      {
        params: limit ? { limit } : undefined,
      }
    );
    return response.data.data;
  },

  getReportTypes: async (): Promise<TPOReportType[]> => {
    const response = await apiClient.get<{ data: TPOReportType[] }>("/tpo/reports/types/");
    return response.data.data;
  },

  previewReport: async (payload: TPOReportPreviewRequest): Promise<TPOReportPreviewResponse> => {
    const response = await apiClient.post<{ data: TPOReportPreviewResponse }>("/tpo/reports/preview/", payload);
    return response.data.data;
  },

  exportReport: async (payload: TPOReportExportRequest): Promise<{ blob: Blob; filename: string }> => {
    const response = await apiClient.post("/tpo/reports/export/", payload, {
      responseType: "blob",
    });
    
    // Extract filename from Content-Disposition header if available
    const disposition = response.headers["content-disposition"] || "";
    let filename = `report_${payload.report_type.toLowerCase()}.${payload.format}`;
    const filenameMatch = disposition.match(/filename="?([^";]+)"?/i);
    if (filenameMatch && filenameMatch[1]) {
      filename = filenameMatch[1];
    }

    return {
      blob: new Blob([response.data], {
        type: payload.format === "csv" ? "text/csv;charset=utf-8;" : "application/json",
      }),
      filename,
    };
  },
};


