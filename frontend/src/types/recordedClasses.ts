export type VideoSourceType = "YOUTUBE" | "DIRECT" | "EXTERNAL" | "LOCKED";

export interface StudentRecordedCourseItem {
  id: string;
  title: string;
  slug: string;
  description: string;
  thumbnail_url: string;
  is_enrolled: boolean;
  enrollment_status: "ACTIVE" | "COMPLETED" | "REVOKED" | "SUSPENDED" | "NOT_ENROLLED";
  total_videos: number;
  preview_videos_count: number;
  completed_videos: number;
  progress_percentage: number;
  has_full_access: boolean;
  free_preview_unrestricted: boolean;
}

export interface RecordedClassItem {
  id: string;
  course_id: string;
  course_title: string;
  module_id: string | null;
  module_title: string | null;
  title: string;
  slug: string;
  order_index: number;
  duration_seconds: number;
  duration_formatted: string;
  thumbnail_url: string;
  is_preview: boolean;
  is_locked: boolean;
  is_completed: boolean;
  last_position_seconds: number;
  lock_reason: string | null;
  description: string;
  video_source_type: VideoSourceType;
  youtube_video_id: string;
  youtube_url: string;
  video_url: string;
  video_file_url: string;
  notes: string;
  resources_url: string;
}

export interface CourseRecordedClassesDetail {
  course: {
    id: string;
    title: string;
    slug: string;
    description: string;
    thumbnail_url: string;
    is_enrolled: boolean;
    enrollment_status: string;
    total_videos: number;
    preview_videos_limit: number;
    completed_videos: number;
    progress_percentage: number;
  };
  videos: RecordedClassItem[];
}

export interface RecordedClassStreamData {
  id: string;
  course_id: string;
  course_title: string;
  title: string;
  slug: string;
  description: string;
  order_index: number;
  video_source_type: VideoSourceType;
  youtube_url: string;
  youtube_video_id: string;
  video_url: string;
  video_file_url: string;
  duration_seconds: number;
  duration_formatted: string;
  thumbnail_url: string;
  is_preview: boolean;
  is_locked: boolean;
  notes: string;
  resources_url: string;
  is_completed: boolean;
  last_position_seconds: number;
}

export interface CourseEnrollmentItem {
  id: string;
  student_id: string;
  student_id_number: string;
  full_name: string;
  email: string;
  batch_code: string;
  avatar_url: string;
  course: string;
  course_title: string;
  status: "ACTIVE" | "COMPLETED" | "REVOKED" | "SUSPENDED";
  enrolled_at: string;
  completed_at: string | null;
}

export interface AdminRecordedClassPayload {
  title: string;
  slug?: string;
  description?: string;
  order_index?: number;
  video_source_type: "YOUTUBE" | "DIRECT" | "EXTERNAL";
  youtube_url?: string;
  video_url?: string;
  duration_seconds?: number;
  duration_formatted?: string;
  thumbnail_url?: string;
  is_preview?: boolean;
  is_published?: boolean;
  notes?: string;
  resources_url?: string;
  module_id?: string | null;
}
