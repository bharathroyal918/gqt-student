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

const getStoredUser = (): User | null => {
  try {
    const raw = getStorageItem("gqt_user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

const getStoredProfile = (): StudentProfile | null => {
  try {
    const raw = getStorageItem("gqt_profile");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

interface AuthStoreState {
  user: User | null;
  studentProfile: StudentProfile | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setAuth: (user: User, tokens: AuthTokens, studentProfile?: StudentProfile) => void;
  updateUser: (user: User) => void;
  updateStudentProfile: (profile: StudentProfile) => void;
  clearAuth: () => void;
  setLoading: (loading: boolean) => void;
  hydrateAuth: (silent?: boolean) => Promise<User | null>;
}

const initialUser = getStoredUser();
const initialProfile = getStoredProfile();
const hasAccessToken = !!getStorageItem("gqt_access_token");

export const useAuthStore = create<AuthStoreState>((set, get) => ({
  user: initialUser,
  studentProfile: initialProfile,
  tokens: hasAccessToken ? { access: getStorageItem("gqt_access_token") || "", refresh: getStorageItem("gqt_refresh_token") || "" } : null,
  isAuthenticated: hasAccessToken,
  isLoading: false,

  setAuth: (user, tokens, studentProfile) => {
    // Invalidate and remove any prior queries belonging to another session
    queryClient.removeQueries({ queryKey: ["student"] });
    queryClient.clear();

    const profile = studentProfile || (user as any).student_profile || null;
    setStorageItem("gqt_access_token", tokens.access);
    setStorageItem("gqt_refresh_token", tokens.refresh);
    setStorageItem("gqt_user", JSON.stringify(user));
    if (profile) {
      setStorageItem("gqt_profile", JSON.stringify(profile));
    } else {
      removeStorageItem("gqt_profile");
    }

    set({
      user,
      tokens,
      studentProfile: profile,
      isAuthenticated: true,
      isLoading: false,
    });
  },

  updateUser: (user) => {
    setStorageItem("gqt_user", JSON.stringify(user));
    const studentProfile = (user as any)?.student_profile || get().studentProfile;
    if (studentProfile) {
      setStorageItem("gqt_profile", JSON.stringify(studentProfile));
    }
    set({ user, studentProfile });
  },

  updateStudentProfile: (studentProfile) => {
    setStorageItem("gqt_profile", JSON.stringify(studentProfile));
    const currentUser = get().user;
    const updatedUser = currentUser
      ? {
          ...currentUser,
          student_profile: {
            ...((currentUser as any).student_profile || {}),
            ...studentProfile,
          },
        }
      : currentUser;
    if (updatedUser) {
      setStorageItem("gqt_user", JSON.stringify(updatedUser));
    }
    set({ studentProfile, user: updatedUser });
  },

  clearAuth: () => {
    // Completely clear all cached queries to prevent stale data leaks
    queryClient.removeQueries({ queryKey: ["student"] });
    queryClient.clear();

    removeStorageItem("gqt_access_token");
    removeStorageItem("gqt_refresh_token");
    removeStorageItem("gqt_user");
    removeStorageItem("gqt_profile");

    set({
      user: null,
      studentProfile: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
    });
  },

  setLoading: (isLoading) => set({ isLoading }),

  hydrateAuth: async (silent = true) => {
    const token = getStorageItem("gqt_access_token");
    if (!token) {
      set({ user: null, studentProfile: null, isAuthenticated: false, isLoading: false });
      return null;
    }

    try {
      if (!silent && !get().user) {
        set({ isLoading: true });
      }
      const user = await authApi.getMe();
      const studentProfile = (user as any).student_profile || null;

      setStorageItem("gqt_user", JSON.stringify(user));
      if (studentProfile) {
        setStorageItem("gqt_profile", JSON.stringify(studentProfile));
      }

      set({
        user,
        studentProfile,
        isAuthenticated: true,
        isLoading: false,
      });
      return user;
    } catch (err: any) {
      // If 401 or network failure
      if (err.response?.status === 401) {
        get().clearAuth();
      }
      set({ isLoading: false });
      return null;
    }
  },
}));
