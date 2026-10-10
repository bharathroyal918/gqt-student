import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Code2,
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
  Calendar,
  Layers,
  Terminal,
  Activity,
  FileCode,
} from "lucide-react";
import { tpoApi } from "../../api/tpoApi";
import { useAuthStore } from "../../store/authStore";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";

export const TPOAssignmentsLabsPage: React.FC = () => {
  const { user } = useAuthStore();
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ["tpo-assignments-labs", user?.id, dateFrom, dateTo],
    queryFn: () => tpoApi.getAssignmentsLabs(dateFrom || undefined, dateTo || undefined),
    staleTime: 60 * 1000,
  });

  if (isLoading) {
    return <LoadingState message="Aggregating coding submissions and lab verdicts..." />;
  }

  if (isError || !data) {
    return (
      <ErrorState
        title="Failed to Load Lab Analytics"
        message={
          (error as any)?.response?.data?.error?.message ||
          "Could not retrieve assignment and lab submission records."
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
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-violet-500/10 text-violet-600 dark:text-violet-400 border border-violet-500/20 shadow-inner">
            <Code2 className="h-7 w-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-violet-600 dark:text-violet-400">
                Assessment Analytics
              </span>
              <Badge variant="brand" size="sm">
                Coding Judge
              </Badge>
            </div>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Assignments & Lab Performance
            </h1>
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
              Evaluation verdicts, student participation, and programming language statistics
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="text-right hidden md:block">
            <span className="text-[10px] text-slate-400 block font-medium">Last Synced</span>
            <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              {lastUpdated || "Live"}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-slate-400" />
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="text-xs rounded-xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 py-1.5 px-2 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="From Date"
            />
            <span className="text-xs text-slate-400">to</span>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="text-xs rounded-xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 py-1.5 px-2 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
              placeholder="To Date"
            />
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
              Student Participation
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400">
              <Activity className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              {data.participating_students}
            </span>
            <span className="text-xs text-slate-400">/ {data.total_students} total</span>
          </div>
          <div className="mt-2 text-xs text-slate-400">
            {data.unattempted_students} students have not attempted labs
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Total Attempts
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-500/10 text-violet-600 dark:text-violet-400">
              <Terminal className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-bold tracking-tight text-violet-600 dark:text-violet-400">
            {data.total_attempts}
          </div>
          <div className="mt-2 text-xs text-slate-400">
            Across {data.unique_questions_attempted} distinct challenges
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Pass Rate (Evaluated)
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-bold tracking-tight text-emerald-600 dark:text-emerald-400">
            {data.pass_rate_percentage}%
          </div>
          <div className="mt-2 text-xs text-slate-400">
            {data.accepted_submissions} accepted of {data.accepted_submissions + data.rejected_submissions} evaluated
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Pending / Queued
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400">
              <Clock className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-bold tracking-tight text-amber-600 dark:text-amber-400">
            {data.pending_submissions}
          </div>
          <div className="mt-2 text-xs text-slate-400">
            Currently running or in judge queue
          </div>
        </Card>
      </div>

      {/* Verdict Breakdown & Languages */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Verdict Breakdown */}
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <Layers className="h-4 w-4 text-violet-500" />
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Submission Verdict Breakdown
            </h3>
          </div>
          <div className="space-y-3">
            {Object.entries(data.verdict_breakdown).map(([verdict, count]) => {
              const isAccepted = verdict === "ACCEPTED";
              const isPending = verdict === "PENDING_OR_QUEUED";
              const colorClass = isAccepted
                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                : isPending
                ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20"
                : "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20";

              return (
                <div
                  key={verdict}
                  className={`flex items-center justify-between p-2.5 rounded-xl border text-xs font-medium ${colorClass}`}
                >
                  <div className="flex items-center gap-2">
                    {isAccepted ? (
                      <CheckCircle2 className="h-4 w-4" />
                    ) : isPending ? (
                      <Clock className="h-4 w-4" />
                    ) : (
                      <XCircle className="h-4 w-4" />
                    )}
                    <span>{verdict.replace(/_/g, " ")}</span>
                  </div>
                  <span className="font-bold">{count}</span>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Language Breakdown */}
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <FileCode className="h-4 w-4 text-violet-500" />
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Language Usage & Pass Rates
            </h3>
          </div>
          {data.language_stats.length === 0 ? (
            <p className="text-xs text-slate-400">No submissions logged for selected period.</p>
          ) : (
            <div className="space-y-4">
              {data.language_stats.map((lang) => (
                <div key={lang.language} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="font-bold text-slate-800 dark:text-slate-200 capitalize">
                      {lang.language}
                    </span>
                    <span className="text-slate-500 dark:text-slate-400">
                      {lang.accepted_submissions}/{lang.total_submissions} accepted ({lang.pass_rate}%)
                    </span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-slate-100 dark:bg-surface-800 overflow-hidden">
                    <div
                      className="h-full bg-violet-500 rounded-full transition-all duration-500"
                      style={{ width: `${lang.pass_rate}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Recent Submission Timeline */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Recent Lab & Coding Activity Timeline
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Live submission stream from students in your institution
            </p>
          </div>
          <span className="text-xs text-slate-400 font-medium">
            Last {data.recent_timeline.length} attempts
          </span>
        </div>

        {data.recent_timeline.length === 0 ? (
          <div className="p-8 text-center text-slate-400">
            <p className="text-sm">No recent submission activities recorded.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="border-b border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-950 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">Student</th>
                  <th className="px-4 py-3">Question</th>
                  <th className="px-4 py-3">Language</th>
                  <th className="px-4 py-3">Verdict</th>
                  <th className="px-4 py-3">Test Cases</th>
                  <th className="px-4 py-3 text-right">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-surface-800">
                {data.recent_timeline.map((item) => (
                  <tr
                    key={item.id}
                    className="hover:bg-slate-50/80 dark:hover:bg-surface-800/40 transition-colors"
                  >
                    <td className="px-4 py-3 text-xs text-slate-400 whitespace-nowrap">
                      {new Date(item.submitted_at).toLocaleDateString()}{" "}
                      {new Date(item.submitted_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {item.student_name}
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        {item.student_id_number}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs font-medium text-slate-800 dark:text-slate-200">
                      {item.question_title}
                    </td>
                    <td className="px-4 py-3 text-xs uppercase font-mono text-slate-500 dark:text-slate-400">
                      {item.language}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold ${
                          item.status === "ACCEPTED"
                            ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                            : item.status === "PENDING" || item.status === "RUNNING"
                            ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                            : "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                        }`}
                      >
                        {item.status.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs font-semibold text-slate-700 dark:text-slate-300">
                      {item.passed_test_cases} / {item.total_test_cases}
                    </td>
                    <td className="px-4 py-3 text-right font-bold text-slate-900 dark:text-white">
                      +{item.score_awarded} pts
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
