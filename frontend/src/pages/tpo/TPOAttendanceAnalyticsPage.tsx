import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  CalendarCheck,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Percent,
  Users,
  Filter,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";
import { tpoApi } from "../../api/tpoApi";
import { useAuthStore } from "../../store/authStore";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";

export const TPOAttendanceAnalyticsPage: React.FC = () => {
  const { user } = useAuthStore();
  const [batchCode, setBatchCode] = useState<string>("ALL");

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ["tpo-attendance-analytics", user?.id, batchCode],
    queryFn: () => tpoApi.getAttendanceAnalytics(batchCode),
    staleTime: 60 * 1000,
  });

  if (isLoading) {
    return <LoadingState message="Computing attendance compliance and distribution bands..." />;
  }

  if (isError || !data) {
    return (
      <ErrorState
        title="Failed to Load Attendance Analytics"
        message={
          (error as any)?.response?.data?.error?.message ||
          "Could not retrieve institutional attendance distribution records."
        }
        onRetry={() => refetch()}
      />
    );
  }

  const lastUpdated = dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString() : "";

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-6 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 shadow-inner">
            <CalendarCheck className="h-7 w-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                Institutional Compliance
              </span>
              <Badge variant="brand" size="sm">
                75% Threshold Policy
              </Badge>
            </div>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Attendance & Eligibility Analytics
            </h1>
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
              Distribution bands, batch compliance summaries, and placement eligibility tracking
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

          <div className="flex items-center gap-1.5">
            <Filter className="h-3.5 w-3.5 text-slate-400" />
            <select
              value={batchCode}
              onChange={(e) => setBatchCode(e.target.value)}
              className="text-xs rounded-xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 py-1.5 px-2.5 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="ALL">All Batches</option>
              {(data?.batch_breakdown || []).map((b) => (
                <option key={b.batch_code} value={b.batch_code}>
                  {b.batch_code}
                </option>
              ))}
            </select>
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
              College Average
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <Percent className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            {data.college_average_attendance}%
          </div>
          <div className="mt-2 text-xs text-slate-400">
            Across {data.total_students} students evaluated
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Excellent (≥85%)
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <ShieldCheck className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-emerald-600 dark:text-emerald-400">
              {data.distribution_bands.excellent_gte_85.count}
            </span>
            <span className="text-xs text-slate-400">
              ({data.distribution_bands.excellent_gte_85.percentage}%)
            </span>
          </div>
          <div className="mt-2 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
            Full eligibility for placement drives
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Satisfactory (75-84%)
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400">
              <CheckCircle2 className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-blue-600 dark:text-blue-400">
              {data.distribution_bands.satisfactory_75_to_84.count}
            </span>
            <span className="text-xs text-slate-400">
              ({data.distribution_bands.satisfactory_75_to_84.percentage}%)
            </span>
          </div>
          <div className="mt-2 text-xs text-slate-400">
            Meets 75% institutional policy
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Critical (Below 75%)
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/10 text-rose-600 dark:text-rose-400">
              <AlertTriangle className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-rose-600 dark:text-rose-400">
              {data.distribution_bands.critical_below_75.count}
            </span>
            <span className="text-xs text-slate-400">
              ({data.distribution_bands.critical_below_75.percentage}%)
            </span>
          </div>
          <div className="mt-2 text-xs text-rose-600 dark:text-rose-400 font-medium">
            Requires attendance intervention
          </div>
        </Card>
      </div>

      {/* Distribution Bands & Batch Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Visual Distribution */}
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <Percent className="h-4 w-4 text-emerald-500" />
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Institutional Compliance Bands
            </h3>
          </div>

          <div className="space-y-4">
            {/* Band 1 */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-emerald-700 dark:text-emerald-300">
                  Tier 1: Excellent (≥ 85%)
                </span>
                <span className="text-slate-500 dark:text-slate-400">
                  {data.distribution_bands.excellent_gte_85.count} students ({data.distribution_bands.excellent_gte_85.percentage}%)
                </span>
              </div>
              <div className="h-2.5 w-full rounded-full bg-slate-100 dark:bg-surface-800 overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                  style={{ width: `${data.distribution_bands.excellent_gte_85.percentage}%` }}
                />
              </div>
            </div>

            {/* Band 2 */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-blue-700 dark:text-blue-300">
                  Tier 2: Satisfactory (75% - 84%)
                </span>
                <span className="text-slate-500 dark:text-slate-400">
                  {data.distribution_bands.satisfactory_75_to_84.count} students ({data.distribution_bands.satisfactory_75_to_84.percentage}%)
                </span>
              </div>
              <div className="h-2.5 w-full rounded-full bg-slate-100 dark:bg-surface-800 overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full transition-all duration-500"
                  style={{ width: `${data.distribution_bands.satisfactory_75_to_84.percentage}%` }}
                />
              </div>
            </div>

            {/* Band 3 */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-rose-700 dark:text-rose-300">
                  Tier 3: Attendance Deficit (&lt; 75%)
                </span>
                <span className="text-slate-500 dark:text-slate-400">
                  {data.distribution_bands.critical_below_75.count} students ({data.distribution_bands.critical_below_75.percentage}%)
                </span>
              </div>
              <div className="h-2.5 w-full rounded-full bg-slate-100 dark:bg-surface-800 overflow-hidden">
                <div
                  className="h-full bg-rose-500 rounded-full transition-all duration-500"
                  style={{ width: `${data.distribution_bands.critical_below_75.percentage}%` }}
                />
              </div>
            </div>
          </div>
        </Card>

        {/* Batch Breakdown */}
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <Users className="h-4 w-4 text-emerald-500" />
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Batch-wise Average Attendance
            </h3>
          </div>
          {(!data.batch_breakdown || data.batch_breakdown.length === 0) ? (
            <p className="text-xs text-slate-400">No batch records found.</p>
          ) : (
            <div className="space-y-2.5">
              {data.batch_breakdown.map((b) => (
                <div
                  key={b.batch_code}
                  className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-surface-900/60 border border-slate-100 dark:border-surface-800/60 text-xs"
                >
                  <div>
                    <span className="font-bold text-slate-900 dark:text-white font-mono">
                      {b.batch_code}
                    </span>
                    <span className="text-[11px] text-slate-400 block mt-0.5">
                      {b.student_count} registered students
                    </span>
                  </div>
                  <div className="text-right">
                    <span
                      className={`text-sm font-bold ${
                        b.average_attendance >= 75
                          ? "text-emerald-600 dark:text-emerald-400"
                          : "text-rose-600 dark:text-rose-400"
                      }`}
                    >
                      {b.average_attendance}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Critical Students Table (<75%) */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-rose-500" />
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Students Below Attendance Policy Threshold (&lt;75%)
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Students requiring remediation before placement drive registration
              </p>
            </div>
          </div>
          <Badge variant="warning" size="sm">
            {(data.critical_students || []).length} flagged
          </Badge>
        </div>

        {(!data.critical_students || data.critical_students.length === 0) ? (
          <div className="p-8 text-center text-slate-400 bg-emerald-50/50 dark:bg-emerald-950/20 rounded-2xl border border-emerald-500/20">
            <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-900 dark:text-white">
              All students meet or exceed the 75% attendance threshold!
            </p>
            <p className="text-xs text-slate-500 mt-1">
              No students are currently at risk of placement disqualification due to attendance.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="border-b border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-950 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3">Student</th>
                  <th className="px-4 py-3">Batch</th>
                  <th className="px-4 py-3">Branch</th>
                  <th className="px-4 py-3">Attendance</th>
                  <th className="px-4 py-3">Classes Attended</th>
                  <th className="px-4 py-3 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-surface-800">
                {(data.critical_students || []).map((s) => (
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
                      {s.batch_code}
                    </td>
                    <td className="px-4 py-3.5 text-xs text-slate-500 dark:text-slate-400">
                      {s.branch}
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-rose-500/10 text-rose-600 dark:text-rose-400">
                        {s.attendance_percentage}%
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-xs font-medium text-slate-700 dark:text-slate-300">
                      {s.attended_classes} / {s.total_classes}
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
