import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Users,
  Award,
  Building2,
  BookOpen,
  FolderKanban,
  GraduationCap,
  ArrowRight,
  RefreshCw,
  Percent,
} from "lucide-react";
import { tpoApi } from "../../api/tpoApi";
import { useAuthStore } from "../../store/authStore";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { UserAvatar } from "../../components/ui/UserAvatar";

export const TPODashboardPage: React.FC = () => {
  const { user } = useAuthStore();

  const {
    data: summary,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ["tpo-college-summary", user?.id],
    queryFn: tpoApi.getCollegeSummary,
    staleTime: 60 * 1000,
  });

  if (isLoading) {
    return <LoadingState message="Loading college telemetry & performance data..." />;
  }

  if (isError || !summary) {
    return (
      <ErrorState
        title="Failed to Load College Dashboard"
        message={
          (error as any)?.response?.data?.error?.message ||
          "Could not retrieve aggregated performance metrics for your assigned college."
        }
        onRetry={() => refetch()}
      />
    );
  }

  const { college } = summary;
  const lastUpdated = dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString() : "";

  return (
    <div className="space-y-6 pb-12">
      {/* -------------------------------------------------------------------------- */}
      {/* 1. INSTITUTIONAL HEADER & IDENTITY BANNER */}
      {/* -------------------------------------------------------------------------- */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-6 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20 shadow-inner">
            <Building2 className="h-7 w-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
                Institutional TPO Dashboard
              </span>
              {college?.code && (
                <Badge variant="brand" size="sm">
                  {college.code}
                </Badge>
              )}
            </div>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              {college?.name}
            </h1>
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
              {college?.city ? `${college.city}, ${college.state}` : "Institutional Campus"}{" "}
              • Real-time academic tracking
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
          <Link
            to="/tpo/students"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-brand-600 hover:bg-brand-500 text-white shadow-sm transition-colors"
          >
            <span>View Roster</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      {/* -------------------------------------------------------------------------- */}
      {/* 2. KEY PERFORMANCE INDICATORS (KPI STATS) */}
      {/* -------------------------------------------------------------------------- */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Students */}
        <Card className="p-5 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Enrolled Students
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400">
              <Users className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              {summary.total_students}
            </span>
            <span className="text-xs text-emerald-600 dark:text-emerald-400 font-semibold">
              {summary.active_students} active
            </span>
          </div>
          <div className="mt-2 text-xs text-slate-400">
            {summary.inactive_students} suspended / inactive
          </div>
        </Card>

        {/* Attendance Average */}
        <Card className="p-5 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Avg Attendance
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <Percent className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              {summary.average_attendance_percentage}%
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">institutional avg</span>
          </div>
          <div className="mt-2 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
            {summary.students_above_75_attendance} of {summary.total_students} students ≥ 75%
          </div>
        </Card>

        {/* Coding & Lab Submissions */}
        <Card className="p-5 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Lab Submissions
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-500/10 text-violet-600 dark:text-violet-400">
              <FolderKanban className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              {summary.total_submissions}
            </span>
            <span className="text-xs text-violet-600 dark:text-violet-400 font-semibold">
              {summary.accepted_submissions} accepted
            </span>
          </div>
          <div className="mt-2 text-xs text-slate-400">
            {summary.total_submissions > 0
              ? `${Math.round(
                  (summary.accepted_submissions / summary.total_submissions) * 100
                )}% pass rate`
              : "No lab submissions yet"}
          </div>
        </Card>

        {/* Top Points Record */}
        <Card className="p-5 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Top Student Points
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400">
              <Award className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              {summary.top_performers[0]?.total_points.toFixed(0) || "0"}
            </span>
            <span className="text-xs text-amber-600 dark:text-amber-400 font-semibold">
              pts high score
            </span>
          </div>
          <div className="mt-2 text-xs text-slate-400 truncate">
            {summary.top_performers[0]?.full_name || "No scored students"}
          </div>
        </Card>
      </div>

      {/* -------------------------------------------------------------------------- */}
      {/* 3. TOP PERFORMERS LEADERBOARD & ACADEMIC TRACKS */}
      {/* -------------------------------------------------------------------------- */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Performers Table */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Award className="h-5 w-5 text-amber-500" />
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Top Performing Students
              </h2>
            </div>
            <Link
              to="/tpo/students"
              className="text-xs font-semibold text-brand-600 dark:text-brand-400 hover:underline flex items-center gap-1"
            >
              Full Roster <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          {summary.top_performers.length === 0 ? (
            <Card className="p-8 text-center text-slate-400">
              <p className="text-sm">No students currently enrolled for this college.</p>
            </Card>
          ) : (
            <div className="overflow-hidden rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
                  <thead className="border-b border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-950 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    <tr>
                      <th className="px-4 py-3">Rank</th>
                      <th className="px-4 py-3">Student</th>
                      <th className="px-4 py-3">Branch</th>
                      <th className="px-4 py-3">Attendance</th>
                      <th className="px-4 py-3 text-right">Points</th>
                      <th className="px-4 py-3 text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-surface-800">
                    {summary.top_performers.map((performer, idx) => (
                      <tr
                        key={performer.id}
                        className="hover:bg-slate-50/80 dark:hover:bg-surface-800/40 transition-colors"
                      >
                        <td className="px-4 py-3.5">
                          <span
                            className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                              idx === 0
                                ? "bg-amber-500 text-white shadow-sm shadow-amber-500/30"
                                : idx === 1
                                ? "bg-slate-300 dark:bg-slate-700 text-slate-900 dark:text-white"
                                : idx === 2
                                ? "bg-amber-700/80 text-white"
                                : "bg-slate-100 dark:bg-surface-800 text-slate-500"
                            }`}
                          >
                            {idx + 1}
                          </span>
                        </td>
                        <td className="px-4 py-3.5">
                          <div className="flex items-center gap-3">
                            <UserAvatar
                              src={performer.avatar_url}
                              name={performer.full_name}
                              initials={performer.full_name.slice(0, 2).toUpperCase()}
                              size="sm"
                            />
                            <div>
                              <div className="font-semibold text-slate-900 dark:text-white">
                                {performer.full_name}
                              </div>
                              <div className="text-[11px] text-slate-400 font-mono">
                                {performer.student_id_number}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3.5 text-xs text-slate-500 dark:text-slate-400">
                          {performer.branch}
                        </td>
                        <td className="px-4 py-3.5">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                              performer.attendance_percentage >= 75
                                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                                : "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                            }`}
                          >
                            {performer.attendance_percentage}%
                          </span>
                        </td>
                        <td className="px-4 py-3.5 text-right font-bold text-slate-900 dark:text-white">
                          {performer.total_points.toFixed(0)}
                        </td>
                        <td className="px-4 py-3.5 text-center">
                          <Link
                            to={`/tpo/students/${performer.id}`}
                            className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold bg-brand-500/10 text-brand-600 dark:text-brand-400 hover:bg-brand-500/20 transition-colors"
                          >
                            View
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Distribution Breakdowns */}
        <div className="space-y-6">
          {/* Technology Tracks */}
          <Card className="p-5">
            <div className="flex items-center gap-2 mb-4">
              <BookOpen className="h-4 w-4 text-brand-500" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Track / Course Distribution
              </h3>
            </div>
            <div className="space-y-3">
              {summary.technology_distribution.length === 0 ? (
                <p className="text-xs text-slate-400">No tracks opted.</p>
              ) : (
                summary.technology_distribution.map((tech) => {
                  const pct =
                    summary.total_students > 0
                      ? Math.round((tech.count / summary.total_students) * 100)
                      : 0;
                  return (
                    <div key={tech.name} className="space-y-1">
                      <div className="flex justify-between text-xs font-medium">
                        <span className="text-slate-700 dark:text-slate-300 truncate max-w-[180px]">
                          {tech.name}
                        </span>
                        <span className="text-slate-500 dark:text-slate-400">
                          {tech.count} ({pct}%)
                        </span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-slate-100 dark:bg-surface-800 overflow-hidden">
                        <div
                          className="h-full bg-brand-500 rounded-full transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </Card>

          {/* Department / Branch Distribution */}
          <Card className="p-5">
            <div className="flex items-center gap-2 mb-4">
              <Building2 className="h-4 w-4 text-brand-500" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Branch Breakdown
              </h3>
            </div>
            <div className="space-y-2.5">
              {summary.branch_distribution.length === 0 ? (
                <p className="text-xs text-slate-400">No branch data available.</p>
              ) : (
                summary.branch_distribution.map((br) => (
                  <div
                    key={br.name}
                    className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-surface-900/60 border border-slate-100 dark:border-surface-800/60 text-xs"
                  >
                    <span className="font-medium text-slate-700 dark:text-slate-300 truncate">
                      {br.name}
                    </span>
                    <Badge variant="neutral" size="sm">
                      {br.count} students
                    </Badge>
                  </div>
                ))
              )}
            </div>
          </Card>

          {/* Batch / Cohort Distribution */}
          <Card className="p-5">
            <div className="flex items-center gap-2 mb-4">
              <FolderKanban className="h-4 w-4 text-brand-500" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Batches & Cohorts
              </h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {summary.batch_distribution.length === 0 ? (
                <p className="text-xs text-slate-400">No batches registered.</p>
              ) : (
                summary.batch_distribution.map((b) => (
                  <div
                    key={b.batch_code}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 text-xs"
                  >
                    <span className="font-semibold text-slate-900 dark:text-white font-mono">
                      {b.batch_code}
                    </span>
                    <span className="text-[10px] font-bold text-brand-600 dark:text-brand-400 px-1.5 py-0.5 rounded bg-brand-500/10">
                      {b.count}
                    </span>
                  </div>
                ))
              )}
            </div>
          </Card>

          {/* Graduation Year Breakdown */}
          <Card className="p-5">
            <div className="flex items-center gap-2 mb-4">
              <GraduationCap className="h-4 w-4 text-brand-500" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Graduation Year Breakdown
              </h3>
            </div>
            <div className="grid grid-cols-2 gap-2.5">
              {!summary.graduation_year_distribution || summary.graduation_year_distribution.length === 0 ? (
                <p className="text-xs text-slate-400 col-span-2">No graduation year records.</p>
              ) : (
                summary.graduation_year_distribution.map((gy) => {
                  const pct =
                    summary.total_students > 0
                      ? Math.round((gy.count / summary.total_students) * 100)
                      : 0;
                  return (
                    <div
                      key={gy.graduation_year}
                      className="p-3 rounded-xl bg-slate-50 dark:bg-surface-900/60 border border-slate-100 dark:border-surface-800/60 flex flex-col justify-between"
                    >
                      <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
                        Class of {gy.graduation_year}
                      </div>
                      <div className="mt-1.5 flex items-baseline justify-between">
                        <span className="text-base font-bold text-slate-900 dark:text-white">
                          {gy.count}
                        </span>
                        <span className="text-[10px] font-semibold text-brand-600 dark:text-brand-400 bg-brand-500/10 px-1.5 py-0.5 rounded">
                          {pct}%
                        </span>
                      </div>
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
