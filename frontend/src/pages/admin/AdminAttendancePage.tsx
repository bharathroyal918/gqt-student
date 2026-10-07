import React, { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Html5Qrcode } from "html5-qrcode";
import {
  QrCode,
  Camera,
  CheckCircle2,
  AlertCircle,
  Search,
  Download,
  Users,
  RefreshCw,
  X,
  UserCheck,
} from "lucide-react";
import { adminApi, AdminAttendanceOverviewData, AdminScanQRResponse } from "../../api/adminApi";
import { useToast } from "../../context/ToastContext";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Modal } from "../../components/ui/Modal";

export const AdminAttendancePage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success: toastSuccess, error: toastError, info: toastInfo } = useToast();

  // Filters State
  const [selectedBatch, setSelectedBatch] = useState<string>("ALL");
  const [selectedTech, setSelectedTech] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );
  const [searchQuery, setSearchQuery] = useState("");

  // Scanner Terminal State
  const [isScannerOpen, setIsScannerOpen] = useState(false);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [scannerTechnology, setScannerTechnology] = useState("Full Stack Development");
  const [manualInputId, setManualInputId] = useState("");
  const [scanResult, setScanResult] = useState<AdminScanQRResponse | null>(null);
  const [scannerError, setScannerError] = useState<string | null>(null);

  // Bulk Modal State
  const [isBulkModalOpen, setIsBulkModalOpen] = useState(false);
  const [bulkBatch, setBulkBatch] = useState("");
  const [bulkStatus, setBulkStatus] = useState<"PRESENT" | "ABSENT">("PRESENT");
  const [bulkTechnology, setBulkTechnology] = useState("Full Stack Development");

  const scannerRef = useRef<Html5Qrcode | null>(null);
  const scannerContainerId = "admin-gqt-qr-reader";

  // 1. Fetch Attendance Overview
  const {
    data: overviewData,
    refetch,
    isFetching,
  } = useQuery<AdminAttendanceOverviewData>({
    queryKey: [
      "admin",
      "attendance",
      selectedBatch,
      selectedTech,
      selectedStatus,
      selectedDate,
      searchQuery,
    ],
    queryFn: () =>
      adminApi.getAttendanceOverview({
        batch_code: selectedBatch,
        technology: selectedTech,
        status: selectedStatus,
        date: selectedDate,
        search: searchQuery,
      }),
    staleTime: 1000 * 20,
  });

  // 2. Scan QR Mutation
  const scanMutation = useMutation({
    mutationFn: adminApi.scanAttendanceQR,
    onSuccess: (data) => {
      setScanResult(data);
      setScannerError(null);
      setManualInputId("");
      queryClient.invalidateQueries({ queryKey: ["admin", "attendance"] });
      toastSuccess("Attendance Marked!", data.message);
    },
    onError: (err: any) => {
      const errMsg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.message ||
        "Failed to record attendance from scanned QR.";
      setScannerError(errMsg);
      toastError("Scan Verification Error", errMsg);
    },
  });

  // 3. Update Status Mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({
      studentId,
      status,
      date,
      technology,
      session_title,
    }: {
      studentId: string;
      status: string;
      date: string;
      technology: string;
      session_title: string;
    }) =>
      adminApi.markStudentAttendance(studentId, {
        date,
        status,
        technology,
        session_title,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "attendance"] });
      toastSuccess("Updated", "Student attendance status updated.");
    },
    onError: (err: any) => {
      toastError("Update Failed", err?.response?.data?.message || "Could not update status.");
    },
  });

  // 4. Bulk Mark Mutation
  const bulkMutation = useMutation({
    mutationFn: adminApi.bulkMarkAttendance,
    onSuccess: (data) => {
      setIsBulkModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ["admin", "attendance"] });
      toastSuccess("Bulk Attendance Complete", data.message);
    },
    onError: (err: any) => {
      toastError("Bulk Mark Failed", err?.response?.data?.message || "Could not mark batch.");
    },
  });

  // Camera Management
  const startCamera = async () => {
    try {
      setScannerError(null);
      setIsCameraActive(true);

      const html5QrCode = new Html5Qrcode(scannerContainerId);
      scannerRef.current = html5QrCode;

      const config = {
        fps: 10,
        qrbox: { width: 250, height: 250 },
        aspectRatio: 1.0,
      };

      await html5QrCode.start(
        { facingMode: "environment" },
        config,
        (decodedText) => {
          handleOnScanSuccess(decodedText);
        },
        () => {
          // Continuous scanning ticks
        }
      );
    } catch (err: any) {
      setIsCameraActive(false);
      setScannerError("Camera access failed or permission denied. You can enter Student ID manually below.");
    }
  };

  const stopCamera = async () => {
    if (scannerRef.current) {
      try {
        if (scannerRef.current.isScanning) {
          await scannerRef.current.stop();
        }
        scannerRef.current.clear();
      } catch (e) {
        // Ignored during cleanup
      }
      scannerRef.current = null;
    }
    setIsCameraActive(false);
  };

  const handleOnScanSuccess = (decodedText: string) => {
    scanMutation.mutate({
      qr_data: decodedText,
      technology: scannerTechnology,
      date: selectedDate,
      status: "PRESENT",
      remarks: "Scanned via Admin Live Terminal",
    });
  };

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualInputId.trim()) return;
    scanMutation.mutate({
      qr_data: manualInputId.trim(),
      technology: scannerTechnology,
      date: selectedDate,
      status: "PRESENT",
      remarks: "Manually verified by Administrator",
    });
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  // Export CSV Handler
  const handleExportCSV = () => {
    const records = overviewData?.records || [];
    if (records.length === 0) {
      toastInfo("No Data", "No attendance records available to export for this selection.");
      return;
    }

    const headers = [
      "Date",
      "Student USN",
      "Full Name",
      "Batch",
      "College",
      "Technology",
      "Session Title",
      "Status",
      "Overall Attendance %",
      "Remarks",
    ];

    const rows = records.map((r) => [
      `"${r.date}"`,
      `"${r.student_id_number}"`,
      `"${r.student_name}"`,
      `"${r.batch_code}"`,
      `"${r.college_name}"`,
      `"${r.technology}"`,
      `"${r.session_title}"`,
      `"${r.status}"`,
      `"${r.overall_attendance_pct}%"`,
      `"${r.remarks}"`,
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `GQT_Attendance_Report_${selectedDate}_${selectedBatch}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const stats = overviewData?.stats;
  const batches = overviewData?.batches || [];
  const technologies = overviewData?.technologies || [
    "Full Stack Development",
    "Python Full Stack",
    "Java Core & Advanced",
    "React & Frontend",
    "SQL & Database Engineering",
    "Data Structures & Algorithms",
  ];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* 1. Header Section */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500/10 text-brand-600 dark:text-brand-400">
              <QrCode className="h-5 w-5" />
            </span>
            <h1 className="text-2xl font-black text-slate-900 dark:text-white">
              Institutional Attendance & QR Scanner
            </h1>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Real-time batch attendance tracking, camera scanner terminal, and technology analytics
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-1.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin text-brand-500" : ""}`} />
            <span>Sync</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleExportCSV}
            className="flex items-center gap-1.5"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Export CSV</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setBulkBatch(batches[0] || "");
              setIsBulkModalOpen(true);
            }}
            className="flex items-center gap-1.5"
          >
            <UserCheck className="h-3.5 w-3.5" />
            <span>Mark Batch</span>
          </Button>

          <Button
            size="sm"
            onClick={() => {
              setIsScannerOpen(true);
              setTimeout(() => startCamera(), 200);
            }}
            className="flex items-center gap-1.5 shadow-lg shadow-brand-500/20"
          >
            <Camera className="h-3.5 w-3.5" />
            <span>Launch QR Scanner Terminal</span>
          </Button>
        </div>
      </div>

      {/* 2. KPI Metrics Strip */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card className="p-4 border-slate-200 dark:border-surface-800">
          <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">
            Total Students
          </span>
          <div className="mt-1 flex items-baseline gap-1">
            <span className="text-2xl font-black text-slate-900 dark:text-white font-mono">
              {stats?.total_students || 0}
            </span>
          </div>
          <p className="text-[10px] text-slate-400 mt-1">In selected cohort</p>
        </Card>

        <Card className="p-4 border-slate-200 dark:border-surface-800">
          <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 uppercase">
            Present (✓)
          </span>
          <div className="mt-1 flex items-baseline gap-1">
            <span className="text-2xl font-black text-emerald-600 dark:text-emerald-400 font-mono">
              {stats?.present_count || 0}
            </span>
            <span className="text-xs text-slate-500">
              ({stats?.attendance_rate || 100}%)
            </span>
          </div>
          <p className="text-[10px] text-slate-400 mt-1">Marked present</p>
        </Card>

        <Card className="p-4 border-slate-200 dark:border-surface-800">
          <span className="text-[11px] font-semibold text-rose-600 dark:text-rose-400 uppercase">
            Absent (✗)
          </span>
          <div className="mt-1 flex items-baseline gap-1">
            <span className="text-2xl font-black text-rose-600 dark:text-rose-400 font-mono">
              {stats?.absent_count || 0}
            </span>
          </div>
          <p className="text-[10px] text-slate-400 mt-1">Marked absent</p>
        </Card>

        <Card className="p-4 border-slate-200 dark:border-surface-800">
          <span className="text-[11px] font-semibold text-amber-500 uppercase">
            Late / Delayed
          </span>
          <div className="mt-1 flex items-baseline gap-1">
            <span className="text-2xl font-black text-amber-500 font-mono">
              {stats?.late_count || 0}
            </span>
          </div>
          <p className="text-[10px] text-slate-400 mt-1">Arrived late</p>
        </Card>
      </div>

      {/* 3. Comprehensive Filter Toolbar */}
      <Card className="p-5 bg-white dark:bg-surface-900 border-slate-200 dark:border-surface-800">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3.5">
          {/* Search Query */}
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search Student / USN / Email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-800 pl-9 pr-3 py-2 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          {/* Batch Selector */}
          <div>
            <select
              value={selectedBatch}
              onChange={(e) => setSelectedBatch(e.target.value)}
              className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-800 px-3 py-2 text-xs font-medium text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="ALL">All Batches</option>
              {batches.map((b) => (
                <option key={b} value={b}>
                  Batch: {b}
                </option>
              ))}
            </select>
          </div>

          {/* Technology Selector */}
          <div>
            <select
              value={selectedTech}
              onChange={(e) => setSelectedTech(e.target.value)}
              className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-800 px-3 py-2 text-xs font-medium text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="ALL">All Technologies</option>
              {technologies.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-800 px-3 py-2 text-xs font-medium text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="PRESENT">✓ Present</option>
              <option value="ABSENT">✗ Absent</option>
              <option value="LATE">Late</option>
              <option value="EXCUSED">Excused</option>
            </select>
          </div>

          {/* Date Picker */}
          <div>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-800 px-3 py-2 text-xs font-medium text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
        </div>
      </Card>

      {/* 4. Interactive Attendance Records Table */}
      <Card className="overflow-hidden border-slate-200 dark:border-surface-800 shadow-xl shadow-brand-500/5">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-surface-950/80 text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-surface-800 font-semibold uppercase">
              <tr>
                <th className="py-3.5 px-4">Student Name & USN</th>
                <th className="py-3.5 px-4">Batch</th>
                <th className="py-3.5 px-4">Technology Track</th>
                <th className="py-3.5 px-4">Date</th>
                <th className="py-3.5 px-4">Attendance Status</th>
                <th className="py-3.5 px-4">Overall Standing</th>
                <th className="py-3.5 px-4 text-right">Remarks</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-surface-800 text-slate-700 dark:text-slate-300">
              {(overviewData?.records || []).length > 0 ? (
                overviewData!.records.map((rec) => (
                  <tr key={rec.id} className="hover:bg-slate-50/80 dark:hover:bg-surface-800/40 transition-colors">
                    {/* Student details */}
                    <td className="py-3.5 px-4">
                      <div>
                        <span className="font-bold text-slate-900 dark:text-white text-xs block">
                          {rec.student_name}
                        </span>
                        <span className="font-mono text-[11px] text-brand-600 dark:text-brand-400 font-semibold">
                          {rec.student_id_number}
                        </span>
                      </div>
                    </td>

                    {/* Batch */}
                    <td className="py-3.5 px-4 font-mono font-medium">
                      <Badge variant="indigo" size="sm">
                        {rec.batch_code}
                      </Badge>
                    </td>

                    {/* Technology */}
                    <td className="py-3.5 px-4 font-semibold text-slate-800 dark:text-slate-200">
                      {rec.technology || "Full Stack Development"}
                    </td>

                    {/* Date */}
                    <td className="py-3.5 px-4 font-mono text-slate-600 dark:text-slate-400">
                      {rec.date}
                    </td>

                    {/* Quick Status Toggle */}
                    <td className="py-3.5 px-4">
                      <select
                        value={rec.status}
                        onChange={(e) =>
                          updateStatusMutation.mutate({
                            studentId: rec.student_id,
                            status: e.target.value,
                            date: rec.date,
                            technology: rec.technology,
                            session_title: rec.session_title,
                          })
                        }
                        className={`rounded-lg px-2.5 py-1 text-xs font-bold border cursor-pointer focus:outline-none ${
                          rec.status === "PRESENT"
                            ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
                            : rec.status === "ABSENT"
                            ? "bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30"
                            : rec.status === "LATE"
                            ? "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30"
                            : "bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border-cyan-500/30"
                        }`}
                      >
                        <option value="PRESENT">✓ Present</option>
                        <option value="ABSENT">✗ Absent</option>
                        <option value="LATE">⏱ Late</option>
                        <option value="EXCUSED">Excused</option>
                      </select>
                    </td>

                    {/* Overall Attendance Standing */}
                    <td className="py-3.5 px-4">
                      <span
                        className={`font-mono font-bold ${
                          rec.overall_attendance_pct >= 75
                            ? "text-emerald-600 dark:text-emerald-400"
                            : "text-rose-600 dark:text-rose-400"
                        }`}
                      >
                        {rec.overall_attendance_pct}%
                      </span>
                    </td>

                    {/* Remarks */}
                    <td className="py-3.5 px-4 text-right text-slate-500 dark:text-slate-400 italic">
                      {rec.remarks || "—"}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500 dark:text-slate-400">
                    <Users className="h-8 w-8 mx-auto mb-2 text-slate-300 dark:text-slate-600" />
                    <p className="font-semibold text-sm text-slate-700 dark:text-slate-300">
                      No attendance records found for the selected filters.
                    </p>
                    <p className="text-xs text-slate-400 mt-1">
                      Scan student QR codes or mark batch attendance to populate records.
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* 5. Live QR Scanner Terminal Modal */}
      <Modal
        isOpen={isScannerOpen}
        onClose={() => {
          stopCamera();
          setIsScannerOpen(false);
        }}
        size="lg"
        title="Live Attendance QR Terminal"
      >
        <div className="p-6 space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-surface-800">
            <div className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500/10 text-brand-600 dark:text-brand-400">
                <Camera className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Live Attendance QR Terminal
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Point camera at student QR code or scan barcode gun
                </p>
              </div>
            </div>

            <button
              onClick={() => {
                stopCamera();
                setIsScannerOpen(false);
              }}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-surface-800"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Session Technology Selector */}
          <div className="flex items-center gap-3">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Technology:
            </label>
            <select
              value={scannerTechnology}
              onChange={(e) => setScannerTechnology(e.target.value)}
              className="flex-1 rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-800 px-3 py-1.5 text-xs font-semibold text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              {technologies.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          {/* Camera Viewport Area */}
          <div className="relative rounded-2xl border-2 border-dashed border-slate-300 dark:border-surface-700 bg-slate-950 overflow-hidden flex flex-col items-center justify-center min-h-[280px]">
            <div id={scannerContainerId} className={`w-full ${isCameraActive ? "block" : "hidden"}`} />

            {!isCameraActive && (
              <div className="text-center p-6 space-y-3">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-500">
                  <Camera className="h-7 w-7" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white">Camera Standby</h4>
                  <p className="text-xs text-slate-400">Click below to start video scanning</p>
                </div>
                <Button size="sm" onClick={startCamera}>
                  <Camera className="h-4 w-4 mr-2" />
                  <span>Start Camera</span>
                </Button>
              </div>
            )}
          </div>

          {/* Scan Error Banner */}
          {scannerError && (
            <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-600 dark:text-rose-400 flex items-start gap-2.5">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>{scannerError}</span>
            </div>
          )}

          {/* Scan Success Banner */}
          {scanResult && (
            <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-4 space-y-2 animate-fadeIn">
              <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-bold text-sm">
                <CheckCircle2 className="h-4 w-4" />
                <span>Marked Present: {scanResult.student.full_name}</span>
              </div>
              <div className="flex justify-between text-xs text-slate-700 dark:text-slate-300">
                <span>USN: <strong className="font-mono">{scanResult.student.student_id_number}</strong></span>
                <span>Batch: <strong>{scanResult.student.batch_code}</strong></span>
                <span>Overall: <strong>{scanResult.student.attendance_percentage}%</strong></span>
              </div>
            </div>
          )}

          {/* Manual Input Fallback */}
          <form onSubmit={handleManualSubmit} className="pt-2 flex items-center gap-2">
            <input
              type="text"
              placeholder="Or enter Student ID / USN manually..."
              value={manualInputId}
              onChange={(e) => setManualInputId(e.target.value)}
              className="flex-1 rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-800 px-3.5 py-2 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
            <Button type="submit" size="sm" disabled={scanMutation.isPending}>
              <span>Verify & Mark Present</span>
            </Button>
          </form>
        </div>
      </Modal>

      {/* 6. Bulk Mark Batch Modal */}
      <Modal
        isOpen={isBulkModalOpen}
        onClose={() => setIsBulkModalOpen(false)}
        size="md"
        title="Bulk Mark Batch Attendance"
      >
        <div className="p-6 space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-surface-800">
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Bulk Mark Batch Attendance
            </h3>
            <button
              onClick={() => setIsBulkModalOpen(false)}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-surface-800"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="font-semibold block mb-1">Select Batch:</label>
              <select
                value={bulkBatch}
                onChange={(e) => setBulkBatch(e.target.value)}
                className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-800 px-3 py-2"
              >
                {batches.map((b) => (
                  <option key={b} value={b}>
                    {b}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="font-semibold block mb-1">Technology Track:</label>
              <select
                value={bulkTechnology}
                onChange={(e) => setBulkTechnology(e.target.value)}
                className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-800 px-3 py-2"
              >
                {technologies.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="font-semibold block mb-1">Mark Status As:</label>
              <select
                value={bulkStatus}
                onChange={(e) => setBulkStatus(e.target.value as any)}
                className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-800 px-3 py-2 font-bold"
              >
                <option value="PRESENT">✓ PRESENT</option>
                <option value="ABSENT">✗ ABSENT</option>
              </select>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200 dark:border-surface-800">
            <Button variant="outline" size="sm" onClick={() => setIsBulkModalOpen(false)}>
              Cancel
            </Button>
            <Button
              size="sm"
              disabled={bulkMutation.isPending || !bulkBatch}
              onClick={() =>
                bulkMutation.mutate({
                  batch_code: bulkBatch,
                  technology: bulkTechnology,
                  date: selectedDate,
                  status: bulkStatus,
                })
              }
            >
              {bulkMutation.isPending ? "Processing..." : `Mark All in ${bulkBatch} as ${bulkStatus}`}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
