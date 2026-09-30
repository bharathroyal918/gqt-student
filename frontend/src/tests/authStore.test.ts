import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore } from "../store/authStore";

describe("useAuthStore — Authentication & Role Ownership State", () => {
  beforeEach(() => {
    useAuthStore.getState().clearAuth();
  });

  it("initializes with unauthenticated default state", () => {
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.studentProfile).toBeNull();
    expect(state.tokens).toBeNull();
  });

  it("updates state correctly upon successful student login", () => {
    const mockUser = {
      id: "student-uuid-1",
      email: "bharath@gqt.local",
      mobile_number: "+919876543210",
      role: "STUDENT" as const,
      is_active: true,
      onboarding_status: "ACTIVE" as const,
    };

    const mockTokens = {
      access: "mock-access-token",
      refresh: "mock-refresh-token",
    };

    const mockProfile = {
      id: "profile-uuid-1",
      full_name: "Bharath Student",
      student_id_number: "GQT2026001",
      batch_code: "2026-JAVA-FS",
      college_name: "GQT Institute",
      graduation_year: 2026,
      total_points: 100,
      current_streak_days: 5,
      highest_streak_days: 10,
    };

    useAuthStore.getState().setAuth(mockUser, mockTokens, mockProfile);

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.tokens?.access).toBe("mock-access-token");
    expect(state.tokens?.refresh).toBe("mock-refresh-token");
    expect(state.user?.role).toBe("STUDENT");
    expect(state.studentProfile?.full_name).toBe("Bharath Student");
  });

  it("updates state correctly upon successful admin login", () => {
    const mockAdmin = {
      id: "admin-uuid-1",
      email: "admin@gqt.local",
      mobile_number: "+919800000000",
      role: "ADMIN" as const,
      is_active: true,
      onboarding_status: "ACTIVE" as const,
    };

    const mockTokens = {
      access: "admin-access",
      refresh: "admin-refresh",
    };

    useAuthStore.getState().setAuth(mockAdmin, mockTokens, undefined);

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user?.role).toBe("ADMIN");
    expect(state.studentProfile).toBeNull();
  });

  it("clears all session state upon clearAuth", () => {
    const mockUser = {
      id: "user-1",
      email: "test@gqt.local",
      mobile_number: "+919876543210",
      role: "STUDENT" as const,
      is_active: true,
      onboarding_status: "ACTIVE" as const,
    };

    const mockTokens = { access: "token-1", refresh: "token-2" };

    useAuthStore.getState().setAuth(mockUser, mockTokens, undefined);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);

    useAuthStore.getState().clearAuth();

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.tokens).toBeNull();
    expect(state.user).toBeNull();
  });
});
