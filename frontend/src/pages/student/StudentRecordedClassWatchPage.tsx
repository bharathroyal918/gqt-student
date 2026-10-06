import React, { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Video,
  Lock,
  Unlock,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  FileText,
  ExternalLink,
  Info,
  Layers,
  Sparkles,
  ShieldCheck,
  Search,
  BookOpen,
  Volume2,
  Folder,
  FolderOpen,
  ChevronDown,
} from "lucide-react";
import { recordedClassesApi } from "../../api/recordedClassesApi";
import { RecordedClassItem } from "../../types/recordedClasses";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { useToast } from "../../context/ToastContext";

export const StudentRecordedClassWatchPage: React.FC = () => {
  const { courseId, videoId } = useParams<{ courseId: string; videoId?: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [searchPlaylist, setSearchPlaylist] = useState("");
  const [activeTab, setActiveTab] = useState<"NOTES" | "RESOURCES" | "CURRICULUM">("NOTES");
  const [collapsedFolders, setCollapsedFolders] = useState<Record<string, boolean>>({});

  // Fetch Course Playlist
  const {
    data: playlistData,
    isLoading: isPlaylistLoading,
    isError: isPlaylistError,
    error: playlistError,
    refetch: refetchPlaylist,
  } = useQuery({
    queryKey: ["student", "recorded-classes", "playlist", courseId],
    queryFn: () => recordedClassesApi.getCoursePlaylist(courseId!),
    enabled: Boolean(courseId),
  });

  const videos: RecordedClassItem[] = playlistData?.videos || [];
  const course = playlistData?.course;

  // Determine active video: either from URL params or default to first video
  const activeVideo = React.useMemo(() => {
    if (!videos || videos.length === 0) return null;
    if (videoId) {
      const found = videos.find((v) => v.id === videoId);
      if (found) return found;
    }
    return videos[0];
  }, [videos, videoId]);

  // If videoId was not in URL, navigate to activeVideo on load
  useEffect(() => {
    if (courseId && activeVideo && !videoId) {
      navigate(`/recorded-classes/${courseId}/video/${activeVideo.id}`, { replace: true });
    }
  }, [courseId, activeVideo, videoId, navigate]);

  // Ensure active video's folder is expanded
  useEffect(() => {
    if (activeVideo?.module_id) {
      setCollapsedFolders((prev) => ({ ...prev, [activeVideo.module_id!]: false }));
    }
  }, [activeVideo?.module_id]);

  // Mark Completed / Progress Mutation
  const progressMutation = useMutation({
    mutationFn: ({ videoId, is_completed }: { videoId: string; is_completed: boolean }) =>
      recordedClassesApi.updateVideoProgress(courseId!, videoId, { is_completed }),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ["student", "recorded-classes", "playlist", courseId] });
      queryClient.invalidateQueries({ queryKey: ["student", "recorded-classes"] });
      if (res.is_completed) {
        success("Lesson Completed", "Progress saved! Great job keeping up your streak.");
      }
    },
    onError: () => {
      toastError("Error", "Could not record lesson progress.");
    },
  });

  // Calculate Next & Previous Video
  const currentIndex = activeVideo ? videos.findIndex((v) => v.id === activeVideo.id) : -1;
  const prevVideo = currentIndex > 0 ? videos[currentIndex - 1] : null;
  const nextVideo = currentIndex >= 0 && currentIndex < videos.length - 1 ? videos[currentIndex + 1] : null;

  const filteredPlaylist = React.useMemo(() => {
    if (!searchPlaylist.trim()) return videos;
    const q = searchPlaylist.toLowerCase();
    return videos.filter(
      (v) =>
        v.title.toLowerCase().includes(q) ||
        v.module_title?.toLowerCase().includes(q)
    );
  }, [videos, searchPlaylist]);

  // Group playlist by folder / module
  const playlistGroups = React.useMemo(() => {
    const groups: Array<{
      key: string;
      title: string;
      videos: RecordedClassItem[];
      completedCount: number;
    }> = [];

    const map = new Map<string, { title: string; videos: RecordedClassItem[] }>();

    filteredPlaylist.forEach((v) => {
      const groupKey = v.module_id || "__root__";
      const groupTitle = v.module_title || "General Sessions";
      if (!map.has(groupKey)) {
        map.set(groupKey, { title: groupTitle, videos: [] });
      }
      map.get(groupKey)!.videos.push(v);
    });

    map.forEach((val, key) => {
      const completed = val.videos.filter((item) => item.is_completed).length;
      groups.push({
        key,
        title: val.title,
        videos: val.videos,
        completedCount: completed,
      });
    });

    return groups;
  }, [filteredPlaylist]);

  const toggleFolderCollapse = (key: string) => {
    setCollapsedFolders((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  if (isPlaylistLoading) {
    return (
      <div className="flex h-96 flex-col items-center justify-center space-y-4">
        <LoadingState message="Loading theater mode and video playlist..." />
      </div>
    );
  }

  if (isPlaylistError || !course) {
    return (
      <ErrorState
        title="Unable to load recorded session"
        message={playlistError instanceof Error ? playlistError.message : "Course playlist failed to load."}
        onRetry={() => refetchPlaylist()}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Course Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Link to="/recorded-classes">
            <Button variant="ghost" size="sm" className="flex items-center gap-1">
              <ArrowLeft className="h-4 w-4" />
              <span>All Courses</span>
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white line-clamp-1">
                {course.title}
              </h1>
              {course.is_enrolled ? (
                <Badge variant="emerald" size="sm" className="hidden sm:inline-flex items-center gap-1">
                  <ShieldCheck className="h-3 w-3" />
                  <span>Full Access Enrolled</span>
                </Badge>
              ) : (
                <Badge variant="indigo" size="sm" className="hidden sm:inline-flex items-center gap-1">
                  <Unlock className="h-3 w-3" />
                  <span>Free Preview (1-5)</span>
                </Badge>
              )}
            </div>
          </div>
        </div>

        {/* Progress Tracker */}
        {course.total_videos > 0 && (
          <div className="flex items-center gap-3 rounded-2xl bg-white dark:bg-surface-900 p-2.5 px-4 border border-slate-200 dark:border-surface-800 text-xs shadow-sm self-start sm:self-auto">
            <span className="text-slate-400">Progress:</span>
            <span className="font-bold text-slate-900 dark:text-white">
              {course.completed_videos}/{course.total_videos} Completed ({course.progress_percentage}%)
            </span>
          </div>
        )}
      </div>

      {/* Main Theater Layout: Video Player + Playlist Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left / Center: Cinema Video Player & Lesson Details (8 Cols) */}
        <div className="lg:col-span-8 space-y-4">
          {/* Cinema Screen Container */}
          <div className="relative aspect-video w-full overflow-hidden rounded-3xl bg-slate-950 shadow-2xl border border-slate-800/80 flex items-center justify-center">
            {activeVideo?.is_locked ? (
              /* Locked State Overlay Screen */
              <div className="relative z-10 p-6 sm:p-10 text-center max-w-lg space-y-4">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-lg shadow-amber-500/10 animate-pulse">
                  <Lock className="h-8 w-8" />
                </div>

                <div className="space-y-1.5">
                  <h3 className="text-xl sm:text-2xl font-extrabold text-white">
                    Premium Class Locked
                  </h3>
                  <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
                    Lesson #{activeVideo.order_index} is part of the full curriculum. Registered students have free preview access to the first 5 videos.
                  </p>
                </div>

                <div className="rounded-2xl bg-white/5 p-4 text-xs text-slate-300 border border-white/10 text-left space-y-1">
                  <div className="font-semibold text-white flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-amber-400" />
                    <span>How to unlock the full video track?</span>
                  </div>
                  <p className="text-slate-400 text-[11px]">
                    Ask your batch coordinator or administrator to allocate this course to your account profile. Once enrolled, all classes unlock immediately.
                  </p>
                </div>

                <div className="pt-2 flex items-center justify-center gap-3">
                  <Link to="/contact">
                    <Button className="font-semibold shadow-md shadow-brand-500/20">
                      <span>Contact Admin for Access</span>
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  </Link>
                  {videos[0] && (
                    <Button
                      variant="outline"
                      onClick={() => navigate(`/recorded-classes/${courseId}/video/${videos[0].id}`)}
                    >
                      <span>Watch Free Preview (Lesson 1)</span>
                    </Button>
                  )}
                </div>
              </div>
            ) : activeVideo?.video_source_type === "YOUTUBE" && activeVideo.youtube_video_id ? (
              /* YouTube Embed Video Player */
              <iframe
                src={`https://www.youtube-nocookie.com/embed/${activeVideo.youtube_video_id}?autoplay=1&rel=0&modestbranding=1`}
                title={activeVideo.title}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                allowFullScreen
                className="h-full w-full border-0"
              />
            ) : activeVideo?.video_file_url || activeVideo?.video_url ? (
              /* Direct HTML5 Video Player */
              <video
                key={activeVideo.id}
                src={activeVideo.video_file_url || activeVideo.video_url}
                controls
                autoPlay
                className="h-full w-full object-contain"
                poster={activeVideo.thumbnail_url}
              >
                Your browser does not support HTML5 video streaming.
              </video>
            ) : (
              /* Fallback / No Video Link Provided */
              <div className="p-8 text-center text-slate-400 space-y-2">
                <Video className="h-12 w-12 mx-auto opacity-50" />
                <p className="text-sm font-semibold text-white">Video Stream Initializing</p>
                <p className="text-xs text-slate-500">
                  The instructor has not uploaded the media file or provided an embed link for this class yet.
                </p>
              </div>
            )}
          </div>

          {/* Video Control Bar & Title */}
          {activeVideo && (
            <Card className="p-5 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    {activeVideo.module_title && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400">
                        📁 {activeVideo.module_title}
                      </span>
                    )}
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-brand-500/10 text-brand-600 dark:text-brand-400">
                      Lesson #{activeVideo.order_index}
                    </span>
                    {activeVideo.duration_formatted && (
                      <span className="text-xs text-slate-400 font-mono">
                        ⏱ {activeVideo.duration_formatted}
                      </span>
                    )}
                    {activeVideo.is_preview ? (
                      <Badge variant="emerald" size="sm">
                        Free Preview
                      </Badge>
                    ) : (
                      <Badge variant="indigo" size="sm">
                        Full Curriculum
                      </Badge>
                    )}
                  </div>
                  <h2 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-white">
                    {activeVideo.title}
                  </h2>
                </div>

                {/* Mark as Completed / Next Navigation */}
                <div className="flex items-center gap-2 shrink-0">
                  <Button
                    variant={activeVideo.is_completed ? "secondary" : "outline"}
                    size="sm"
                    onClick={() =>
                      progressMutation.mutate({
                        videoId: activeVideo.id,
                        is_completed: !activeVideo.is_completed,
                      })
                    }
                    disabled={progressMutation.isPending || activeVideo.is_locked}
                    className="flex items-center gap-1.5"
                  >
                    <CheckCircle2
                      className={`h-4 w-4 ${
                        activeVideo.is_completed ? "text-emerald-500" : "text-slate-400"
                      }`}
                    />
                    <span>{activeVideo.is_completed ? "Completed" : "Mark Watched"}</span>
                  </Button>

                  {nextVideo && (
                    <Button
                      size="sm"
                      onClick={() =>
                        navigate(`/recorded-classes/${courseId}/video/${nextVideo.id}`)
                      }
                      className="flex items-center gap-1"
                    >
                      <span>Next</span>
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>

              {/* Navigation Arrows for Previous / Next */}
              <div className="flex items-center justify-between pt-3 border-t border-slate-200 dark:border-surface-800 text-xs">
                {prevVideo ? (
                  <button
                    onClick={() =>
                      navigate(`/recorded-classes/${courseId}/video/${prevVideo.id}`)
                    }
                    className="flex items-center gap-1.5 text-slate-600 dark:text-slate-400 hover:text-brand-600 dark:hover:text-brand-400 font-medium transition-colors"
                  >
                    <ChevronLeft className="h-4 w-4" />
                    <span>Previous: {prevVideo.title.slice(0, 35)}...</span>
                  </button>
                ) : (
                  <span />
                )}

                {nextVideo ? (
                  <button
                    onClick={() =>
                      navigate(`/recorded-classes/${courseId}/video/${nextVideo.id}`)
                    }
                    className="flex items-center gap-1.5 text-slate-600 dark:text-slate-400 hover:text-brand-600 dark:hover:text-brand-400 font-medium transition-colors ml-auto"
                  >
                    <span>Next: {nextVideo.title.slice(0, 35)}...</span>
                    <ChevronRight className="h-4 w-4" />
                  </button>
                ) : (
                  <span className="text-emerald-500 font-semibold flex items-center gap-1 ml-auto">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Final Lesson Reached</span>
                  </span>
                )}
              </div>
            </Card>
          )}

          {/* Bottom Tabs: Notes, Resources, Overview */}
          <Card className="p-5 space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-200 dark:border-surface-800 pb-3">
              <button
                onClick={() => setActiveTab("NOTES")}
                className={`flex items-center gap-1.5 rounded-xl px-3.5 py-1.5 text-xs font-bold transition-colors ${
                  activeTab === "NOTES"
                    ? "bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                <FileText className="h-3.5 w-3.5" />
                <span>Lecture Notes & Summary</span>
              </button>

              <button
                onClick={() => setActiveTab("RESOURCES")}
                className={`flex items-center gap-1.5 rounded-xl px-3.5 py-1.5 text-xs font-bold transition-colors ${
                  activeTab === "RESOURCES"
                    ? "bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                <ExternalLink className="h-3.5 w-3.5" />
                <span>Resources & Code</span>
              </button>

              <button
                onClick={() => setActiveTab("CURRICULUM")}
                className={`flex items-center gap-1.5 rounded-xl px-3.5 py-1.5 text-xs font-bold transition-colors ${
                  activeTab === "CURRICULUM"
                    ? "bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                <Info className="h-3.5 w-3.5" />
                <span>Course Info</span>
              </button>
            </div>

            <div className="pt-1">
              {activeTab === "NOTES" && (
                <div className="space-y-3">
                  {activeVideo?.notes ? (
                    <div className="prose dark:prose-invert max-w-none text-xs leading-relaxed whitespace-pre-line text-slate-700 dark:text-slate-300">
                      {activeVideo.notes}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 italic">
                      {activeVideo?.description || "No specific lecture notes attached to this session. Focus on the video walkthrough and lab exercises."}
                    </p>
                  )}
                </div>
              )}

              {activeTab === "RESOURCES" && (
                <div className="space-y-3 text-xs">
                  {activeVideo?.resources_url ? (
                    <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-surface-900 border border-slate-200 dark:border-surface-800">
                      <div className="flex items-center gap-2">
                        <ExternalLink className="h-4 w-4 text-brand-500" />
                        <span className="font-semibold text-slate-900 dark:text-white">Supplementary Code Repository</span>
                      </div>
                      <a
                        href={activeVideo.resources_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-brand-600 dark:text-brand-400 hover:underline font-semibold flex items-center gap-1"
                      >
                        <span>Open Link</span>
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 italic">
                      No external supplementary repositories linked for this lesson.
                    </p>
                  )}
                </div>
              )}

              {activeTab === "CURRICULUM" && (
                <div className="space-y-3 text-xs text-slate-600 dark:text-slate-400">
                  <p>{course.description || "Comprehensive recorded masterclasses with structured sequential modules."}</p>
                  <div className="flex items-center gap-2 pt-2">
                    <Link to={`/courses/${course.id}`}>
                      <Button variant="outline" size="sm" className="flex items-center gap-1.5">
                        <BookOpen className="h-3.5 w-3.5" />
                        <span>View Curriculum Milestones & Assessments</span>
                      </Button>
                    </Link>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Right: Interactive Grouped Playlist Drawer (4 Cols) */}
        <div className="lg:col-span-4 space-y-4">
          <Card className="p-4 flex flex-col h-[700px]">
            {/* Playlist Header */}
            <div className="space-y-3 border-b border-slate-200 dark:border-surface-800 pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-bold text-slate-900 dark:text-white text-sm">
                  <Layers className="h-4 w-4 text-brand-500" />
                  <span>Course Curriculum Folders</span>
                </div>
                <span className="text-xs font-mono text-slate-400">
                  {videos.length} Sessions
                </span>
              </div>

              {/* Search playlist */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Filter lessons or folders..."
                  value={searchPlaylist}
                  onChange={(e) => setSearchPlaylist(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900 py-1.5 pl-8 pr-3 text-xs font-medium text-slate-900 dark:text-white placeholder:text-slate-400 focus:border-brand-500 focus:outline-none"
                />
              </div>
            </div>

            {/* Scrollable Grouped Playlist Tree */}
            <div className="flex-1 overflow-y-auto space-y-3 py-3 pr-1">
              {playlistGroups.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-400">No lessons matching search.</div>
              ) : (
                playlistGroups.map((group) => {
                  const isCollapsed = collapsedFolders[group.key] ?? false;

                  return (
                    <div
                      key={group.key}
                      className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-slate-50/50 dark:bg-surface-900/40 overflow-hidden"
                    >
                      {/* Folder / Group Header */}
                      <button
                        type="button"
                        onClick={() => toggleFolderCollapse(group.key)}
                        className="w-full flex items-center justify-between p-2.5 px-3 text-left hover:bg-slate-100/80 dark:hover:bg-surface-800/80 transition-colors border-b border-slate-100 dark:border-surface-800/60"
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          {isCollapsed ? (
                            <Folder className="h-4 w-4 text-amber-500 shrink-0" />
                          ) : (
                            <FolderOpen className="h-4 w-4 text-amber-500 shrink-0" />
                          )}
                          <span className="text-xs font-bold text-slate-900 dark:text-white truncate">
                            {group.title}
                          </span>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <span className="text-[10px] font-mono text-slate-400">
                            {group.completedCount}/{group.videos.length}
                          </span>
                          {isCollapsed ? (
                            <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
                          ) : (
                            <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
                          )}
                        </div>
                      </button>

                      {/* Sub-Videos Under This Folder */}
                      {!isCollapsed && (
                        <div className="p-1.5 space-y-1">
                          {group.videos.map((v, subIdx) => {
                            const isSelected = activeVideo?.id === v.id;

                            return (
                              <button
                                key={v.id}
                                onClick={() => navigate(`/recorded-classes/${courseId}/video/${v.id}`)}
                                className={`w-full text-left rounded-xl p-2.5 transition-all flex items-start gap-2.5 border ${
                                  isSelected
                                    ? "bg-brand-500/10 border-brand-500/40 shadow-sm"
                                    : "bg-white dark:bg-surface-900 border-transparent hover:border-slate-200 dark:hover:border-surface-700"
                                }`}
                              >
                                {/* Index or lock badge */}
                                <div
                                  className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-bold ${
                                    isSelected
                                      ? "bg-brand-600 text-white shadow-md shadow-brand-500/30"
                                      : v.is_completed
                                      ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                                      : v.is_locked
                                      ? "bg-slate-200 dark:bg-surface-800 text-slate-400"
                                      : "bg-slate-100 dark:bg-surface-800 text-slate-600 dark:text-slate-300"
                                  }`}
                                >
                                  {v.is_completed ? (
                                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                                  ) : v.is_locked ? (
                                    <Lock className="h-3 w-3 text-slate-400" />
                                  ) : (
                                    <span className="text-[11px] font-mono">
                                      {String(subIdx + 1).padStart(2, "0")}
                                    </span>
                                  )}
                                </div>

                                {/* Content Details */}
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center justify-between gap-1 mb-0.5">
                                    <div className="flex items-center gap-1.5">
                                      {v.is_preview ? (
                                        <span className="text-[9px] font-extrabold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                                          Free Preview
                                        </span>
                                      ) : (
                                        <span className="text-[9px] font-extrabold uppercase tracking-wider text-slate-400">
                                          Lec-{subIdx + 1}
                                        </span>
                                      )}
                                    </div>
                                    {v.duration_formatted && (
                                      <span className="text-[10px] text-slate-400 font-mono">
                                        {v.duration_formatted}
                                      </span>
                                    )}
                                  </div>

                                  <div
                                    className={`text-xs font-semibold line-clamp-1 ${
                                      isSelected
                                        ? "text-brand-600 dark:text-brand-400"
                                        : "text-slate-800 dark:text-slate-200"
                                    }`}
                                  >
                                    {v.title}
                                  </div>

                                  {isSelected && (
                                    <div className="mt-1 flex items-center gap-1 text-[10px] font-bold text-brand-500">
                                      <Volume2 className="h-3 w-3 animate-pulse" />
                                      <span>Now Playing</span>
                                    </div>
                                  )}
                                </div>
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
