import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { ApiErrorResponse, ApiSuccessResponse } from "../types/api";

const rawApiBaseUrl = (import.meta as any).env?.VITE_API_BASE_URL || "/api/v1";
export const API_BASE_URL = rawApiBaseUrl.replace(/\/+$/, "");

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 20000,
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

// Single-flight refresh token queue to prevent race conditions during concurrent API 401s
let isRefreshing = false;
let refreshSubscribers: Array<{
  resolve: (token: string) => void;
  reject: (error: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  refreshSubscribers.forEach((subscriber) => {
    if (error) {
      subscriber.reject(error);
    } else if (token) {
      subscriber.resolve(token);
    }
  });
  refreshSubscribers = [];
};

// Response Interceptor: Token Refresh & Standard Envelope Unwrapping
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError<ApiErrorResponse>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 Unauthorized with Single-Flight Token Refresh
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      // Don't retry token refresh endpoint itself
      if (originalRequest.url?.includes("/auth/token/refresh/") || originalRequest.url?.includes("/auth/login/")) {
        return Promise.reject(error);
      }

      originalRequest._retry = true;

      if (isRefreshing) {
        // Queue this request until the in-flight refresh completes
        return new Promise<string>((resolve, reject) => {
          refreshSubscribers.push({ resolve, reject });
        })
          .then((newAccessToken) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      isRefreshing = true;
      const refreshToken = localStorage.getItem("gqt_refresh_token");

      if (refreshToken) {
        try {
          const { data } = await axios.post<ApiSuccessResponse<{ access: string; refresh: string }>>(
            `${API_BASE_URL}/auth/token/refresh/`,
            { refresh: refreshToken }
          );

          const newAccessToken = data.data.access;
          localStorage.setItem("gqt_access_token", newAccessToken);
          if (data.data.refresh) {
            localStorage.setItem("gqt_refresh_token", data.data.refresh);
          }

          processQueue(null, newAccessToken);

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          }
          return apiClient(originalRequest);
        } catch (refreshError) {
          processQueue(refreshError, null);

          // Invalidate tokens and redirect to portal-specific login
          localStorage.removeItem("gqt_access_token");
          localStorage.removeItem("gqt_refresh_token");
          localStorage.removeItem("gqt_user");
          localStorage.removeItem("gqt_profile");

          const path = window.location.pathname;
          if (path.startsWith("/admin")) {
            window.location.href = "/admin/login";
          } else if (path.startsWith("/tpo")) {
            window.location.href = "/tpo/login";
          } else {
            window.location.href = "/login";
          }
          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
        }
      }
    }

    return Promise.reject(error);
  }
);
