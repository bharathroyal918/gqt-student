import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Video,
  PlayCircle,
  Lock,
  Unlock,
  CheckCircle2,
  Sparkles,
  Search,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import { recordedClassesApi } from "../../api/recordedClassesApi";
import { StudentRecordedCourseItem } from "../../types/recordedClasses";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";

export const StudentRecordedClassesPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterTab, setFilterTab] = useState<"ALL" | "ENROLLED" | "FREE_PREVIEW">("ALL");

  const {
    data: courses,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery<StudentRecordedCourseItem[]>({
    queryKey: ["student", "recorded-classes"],
    queryFn: recordedClassesApi.getStudentCourses,
    staleTime: 1000 * 60,
  });

  const filteredCourses = React.useMemo(() => {
    if (!courses) return [];
    return courses.filter((course) => {
      const matchesSearch =
        course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        course.description.toLowerCase().includes(searchQuery.toLowerCase());

      if (!matchesSearch) return false;

      if (filterTab === "ENROLLED") return course.is_enrolled;
      if (filterTab === "FREE_PREVIEW") return !course.is_enrolled;
      return true;
    });
  }, [courses, searchQuery, filterTab]);

  if (isLoading) {
    return (
      <div className="flex h-96 flex-col items-center justify-center space-y-4">
        <LoadingState message="Loading recorded classes and curriculum sessions..." />
      </div>
    );
  }

  if (isError || !courses) {
    return (
      <ErrorState
        title="Unable to load recorded classes"
        message={error instanceof Error ? error.message : "Failed to load recorded classes from server."}
        onRetry={() => refetch()}
      />
    );
  }

  const totalCourses = courses.length;
  const enrolledCount = courses.filter((c) => c.is_enrolled).length;
  const totalVideosAvailable = courses.reduce((acc, c) => acc + c.total_videos, 0);

  return (
    <div className="space-y-6">
      {/* Hero Banner with Aesthetic Gradient & Dynamic Access Info */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-900 via-slate-900 to-surface-950 p-6 sm:p-8 text-white shadow-xl border border-indigo-500/20">
        <div className="absolute -right-16 -top-16 h-64 w-64 rounded-full bg-brand-500/10 blur-3xl" />
        <div className="absolute -bottom-16 right-32 h-64 w-64 rounded-full bg-indigo-500/10 blur-3xl" />

        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full bg-indigo-500/20 px-3 py-1 text-xs font-semibold text-indigo-300 border border-indigo-500/30">
            <Sparkles className="h-3.5 w-3.5 text-amber-400" />
            <span>Interactive Video Lecture Library</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Recorded Classes & Video Lectures
          </h1>

          <p className="text-sm text-slate-300 leading-relaxed">
            Access recorded lessons from expert instructors. All registered students enjoy free preview access to the{" "}
            <span className="font-semibold text-emerald-400">first 5 classes</span> of every course module. Enrolled students receive full access to the complete video curriculum.
          </p>

          {/* Highlights ribbon */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2">
            <div className="rounded-2xl bg-white/5 p-3 backdrop-blur-sm border border-white/10">
              <div className="text-xs text-slate-400">Available Tracks</div>
              <div className="text-lg font-bold text-white mt-0.5">{totalCourses} Courses</div>
            </div>
            <div className="rounded-2xl bg-white/5 p-3 backdrop-blur-sm border border-white/10">
              <div className="text-xs text-slate-400">Total Video Lessons</div>
              <div className="text-lg font-bold text-indigo-400 mt-0.5">{totalVideosAvailable} Lessons</div>
            </div>
            <div className="rounded-2xl bg-white/5 p-3 backdrop-blur-sm border border-white/10 col-span-2 sm:col-span-1">
              <div className="text-xs text-slate-400">Your Full Access</div>
              <div className="text-lg font-bold text-emerald-400 mt-0.5">{enrolledCount} Enrolled</div>
            </div>
          </div>
        </div>
      </div>

      {/* Control Bar: Search & Filter Tabs */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <div className="relative flex-1 sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search course tracks (e.g. Java, Python)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 py-2 pl-9 pr-4 text-xs font-medium text-slate-900 dark:text-white placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-1.5 shrink-0"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin text-brand-500" : ""}`} />
            <span className="hidden sm:inline">Refresh</span>
          </Button>
        </div>

        {/* Filter Pills */}
        <div className="flex rounded-xl bg-slate-100 dark:bg-surface-900 p-1 self-start sm:self-auto border border-slate-200 dark:border-surface-800">
          <button
            onClick={() => setFilterTab("ALL")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
              filterTab === "ALL"
                ? "bg-white dark:bg-surface-800 text-slate-900 dark:text-white shadow-sm"
                : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            All Tracks ({courses.length})
          </button>
          <button
            onClick={() => setFilterTab("ENROLLED")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
              filterTab === "ENROLLED"
                ? "bg-white dark:bg-surface-800 text-emerald-600 dark:text-emerald-400 shadow-sm"
                : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            Full Access ({enrolledCount})
          </button>
          <button
            onClick={() => setFilterTab("FREE_PREVIEW")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
              filterTab === "FREE_PREVIEW"
                ? "bg-white dark:bg-surface-800 text-indigo-600 dark:text-indigo-400 shadow-sm"
                : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            Free Preview ({courses.length - enrolledCount})
          </button>
        </div>
      </div>

      {/* Courses Grid */}
      {filteredCourses.length === 0 ? (
        <Card className="p-12 text-center">
          <Video className="h-12 w-12 text-slate-400 mx-auto mb-3 opacity-60" />
          <h3 className="text-base font-semibold text-slate-900 dark:text-white">
            No Recorded Courses Matching Filter
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto mt-1">
            Try adjusting your search keyword or toggle to "All Tracks" to explore the full library.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredCourses.map((course) => {
            return (
              <Card
                key={course.id}
                className="group relative flex flex-col justify-between overflow-hidden border border-slate-200 dark:border-surface-800/80 hover:border-brand-500/50 hover:shadow-lg transition-all duration-200"
              >
                {/* Header Banner / Card Top */}
                <div className="p-5">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-500 border border-indigo-500/20 group-hover:scale-105 transition-transform">
                      <Video className="h-6 w-6" />
                    </div>

                    {course.is_enrolled ? (
                      <Badge variant="emerald" size="sm" className="flex items-center gap-1 shadow-sm">
                        <ShieldCheck className="h-3 w-3" />
                        <span>Full Access</span>
                      </Badge>
                    ) : (
                      <Badge variant="indigo" size="sm" className="flex items-center gap-1">
                        <Unlock className="h-3 w-3" />
                        <span>5 Free Lessons</span>
                      </Badge>
                    )}
                  </div>

                  <h3 className="text-lg font-bold text-slate-900 dark:text-white group-hover:text-brand-600 dark:group-hover:text-brand-400 transition-colors line-clamp-1">
                    {course.title}
                  </h3>

                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 line-clamp-2 leading-relaxed">
                    {course.description || "Comprehensive recorded masterclasses with structured lectures, YouTube streams, and coding walkthroughs."}
                  </p>

                  {/* Course Video Statistics */}
                  <div className="mt-4 grid grid-cols-2 gap-2 rounded-xl bg-slate-50 dark:bg-surface-900/60 p-3 text-xs border border-slate-100 dark:border-surface-800/60">
                    <div>
                      <div className="text-[11px] text-slate-400">Total Lessons</div>
                      <div className="font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                        {course.total_videos} {course.total_videos === 1 ? "Video" : "Videos"}
                      </div>
                    </div>
                    <div>
                      <div className="text-[11px] text-slate-400">Access Status</div>
                      <div className="font-bold mt-0.5 flex items-center gap-1">
                        {course.is_enrolled ? (
                          <span className="text-emerald-600 dark:text-emerald-400">Unlocked 100%</span>
                        ) : (
                          <span className="text-amber-500 dark:text-amber-400">Preview (1–5)</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Progress Bar if enrolled */}
                  {course.is_enrolled && course.total_videos > 0 && (
                    <div className="mt-4 space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">Watch Progress</span>
                        <span className="font-bold text-slate-800 dark:text-slate-200">
                          {course.completed_videos}/{course.total_videos} watched
                        </span>
                      </div>
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-surface-800">
                        <div
                          className="h-full bg-brand-500 rounded-full transition-all duration-500"
                          style={{ width: `${course.progress_percentage}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Footer Action */}
                <div className="border-t border-slate-200 dark:border-surface-800/80 bg-slate-50/50 dark:bg-surface-900/40 p-4 flex items-center justify-between">
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    {course.is_enrolled ? (
                      <>
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                        <span>Curriculum Approved</span>
                      </>
                    ) : (
                      <>
                        <Lock className="h-3.5 w-3.5 text-slate-400" />
                        <span>Lessons 6+ Locked</span>
                      </>
                    )}
                  </span>

                  <Link to={`/recorded-classes/${course.id}`}>
                    <Button size="sm" className="flex items-center gap-1.5 font-semibold">
                      <PlayCircle className="h-4 w-4" />
                      <span>{course.is_enrolled ? "Watch Classes" : "Preview Classes"}</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Button>
                  </Link>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};
