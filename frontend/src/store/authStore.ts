import { create } from "zustand";
import { User, StudentProfile, AuthTokens } from "../types/auth";
import { authApi } from "../api/authApi";
import { queryClient } from "../app/queryClient";

const isClient = typeof window !== "undefined" && typeof window.localStorage !== "undefined";
const getStorageItem = (key: string): string | null => (isClient ? localStorage.getItem(key) : null);
const setStorageItem = (key: string, val: string): void => {
  if (isClient) localStorage.setItem(key, val);
};
const removeStorageItem = (key: string): void => {
  if (isClient) localStorage.removeItem(key);
};

interface AuthStoreState {
  user: User | null;
  studentProfile: StudentProfile | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setAuth: (user: User, tokens: AuthTokens, studentProfile?: StudentProfile) => void;
  clearAuth: () => void;
  setLoading: (loading: boolean) => void;
  hydrateAuth: () => Promise<User | null>;
}

export const useAuthStore = create<AuthStoreState>((set, get) => ({
  user: null,
  studentProfile: null,
  tokens: null,
  isAuthenticated: !!getStorageItem("gqt_access_token"),
  isLoading: true,

  setAuth: (user, tokens, studentProfile) => {
    // Invalidate and remove any prior queries belonging to another session
    queryClient.removeQueries({ queryKey: ["student"] });
    queryClient.clear();

    setStorageItem("gqt_access_token", tokens.access);
    setStorageItem("gqt_refresh_token", tokens.refresh);
    set({
      user,
      tokens,
      studentProfile: studentProfile || (user as any).student_profile || null,
      isAuthenticated: true,
      isLoading: false,
    });
  },

  clearAuth: () => {
    // Completely clear all cached queries to prevent stale data leaks
    queryClient.removeQueries({ queryKey: ["student"] });
    queryClient.clear();

    removeStorageItem("gqt_access_token");
    removeStorageItem("gqt_refresh_token");
    set({
      user: null,
      studentProfile: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
    });
  },

  setLoading: (isLoading) => set({ isLoading }),

  hydrateAuth: async () => {
    const token = getStorageItem("gqt_access_token");
    if (!token) {
      set({ user: null, studentProfile: null, isAuthenticated: false, isLoading: false });
      return null;
    }

    try {
      set({ isLoading: true });
      const user = await authApi.getMe();
      const studentProfile = (user as any).student_profile || null;
      set({
        user,
        studentProfile,
        isAuthenticated: true,
        isLoading: false,
      });
      return user;
    } catch (err) {
      // Token is invalid or expired
      get().clearAuth();
      return null;
    }
  },
}));
