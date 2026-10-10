export type UserRole = "ADMIN" | "STUDENT" | "TPO";

export interface User {
  id: string;
  email: string | null;
  mobile_number: string | null;
  role: UserRole;
  is_active: boolean;
  onboarding_status: "PENDING_ACTIVATION" | "ACTIVE" | "SUSPENDED";
}

export interface StudentProfile {
  id: string;
  student_id_number: string;
  full_name: string;
  batch_code: string;
  college_name?: string;
  graduation_year?: number;
  current_streak_days: number;
  highest_streak_days: number;
  total_points: number;
  avatar_url?: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthState {
  user: User | null;
  studentProfile: StudentProfile | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
