import { apiClient } from "./client";
import {
  CreateTPOPayload,
  ReassignCollegePayload,
  TPOAuditLog,
  TPOProfile,
  UpdateTPOPayload,
} from "../types/tpo";

export interface GetTPOsParams {
  search?: string;
  college_id?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export interface PaginatedTPOResponse {
  data: TPOProfile[];
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

export const adminTpoApi = {
  getTPOs: async (params?: GetTPOsParams): Promise<PaginatedTPOResponse> => {
    const response = await apiClient.get<PaginatedTPOResponse>("/admin/tpos/", {
      params,
    });
    return response.data;
  },

  getTPODetail: async (id: string): Promise<TPOProfile> => {
    const response = await apiClient.get<{ data: TPOProfile }>(`/admin/tpos/${id}/`);
    return response.data.data;
  },

  provisionTPO: async (payload: CreateTPOPayload): Promise<TPOProfile> => {
    const response = await apiClient.post<{ data: TPOProfile }>("/admin/tpos/", payload);
    return response.data.data;
  },

  updateTPO: async (id: string, payload: UpdateTPOPayload): Promise<TPOProfile> => {
    const response = await apiClient.patch<{ data: TPOProfile }>(`/admin/tpos/${id}/`, payload);
    return response.data.data;
  },

  reassignCollege: async (id: string, payload: ReassignCollegePayload): Promise<TPOProfile> => {
    const response = await apiClient.post<{ data: TPOProfile }>(
      `/admin/tpos/${id}/reassign-college/`,
      payload
    );
    return response.data.data;
  },

  deactivateTPO: async (id: string): Promise<TPOProfile> => {
    const response = await apiClient.post<{ data: TPOProfile }>(`/admin/tpos/${id}/deactivate/`);
    return response.data.data;
  },

  reactivateTPO: async (id: string): Promise<TPOProfile> => {
    const response = await apiClient.post<{ data: TPOProfile }>(`/admin/tpos/${id}/reactivate/`);
    return response.data.data;
  },

  getTPOAuditHistory: async (id: string): Promise<TPOAuditLog[]> => {
    const response = await apiClient.get<{ data: TPOAuditLog[] }>(
      `/admin/tpos/${id}/audit-history/`
    );
    return response.data.data;
  },
};
