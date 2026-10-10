import { apiClient } from "./client";
import { ApiSuccessResponse } from "../types/api";
import { User, StudentProfile } from "../types/auth";
import { RegisterTPOPayload } from "../types/tpo";

export interface LoginResult {
  access: string;
  refresh: string;
  user: User & { student_profile?: StudentProfile; admin_profile?: any };
}

export interface RegisterStudentPayload {
  full_name: string;
  email: string;
  mobile_number: string;
  password: string;
  student_id_number?: string;
  college_name?: string;
  batch_code?: string;
  graduation_year?: number;
}

export interface OTPRequestResult {
  target: string;
  channel: "email" | "mobile";
  message: string;
}

export interface OTPVerifyResult {
  reset_token: string;
  message: string;
}

export const authApi = {
  // Student Registration
  registerStudent: async (payload: RegisterStudentPayload): Promise<LoginResult> => {
    const { data } = await apiClient.post<ApiSuccessResponse<LoginResult>>(
      "/auth/register/",
      payload
    );
    return data.data;
  },

  // TPO Registration
  registerTPO: async (payload: RegisterTPOPayload): Promise<any> => {
    const { data } = await apiClient.post<ApiSuccessResponse<any>>(
      "/tpo/auth/register/",
      payload
    );
    return data.data;
  },

  // Dedicated Role-Based Logins
  loginStudent: async (email: string, password: string): Promise<LoginResult> => {
    const { data } = await apiClient.post<ApiSuccessResponse<LoginResult>>(
      "/auth/login/student/",
      { email, password }
    );
    return data.data;
  },

  loginAdmin: async (email: string, password: string): Promise<LoginResult> => {
    const { data } = await apiClient.post<ApiSuccessResponse<LoginResult>>(
      "/auth/login/admin/",
      { email, password }
    );
    return data.data;
  },

  loginTPO: async (email: string, password: string): Promise<LoginResult> => {
    const { data } = await apiClient.post<ApiSuccessResponse<LoginResult>>(
      "/tpo/auth/login/",
      { email, password }
    );
    return data.data;
  },

  loginEmail: async (email: string, password: string): Promise<LoginResult> => {
    const { data } = await apiClient.post<ApiSuccessResponse<LoginResult>>(
      "/auth/login/email/",
      { email, password }
    );
    return data.data;
  },

  // OTP Login
  requestOtp: async (mobile_number: string): Promise<{ mobile_number: string }> => {
    const { data } = await apiClient.post<ApiSuccessResponse<{ mobile_number: string }>>(
      "/auth/otp/request/",
      { mobile_number }
    );
    return data.data;
  },

  verifyOtp: async (mobile_number: string, otp: string): Promise<LoginResult> => {
    const { data } = await apiClient.post<ApiSuccessResponse<LoginResult>>(
      "/auth/otp/verify/",
      { mobile_number, otp }
    );
    return data.data;
  },

  // OTP Password Recovery
  requestPasswordResetOtp: async (identifier: string): Promise<OTPRequestResult> => {
    const { data } = await apiClient.post<ApiSuccessResponse<OTPRequestResult>>(
      "/auth/password/forgot-otp/",
      { identifier }
    );
    return data.data;
  },

  verifyPasswordResetOtp: async (identifier: string, otp: string): Promise<OTPVerifyResult> => {
    const { data } = await apiClient.post<ApiSuccessResponse<OTPVerifyResult>>(
      "/auth/password/verify-reset-otp/",
      { identifier, otp }
    );
    return data.data;
  },

  requestPasswordReset: async (email: string): Promise<{ email: string }> => {
    const { data } = await apiClient.post<ApiSuccessResponse<{ email: string }>>(
      "/auth/password/forgot/",
      { email }
    );
    return data.data;
  },

  resetPassword: async (
    token: string,
    new_password: string,
    identifier?: string,
    otp?: string
  ): Promise<void> => {
    await apiClient.post<ApiSuccessResponse<{}>>("/auth/password/reset/", {
      token,
      new_password,
      identifier,
      otp,
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
