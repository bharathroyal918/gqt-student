import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Video,
  Plus,
  Edit2,
  Trash2,
  Youtube,
  FileVideo,
  Users,
  Search,
  CheckCircle2,
  UserPlus,
  RefreshCw,
} from "lucide-react";
import { adminApi } from "../../api/adminApi";
import { recordedClassesApi } from "../../api/recordedClassesApi";
import { RecordedClassItem } from "../../types/recordedClasses";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Modal } from "../../components/ui/Modal";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { FormField, Input, Textarea, Checkbox, Select } from "../../components/ui/Form";
import { LoadingState } from "../../components/ui/LoadingState";
import { useToast } from "../../context/ToastContext";
import { UserAvatar } from "../../components/ui/UserAvatar";

export const AdminRecordedClassesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [selectedCourseId, setSelectedCourseId] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"VIDEOS" | "STUDENTS">("VIDEOS");
  const [searchVideoQuery, setSearchVideoQuery] = useState("");
  const [searchStudentQuery, setSearchStudentQuery] = useState("");

  // Video Modals
  const [isAddVideoOpen, setIsAddVideoOpen] = useState(false);
  const [editingVideo, setEditingVideo] = useState<RecordedClassItem | null>(null);
  const [deletingVideoId, setDeletingVideoId] = useState<string | null>(null);

  // Allocation Modals
  const [isAllocateModalOpen, setIsAllocateModalOpen] = useState(false);
  const [studentSearchInput, setStudentSearchInput] = useState("");
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [revokingStudentId, setRevokingStudentId] = useState<string | null>(null);

  // Video Form State
  const [videoSourceType, setVideoSourceType] = useState<"YOUTUBE" | "DIRECT">("YOUTUBE");
  const [videoForm, setVideoForm] = useState({
    title: "",
    slug: "",
    description: "",
    order_index: 1,
    youtube_url: "",
    video_url: "",
    duration_formatted: "30:00",
    is_preview: false,
    is_published: true,
    notes: "",
    resources_url: "",
  });
  const [uploadedVideoFile, setUploadedVideoFile] = useState<File | null>(null);

  // Fetch all courses for selector
  const { data: coursesData, isLoading: isCoursesLoading } = useQuery({
    queryKey: ["admin-courses-list"],
    queryFn: () => adminApi.getCourses({ page_size: 100 }),
  });

  const courses = coursesData?.data || [];

  // Auto-select first course if none selected
  React.useEffect(() => {
    if (courses.length > 0 && !selectedCourseId) {
      setSelectedCourseId(courses[0].id);
    }
  }, [courses, selectedCourseId]);

  // Fetch Recorded Classes for selected course
  const {
    data: videosData,
    refetch: refetchVideos,
    isFetching: isVideosFetching,
  } = useQuery({
    queryKey: ["admin-recorded-videos", selectedCourseId],
    queryFn: () => recordedClassesApi.getAdminCourseVideos(selectedCourseId),
    enabled: Boolean(selectedCourseId),
  });

  // Fetch Enrolled Students for selected course
  const {
    data: enrollmentsData,
    refetch: refetchEnrollments,
    isFetching: isEnrollmentsFetching,
  } = useQuery({
    queryKey: ["admin-course-enrollments", selectedCourseId],
    queryFn: () => recordedClassesApi.getAdminCourseEnrollments(selectedCourseId),
    enabled: Boolean(selectedCourseId),
  });

  // Fetch all students for allocation picker
  const { data: allStudentsData } = useQuery({
    queryKey: ["admin-students-picker"],
    queryFn: () => adminApi.getStudents({ page_size: 150 }),
    enabled: isAllocateModalOpen,
  });

  const allStudents = allStudentsData?.data || [];
  const filteredStudentsPicker = React.useMemo(() => {
    if (!studentSearchInput.trim()) return allStudents;
    const q = studentSearchInput.toLowerCase();
    return allStudents.filter(
      (s) =>
        s.full_name?.toLowerCase().includes(q) ||
        s.email?.toLowerCase().includes(q) ||
        s.student_id_number?.toLowerCase().includes(q) ||
        s.batch_code?.toLowerCase().includes(q)
    );
  }, [allStudents, studentSearchInput]);

  const videos = videosData || [];
  const enrollments = enrollmentsData || [];

  const selectedCourse = courses.find((c) => c.id === selectedCourseId);

  // Mutations
  const createVideoMutation = useMutation({
    mutationFn: (formData: FormData | object) =>
      recordedClassesApi.createAdminVideo(selectedCourseId, formData),
    onSuccess: () => {
      success("Video Created", "Recorded class session added to course.");
      setIsAddVideoOpen(false);
      resetVideoForm();
      queryClient.invalidateQueries({ queryKey: ["admin-recorded-videos", selectedCourseId] });
      queryClient.invalidateQueries({ queryKey: ["student", "recorded-classes"] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.message || err.response?.data?.error?.message || "Failed to create video";
      toastError("Creation Failed", msg);
    },
  });

  const updateVideoMutation = useMutation({
    mutationFn: ({ videoId, formData }: { videoId: string; formData: FormData | object }) =>
      recordedClassesApi.updateAdminVideo(selectedCourseId, videoId, formData),
    onSuccess: () => {
      success("Video Updated", "Recorded class details updated.");
      setEditingVideo(null);
      resetVideoForm();
      queryClient.invalidateQueries({ queryKey: ["admin-recorded-videos", selectedCourseId] });
      queryClient.invalidateQueries({ queryKey: ["student", "recorded-classes"] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.message || err.response?.data?.error?.message || "Failed to update video";
      toastError("Update Failed", msg);
    },
  });

  const deleteVideoMutation = useMutation({
    mutationFn: (videoId: string) =>
      recordedClassesApi.deleteAdminVideo(selectedCourseId, videoId),
    onSuccess: () => {
      success("Video Deleted", "Recorded class removed.");
      setDeletingVideoId(null);
      queryClient.invalidateQueries({ queryKey: ["admin-recorded-videos", selectedCourseId] });
      queryClient.invalidateQueries({ queryKey: ["student", "recorded-classes"] });
    },
    onError: () => toastError("Delete Failed", "Could not delete video class."),
  });

  const allocateStudentMutation = useMutation({
    mutationFn: (payload: { student_id: string }) =>
      recordedClassesApi.allocateCourseEnrollment(selectedCourseId, payload),
    onSuccess: () => {
      success("Access Approved", "Student successfully enrolled into course with full video access.");
      setIsAllocateModalOpen(false);
      setSelectedStudentId("");
      setStudentSearchInput("");
      queryClient.invalidateQueries({ queryKey: ["admin-course-enrollments", selectedCourseId] });
      queryClient.invalidateQueries({ queryKey: ["student", "recorded-classes"] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.message || "Failed to allocate course.";
      toastError("Allocation Failed", msg);
    },
  });

  const revokeStudentMutation = useMutation({
    mutationFn: (studentId: string) =>
      recordedClassesApi.revokeCourseEnrollment(selectedCourseId, studentId),
    onSuccess: () => {
      success("Access Revoked", "Student full course access has been revoked.");
      setRevokingStudentId(null);
      queryClient.invalidateQueries({ queryKey: ["admin-course-enrollments", selectedCourseId] });
      queryClient.invalidateQueries({ queryKey: ["student", "recorded-classes"] });
    },
    onError: () => toastError("Error", "Could not revoke course enrollment."),
  });

  const resetVideoForm = () => {
    setVideoForm({
      title: "",
      slug: "",
      description: "",
      order_index: (videos.length || 0) + 1,
      youtube_url: "",
      video_url: "",
      duration_formatted: "30:00",
      is_preview: false,
      is_published: true,
      notes: "",
      resources_url: "",
    });
    setUploadedVideoFile(null);
    setVideoSourceType("YOUTUBE");
  };

  const handleOpenAddVideo = () => {
    resetVideoForm();
    setIsAddVideoOpen(true);
  };

  const handleOpenEditVideo = (v: RecordedClassItem) => {
    setEditingVideo(v);
    setVideoSourceType(v.video_source_type === "DIRECT" ? "DIRECT" : "YOUTUBE");
    setVideoForm({
      title: v.title,
      slug: v.slug,
      description: v.description || "",
      order_index: v.order_index,
      youtube_url: v.youtube_url || "",
      video_url: v.video_url || "",
      duration_formatted: v.duration_formatted || "30:00",
      is_preview: v.is_preview,
      is_published: true,
      notes: v.notes || "",
      resources_url: v.resources_url || "",
    });
    setUploadedVideoFile(null);
  };

  const handleSubmitVideo = (e: React.FormEvent) => {
    e.preventDefault();
    if (!videoForm.title.trim()) {
      toastError("Validation Error", "Please provide a video title.");
      return;
    }

    const formData = new FormData();
    formData.append("title", videoForm.title.trim());
    if (videoForm.slug) formData.append("slug", videoForm.slug.trim());
    formData.append("description", videoForm.description.trim());
    formData.append("order_index", String(videoForm.order_index));
    formData.append("video_source_type", videoSourceType);
    formData.append("duration_formatted", videoForm.duration_formatted.trim());
    formData.append("is_preview", String(videoForm.is_preview));
    formData.append("is_published", String(videoForm.is_published));
    formData.append("notes", videoForm.notes.trim());
    formData.append("resources_url", videoForm.resources_url.trim());

    if (videoSourceType === "YOUTUBE") {
      formData.append("youtube_url", videoForm.youtube_url.trim());
    } else {
      if (uploadedVideoFile) {
        formData.append("video_file", uploadedVideoFile);
      }
      if (videoForm.video_url) {
        formData.append("video_url", videoForm.video_url.trim());
      }
    }

    if (editingVideo) {
      updateVideoMutation.mutate({ videoId: editingVideo.id, formData });
    } else {
      createVideoMutation.mutate(formData);
    }
  };

  const filteredVideos = React.useMemo(() => {
    if (!searchVideoQuery.trim()) return videos;
    const q = searchVideoQuery.toLowerCase();
    return videos.filter((v) => v.title.toLowerCase().includes(q) || v.description?.toLowerCase().includes(q));
  }, [videos, searchVideoQuery]);

  const filteredEnrollments = React.useMemo(() => {
    if (!searchStudentQuery.trim()) return enrollments;
    const q = searchStudentQuery.toLowerCase();
    return enrollments.filter(
      (e) =>
        e.full_name?.toLowerCase().includes(q) ||
        e.email?.toLowerCase().includes(q) ||
        e.student_id_number?.toLowerCase().includes(q) ||
        e.batch_code?.toLowerCase().includes(q)
    );
  }, [enrollments, searchStudentQuery]);

  if (isCoursesLoading) {
    return (
      <div className="flex h-96 flex-col items-center justify-center space-y-4">
        <LoadingState message="Loading administrative recorded classes..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <Video className="h-6 w-6 text-brand-500" />
            <span>Recorded Classes Management</span>
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Upload video lessons, embed YouTube lectures, and allocate student curriculum access with first 5 free preview logic.
          </p>
        </div>

        {/* Course Switcher Selector */}
        <div className="flex items-center gap-3 self-start sm:self-auto">
          <div className="w-64">
            <Select
              value={selectedCourseId}
              onChange={(e) => setSelectedCourseId(e.target.value)}
              className="text-xs font-semibold"
            >
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title}
                </option>
              ))}
            </Select>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              refetchVideos();
              refetchEnrollments();
            }}
            disabled={isVideosFetching || isEnrollmentsFetching}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isVideosFetching ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Course Overview Banner */}
      {selectedCourse && (
        <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-surface-900 p-5 text-white border border-indigo-500/20 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">
                Active Curriculum Track
              </span>
              <Badge variant="indigo" size="sm">
                {videos.length} Total Lessons
              </Badge>
              <Badge variant="emerald" size="sm">
                5 Free Preview Lessons
              </Badge>
            </div>
            <h2 className="text-lg font-bold">{selectedCourse.title}</h2>
          </div>

          <div className="flex items-center gap-2">
            <Button
              onClick={handleOpenAddVideo}
              size="sm"
              className="flex items-center gap-1.5 shadow-md shadow-brand-500/20"
            >
              <Plus className="h-4 w-4" />
              <span>Add Video Lecture</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsAllocateModalOpen(true)}
              className="flex items-center gap-1.5 bg-white/10 hover:bg-white/20 text-white border-white/20"
            >
              <UserPlus className="h-4 w-4" />
              <span>Allocate Student</span>
            </Button>
          </div>
        </div>
      )}

      {/* Tabs: Videos vs Enrolled Students */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-surface-800 pb-2">
        <button
          onClick={() => setActiveTab("VIDEOS")}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
            activeTab === "VIDEOS"
              ? "bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20 shadow-sm"
              : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
          }`}
        >
          <Video className="h-4 w-4" />
          <span>Recorded Videos ({videos.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("STUDENTS")}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
            activeTab === "STUDENTS"
              ? "bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20 shadow-sm"
              : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
          }`}
        >
          <Users className="h-4 w-4" />
          <span>Enrolled Students ({enrollments.length})</span>
        </button>
      </div>

      {/* TAB 1: VIDEOS MANAGEMENT */}
      {activeTab === "VIDEOS" && (
        <div className="space-y-4">
          {/* Search bar */}
          <div className="flex items-center justify-between gap-3">
            <div className="relative w-72">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search lessons..."
                value={searchVideoQuery}
                onChange={(e) => setSearchVideoQuery(e.target.value)}
                className="w-full rounded-xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 py-1.5 pl-8 pr-3 text-xs font-medium text-slate-900 dark:text-white placeholder:text-slate-400 focus:border-brand-500 focus:outline-none"
              />
            </div>
          </div>

          {videos.length === 0 ? (
            <Card className="p-12 text-center">
              <Video className="h-12 w-12 text-slate-400 mx-auto mb-3 opacity-60" />
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">
                No Recorded Classes Added Yet
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto mt-1 mb-4">
                Add your first YouTube or direct video session for this course. First 5 videos are free previews for all registered students.
              </p>
              <Button onClick={handleOpenAddVideo} size="sm" className="inline-flex items-center gap-1.5">
                <Plus className="h-4 w-4" />
                <span>Add First Video</span>
              </Button>
            </Card>
          ) : (
            <Card className="overflow-hidden border border-slate-200 dark:border-surface-800">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900 text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4"># Order</th>
                      <th className="py-3 px-4">Lesson Details</th>
                      <th className="py-3 px-4">Video Type</th>
                      <th className="py-3 px-4">Duration</th>
                      <th className="py-3 px-4">Preview Status</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-surface-800/80">
                    {filteredVideos.map((v) => {
                      const isFirstFive = v.order_index <= 5;

                      return (
                        <tr
                          key={v.id}
                          className="hover:bg-slate-50 dark:hover:bg-surface-900/50 transition-colors"
                        >
                          {/* Order index */}
                          <td className="py-3 px-4 font-bold font-mono text-slate-700 dark:text-slate-300">
                            #{String(v.order_index).padStart(2, "0")}
                          </td>

                          {/* Title & Notes snippet */}
                          <td className="py-3 px-4 max-w-sm">
                            <div className="font-bold text-slate-900 dark:text-white line-clamp-1">
                              {v.title}
                            </div>
                            <div className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">
                              {v.description || v.notes || "No notes"}
                            </div>
                          </td>

                          {/* Video source type */}
                          <td className="py-3 px-4">
                            {v.video_source_type === "YOUTUBE" ? (
                              <Badge variant="rose" size="sm" className="flex items-center gap-1 w-fit">
                                <Youtube className="h-3 w-3" />
                                <span>YouTube</span>
                              </Badge>
                            ) : (
                              <Badge variant="indigo" size="sm" className="flex items-center gap-1 w-fit">
                                <FileVideo className="h-3 w-3" />
                                <span>Direct Upload</span>
                              </Badge>
                            )}
                          </td>

                          {/* Duration */}
                          <td className="py-3 px-4 font-mono text-slate-600 dark:text-slate-400">
                            ⏱ {v.duration_formatted || "30:00"}
                          </td>

                          {/* Free Preview badge */}
                          <td className="py-3 px-4">
                            {isFirstFive || v.is_preview ? (
                              <Badge variant="emerald" size="sm" className="flex items-center gap-1 w-fit">
                                <CheckCircle2 className="h-3 w-3" />
                                <span>Free Preview ({isFirstFive ? "Auto 1-5" : "Override"})</span>
                              </Badge>
                            ) : (
                              <Badge variant="neutral" size="sm" className="w-fit">
                                Enrolled Only
                              </Badge>
                            )}
                          </td>

                          {/* Actions */}
                          <td className="py-3 px-4 text-right">
                            <div className="flex items-center justify-end gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleOpenEditVideo(v)}
                                className="h-8 w-8 p-0"
                              >
                                <Edit2 className="h-3.5 w-3.5" />
                              </Button>

                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setDeletingVideoId(v.id)}
                                className="h-8 w-8 p-0 text-rose-500 hover:text-rose-600 hover:bg-rose-500/10"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* TAB 2: STUDENT ALLOCATIONS */}
      {activeTab === "STUDENTS" && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="relative w-72">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search enrolled students..."
                value={searchStudentQuery}
                onChange={(e) => setSearchStudentQuery(e.target.value)}
                className="w-full rounded-xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 py-1.5 pl-8 pr-3 text-xs font-medium text-slate-900 dark:text-white placeholder:text-slate-400 focus:border-brand-500 focus:outline-none"
              />
            </div>

            <Button
              onClick={() => setIsAllocateModalOpen(true)}
              size="sm"
              className="flex items-center gap-1.5"
            >
              <UserPlus className="h-4 w-4" />
              <span>Enroll Student into Course</span>
            </Button>
          </div>

          {enrollments.length === 0 ? (
            <Card className="p-12 text-center">
              <Users className="h-12 w-12 text-slate-400 mx-auto mb-3 opacity-60" />
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">
                No Students Enrolled in this Course Yet
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto mt-1 mb-4">
                Students without enrollment can only see the first 5 preview videos. Allocate students to grant full access.
              </p>
              <Button onClick={() => setIsAllocateModalOpen(true)} size="sm">
                Allocate Student Now
              </Button>
            </Card>
          ) : (
            <Card className="overflow-hidden border border-slate-200 dark:border-surface-800">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900 text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4">Student Profile</th>
                      <th className="py-3 px-4">Student ID</th>
                      <th className="py-3 px-4">Batch</th>
                      <th className="py-3 px-4">Enrolled Date</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-surface-800/80">
                    {filteredEnrollments.map((enr) => {
                      const isActive = enr.status === "ACTIVE";

                      return (
                        <tr
                          key={enr.id}
                          className="hover:bg-slate-50 dark:hover:bg-surface-900/50 transition-colors"
                        >
                          {/* Student */}
                          <td className="py-3 px-4">
                            <div className="flex items-center gap-2.5">
                              <UserAvatar
                                src={enr.avatar_url}
                                name={enr.full_name}
                                size="sm"
                              />
                              <div>
                                <div className="font-bold text-slate-900 dark:text-white">
                                  {enr.full_name}
                                </div>
                                <div className="text-[11px] text-slate-400">{enr.email}</div>
                              </div>
                            </div>
                          </td>

                          {/* ID Number */}
                          <td className="py-3 px-4 font-mono text-slate-700 dark:text-slate-300">
                            {enr.student_id_number || "—"}
                          </td>

                          {/* Batch code */}
                          <td className="py-3 px-4">
                            <Badge variant="indigo" size="sm">
                              {enr.batch_code || "General"}
                            </Badge>
                          </td>

                          {/* Enrolled date */}
                          <td className="py-3 px-4 text-slate-500">
                            {new Date(enr.enrolled_at).toLocaleDateString()}
                          </td>

                          {/* Status */}
                          <td className="py-3 px-4">
                            {isActive ? (
                              <Badge variant="emerald" size="sm">
                                Full Access
                              </Badge>
                            ) : (
                              <Badge variant="rose" size="sm">
                                {enr.status}
                              </Badge>
                            )}
                          </td>

                          {/* Actions */}
                          <td className="py-3 px-4 text-right">
                            {isActive ? (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setRevokingStudentId(enr.student_id)}
                                className="text-rose-500 hover:text-rose-600 hover:bg-rose-500/10 border-rose-500/20 text-xs py-1"
                              >
                                Revoke Access
                              </Button>
                            ) : (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() =>
                                  allocateStudentMutation.mutate({ student_id: enr.student_id })
                                }
                                className="text-emerald-600 dark:text-emerald-400 text-xs py-1"
                              >
                                Re-activate
                              </Button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* MODAL: ADD / EDIT VIDEO LECTURE */}
      <Modal
        isOpen={isAddVideoOpen || Boolean(editingVideo)}
        onClose={() => {
          setIsAddVideoOpen(false);
          setEditingVideo(null);
        }}
        title={editingVideo ? "Edit Recorded Class Lecture" : "Add Recorded Class Lecture"}
        size="lg"
      >
        <form onSubmit={handleSubmitVideo} className="space-y-4">
          {/* Video Source Type Switcher (YouTube vs Direct Upload) */}
          <div className="rounded-2xl bg-slate-100 dark:bg-surface-900 p-1.5 flex gap-2 border border-slate-200 dark:border-surface-800">
            <button
              type="button"
              onClick={() => setVideoSourceType("YOUTUBE")}
              className={`flex-1 flex items-center justify-center gap-2 rounded-xl py-2 text-xs font-bold transition-all ${
                videoSourceType === "YOUTUBE"
                  ? "bg-white dark:bg-surface-800 text-rose-600 dark:text-rose-400 shadow-sm"
                  : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              <Youtube className="h-4 w-4 text-rose-500" />
              <span>YouTube Video Link</span>
            </button>

            <button
              type="button"
              onClick={() => setVideoSourceType("DIRECT")}
              className={`flex-1 flex items-center justify-center gap-2 rounded-xl py-2 text-xs font-bold transition-all ${
                videoSourceType === "DIRECT"
                  ? "bg-white dark:bg-surface-800 text-brand-600 dark:text-brand-400 shadow-sm"
                  : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              <FileVideo className="h-4 w-4 text-brand-500" />
              <span>Direct Video Upload / Stream URL</span>
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormField label="Lesson Title" required>
              <Input
                placeholder="e.g. 01 - Java Syntax & JVM Internals"
                value={videoForm.title}
                onChange={(e) => setVideoForm({ ...videoForm, title: e.target.value })}
                required
              />
            </FormField>

            <FormField label="Order / Sequence Index" required>
              <Input
                type="number"
                min={1}
                value={videoForm.order_index}
                onChange={(e) => setVideoForm({ ...videoForm, order_index: Number(e.target.value) })}
                required
              />
            </FormField>
          </div>

          {videoSourceType === "YOUTUBE" ? (
            <FormField label="YouTube URL (Regular, Short, or Embed)" required>
              <Input
                placeholder="https://www.youtube.com/watch?v=... or https://youtu.be/..."
                value={videoForm.youtube_url}
                onChange={(e) => setVideoForm({ ...videoForm, youtube_url: e.target.value })}
                required
              />
            </FormField>
          ) : (
            <div className="space-y-3">
              <FormField label="Direct Video File Upload (MP4 / WebM / MKV)">
                <input
                  type="file"
                  accept="video/*"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setUploadedVideoFile(e.target.files[0]);
                    }
                  }}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-800 p-2 text-xs"
                />
              </FormField>

              <FormField label="Or External Cloud / Storage Stream URL">
                <Input
                  placeholder="https://storage.supabase.co/..."
                  value={videoForm.video_url}
                  onChange={(e) => setVideoForm({ ...videoForm, video_url: e.target.value })}
                />
              </FormField>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormField label="Duration (MM:SS or HH:MM:SS)">
              <Input
                placeholder="45:00"
                value={videoForm.duration_formatted}
                onChange={(e) => setVideoForm({ ...videoForm, duration_formatted: e.target.value })}
              />
            </FormField>

            <FormField label="Supplementary Resources / Repo URL">
              <Input
                placeholder="https://github.com/..."
                value={videoForm.resources_url}
                onChange={(e) => setVideoForm({ ...videoForm, resources_url: e.target.value })}
              />
            </FormField>
          </div>

          <FormField label="Lecture Notes & Syllabus Markdown Summary">
            <Textarea
              rows={3}
              placeholder="Summary of topics covered, code highlights, and key definitions..."
              value={videoForm.notes}
              onChange={(e) => setVideoForm({ ...videoForm, notes: e.target.value })}
            />
          </FormField>

          <div className="rounded-xl bg-slate-50 dark:bg-surface-900 p-3 text-xs border border-slate-200 dark:border-surface-800 flex items-center justify-between">
            <div>
              <div className="font-semibold text-slate-900 dark:text-white">Preview Access Rule</div>
              <div className="text-[11px] text-slate-400">
                Videos with order index 1 to 5 are automatically free previews for all registered students.
              </div>
            </div>
            <Checkbox
              label="Explicit Free Preview"
              checked={videoForm.is_preview}
              onChange={(e) => setVideoForm({ ...videoForm, is_preview: e.target.checked })}
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200 dark:border-surface-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsAddVideoOpen(false);
                setEditingVideo(null);
              }}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createVideoMutation.isPending || updateVideoMutation.isPending}
            >
              {createVideoMutation.isPending || updateVideoMutation.isPending
                ? "Saving Video..."
                : editingVideo
                ? "Update Video"
                : "Add Video Lecture"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* MODAL: ALLOCATE STUDENT TO COURSE */}
      <Modal
        isOpen={isAllocateModalOpen}
        onClose={() => setIsAllocateModalOpen(false)}
        title="Allocate Course Access to Student"
        size="md"
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-500">
            Search for a registered student by name, email, student ID number, or batch code. Allocating grants full unlocked access to all video sessions for <strong className="text-slate-800 dark:text-slate-200">{selectedCourse?.title}</strong>.
          </p>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search student..."
              value={studentSearchInput}
              onChange={(e) => setStudentSearchInput(e.target.value)}
              className="pl-9"
            />
          </div>

          <div className="max-h-60 overflow-y-auto space-y-1.5 border border-slate-200 dark:border-surface-800 rounded-2xl p-2 bg-slate-50 dark:bg-surface-900/60">
            {filteredStudentsPicker.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-400">No matching students found</div>
            ) : (
              filteredStudentsPicker.map((stu) => {
                const isSelected = selectedStudentId === stu.id;
                const isAlreadyEnrolled = enrollments.some((e) => e.student_id === stu.id && e.status === "ACTIVE");

                return (
                  <button
                    key={stu.id}
                    type="button"
                    disabled={isAlreadyEnrolled}
                    onClick={() => setSelectedStudentId(stu.id)}
                    className={`w-full text-left rounded-xl p-2.5 transition-all flex items-center justify-between border ${
                      isAlreadyEnrolled
                        ? "opacity-50 cursor-not-allowed bg-slate-100 dark:bg-surface-800 border-transparent"
                        : isSelected
                        ? "bg-brand-500/10 border-brand-500/40 text-brand-600 dark:text-brand-400 shadow-sm"
                        : "bg-white dark:bg-surface-900 border-slate-100 dark:border-surface-800 hover:bg-slate-50 dark:hover:bg-surface-800"
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <UserAvatar src={stu.avatar_url} name={stu.full_name} size="sm" />
                      <div className="min-w-0">
                        <div className="font-bold text-xs text-slate-900 dark:text-white truncate">
                          {stu.full_name}
                        </div>
                        <div className="text-[11px] text-slate-400 truncate">{stu.email}</div>
                      </div>
                    </div>

                    <div>
                      {isAlreadyEnrolled ? (
                        <Badge variant="emerald" size="sm">
                          Already Enrolled
                        </Badge>
                      ) : isSelected ? (
                        <Badge variant="indigo" size="sm">
                          Selected
                        </Badge>
                      ) : (
                        <span className="text-xs font-mono text-slate-400">{stu.batch_code || stu.student_id_number}</span>
                      )}
                    </div>
                  </button>
                );
              })
            )}
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-200 dark:border-surface-800">
            <Button variant="outline" onClick={() => setIsAllocateModalOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={!selectedStudentId || allocateStudentMutation.isPending}
              onClick={() => allocateStudentMutation.mutate({ student_id: selectedStudentId })}
            >
              {allocateStudentMutation.isPending ? "Allocating..." : "Confirm & Grant Access"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* CONFIRM DELETE VIDEO DIALOG */}
      <ConfirmDialog
        isOpen={Boolean(deletingVideoId)}
        onClose={() => setDeletingVideoId(null)}
        onConfirm={() => deletingVideoId && deleteVideoMutation.mutate(deletingVideoId)}
        title="Delete Recorded Video Lesson"
        message="Are you sure you want to permanently delete this recorded class video? This action cannot be undone."
        confirmText="Delete Video"
        variant="danger"
      />

      {/* CONFIRM REVOKE STUDENT DIALOG */}
      <ConfirmDialog
        isOpen={Boolean(revokingStudentId)}
        onClose={() => setRevokingStudentId(null)}
        onConfirm={() => revokingStudentId && revokeStudentMutation.mutate(revokingStudentId)}
        title="Revoke Course Access"
        message="Are you sure you want to revoke full course access for this student? They will only be able to view the first 5 free preview classes."
        confirmText="Revoke Access"
        variant="danger"
      />
    </div>
  );
};
