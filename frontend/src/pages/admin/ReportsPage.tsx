import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  FileSpreadsheet,
  Download,
  Clock,
  Loader2,
  RefreshCw,
  FileText,
} from "lucide-react";
import { adminApi } from "../../api/adminApi";
import { ExportJobItem } from "../../types/admin";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { Select } from "../../components/ui/Form";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { useToast } from "../../context/ToastContext";

export const ReportsPage: React.FC = () => {
  const { success, error: toastError } = useToast();
  const queryClient = useQueryClient();

  const [reportType, setReportType] = useState<
    "performance" | "completion" | "assignment" | "project" | "monthly"
  >("performance");
  const [batchFilter, setBatchFilter] = useState("");
  const [showExportsDrawer, setShowExportsDrawer] = useState(false);

  // Queries for Domain Reports
  const {
    data: perfReport,
    isLoading: isPerfLoading,
    isError: isPerfError,
  } = useQuery({
    queryKey: ["admin-report-performance", batchFilter],
    queryFn: () => adminApi.getPerformanceReport({ batch_code: batchFilter || undefined }),
    enabled: reportType === "performance",
  });

  const {
    data: compReport,
    isLoading: isCompLoading,
    isError: isCompError,
  } = useQuery({
    queryKey: ["admin-report-completion"],
    queryFn: () => adminApi.getCompletionReport(),
    enabled: reportType === "completion",
  });

  const {
    data: assignReport,
    isLoading: isAssignLoading,
    isError: isAssignError,
  } = useQuery({
    queryKey: ["admin-report-assignment"],
    queryFn: () => adminApi.getAssignmentReport(),
    enabled: reportType === "assignment",
  });

  const {
    data: projReport,
    isLoading: isProjLoading,
    isError: isProjError,
  } = useQuery({
    queryKey: ["admin-report-project"],
    queryFn: () => adminApi.getProjectReport(),
    enabled: reportType === "project",
  });

  const {
    data: monthReport,
    isLoading: isMonthLoading,
    isError: isMonthError,
  } = useQuery({
    queryKey: ["admin-report-monthly"],
    queryFn: () => adminApi.getMonthlyActivityReport(30),
    enabled: reportType === "monthly",
  });

  // Query background export jobs
  const {
    data: exportsData,
    refetch: refetchExports,
    isFetching: isFetchingExports,
  } = useQuery({
    queryKey: ["admin-export-jobs"],
    queryFn: adminApi.getExportJobs,
    refetchInterval: showExportsDrawer ? 4000 : false, // Auto-poll when drawer is open
  });

  // Asynchronous Export Mutation
  const exportMutation = useMutation({
    mutationFn: (payload: { report_type: string; format: "CSV" | "JSON"; filters?: Record<string, any> }) =>
      adminApi.createExportJob(payload),
    onSuccess: (job: ExportJobItem) => {
      queryClient.invalidateQueries({ queryKey: ["admin-export-jobs"] });
      success(
        "Export Job Dispatched",
        `Job #${job.id.slice(0, 8)} started in background. File will be ready shortly.`
      );
      setShowExportsDrawer(true);
    },
    onError: (err: any) => {
      toastError(
        "Export Initiation Failed",
        err?.response?.data?.error?.message || "Could not dispatch background export job."
      );
    },
  });

  const getBackendReportTypeEnum = (type: string) => {
    switch (type) {
      case "performance":
        return "STUDENT_PERFORMANCE";
      case "completion":
        return "COURSE_STATISTICS";
      case "assignment":
        return "ASSIGNMENT_COMPLETION";
      case "project":
        return "PROJECT_PERFORMANCE";
      case "monthly":
        return "MONTHLY_ACTIVITY";
      default:
        return "FULL_EXECUTIVE";
    }
  };

  const handleTriggerExport = (format: "CSV" | "JSON") => {
    const reportEnum = getBackendReportTypeEnum(reportType);
    const filters: Record<string, any> = {};
    if (batchFilter) filters.batch_code = batchFilter;

    exportMutation.mutate({
      report_type: reportEnum,
      format,
      filters,
    });
  };

  const exportJobs = exportsData?.jobs || [];

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <FileSpreadsheet className="h-6 w-6 text-brand-400" />
            Executive Reports & Exports
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Compile aggregated cohort data, curriculum completion stats, and dispatch asynchronous exports.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowExportsDrawer(true)}
            className="flex items-center gap-1.5"
          >
            <Clock className="h-4 w-4 text-brand-400" />
            Export Jobs ({exportJobs.length})
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => handleTriggerExport("JSON")}
            disabled={exportMutation.isPending}
          >
            <Download className="h-4 w-4 mr-1.5" />
            Export JSON
          </Button>
          <Button
            size="sm"
            onClick={() => handleTriggerExport("CSV")}
            disabled={exportMutation.isPending}
            className="flex items-center gap-1.5"
          >
            {exportMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <FileSpreadsheet className="h-4 w-4" />
            )}
            Export CSV
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-surface-800 overflow-x-auto">
        <button
          onClick={() => setReportType("performance")}
          className={`px-5 py-3 text-sm font-medium border-b-2 whitespace-nowrap transition-all ${
            reportType === "performance"
              ? "border-brand-500 text-brand-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          Cohort Performance
        </button>
        <button
          onClick={() => setReportType("completion")}
          className={`px-5 py-3 text-sm font-medium border-b-2 whitespace-nowrap transition-all ${
            reportType === "completion"
              ? "border-brand-500 text-brand-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          Curriculum Track Completion
        </button>
        <button
          onClick={() => setReportType("assignment")}
          className={`px-5 py-3 text-sm font-medium border-b-2 whitespace-nowrap transition-all ${
            reportType === "assignment"
              ? "border-brand-500 text-brand-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          Assignment Solve Rates
        </button>
        <button
          onClick={() => setReportType("project")}
          className={`px-5 py-3 text-sm font-medium border-b-2 whitespace-nowrap transition-all ${
            reportType === "project"
              ? "border-brand-500 text-brand-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          Capstone Evaluations
        </button>
        <button
          onClick={() => setReportType("monthly")}
          className={`px-5 py-3 text-sm font-medium border-b-2 whitespace-nowrap transition-all ${
            reportType === "monthly"
              ? "border-brand-500 text-brand-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          Time Series Activity
        </button>
      </div>

      {/* 1. Performance Report View */}
      {reportType === "performance" && (
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <div className="w-48">
              <Select
                value={batchFilter}
                onChange={(e) => setBatchFilter(e.target.value)}
              >
                <option value="">All Cohorts / Batches</option>
                <option value="BATCH-2025-A">BATCH-2025-A</option>
                <option value="BATCH-2025-B">BATCH-2025-B</option>
                <option value="BATCH-2026-A">BATCH-2026-A</option>
              </Select>
            </div>
            {batchFilter && (
              <Button variant="secondary" size="sm" onClick={() => setBatchFilter("")}>
                Clear Filter
              </Button>
            )}
          </div>

          {isPerfLoading ? (
            <LoadingState message="Generating cohort performance calculations..." />
          ) : isPerfError || !perfReport ? (
            <ErrorState title="Report Error" message="Unable to generate performance report." />
          ) : (
            <>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
                <Card className="p-4">
                  <div className="text-xs text-slate-400">Total Enrolled Cohort</div>
                  <div className="text-2xl font-bold text-white mt-1">
                    {perfReport.total_students} students
                  </div>
                </Card>
                <Card className="p-4">
                  <div className="text-xs text-slate-400">Average Points Awarded</div>
                  <div className="text-2xl font-bold text-amber-400 mt-1">
                    {parseFloat(perfReport.average_points).toFixed(1)} pts
                  </div>
                </Card>
                <Card className="p-4">
                  <div className="text-xs text-slate-400">Top Score Recorded</div>
                  <div className="text-2xl font-bold text-emerald-400 mt-1">
                    {parseFloat(perfReport.highest_points).toFixed(1)} pts
                  </div>
                </Card>
                <Card className="p-4">
                  <div className="text-xs text-slate-400">Average Streak</div>
                  <div className="text-2xl font-bold text-rose-400 mt-1">
                    {perfReport.average_streak_days} days
                  </div>
                </Card>
              </div>

              {/* Batch Breakdown Table */}
              <div className="divide-y divide-surface-800 rounded-2xl border border-surface-800 bg-surface-900/60 overflow-hidden">
                <div className="p-4 bg-surface-900 text-xs font-semibold text-slate-400 uppercase tracking-wider grid grid-cols-12">
                  <div className="col-span-4">Batch Code</div>
                  <div className="col-span-3">Student Count</div>
                  <div className="col-span-3">Average Points</div>
                  <div className="col-span-2 text-right">Total Points</div>
                </div>
                {perfReport.batch_breakdown?.map((b) => (
                  <div key={b.batch_code} className="p-4 text-xs grid grid-cols-12 items-center">
                    <div className="col-span-4">
                      <Badge variant="indigo" size="sm">{b.batch_code}</Badge>
                    </div>
                    <div className="col-span-3 text-slate-300 font-medium">
                      {b.student_count} students
                    </div>
                    <div className="col-span-3 font-semibold text-amber-400">
                      {parseFloat(b.average_points).toFixed(1)} pts
                    </div>
                    <div className="col-span-2 text-right font-bold text-white">
                      {parseFloat(b.total_points).toLocaleString()} pts
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* 2. Completion Report View */}
      {reportType === "completion" && (
        <div className="space-y-6">
          {isCompLoading ? (
            <LoadingState message="Calculating curriculum completion statistics..." />
          ) : isCompError || !compReport ? (
            <ErrorState title="Report Error" message="Unable to generate completion report." />
          ) : (
            <div className="space-y-4">
              {compReport.courses?.map((course) => (
                <Card key={course.course_id} className="p-6">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-surface-800 pb-4">
                    <div>
                      <h3 className="font-bold text-white text-base">{course.course_title}</h3>
                      <div className="flex items-center gap-4 text-xs text-slate-400 mt-1">
                        <span>Active: {course.active_enrollments} students</span>
                        <span>•</span>
                        <span className="text-emerald-400 font-medium">
                          Completed: {course.completed_enrollments} students
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 divide-y divide-surface-800 rounded-xl border border-surface-800 bg-surface-900/40 overflow-hidden">
                    <div className="p-3 bg-surface-900 text-xs font-semibold text-slate-400 uppercase tracking-wider grid grid-cols-12">
                      <div className="col-span-1">#</div>
                      <div className="col-span-6">Module Title</div>
                      <div className="col-span-3">Completed Students</div>
                      <div className="col-span-2 text-right">Completion Rate</div>
                    </div>
                    {course.modules?.map((m) => (
                      <div key={m.module_id} className="p-3 text-xs grid grid-cols-12 items-center">
                        <div className="col-span-1 font-mono text-slate-400">#{m.order_index}</div>
                        <div className="col-span-6 font-medium text-slate-200">{m.module_title}</div>
                        <div className="col-span-3 text-slate-300">{m.completed_students} students</div>
                        <div className="col-span-2 text-right font-bold text-emerald-400">
                          {m.completion_rate}%
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 3. Assignment Metrics Report View */}
      {reportType === "assignment" && (
        <div className="space-y-6">
          {isAssignLoading ? (
            <LoadingState message="Aggregating assignment pass rates..." />
          ) : isAssignError || !assignReport ? (
            <ErrorState title="Report Error" message="Unable to generate assignment report." />
          ) : (
            <div className="divide-y divide-surface-800 rounded-2xl border border-surface-800 bg-surface-900/60 overflow-hidden">
              <div className="p-4 bg-surface-900 text-xs font-semibold text-slate-400 uppercase tracking-wider grid grid-cols-12">
                <div className="col-span-5">Problem Statement</div>
                <div className="col-span-2">Difficulty</div>
                <div className="col-span-2">Submissions</div>
                <div className="col-span-3 text-right">Pass Rate</div>
              </div>
              {assignReport.questions?.map((q) => (
                <div key={q.question_id} className="p-4 text-xs grid grid-cols-12 items-center">
                  <div className="col-span-5">
                    <div className="font-semibold text-white">{q.title}</div>
                    <div className="text-slate-400 mt-0.5">{q.module_title}</div>
                  </div>
                  <div className="col-span-2">
                    <Badge
                      variant={
                        q.difficulty === "EASY"
                          ? "emerald"
                          : q.difficulty === "MEDIUM"
                          ? "amber"
                          : "rose"
                      }
                      size="sm"
                    >
                      {q.difficulty}
                    </Badge>
                  </div>
                  <div className="col-span-2 text-slate-300 font-medium">
                    {q.total_submissions} attempts
                  </div>
                  <div className="col-span-3 text-right font-bold text-emerald-400">
                    {q.pass_rate}%
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 4. Capstone Submissions Report View */}
      {reportType === "project" && (
        <div className="space-y-6">
          {isProjLoading ? (
            <LoadingState message="Gathering capstone grading records..." />
          ) : isProjError || !projReport ? (
            <ErrorState title="Report Error" message="Unable to generate project report." />
          ) : (
            <div className="divide-y divide-surface-800 rounded-2xl border border-surface-800 bg-surface-900/60 overflow-hidden">
              <div className="p-4 bg-surface-900 text-xs font-semibold text-slate-400 uppercase tracking-wider grid grid-cols-12">
                <div className="col-span-4">Project Title</div>
                <div className="col-span-3">Course Track</div>
                <div className="col-span-3">Approved / Total</div>
                <div className="col-span-2 text-right">Average Score</div>
              </div>
              {projReport.projects?.map((p) => (
                <div key={p.project_id} className="p-4 text-xs grid grid-cols-12 items-center">
                  <div className="col-span-4 font-semibold text-white">{p.title}</div>
                  <div className="col-span-3 text-slate-300">{p.course_title || "General"}</div>
                  <div className="col-span-3 text-slate-300">
                    <span className="font-semibold text-emerald-400">{p.approved_submissions}</span> of{" "}
                    {p.total_submissions} approved
                  </div>
                  <div className="col-span-2 text-right font-bold text-amber-400">
                    {parseFloat(p.average_score).toFixed(1)} / {p.max_score} pts
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 5. Time Series Activity Report View */}
      {reportType === "monthly" && (
        <div className="space-y-6">
          {isMonthLoading ? (
            <LoadingState message="Compiling daily time series logs..." />
          ) : isMonthError || !monthReport ? (
            <ErrorState title="Report Error" message="Unable to generate monthly activity report." />
          ) : (
            <div className="divide-y divide-surface-800 rounded-2xl border border-surface-800 bg-surface-900/60 overflow-hidden">
              <div className="p-4 bg-surface-900 text-xs font-semibold text-slate-400 uppercase tracking-wider grid grid-cols-12">
                <div className="col-span-4">Date</div>
                <div className="col-span-4">Code Submissions</div>
                <div className="col-span-4 text-right">Active Learners</div>
              </div>
              {monthReport.timeline?.map((t) => (
                <div key={t.date} className="p-4 text-xs grid grid-cols-12 items-center">
                  <div className="col-span-4 font-mono font-medium text-slate-300">{t.date}</div>
                  <div className="col-span-4 font-semibold text-emerald-400">
                    {t.submissions_count} submissions
                  </div>
                  <div className="col-span-4 text-right font-bold text-indigo-400">
                    {t.active_students} students
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Exports History Modal / Drawer */}
      {showExportsDrawer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
          <div className="w-full max-w-2xl rounded-2xl border border-surface-800 bg-surface-900 p-6 shadow-2xl flex flex-col max-h-[85vh]">
            <div className="flex items-center justify-between border-b border-surface-800 pb-4">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Clock className="h-5 w-5 text-brand-400" />
                  Background Export Jobs
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Asynchronous compilation prevents server overload for large datasets.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refetchExports()}
                  disabled={isFetchingExports}
                  className="flex items-center gap-1.5"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${isFetchingExports ? "animate-spin" : ""}`} />
                  Refresh
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setShowExportsDrawer(false)}
                >
                  Close
                </Button>
              </div>
            </div>

            <div className="mt-4 flex-1 overflow-y-auto space-y-3">
              {exportJobs.length === 0 ? (
                <div className="py-12 text-center text-xs text-slate-400">
                  <FileText className="mx-auto h-10 w-10 text-slate-600 mb-2" />
                  No export jobs requested yet.
                </div>
              ) : (
                exportJobs.map((job) => (
                  <div
                    key={job.id}
                    className="p-4 rounded-xl border border-surface-800 bg-surface-950/60 flex items-center justify-between gap-4"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-xs text-white">
                          {job.report_type.replace(/_/g, " ")}
                        </span>
                        <Badge
                          variant={
                            job.status === "COMPLETED"
                              ? "emerald"
                              : job.status === "PROCESSING" || job.status === "PENDING"
                              ? "amber"
                              : "rose"
                          }
                          size="sm"
                        >
                          {job.status}
                        </Badge>
                        <Badge variant="indigo" size="sm">
                          {job.format}
                        </Badge>
                      </div>

                      <div className="mt-1 text-[11px] text-slate-400 flex items-center gap-3">
                        <span>Requested: {new Date(job.created_at).toLocaleTimeString()}</span>
                        {job.row_count > 0 && <span>• {job.row_count} rows</span>}
                        {job.file_size_bytes > 0 && (
                          <span>• {(job.file_size_bytes / 1024).toFixed(1)} KB</span>
                        )}
                      </div>
                    </div>

                    <div>
                      {job.status === "COMPLETED" && job.download_url ? (
                        <a
                          href={job.download_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white shadow-md hover:bg-brand-500 transition-colors"
                        >
                          <Download className="h-3.5 w-3.5" />
                          Download
                        </a>
                      ) : job.status === "FAILED" ? (
                        <span className="text-xs text-rose-400 font-medium">Failed</span>
                      ) : (
                        <div className="flex items-center gap-1.5 text-xs text-amber-400">
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          Processing
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
