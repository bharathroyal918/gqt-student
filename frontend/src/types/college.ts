export interface College {
  id: string;
  name: string;
  code?: string;
  city?: string;
  state?: string;
  is_active: boolean;
  student_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface CreateCollegePayload {
  name: string;
  code?: string;
  city?: string;
  state?: string;
  is_active?: boolean;
}

export interface UpdateCollegePayload {
  name?: string;
  code?: string;
  city?: string;
  state?: string;
  is_active?: boolean;
}
