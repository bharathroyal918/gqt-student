import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { ApiErrorResponse, ApiSuccessResponse } from "../types/api";

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || "/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

// Request Interceptor: Attach Access Token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem("gqt_access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Token Refresh & Standard Envelope Unwrapping
apiClient.interceptors.response.use(
  (response) => {
    // Return standard success payload
    return response;
  },
  async (error: AxiosError<ApiErrorResponse>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 Unauthorized with Token Refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem("gqt_refresh_token");

      if (refreshToken) {
        try {
          const { data } = await axios.post<ApiSuccessResponse<{ access: string; refresh: string }>>(
            `${API_BASE_URL}/auth/token/refresh/`,
            { refresh: refreshToken }
          );

          localStorage.setItem("gqt_access_token", data.data.access);
          if (data.data.refresh) {
            localStorage.setItem("gqt_refresh_token", data.data.refresh);
          }

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${data.data.access}`;
          }
          return apiClient(originalRequest);
        } catch (refreshError) {
          // Invalidate tokens and redirect to login
          localStorage.removeItem("gqt_access_token");
          localStorage.removeItem("gqt_refresh_token");
          window.location.href = "/auth/login";
          return Promise.reject(refreshError);
        }
      }
    }

    return Promise.reject(error);
  }
);
