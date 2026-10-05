import { apiClient } from "./client";
import { ApiSuccessResponse } from "../types/api";
import {
  PlacementDrive,
  PlacementApplication,
  PlacementAdminMetrics,
  PlacementDriveApplicantsStats,
  CreatePlacementDrivePayload,
  ApplyPlacementPayload,
  UpdateApplicationStatusPayload,
} from "../types/placement";

export const placementsApi = {
  // ================= ADMIN ENDPOINTS =================
  adminGetDrives: async (params?: {
    status?: string;
    mode_of_work?: string;
    search?: string;
  }) => {
    const response = await apiClient.get<
      ApiSuccessResponse<{
        drives: PlacementDrive[];
        metrics: PlacementAdminMetrics;
      }>
    >("/admin/placements/drives/", { params });
    return response.data.data;
  },

  adminGetDrive: async (driveId: string) => {
    const response = await apiClient.get<
      ApiSuccessResponse<{
        drive: PlacementDrive;
        stats: PlacementDriveApplicantsStats;
      }>
    >(`/admin/placements/drives/${driveId}/`);
    return response.data.data;
  },

  adminCreateDrive: async (payload: CreatePlacementDrivePayload) => {
    const response = await apiClient.post<ApiSuccessResponse<PlacementDrive>>(
      "/admin/placements/drives/",
      payload
    );
    return response.data.data;
  },

  adminUpdateDrive: async (
    driveId: string,
    payload: Partial<CreatePlacementDrivePayload>
  ) => {
    const response = await apiClient.patch<ApiSuccessResponse<PlacementDrive>>(
      `/admin/placements/drives/${driveId}/`,
      payload
    );
    return response.data.data;
  },

  adminDeleteDrive: async (driveId: string) => {
    const response = await apiClient.delete<ApiSuccessResponse<void>>(
      `/admin/placements/drives/${driveId}/`
    );
    return response.data;
  },

  adminGetApplications: async (params?: {
    drive_id?: string;
    status?: string;
    search?: string;
  }) => {
    const url = params?.drive_id
      ? `/admin/placements/drives/${params.drive_id}/applications/`
      : "/admin/placements/applications/";
    const response = await apiClient.get<
      ApiSuccessResponse<{
        applications: PlacementApplication[];
        stats: PlacementDriveApplicantsStats;
      }>
    >(url, { params });
    return response.data.data;
  },

  adminUpdateApplicationStatus: async (
    applicationId: string,
    payload: UpdateApplicationStatusPayload
  ) => {
    const response = await apiClient.post<
      ApiSuccessResponse<PlacementApplication>
    >(`/admin/placements/applications/${applicationId}/status/`, payload);
    return response.data.data;
  },

  adminGetStats: async () => {
    const response = await apiClient.get<
      ApiSuccessResponse<PlacementAdminMetrics>
    >("/admin/placements/stats/");
    return response.data.data;
  },

  // ================= STUDENT ENDPOINTS =================
  studentGetAvailableDrives: async (params?: {
    mode_of_work?: string;
    search?: string;
  }) => {
    const response = await apiClient.get<
      ApiSuccessResponse<{
        drives: PlacementDrive[];
        summary: {
          total_available_drives: number;
          my_applications_count: number;
          my_shortlisted_count: number;
          my_selected_count: number;
        };
      }>
    >("/students/placements/drives/", { params });
    return response.data.data;
  },

  studentGetDriveDetail: async (driveId: string) => {
    const response = await apiClient.get<ApiSuccessResponse<PlacementDrive>>(
      `/students/placements/drives/${driveId}/`
    );
    return response.data.data;
  },

  studentApplyToDrive: async (
    driveId: string,
    payload: ApplyPlacementPayload
  ) => {
    let body: any = payload;

    if (payload.resume_file instanceof File) {
      const formData = new FormData();
      formData.append("phone_number", payload.phone_number || "");
      if (payload.college_name) formData.append("college_name", payload.college_name);
      if (payload.branch) formData.append("branch", payload.branch);
      if (payload.graduation_year) formData.append("graduation_year", String(payload.graduation_year));
      formData.append("cgpa_or_percentage", payload.cgpa_or_percentage || "");
      formData.append("resume_file", payload.resume_file);
      if (payload.resume_url) formData.append("resume_url", payload.resume_url);
      if (payload.portfolio_url) formData.append("portfolio_url", payload.portfolio_url);
      if (payload.github_url) formData.append("github_url", payload.github_url);
      if (payload.linkedin_url) formData.append("linkedin_url", payload.linkedin_url);
      if (payload.skills_summary) formData.append("skills_summary", payload.skills_summary);
      if (payload.cover_note) formData.append("cover_note", payload.cover_note);

      body = formData;
    }

    const response = await apiClient.post<
      ApiSuccessResponse<PlacementApplication>
    >(`/students/placements/drives/${driveId}/apply/`, body);
    return response.data.data;
  },

  studentGetMyApplications: async () => {
    const response = await apiClient.get<
      ApiSuccessResponse<{ applications: PlacementApplication[] }>
    >("/students/placements/my-applications/");
    return response.data.data.applications;
  },
};
