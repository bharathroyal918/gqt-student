import { apiClient } from "./client";
import { ApiSuccessResponse } from "../types/api";
import {
  StudentRecordedCourseItem,
  CourseRecordedClassesDetail,
  RecordedClassStreamData,
  RecordedClassItem,
  CourseEnrollmentItem,
} from "../types/recordedClasses";

export const recordedClassesApi = {
  // ---------------------------------------------------------------------------
  // STUDENT ENDPOINTS
  // ---------------------------------------------------------------------------

  /** List all courses with recorded class statistics and enrollment status */
  getStudentCourses: async (): Promise<StudentRecordedCourseItem[]> => {
    const res = await apiClient.get<ApiSuccessResponse<{ courses: StudentRecordedCourseItem[] }>>(
      "/students/recorded-classes/"
    );
    return res.data.data.courses;
  },

  /** Get playlist of recorded classes for a course with lock flags */
  getCoursePlaylist: async (courseId: string): Promise<CourseRecordedClassesDetail> => {
    const res = await apiClient.get<ApiSuccessResponse<CourseRecordedClassesDetail>>(
      `/students/recorded-classes/${courseId}/`
    );
    return res.data.data;
  },

  /** Get full stream source for a video (returns 403 if restricted) */
  getVideoStream: async (courseId: string, videoId: string): Promise<RecordedClassStreamData> => {
    const res = await apiClient.get<ApiSuccessResponse<RecordedClassStreamData>>(
      `/students/recorded-classes/${courseId}/videos/${videoId}/`
    );
    return res.data.data;
  },

  /** Save playback progress or mark video completed */
  updateVideoProgress: async (
    courseId: string,
    videoId: string,
    payload: { last_position_seconds?: number; is_completed?: boolean }
  ): Promise<{ video_id: string; last_position_seconds: number; is_completed: boolean }> => {
    const res = await apiClient.post<
      ApiSuccessResponse<{ video_id: string; last_position_seconds: number; is_completed: boolean }>
    >(`/students/recorded-classes/${courseId}/videos/${videoId}/progress/`, payload);
    return res.data.data;
  },

  // ---------------------------------------------------------------------------
  // ADMIN ENDPOINTS
  // ---------------------------------------------------------------------------

  /** Admin list all recorded classes for a course */
  getAdminCourseVideos: async (courseId: string): Promise<RecordedClassItem[]> => {
    const res = await apiClient.get<ApiSuccessResponse<RecordedClassItem[]>>(
      `/admin/courses/${courseId}/recorded-classes/`
    );
    return res.data.data;
  },

  /** Admin create recorded class (supports JSON or multipart FormData for video upload) */
  createAdminVideo: async (courseId: string, data: FormData | object): Promise<RecordedClassItem> => {
    const headers = data instanceof FormData ? { "Content-Type": "multipart/form-data" } : {};
    const res = await apiClient.post<ApiSuccessResponse<RecordedClassItem>>(
      `/admin/courses/${courseId}/recorded-classes/`,
      data,
      { headers }
    );
    return res.data.data;
  },

  /** Admin update recorded class */
  updateAdminVideo: async (
    courseId: string,
    videoId: string,
    data: FormData | object
  ): Promise<RecordedClassItem> => {
    const headers = data instanceof FormData ? { "Content-Type": "multipart/form-data" } : {};
    const res = await apiClient.patch<ApiSuccessResponse<RecordedClassItem>>(
      `/admin/courses/${courseId}/recorded-classes/${videoId}/`,
      data,
      { headers }
    );
    return res.data.data;
  },

  /** Admin delete recorded class */
  deleteAdminVideo: async (courseId: string, videoId: string): Promise<void> => {
    await apiClient.delete(`/admin/courses/${courseId}/recorded-classes/${videoId}/`);
  },

  /** Admin bulk reorder recorded classes */
  reorderAdminVideos: async (
    courseId: string,
    orderItems: Array<{ id: string; order_index: number }>
  ): Promise<void> => {
    await apiClient.post(`/admin/courses/${courseId}/recorded-classes/reorder/`, {
      order_items: orderItems,
    });
  },

  /** Admin list enrolled students for a course */
  getAdminCourseEnrollments: async (courseId: string): Promise<CourseEnrollmentItem[]> => {
    const res = await apiClient.get<ApiSuccessResponse<CourseEnrollmentItem[]>>(
      `/admin/courses/${courseId}/enrollments/`
    );
    return res.data.data;
  },

  /** Admin allocate / approve course enrollment for a student */
  allocateCourseEnrollment: async (
    courseId: string,
    payload: { student_id: string; status?: string }
  ): Promise<CourseEnrollmentItem> => {
    const res = await apiClient.post<ApiSuccessResponse<CourseEnrollmentItem>>(
      `/admin/courses/${courseId}/enrollments/allocate/`,
      payload
    );
    return res.data.data;
  },

  /** Admin revoke course enrollment for a student */
  revokeCourseEnrollment: async (courseId: string, studentId: string): Promise<void> => {
    await apiClient.post(`/admin/courses/${courseId}/enrollments/${studentId}/revoke/`);
  },

  // ---------------------------------------------------------------------------
  // MODULE / FOLDER MANAGEMENT (CUSTOM FOLDERS & COMPONENTS)
  // ---------------------------------------------------------------------------

  /** Admin list all folders / modules for a course */
  getCourseModules: async (courseId: string): Promise<any[]> => {
    const res = await apiClient.get<any>("/admin/modules/", {
      params: { course_id: courseId, page_size: 100 },
    });
    if (res.data?.results) return res.data.results;
    if (res.data?.data) {
      if (Array.isArray(res.data.data)) return res.data.data;
      if (res.data.data.results) return res.data.data.results;
    }
    if (Array.isArray(res.data)) return res.data;
    return [];
  },

  /** Admin create a new custom folder / module component */
  createCourseModule: async (payload: {
    course_id: string;
    title: string;
    summary?: string;
    order_index?: number;
  }): Promise<any> => {
    const res = await apiClient.post<any>("/admin/modules/", payload);
    return res.data?.data || res.data;
  },

  /** Admin update / rename folder module component */
  updateCourseModule: async (
    moduleId: string,
    payload: { title?: string; summary?: string; order_index?: number }
  ): Promise<any> => {
    const res = await apiClient.patch<any>(`/admin/modules/${moduleId}/`, payload);
    return res.data?.data || res.data;
  },

  /** Admin delete a folder module component */
  deleteCourseModule: async (moduleId: string): Promise<void> => {
    await apiClient.delete(`/admin/modules/${moduleId}/`);
  },
};
