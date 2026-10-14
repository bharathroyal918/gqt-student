import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { ApiErrorResponse, ApiSuccessResponse } from "../types/api";

const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL || "/api/v1";
export const API_BASE_URL = rawApiBaseUrl.replace(/\/+$/, "");

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 20000,
});

/**
 * Checks if a JWT token is expired or close to expiry (within threshold).
 */
const isTokenExpiring = (token: string, thresholdSeconds = 45): boolean => {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return true;
    const payload = JSON.parse(atob(parts[1]));
    if (!payload.exp) return false;
    return payload.exp * 1000 - Date.now() < thresholdSeconds * 1000;
  } catch {
    return true;
  }
};

let refreshPromise: Promise<string> | null = null;

/**
 * Executes a single-flight token refresh, de-duplicating all concurrent requests.
 */
const executeTokenRefresh = async (): Promise<string> => {
  if (refreshPromise) {
    return refreshPromise;
  }

  const refreshToken = localStorage.getItem("gqt_refresh_token");
  if (!refreshToken) {
    throw new Error("No refresh token available");
  }

  refreshPromise = (async () => {
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
      return newAccessToken;
    } catch (err) {
      localStorage.removeItem("gqt_access_token");
      localStorage.removeItem("gqt_refresh_token");
      localStorage.removeItem("gqt_user");
      localStorage.removeItem("gqt_profile");
      throw err;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
};

// Request Interceptor: Proactive Token Validation & Attachment
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // Skip token refresh for auth endpoints themselves
    if (config.url?.includes("/auth/token/refresh/") || config.url?.includes("/auth/login/")) {
      return config;
    }

    let token = localStorage.getItem("gqt_access_token");
    const refreshToken = localStorage.getItem("gqt_refresh_token");

    // If access token is expired/expiring soon and we have a refresh token, proactively refresh
    if (refreshToken && (!token || isTokenExpiring(token))) {
      try {
        token = await executeTokenRefresh();
      } catch {
        // Fall back to existing token or proceed; response interceptor will handle if unauthorized
      }
    }

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: 401 Fallback & Auto-Redirect
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorResponse>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle unexpected 401 Unauthorized with single-flight retry
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      if (originalRequest.url?.includes("/auth/token/refresh/") || originalRequest.url?.includes("/auth/login/")) {
        return Promise.reject(error);
      }

      originalRequest._retry = true;

      try {
        const newAccessToken = await executeTokenRefresh();
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        }
        return apiClient(originalRequest);
      } catch (refreshError) {
        const path = window.location.pathname;
        if (path.startsWith("/admin")) {
          window.location.href = "/admin/login";
        } else if (path.startsWith("/tpo")) {
          window.location.href = "/tpo/login";
        } else {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
