import { apiClient } from "./client";
import { ApiSuccessResponse } from "../types/api";
import { User, StudentProfile } from "../types/auth";

export interface LoginResult {
  access: string;
  refresh: string;
  user: User & { student_profile?: StudentProfile; admin_profile?: any };
}

export const authApi = {
  loginEmail: async (email: string, password: string): Promise<LoginResult> => {
    const { data } = await apiClient.post<ApiSuccessResponse<LoginResult>>("/auth/login/email/", {
      email,
      password,
    });
    return data.data;
  },

  requestOtp: async (mobile_number: string): Promise<{ mobile_number: string }> => {
    const { data } = await apiClient.post<ApiSuccessResponse<{ mobile_number: string }>>(
      "/auth/otp/request/",
      { mobile_number }
    );
    return data.data;
  },

  verifyOtp: async (mobile_number: string, otp: string): Promise<LoginResult> => {
    const { data } = await apiClient.post<ApiSuccessResponse<LoginResult>>("/auth/otp/verify/", {
      mobile_number,
      otp,
    });
    return data.data;
  },

  requestPasswordReset: async (email: string): Promise<{ email: string }> => {
    const { data } = await apiClient.post<ApiSuccessResponse<{ email: string }>>(
      "/auth/password/forgot/",
      { email }
    );
    return data.data;
  },

  resetPassword: async (token: string, new_password: string): Promise<void> => {
    await apiClient.post<ApiSuccessResponse<{}>>("/auth/password/reset/", {
      token,
      new_password,
    });
  },

  getMe: async (): Promise<User> => {
    const { data } = await apiClient.get<ApiSuccessResponse<{ user: User }>>("/auth/me/");
    return data.data.user;
  },

  logout: async (refresh: string): Promise<void> => {
    await apiClient.post<ApiSuccessResponse<{}>>("/auth/logout/", { refresh });
  },
};
