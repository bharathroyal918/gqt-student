import React, { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  FileSpreadsheet,
  Download,
  Filter,
  ShieldCheck,
  AlertCircle,
  FileJson,
  CheckCircle2,
  RefreshCw,
  Info,
  Layers,
} from "lucide-react";
import { tpoApi } from "../../api/tpoApi";
import { useAuthStore } from "../../store/authStore";
import {
  TPOReportFilterPayload,
  TPOReportPreviewResponse,
} from "../../types/tpo";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";


export const TPOReportsPage: React.FC = () => {
  const { user } = useAuthStore();

  const { data: profile } = useQuery({
    queryKey: ["tpo-profile-me", user?.id],
    queryFn: tpoApi.getMe,
    staleTime: 60 * 1000,
  });

  const {
    data: reportTypes,
    isLoading: isTypesLoading,
    isError: isTypesError,
    error: typesError,
    refetch: refetchTypes,
  } = useQuery({
    queryKey: ["tpo-report-types"],
    queryFn: tpoApi.getReportTypes,
    staleTime: 5 * 60 * 1000,
  });

  // Selected report type
  const [selectedType, setSelectedType] = useState<string>("STUDENT_ROSTER");
  const [exportFormat, setExportFormat] = useState<"csv" | "json">("csv");

  // Filters
  const [batchCode, setBatchCode] = useState<string>("");
  const [courseOpted, setCourseOpted] = useState<string>("");
  const [isActiveFilter, setIsActiveFilter] = useState<string>("ALL");
  const [riskType, setRiskType] = useState<string>("ALL");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");

  // Preview Data
  const [previewData, setPreviewData] = useState<TPOReportPreviewResponse | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [exportSuccessMessage, setExportSuccessMessage] = useState<string | null>(null);

  // Set default selected type once loaded
  useEffect(() => {
    if (reportTypes && reportTypes.length > 0 && !selectedType) {
      setSelectedType(reportTypes[0].id);
    }
  }, [reportTypes, selectedType]);

  // Construct filters payload
  const buildFiltersPayload = (): TPOReportFilterPayload => {
    const filters: TPOReportFilterPayload = {};
    if (batchCode.trim()) filters.batch_code = batchCode.trim();
    if (courseOpted.trim()) filters.course_opted = courseOpted.trim();
    if (isActiveFilter === "TRUE") filters.is_active = true;
    if (isActiveFilter === "FALSE") filters.is_active = false;
    if (riskType !== "ALL" && selectedType === "STUDENTS_NEEDING_SUPPORT") {
      filters.risk_type = riskType;
    }
    if (dateFrom) filters.date_from = dateFrom;
    if (dateTo) filters.date_to = dateTo;
    return filters;
  };

  // Preview Mutation
  const previewMutation = useMutation({
    mutationFn: () =>
      tpoApi.previewReport({
        report_type: selectedType,
        filters: buildFiltersPayload(),
      }),
    onSuccess: (data) => {
      setPreviewData(data);
      setPreviewError(null);
    },
    onError: (err: any) => {
      setPreviewError(
        err?.response?.data?.error?.message ||
          "Failed to generate report preview. Please check your filter values."
      );
      setPreviewData(null);
    },
  });

  // Export Mutation
  const exportMutation = useMutation({
    mutationFn: () =>
      tpoApi.exportReport({
        report_type: selectedType,
        format: exportFormat,
        filters: buildFiltersPayload(),
      }),
    onSuccess: ({ blob, filename }) => {
      // Trigger native browser download
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setExportSuccessMessage(`Export generated successfully: ${filename}`);
      setTimeout(() => setExportSuccessMessage(null), 5000);
    },
    onError: (err: any) => {
      setPreviewError(
        err?.response?.data?.error?.message ||
          "Failed to export report file. Please verify parameters and try again."
      );
    },
  });

  // Automatically trigger initial preview when report type changes
  useEffect(() => {
    if (selectedType) {
      previewMutation.mutate();
    }
  }, [selectedType]);

  if (isTypesLoading) {
    return <LoadingState message="Loading reporting capabilities and security schemas..." />;
  }

  if (isTypesError || !reportTypes) {
    return (
      <ErrorState
        title="Failed to Load Report Definitions"
        message={
          (typesError as any)?.response?.data?.error?.message ||
          "Could not initialize reporting module. Please check your network connection."
        }
        onRetry={() => refetchTypes()}
      />
    );
  }

  const currentReportMeta = reportTypes.find((r) => r.id === selectedType);
  const college = profile?.college;

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-6 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20 shadow-inner">
            <FileSpreadsheet className="h-7 w-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
                Data Governance & Reporting
              </span>
              <Badge variant="success" size="sm" className="flex items-center gap-1">
                <ShieldCheck className="h-3 w-3" />
                Zero-Trust College Scope
              </Badge>
            </div>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              TPO Reports & Secure Exports
            </h1>
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
              Authoritative, compliance-verified academic and placement reporting for{" "}
              <span className="font-semibold text-slate-800 dark:text-slate-200">
                {college?.name || "your institution"}
              </span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => previewMutation.mutate()}
            disabled={previewMutation.isPending}
            className="flex items-center gap-2"
          >
            <RefreshCw
              className={`h-4 w-4 ${previewMutation.isPending ? "animate-spin text-brand-500" : ""}`}
            />
            <span>Refresh Preview</span>
          </Button>
        </div>
      </div>

      {/* Security & Audit Notice */}
      <div className="rounded-xl border border-blue-500/20 bg-blue-50/60 dark:bg-blue-950/20 p-4 text-xs text-blue-800 dark:text-blue-300 flex items-start gap-3">
        <ShieldCheck className="h-4 w-4 shrink-0 text-blue-600 dark:text-blue-400 mt-0.5" />
        <div>
          <span className="font-semibold">Authoritative Security Scope: </span>
          All previews and exports strictly derive authorization from your server-side identity (
          <span className="font-mono font-medium">{user?.email}</span>). CSV downloads include UTF-8 BOM
          encoding and active spreadsheet formula-injection mitigation. All preview and export events
          are immutably recorded in the compliance audit log.
        </div>
      </div>

      {/* Export Success Notification */}
      {exportSuccessMessage && (
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-50/80 dark:bg-emerald-950/30 p-4 text-xs text-emerald-800 dark:text-emerald-300 flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
          <span>{exportSuccessMessage}</span>
        </div>
      )}

      {/* Main Reporting Workspace: Controls & Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Report Selection & Filter Controls */}
        <div className="space-y-6">
          {/* Report Type Selector Card */}
          <Card className="p-5">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
              <Layers className="h-4 w-4 text-brand-500" />
              1. Select Report Template
            </h3>

            <div className="space-y-2">
              {reportTypes.map((type) => {
                const isSelected = selectedType === type.id;
                return (
                  <button
                    key={type.id}
                    onClick={() => setSelectedType(type.id)}
                    className={`w-full text-left p-3 rounded-xl border transition-all ${
                      isSelected
                        ? "border-brand-500 bg-brand-50/50 dark:bg-brand-950/30 ring-1 ring-brand-500/50"
                        : "border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 hover:border-slate-300 dark:hover:border-surface-700"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <p
                        className={`text-sm font-semibold ${
                          isSelected
                            ? "text-brand-600 dark:text-brand-400"
                            : "text-slate-900 dark:text-white"
                        }`}
                      >
                        {type.name}
                      </p>
                      {isSelected && (
                        <CheckCircle2 className="h-4 w-4 text-brand-600 dark:text-brand-400 shrink-0" />
                      )}
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                      {type.description}
                    </p>
                  </button>
                );
              })}
            </div>
          </Card>

          {/* Report Filter Controls Card */}
          <Card className="p-5">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
              <Filter className="h-4 w-4 text-brand-500" />
              2. Filter Parameters
            </h3>

            <div className="space-y-4">
              {/* Batch Code */}
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Batch Code (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. 2025-CS-A"
                  value={batchCode}
                  onChange={(e) => setBatchCode(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>

              {/* Course / Technology Track */}
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Course / Track (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Full Stack Java"
                  value={courseOpted}
                  onChange={(e) => setCourseOpted(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>

              {/* Active Status */}
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Student Status
                </label>
                <select
                  value={isActiveFilter}
                  onChange={(e) => setIsActiveFilter(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                >
                  <option value="ALL">All Students</option>
                  <option value="TRUE">Active Only</option>
                  <option value="FALSE">Inactive Only</option>
                </select>
              </div>

              {/* Specific Support Risk Filter (if applicable) */}
              {selectedType === "STUDENTS_NEEDING_SUPPORT" && (
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Support Reason Filter
                  </label>
                  <select
                    value={riskType}
                    onChange={(e) => setRiskType(e.target.value)}
                    className="w-full text-xs rounded-lg border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                  >
                    <option value="ALL">All Support Reasons</option>
                    <option value="LOW_ATTENDANCE">Low Attendance (&lt; 75%)</option>
                    <option value="ZERO_SUBMISSIONS">Zero Lab Submissions</option>
                    <option value="HIGH_FAILURE_RATE">High Lab Failure Rate</option>
                    <option value="STALLED_PROGRESS">Stalled Progress</option>
                  </select>
                </div>
              )}

              {/* Date Ranges (for supported reports) */}
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    From Date
                  </label>
                  <input
                    type="date"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                    className="w-full text-xs rounded-lg border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 px-2 py-1.5 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    To Date
                  </label>
                  <input
                    type="date"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                    className="w-full text-xs rounded-lg border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 px-2 py-1.5 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
              </div>

              <Button
                variant="outline"
                size="sm"
                className="w-full text-xs"
                onClick={() => previewMutation.mutate()}
                disabled={previewMutation.isPending}
              >
                Apply Filters & Update Preview
              </Button>
            </div>
          </Card>

          {/* Export Action Card */}
          <Card className="p-5 border-brand-500/20 bg-gradient-to-b from-brand-500/[0.03] to-transparent">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
              <Download className="h-4 w-4 text-brand-500" />
              3. Generate & Download Export
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Export Format
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setExportFormat("csv")}
                    className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg border text-xs font-semibold transition-colors ${
                      exportFormat === "csv"
                        ? "border-emerald-500 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300"
                        : "border-slate-200 dark:border-surface-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-surface-800"
                    }`}
                  >
                    <FileSpreadsheet className="h-4 w-4" />
                    CSV (Excel UTF-8)
                  </button>
                  <button
                    type="button"
                    onClick={() => setExportFormat("json")}
                    className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg border text-xs font-semibold transition-colors ${
                      exportFormat === "json"
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300"
                        : "border-slate-200 dark:border-surface-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-surface-800"
                    }`}
                  >
                    <FileJson className="h-4 w-4" />
                    JSON (Data)
                  </button>
                </div>
              </div>

              <Button
                variant="primary"
                size="md"
                className="w-full flex items-center justify-center gap-2 shadow-lg shadow-brand-500/20"
                onClick={() => exportMutation.mutate()}
                disabled={exportMutation.isPending}
              >
                {exportMutation.isPending ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Generating Authoritative Export...</span>
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4" />
                    <span>Download {exportFormat.toUpperCase()} Export</span>
                  </>
                )}
              </Button>
            </div>
          </Card>
        </div>

        {/* Right Column: Live Report Preview & Column Definitions */}
        <div className="lg:col-span-2 space-y-6">
          {/* Preview Panel Card */}
          <Card className="p-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-200 dark:border-surface-800">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                    {previewData?.report_name || currentReportMeta?.name || "Report Preview"}
                  </h2>
                  {previewData && (
                    <Badge variant="primary" size="sm">
                      {previewData.total_rows} matching rows
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  {currentReportMeta?.description}
                </p>
              </div>

              {previewData && (
                <div className="text-right text-xs text-slate-400">
                  <span>Generated: </span>
                  <span className="font-mono text-slate-600 dark:text-slate-300">
                    {new Date(previewData.generated_at).toLocaleTimeString()}
                  </span>
                </div>
              )}
            </div>

            {/* Limitations / Disclaimers notice */}
            {previewData?.limitations && (
              <div className="mt-4 rounded-lg bg-amber-500/10 border border-amber-500/20 p-3 text-xs text-amber-700 dark:text-amber-300 flex items-start gap-2">
                <Info className="h-4 w-4 shrink-0 text-amber-500 mt-0.5" />
                <span>{previewData.limitations}</span>
              </div>
            )}

            {/* Error in Preview */}
            {previewError && (
              <div className="mt-4 rounded-lg bg-rose-500/10 border border-rose-500/20 p-3 text-xs text-rose-700 dark:text-rose-300 flex items-start gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-500 mt-0.5" />
                <span>{previewError}</span>
              </div>
            )}

            {/* Loading Preview State */}
            {previewMutation.isPending && (
              <div className="py-16 text-center">
                <RefreshCw className="h-8 w-8 animate-spin mx-auto text-brand-500 mb-3" />
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                  Building authoritative report preview...
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Enforcing college boundary and sanitizing dataset
                </p>
              </div>
            )}

            {/* Preview Table */}
            {!previewMutation.isPending && previewData && (
              <div className="mt-4 space-y-4">
                {previewData.sample_rows.length === 0 ? (
                  <div className="py-16 text-center rounded-xl border border-dashed border-slate-200 dark:border-surface-800">
                    <AlertCircle className="h-10 w-10 text-slate-400 mx-auto mb-2" />
                    <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                      No Records Matched Active Filters
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      Try clearing or adjusting your batch, course, or date filters.
                    </p>
                  </div>
                ) : (
                  <>
                    <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-surface-800">
                      <table className="w-full text-left text-xs text-slate-700 dark:text-slate-300">
                        <thead className="bg-slate-50 dark:bg-surface-950/80 text-slate-900 dark:text-white font-semibold border-b border-slate-200 dark:border-surface-800">
                          <tr>
                            {previewData.columns.map((col) => (
                              <th key={col.field} className="px-3.5 py-3 whitespace-nowrap">
                                {col.label}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-surface-800 bg-white dark:bg-surface-900">
                          {previewData.sample_rows.map((row, idx) => (
                            <tr
                              key={idx}
                              className="hover:bg-slate-50/80 dark:hover:bg-surface-800/50 transition-colors"
                            >
                              {previewData.columns.map((col) => {
                                const val = row[col.field];
                                return (
                                  <td
                                    key={col.field}
                                    className="px-3.5 py-2.5 whitespace-nowrap text-slate-800 dark:text-slate-200"
                                  >
                                    {val === true ? (
                                      <Badge variant="success" size="sm">
                                        Yes
                                      </Badge>
                                    ) : val === false ? (
                                      <Badge variant="neutral" size="sm">
                                        No
                                      </Badge>
                                    ) : val === null || val === undefined || val === "" ? (
                                      <span className="text-slate-400 italic">—</span>
                                    ) : (
                                      String(val)
                                    )}
                                  </td>
                                );
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {previewData.is_truncated && (
                      <p className="text-xs text-slate-500 dark:text-slate-400 italic text-center">
                        Showing sample preview of first 25 records out of {previewData.total_rows} total rows.
                        The complete dataset will be included in the exported file.
                      </p>
                    )}
                  </>
                )}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
