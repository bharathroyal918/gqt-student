import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  BookOpen,
  CheckCircle2,
  Clock,
  Search,
  Filter,
  RefreshCw,
  ArrowRight,
  Layers,
  GraduationCap,
  Sparkles,
} from "lucide-react";
import { tpoApi } from "../../api/tpoApi";
import { useAuthStore } from "../../store/authStore";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";

export const TPOLearningProgressPage: React.FC = () => {
  const { user } = useAuthStore();
  const [selectedCourseId, setSelectedCourseId] = useState<string>("");
  const [search, setSearch] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ["tpo-learning-progress", user?.id, selectedCourseId],
    queryFn: () => tpoApi.getLearningProgress(selectedCourseId || undefined),
    staleTime: 60 * 1000,
  });

  if (isLoading) {
    return <LoadingState message="Calculating curriculum & module progression matrix..." />;
  }

  if (isError || !data) {
    return (
      <ErrorState
        title="Failed to Load Learning Progress"
        message={
          (error as any)?.response?.data?.error?.message ||
          "Could not retrieve curriculum progression records for your assigned institution."
        }
        onRetry={() => refetch()}
      />
    );
  }

  const lastUpdated = dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString() : "";

  // Filter student progress list
  const filteredStudents = data.student_progress.filter((s) => {
    const matchesSearch =
      search === "" ||
      s.full_name.toLowerCase().includes(search.toLowerCase()) ||
      s.student_id_number.toLowerCase().includes(search.toLowerCase()) ||
      (s.course_opted && s.course_opted.toLowerCase().includes(search.toLowerCase()));

    const matchesStatus =
      statusFilter === "ALL" || s.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const completedStudentsCount = data.student_progress.filter(
    (s) => s.status === "COMPLETED"
  ).length;
  const onTrackStudentsCount = data.student_progress.filter(
    (s) => s.status === "ON_TRACK"
  ).length;
  const notStartedStudentsCount = data.student_progress.filter(
    (s) => s.status === "NOT_STARTED"
  ).length;

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-6 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 shadow-inner">
            <BookOpen className="h-7 w-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
                Curriculum Analytics
              </span>
              <Badge variant="brand" size="sm">
                Live Matrix
              </Badge>
            </div>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Student Learning Progress
            </h1>
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
              Module completion rates, track progression, and syllabus milestones
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 self-start sm:self-center">
          <div className="text-right hidden md:block">
            <span className="text-[10px] text-slate-400 block font-medium">Last Synced</span>
            <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              {lastUpdated || "Live"}
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Enrolled Students
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400">
              <GraduationCap className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            {data.total_students}
          </div>
          <div className="mt-2 text-xs text-slate-400">
            Across {data.total_courses} published courses
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Completed Curriculum
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-bold tracking-tight text-emerald-600 dark:text-emerald-400">
            {completedStudentsCount}
          </div>
          <div className="mt-2 text-xs text-slate-400">
            {data.total_students > 0
              ? `${Math.round((completedStudentsCount / data.total_students) * 100)}% 100% completion`
              : "No students"}
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Actively On Track
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400">
              <Clock className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-bold tracking-tight text-amber-600 dark:text-amber-400">
            {onTrackStudentsCount}
          </div>
          <div className="mt-2 text-xs text-slate-400">
            Partial modules or streak active
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Not Started
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/10 text-rose-600 dark:text-rose-400">
              <Layers className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-bold tracking-tight text-rose-600 dark:text-rose-400">
            {notStartedStudentsCount}
          </div>
          <div className="mt-2 text-xs text-slate-400">
            0 modules completed
          </div>
        </Card>
      </div>

      {/* Courses & Module Completion Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Course Progression */}
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <Layers className="h-4 w-4 text-indigo-500" />
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Course Progression Overview
            </h3>
          </div>
          {data.course_progression.length === 0 ? (
            <p className="text-xs text-slate-400">No course enrollments logged.</p>
          ) : (
            <div className="space-y-4">
              {data.course_progression.map((cp) => (
                <div key={cp.course_id} className="p-3.5 rounded-xl border border-slate-100 dark:border-surface-800 bg-slate-50/50 dark:bg-surface-900/40">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-bold text-sm text-slate-900 dark:text-white">
                      {cp.course_title}
                    </span>
                    <Badge variant="neutral" size="sm">
                      {cp.enrolled_count} Enrolled
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs text-slate-500 dark:text-slate-400">
                    <div>
                      Completed:{" "}
                      <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                        {cp.completed_count}
                      </span>
                    </div>
                    <div>
                      In Progress:{" "}
                      <span className="font-semibold text-indigo-600 dark:text-indigo-400">
                        {cp.in_progress_count}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Module Completion Counts */}
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="h-4 w-4 text-indigo-500" />
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Module Completion Milestone Breakdown
            </h3>
          </div>
          {data.module_completion.length === 0 ? (
            <p className="text-xs text-slate-400">No active curriculum modules found.</p>
          ) : (
            <div className="space-y-3 max-h-[280px] overflow-y-auto pr-1">
              {data.module_completion.map((mod) => (
                <div
                  key={mod.module_id}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-surface-900/60 border border-slate-100 dark:border-surface-800/60 text-xs"
                >
                  <div className="min-w-0 flex-1 mr-2">
                    <div className="font-semibold text-slate-800 dark:text-slate-200 truncate">
                      {mod.module_title}
                    </div>
                    <div className="text-[10px] text-slate-400 truncate">
                      {mod.course_title}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                      {mod.completed_count} done
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Student Progress Detail Table */}
      <Card className="p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Student Curriculum Progression
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Verified completion metrics for each student in your institution
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search students..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-48 sm:w-64 pl-9 pr-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            {/* Course Filter */}
            {data.course_progression.length > 0 && (
              <div className="flex items-center gap-1.5">
                <BookOpen className="h-3.5 w-3.5 text-slate-400" />
                <select
                  value={selectedCourseId}
                  onChange={(e) => setSelectedCourseId(e.target.value)}
                  className="text-xs rounded-xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 py-1.5 px-2.5 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="">All Courses</option>
                  {data.course_progression.map((c) => (
                    <option key={c.course_id} value={c.course_id}>
                      {c.course_title}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Status Filter */}
            <div className="flex items-center gap-1.5">
              <Filter className="h-3.5 w-3.5 text-slate-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="text-xs rounded-xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 py-1.5 px-2.5 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="ALL">All Statuses</option>
                <option value="COMPLETED">Completed</option>
                <option value="ON_TRACK">On Track</option>
                <option value="NOT_STARTED">Not Started</option>
              </select>
            </div>
          </div>
        </div>

        {filteredStudents.length === 0 ? (
          <div className="p-8 text-center text-slate-400">
            <p className="text-sm">No student progress records match the selected filters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="border-b border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-950 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3">Student</th>
                  <th className="px-4 py-3">Batch & Branch</th>
                  <th className="px-4 py-3">Track Opted</th>
                  <th className="px-4 py-3">Completed Modules</th>
                  <th className="px-4 py-3">Progress</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-surface-800">
                {filteredStudents.map((s) => (
                  <tr
                    key={s.id}
                    className="hover:bg-slate-50/80 dark:hover:bg-surface-800/40 transition-colors"
                  >
                    <td className="px-4 py-3.5">
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {s.full_name}
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        {s.student_id_number}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 text-xs text-slate-500 dark:text-slate-400">
                      <div>{s.batch_code}</div>
                      <div className="text-[11px] text-slate-400">{s.branch}</div>
                    </td>
                    <td className="px-4 py-3.5 text-xs font-medium text-slate-700 dark:text-slate-300">
                      {s.course_opted || "General"}
                    </td>
                    <td className="px-4 py-3.5 text-xs font-semibold text-slate-900 dark:text-white">
                      {s.completed_modules} / {s.total_modules}
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="w-32 space-y-1">
                        <div className="flex justify-between text-[11px] font-medium">
                          <span>{s.progress_percentage}%</span>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-slate-100 dark:bg-surface-800 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              s.status === "COMPLETED"
                                ? "bg-emerald-500"
                                : s.status === "ON_TRACK"
                                ? "bg-indigo-500"
                                : "bg-slate-400"
                            }`}
                            style={{ width: `${s.progress_percentage}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                          s.status === "COMPLETED"
                            ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                            : s.status === "ON_TRACK"
                            ? "bg-indigo-500/10 text-indigo-600 dark:text-indigo-400"
                            : "bg-slate-500/10 text-slate-600 dark:text-slate-400"
                        }`}
                      >
                        {s.status === "COMPLETED"
                          ? "Completed"
                          : s.status === "ON_TRACK"
                          ? "On Track"
                          : "Not Started"}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-center">
                      <Link
                        to={`/tpo/students/${s.id}`}
                        className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold bg-brand-500/10 text-brand-600 dark:text-brand-400 hover:bg-brand-500/20 transition-colors"
                      >
                        Detail <ArrowRight className="h-3 w-3 ml-1" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};
