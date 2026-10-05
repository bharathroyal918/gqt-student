export type WorkMode = "ON_SITE" | "REMOTE" | "HYBRID";

export type DriveStatus = "UPCOMING" | "ONGOING" | "CLOSED" | "CANCELLED";

export type ApplicationStatus =
  | "APPLIED"
  | "UNDER_REVIEW"
  | "SHORTLISTED"
  | "SELECTED"
  | "REJECTED";

export interface PlacementDrive {
  id: string;
  company_name: string;
  company_code: string;
  company_logo_url?: string;
  role: string;
  skills: string;
  location: string;
  mode_of_work: WorkMode;
  stipend_or_ctc: string;
  bond_period: string;
  eligibility_criteria: string;
  min_cgpa: string | number;
  eligible_batches: string;
  job_description: string;
  application_deadline: string;
  drive_date?: string | null;
  status: DriveStatus;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  total_applications?: number;
  selected_count?: number;
  shortlisted_count?: number;
  rejected_count?: number;
  has_applied?: boolean;
  my_application_status?: ApplicationStatus | null;
  my_application_id?: string | null;
}

export interface PlacementApplication {
  id: string;
  drive: string;
  drive_details?: {
    id: string;
    company_name: string;
    company_code: string;
    role: string;
    stipend_or_ctc: string;
    location: string;
    mode_of_work: WorkMode;
    bond_period: string;
    application_deadline: string;
    status: DriveStatus;
  };
  student: string;
  status: ApplicationStatus;
  submitted_at: string;
  reviewed_at?: string | null;
  admin_notes: string;
  rejection_reason: string;
  student_name: string;
  student_id_number: string;
  email: string;
  phone_number: string;
  college_name: string;
  branch: string;
  graduation_year?: number | null;
  cgpa_or_percentage: string;
  resume_file?: string | null;
  resume_filename?: string;
  has_resume_file?: boolean;
  resume_download_url?: string | null;
  resume_url?: string;
  portfolio_url?: string;
  github_url?: string;
  linkedin_url?: string;
  skills_summary?: string;
  cover_note?: string;
  created_at: string;
  updated_at: string;
}

export interface PlacementAdminMetrics {
  total_drives: number;
  active_drives: number;
  total_applications: number;
  selected_candidates: number;
  shortlisted_candidates: number;
  rejected_candidates: number;
}

export interface PlacementDriveApplicantsStats {
  total: number;
  applied: number;
  under_review: number;
  shortlisted: number;
  selected: number;
  rejected: number;
}

export interface CreatePlacementDrivePayload {
  company_name: string;
  company_code?: string;
  company_logo_url?: string;
  role: string;
  skills: string;
  location: string;
  mode_of_work: WorkMode;
  stipend_or_ctc: string;
  bond_period: string;
  eligibility_criteria: string;
  min_cgpa?: number | string;
  eligible_batches?: string;
  job_description: string;
  application_deadline: string;
  drive_date?: string | null;
  status?: DriveStatus;
  is_active?: boolean;
}

export interface ApplyPlacementPayload {
  phone_number: string;
  college_name?: string;
  branch?: string;
  graduation_year?: number;
  cgpa_or_percentage: string;
  resume_file?: File | null;
  resume_url?: string;
  portfolio_url?: string;
  github_url?: string;
  linkedin_url?: string;
  skills_summary?: string;
  cover_note?: string;
}

export interface UpdateApplicationStatusPayload {
  status: ApplicationStatus;
  admin_notes?: string;
  rejection_reason?: string;
}
