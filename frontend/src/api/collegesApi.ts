import { apiClient } from "./client";
import { College, CreateCollegePayload, UpdateCollegePayload } from "../types/college";

export const collegesApi = {
  getColleges: async (search?: string): Promise<College[]> => {
    const response = await apiClient.get<{ data: College[] }>("/students/colleges/", {
      params: search ? { search } : undefined,
    });
    return response.data.data;
  },

  adminGetColleges: async (params?: { search?: string; is_active?: boolean }): Promise<College[]> => {
    const response = await apiClient.get<{ data: College[] }>("/admin/students/colleges/", {
      params,
    });
    return response.data.data;
  },

  adminCreateCollege: async (payload: CreateCollegePayload): Promise<College> => {
    const response = await apiClient.post<{ data: College }>("/admin/students/colleges/", payload);
    return response.data.data;
  },

  adminUpdateCollege: async (id: string, payload: UpdateCollegePayload): Promise<College> => {
    const response = await apiClient.patch<{ data: College }>(`/admin/students/colleges/${id}/`, payload);
    return response.data.data;
  },

  adminDeleteCollege: async (id: string): Promise<void> => {
    await apiClient.delete(`/admin/students/colleges/${id}/`);
  },
};
