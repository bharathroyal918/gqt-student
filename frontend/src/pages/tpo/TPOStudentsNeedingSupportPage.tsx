import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  Search,
  Filter,
  RefreshCw,
  ArrowRight,
  ShieldAlert,
  AlertCircle,
  Code2,
  Percent,
  CheckCircle2,
} from "lucide-react";
import { tpoApi } from "../../api/tpoApi";
import { useAuthStore } from "../../store/authStore";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";

export const TPOStudentsNeedingSupportPage: React.FC = () => {
  const { user } = useAuthStore();
  const [riskType, setRiskType] = useState<string>("ALL");
  const [search, setSearch] = useState<string>("");

  const {
    data: students,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ["tpo-students-needing-support", user?.id, riskType],
    queryFn: () => tpoApi.getStudentsNeedingSupport(riskType),
    staleTime: 60 * 1000,
  });

  if (isLoading) {
    return <LoadingState message="Scanning academic progress & attendance telemetry for support signals..." />;
  }

  if (isError || !students) {
    return (
      <ErrorState
        title="Failed to Load Support Signals"
        message={
          (error as any)?.response?.data?.error?.message ||
          "Could not analyze student records for academic support needs."
        }
        onRetry={() => refetch()}
      />
    );
  }

  const lastUpdated = dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString() : "";

  // Filter by search string
  const filteredList = students.filter((s) => {
    if (!search) return true;
    const term = search.toLowerCase();
    return (
      s.full_name.toLowerCase().includes(term) ||
      s.student_id_number.toLowerCase().includes(term) ||
      (s.branch && s.branch.toLowerCase().includes(term)) ||
      (s.batch_code && s.batch_code.toLowerCase().includes(term))
    );
  });

  const highSeverityCount = students.filter((s) =>
    s.reasons.some((r) => r.severity === "HIGH")
  ).length;

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-6 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 shadow-inner">
            <ShieldAlert className="h-7 w-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400">
                Academic Support & Mentorship
              </span>
              <Badge variant="warning" size="sm">
                Transparent Criteria
              </Badge>
            </div>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Students Needing Support
            </h1>
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
              Rule-based indicators for low attendance, zero lab attempts, and stalled progress
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
              Flagged for Support
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400">
              <AlertTriangle className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            {students.length}
          </div>
          <div className="mt-2 text-xs text-slate-400">
            Total students meeting support rules
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              High Severity Signals
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/10 text-rose-600 dark:text-rose-400">
              <AlertCircle className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-bold tracking-tight text-rose-600 dark:text-rose-400">
            {highSeverityCount}
          </div>
          <div className="mt-2 text-xs text-slate-400">
            Critical attendance (&lt;60%) or 0 lab pass
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Attendance Deficit
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-500/10 text-red-600 dark:text-red-400">
              <Percent className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-bold tracking-tight text-red-600 dark:text-red-400">
            {students.filter((s) => s.reasons.some((r) => r.code === "LOW_ATTENDANCE")).length}
          </div>
          <div className="mt-2 text-xs text-slate-400">
            Below 75% institutional threshold
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Zero Lab Activity
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-500/10 text-violet-600 dark:text-violet-400">
              <Code2 className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-bold tracking-tight text-violet-600 dark:text-violet-400">
            {students.filter((s) => s.reasons.some((r) => r.code === "ZERO_SUBMISSIONS")).length}
          </div>
          <div className="mt-2 text-xs text-slate-400">
            0 coding submissions submitted
          </div>
        </Card>
      </div>

      {/* Main Support Table */}
      <Card className="p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Student Remediation & Support List
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Review underlying factors and click to inspect full academic record
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

            {/* Filter by Risk Type */}
            <div className="flex items-center gap-1.5">
              <Filter className="h-3.5 w-3.5 text-slate-400" />
              <select
                value={riskType}
                onChange={(e) => setRiskType(e.target.value)}
                className="text-xs rounded-xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 py-1.5 px-2.5 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="ALL">All Support Reasons</option>
                <option value="LOW_ATTENDANCE">Low Attendance (&lt;75%)</option>
                <option value="ZERO_SUBMISSIONS">Zero Lab Attempts</option>
                <option value="HIGH_FAILURE_RATE">High Lab Failure Rate</option>
                <option value="STALLED_PROGRESS">Stalled Learning Progress</option>
              </select>
            </div>
          </div>
        </div>

        {filteredList.length === 0 ? (
          <div className="p-8 text-center text-slate-400 bg-emerald-50/50 dark:bg-emerald-950/20 rounded-2xl border border-emerald-500/20">
            <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-900 dark:text-white">
              No students currently flagged for academic support!
            </p>
            <p className="text-xs text-slate-500 mt-1">
              All students are meeting institutional attendance and curriculum benchmarks.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="border-b border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-950 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3">Student</th>
                  <th className="px-4 py-3">Batch & Branch</th>
                  <th className="px-4 py-3">Attendance</th>
                  <th className="px-4 py-3">Lab Submissions</th>
                  <th className="px-4 py-3">Support Indicators & Context</th>
                  <th className="px-4 py-3 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-surface-800">
                {filteredList.map((s) => (
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
                    <td className="px-4 py-3.5">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${
                          s.attendance_percentage < 60
                            ? "bg-rose-500/20 text-rose-700 dark:text-rose-300"
                            : s.attendance_percentage < 75
                            ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                            : "bg-slate-100 dark:bg-surface-800 text-slate-600 dark:text-slate-300"
                        }`}
                      >
                        {s.attendance_percentage}%
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-xs">
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {s.submissions_count} attempts
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {s.accepted_submissions_count} accepted
                      </div>
                    </td>
                    <td className="px-4 py-3.5 space-y-1">
                      {s.reasons.map((r, i) => (
                        <div key={i} className="flex items-center gap-1.5 text-xs">
                          <span
                            className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              r.severity === "HIGH"
                                ? "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                                : "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                            }`}
                          >
                            {r.label}
                          </span>
                          <span className="text-[11px] text-slate-500 dark:text-slate-400">
                            {r.detail}
                          </span>
                        </div>
                      ))}
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
