import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { QRCodeSVG } from "qrcode.react";
import {
  QrCode,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Calendar,
  RefreshCw,
  Download,
  Copy,
  Check,
  Layers,
  Mail,
} from "lucide-react";
import { studentApi } from "../../api/studentApi";
import { useAuthStore } from "../../store/authStore";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { StudentQRCodeModal } from "../../components/student/StudentQRCodeModal";

export const StudentAttendancePage: React.FC = () => {
  const { user, studentProfile } = useAuthStore();
  const [selectedTech, setSelectedTech] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [isCopied, setIsCopied] = useState(false);
  const [isPopupOpen, setIsPopupOpen] = useState(false);

  // Fetch Attendance Telemetry
  const {
    data: attendanceData,
    refetch: refetchAttendance,
    isFetching,
  } = useQuery({
    queryKey: ["student", "attendance"],
    queryFn: studentApi.getAttendanceTelemetry,
    staleTime: 1000 * 30, // 30s fresh
  });

  // Student Telemetry Resolution
  const fullName =
    attendanceData?.student?.full_name ||
    studentProfile?.full_name ||
    user?.email ||
    "Enrolled Student";

  const studentId =
    attendanceData?.student?.student_id ||
    studentProfile?.student_id_number ||
    "GQT-STUDENT";

  const batchCode =
    attendanceData?.student?.batch_code ||
    studentProfile?.batch_code ||
    "BATCH-2026";

  const collegeName =
    attendanceData?.student?.college_name ||
    studentProfile?.college_name ||
    "GQT Engineering Academy";

  // Course Registration Verification Guard
  const hasCourse = Boolean(
    (attendanceData?.student?.has_enrollments) ||
    (attendanceData?.student?.enrolled_courses && attendanceData.student.enrolled_courses.length > 0) ||
    ((studentProfile as any)?.course_opted && (studentProfile as any).course_opted.trim().length > 0) ||
    (attendanceData?.student?.course_name && attendanceData.student.course_name !== "Not Enrolled")
  );

  const courseName =
    attendanceData?.student?.course_name ||
    (studentProfile as any)?.course_opted ||
    (studentProfile as any)?.course_name ||
    (hasCourse ? "Full Stack Software Development" : "Not Enrolled");

  const attendancePct = attendanceData?.attendance_percentage ?? 100.0;
  const isAttendanceHealthy = attendancePct >= 75.0;

  // Personal QR Payload for Classroom Scanner / Admin Terminal
  const qrPayload = JSON.stringify({
    type: "STUDENT_ATTENDANCE_ID",
    student_id: studentId,
    full_name: fullName,
    batch_code: batchCode,
    course: courseName,
    college: collegeName,
    email: user?.email || "",
  });

  const handleCopyId = () => {
    navigator.clipboard.writeText(studentId);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const handleDownloadQR = () => {
    const svgElement = document.getElementById("attendance-page-qrcode-svg");
    if (!svgElement) return;

    const svgData = new XMLSerializer().serializeToString(svgElement);
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    const img = new Image();

    img.onload = () => {
      canvas.width = 600;
      canvas.height = 600;
      if (ctx) {
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, 600, 600);
        ctx.drawImage(img, 50, 50, 500, 500);
        const pngFile = canvas.toDataURL("image/png");
        const downloadLink = document.createElement("a");
        downloadLink.download = `${studentId}-attendance-qr.png`;
        downloadLink.href = pngFile;
        downloadLink.click();
      }
    };
    img.src = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(svgData)));
  };

  const availableTechnologies = [
    { id: "ALL", name: "All Technologies" },
    { id: "Full Stack Development", name: "Full Stack Track" },
    { id: "Python Full Stack", name: "Python Full Stack" },
    { id: "Java Core & Advanced", name: "Java Core & Adv" },
    { id: "React & Frontend", name: "React & Frontend" },
    { id: "SQL & Database Engineering", name: "SQL & DBMS" },
    { id: "Data Structures & Algorithms", name: "DSA & Problem Solving" },
  ];

  const allRecords = attendanceData?.records || [];

  // Filtering records by technology and status
  const filteredRecords = allRecords.filter((rec) => {
    const matchesTech =
      selectedTech === "ALL" ||
      (rec.technology || "").toLowerCase().includes(selectedTech.toLowerCase()) ||
      (rec.session_title || "").toLowerCase().includes(selectedTech.toLowerCase());

    const matchesStatus =
      statusFilter === "ALL" || rec.status.toUpperCase() === statusFilter.toUpperCase();

    return matchesTech && matchesStatus;
  });

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Pop-up QR Modal */}
      <StudentQRCodeModal
        isOpen={isPopupOpen}
        onClose={() => setIsPopupOpen(false)}
        attendanceData={attendanceData}
      />

      {/* Header Section */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500/10 text-brand-600 dark:text-brand-400">
              <QrCode className="h-5 w-5" />
            </span>
            <h1 className="text-2xl font-black text-slate-900 dark:text-white">
              Student Attendance & Digital QR
            </h1>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Display your verified student QR code for classroom entry and automated attendance tracking
          </p>
        </div>

        {/* Live Sync Action */}
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetchAttendance()}
            disabled={isFetching}
            className="flex items-center gap-1.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin text-brand-500" : ""}`} />
            <span>{isFetching ? "Syncing..." : "Refresh Attendance"}</span>
          </Button>

          <Button
            size="sm"
            onClick={() => setIsPopupOpen(true)}
            className="flex items-center gap-1.5 shadow-md shadow-brand-500/20"
          >
            <QrCode className="h-3.5 w-3.5" />
            <span>Open QR Popup</span>
          </Button>
        </div>
      </div>

      {/* NON-ENROLLED STUDENT ERROR GUARD BANNER */}
      {!hasCourse && (
        <div className="rounded-3xl border-2 border-rose-500/40 bg-gradient-to-r from-rose-500/15 via-rose-500/10 to-transparent p-6 shadow-xl shadow-rose-500/5 animate-pulse">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-rose-500 text-white shadow-lg shadow-rose-500/30">
                <AlertCircle className="h-7 w-7" />
              </div>
              <div className="space-y-1">
                <h3 className="text-base font-bold text-rose-600 dark:text-rose-400">
                  Course Enrollment Required
                </h3>
                <p className="text-sm font-semibold text-slate-900 dark:text-white">
                  You are not registered yet for any course. Please contact administrator to enroll in the course.
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Attendance cannot be recorded without an active course registration assigned by the institution.
                </p>
              </div>
            </div>

            <a href="mailto:admin@gqt.com?subject=Course%20Enrollment%20Request">
              <Button variant="danger" size="sm" className="whitespace-nowrap">
                <Mail className="h-4 w-4 mr-1.5" />
                <span>Contact Administrator</span>
              </Button>
            </a>
          </div>
        </div>
      )}

      {/* Main Grid: Student Digital QR Pass on Left, Telemetry & Stats on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Student QR Card */}
        <div className="lg:col-span-5 space-y-6">
          <Card className="p-6 sm:p-7 bg-white dark:bg-surface-900 border-slate-200 dark:border-surface-800 shadow-xl shadow-brand-500/5 text-center">
            <div className="flex items-center justify-between mb-5">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Official Digital ID Pass
              </span>
              <Badge variant={isAttendanceHealthy ? "success" : "warning"} size="sm">
                {isAttendanceHealthy ? "Good Standing" : "Low Attendance"}
              </Badge>
            </div>

            {/* QR Code Container */}
            {hasCourse ? (
              <div className="relative mx-auto inline-block rounded-3xl p-5 bg-white border-2 border-slate-200 dark:border-surface-700 shadow-xl shadow-brand-500/10 mb-5">
                <QRCodeSVG
                  id="attendance-page-qrcode-svg"
                  value={qrPayload}
                  size={200}
                  level="H"
                  includeMargin={false}
                  bgColor="#ffffff"
                  fgColor="#0f172a"
                />
                {/* Visual Corner Markers */}
                <div className="pointer-events-none absolute -top-1.5 -left-1.5 h-6 w-6 border-t-4 border-l-4 border-brand-500 rounded-tl-lg" />
                <div className="pointer-events-none absolute -top-1.5 -right-1.5 h-6 w-6 border-t-4 border-r-4 border-brand-500 rounded-tr-lg" />
                <div className="pointer-events-none absolute -bottom-1.5 -left-1.5 h-6 w-6 border-b-4 border-l-4 border-brand-500 rounded-bl-lg" />
                <div className="pointer-events-none absolute -bottom-1.5 -right-1.5 h-6 w-6 border-b-4 border-r-4 border-brand-500 rounded-br-lg" />
              </div>
            ) : (
              <div className="mx-auto flex h-48 w-48 items-center justify-center rounded-3xl bg-rose-500/10 border-2 border-dashed border-rose-500/30 text-rose-500 mb-5">
                <div className="text-center p-4">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                  <p className="text-xs font-bold">QR Disabled</p>
                  <p className="text-[10px] text-slate-500 dark:text-slate-400 font-medium">Not Enrolled</p>
                </div>
              </div>
            )}

            {/* Verified Credentials */}
            <div className="rounded-2xl bg-slate-50 dark:bg-surface-950/70 p-4 border border-slate-200 dark:border-surface-800 text-left space-y-2 mb-5">
              <div className="flex items-center justify-between">
                <span className="font-extrabold text-slate-900 dark:text-white text-sm">{fullName}</span>
                <Badge variant="indigo" size="sm" className="font-mono">
                  {batchCode}
                </Badge>
              </div>

              <div className="flex justify-between text-xs pt-1 border-t border-slate-200/60 dark:border-surface-800/60">
                <span className="text-slate-500 dark:text-slate-400">Student ID / USN:</span>
                <span className="font-mono font-bold text-brand-600 dark:text-brand-400">{studentId}</span>
              </div>

              <div className="flex justify-between text-xs">
                <span className="text-slate-500 dark:text-slate-400">Course Opted:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200 truncate max-w-[180px]">
                  {courseName}
                </span>
              </div>

              <div className="flex justify-between text-xs">
                <span className="text-slate-500 dark:text-slate-400">College / Center:</span>
                <span className="text-slate-600 dark:text-slate-300 truncate max-w-[180px]">{collegeName}</span>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopyId}
                className="flex-1 flex items-center justify-center gap-1.5 text-xs"
              >
                {isCopied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                <span>{isCopied ? "Copied!" : "Copy USN"}</span>
              </Button>

              <Button
                variant="primary"
                size="sm"
                onClick={handleDownloadQR}
                disabled={!hasCourse}
                className="flex-1 flex items-center justify-center gap-1.5 text-xs shadow-md shadow-brand-500/20"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Save QR Code</span>
              </Button>
            </div>
          </Card>
        </div>

        {/* Right Column: Attendance Telemetry & Performance */}
        <div className="lg:col-span-7 space-y-6">
          {/* KPI Stat Cards */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Card className="p-4 border-slate-200 dark:border-surface-800">
              <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase">
                Attendance Rate
              </span>
              <div className="mt-1 flex items-baseline gap-1">
                <span className="text-2xl font-black text-brand-600 dark:text-brand-400 font-mono">
                  {attendancePct}%
                </span>
              </div>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">Institutional requirement: 75%</p>
            </Card>

            <Card className="p-4 border-slate-200 dark:border-surface-800">
              <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 uppercase">
                Attended (✓)
              </span>
              <div className="mt-1 flex items-baseline gap-1">
                <span className="text-2xl font-black text-emerald-600 dark:text-emerald-400 font-mono">
                  {attendanceData?.attended_classes || 0}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">Days</span>
              </div>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">Sessions present</p>
            </Card>

            <Card className="p-4 border-slate-200 dark:border-surface-800">
              <span className="text-[11px] font-semibold text-rose-600 dark:text-rose-400 uppercase">
                Missed (✗)
              </span>
              <div className="mt-1 flex items-baseline gap-1">
                <span className="text-2xl font-black text-rose-600 dark:text-rose-400 font-mono">
                  {attendanceData?.missed_classes || 0}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">Days</span>
              </div>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">Absence records</p>
            </Card>

            <Card className="p-4 border-slate-200 dark:border-surface-800">
              <span className="text-[11px] font-semibold text-amber-500 uppercase">
                Learning Streak
              </span>
              <div className="mt-1 flex items-baseline gap-1">
                <span className="text-2xl font-black text-amber-500 font-mono">
                  {attendanceData?.current_streak_days || 0}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">Days</span>
              </div>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">Consecutive activity</p>
            </Card>
          </div>

          {/* Technology Filter Tabs */}
          <Card className="p-6 bg-white dark:bg-surface-900 border-slate-200 dark:border-surface-800 shadow-xl shadow-brand-500/5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Layers className="h-4 w-4 text-brand-500" />
                  <span>Session History by Technology</span>
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Select a technology track to inspect daily present/absent logs
                </p>
              </div>

              {/* Status Filter */}
              <div className="flex items-center gap-2">
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-800 px-3 py-1.5 text-xs font-semibold text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="PRESENT">✓ Present Only</option>
                  <option value="ABSENT">✗ Absent Only</option>
                  <option value="LATE">⏱ Late Only</option>
                </select>
              </div>
            </div>

            {/* Horizontal Technology Tabs */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none mb-5">
              {availableTechnologies.map((tech) => {
                const isSelected = selectedTech === tech.id;
                return (
                  <button
                    key={tech.id}
                    onClick={() => setSelectedTech(tech.id)}
                    className={`whitespace-nowrap px-3 py-1 rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5 ${
                      isSelected
                        ? "bg-brand-600 text-white shadow-sm shadow-brand-600/30"
                        : "bg-slate-100 dark:bg-surface-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-surface-700"
                    }`}
                  >
                    <span>{tech.name}</span>
                  </button>
                );
              })}
            </div>

            {/* Table */}
            <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-surface-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-surface-950/80 text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-surface-800 font-semibold uppercase">
                  <tr>
                    <th className="py-3 px-3">Date</th>
                    <th className="py-3 px-3">Technology</th>
                    <th className="py-3 px-3">Session</th>
                    <th className="py-3 px-3">Status</th>
                    <th className="py-3 px-3 text-right">Remarks</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-surface-800 text-slate-700 dark:text-slate-300">
                  {filteredRecords.length > 0 ? (
                    filteredRecords.map((rec) => (
                      <tr key={rec.id} className="hover:bg-slate-50/80 dark:hover:bg-surface-800/40 transition-colors">
                        <td className="py-3 px-3 font-mono font-medium text-slate-900 dark:text-white whitespace-nowrap">
                          {rec.date}
                        </td>
                        <td className="py-3 px-3 font-semibold text-slate-900 dark:text-slate-100">
                          {rec.technology || "Full Stack Development"}
                        </td>
                        <td className="py-3 px-3 text-slate-600 dark:text-slate-300">
                          {rec.session_title}
                        </td>
                        <td className="py-3 px-3">
                          {rec.status === "PRESENT" && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">
                              <CheckCircle2 className="h-3 w-3" />
                              <span>✓ Present</span>
                            </span>
                          )}
                          {rec.status === "ABSENT" && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-bold bg-rose-500/15 text-rose-600 dark:text-rose-400">
                              <XCircle className="h-3 w-3" />
                              <span>✗ Absent</span>
                            </span>
                          )}
                          {rec.status === "LATE" && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400">
                              <Clock className="h-3 w-3" />
                              <span>Late</span>
                            </span>
                          )}
                          {rec.status === "EXCUSED" && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-bold bg-cyan-500/15 text-cyan-600 dark:text-cyan-400">
                              <span>Excused</span>
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-3 text-right text-slate-500 dark:text-slate-400 italic">
                          {rec.remarks || "Verified via QR Terminal"}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="py-10 text-center text-slate-500 dark:text-slate-400">
                        <Calendar className="h-7 w-7 mx-auto mb-1.5 text-slate-300 dark:text-slate-600" />
                        <p className="font-semibold text-xs text-slate-700 dark:text-slate-300">
                          No attendance records found for {selectedTech === "ALL" ? "your account" : selectedTech}.
                        </p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
