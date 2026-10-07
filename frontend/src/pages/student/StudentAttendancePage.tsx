import React, { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import { Html5Qrcode, Html5QrcodeSupportedFormats } from "html5-qrcode";
import {
  QrCode,
  Camera,
  CheckCircle2,
  AlertCircle,
  Calendar,
  Sparkles,
  ShieldCheck,
  RefreshCw,
  Search,
  Copy,
  Check,
  Zap,
  Flame,
  BookOpen,
  Upload,
  ArrowRight,
} from "lucide-react";
import { studentApi, ScanAttendanceQRResponse } from "../../api/studentApi";
import { useAuthStore } from "../../store/authStore";
import { useToast } from "../../context/ToastContext";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { BrandLogo } from "../../components/common/BrandLogo";

export const StudentAttendancePage: React.FC = () => {
  const queryClient = useQueryClient();
  const { user, studentProfile } = useAuthStore();
  const { success: toastSuccess, error: toastError, info: toastInfo } = useToast();

  const [activeTab, setActiveTab] = useState<"scan" | "pass" | "history">("scan");
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [manualCode, setManualCode] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [scanResult, setScanResult] = useState<ScanAttendanceQRResponse | null>(null);
  const [notEnrolledError, setNotEnrolledError] = useState<string | null>(null);
  const [isCopied, setIsCopied] = useState(false);
  const [showDemoProjector, setShowDemoProjector] = useState(false);
  const demoSessionTitle = "Daily Training & Coding Lab";

  const scannerRef = useRef<Html5Qrcode | null>(null);
  const scannerContainerId = "gqt-qr-reader";

  // 1. Fetch Attendance Telemetry
  const {
    data: attendanceData,
    isLoading: isLoadingData,
    refetch: refetchAttendance,
  } = useQuery({
    queryKey: ["student", "attendance"],
    queryFn: studentApi.getAttendanceTelemetry,
    staleTime: 1000 * 30, // 30s fresh
  });

  // 2. Scan Attendance Mutation
  const scanMutation = useMutation({
    mutationFn: studentApi.scanAttendanceQR,
    onSuccess: (data) => {
      setScanResult(data);
      setNotEnrolledError(null);
      queryClient.invalidateQueries({ queryKey: ["student", "attendance"] });
      queryClient.invalidateQueries({ queryKey: ["student", "dashboard"] });

      if (data.is_already_marked) {
        toastInfo("Attendance Already Logged", data.message);
      } else {
        toastSuccess("Attendance Marked!", data.message);
      }
      stopCamera();
    },
    onError: (err: any) => {
      const errMsg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.message ||
        "Failed to record attendance from scanned QR.";

      // Check for Course Registration / Enrollment issue
      if (
        errMsg.toLowerCase().includes("not registered yet for any course") ||
        errMsg.toLowerCase().includes("contact administrator to enroll") ||
        err?.response?.data?.error?.code === "NO_COURSE_ENROLLMENT"
      ) {
        setNotEnrolledError(
          "You are not registered yet for any course. Please contact administrator to enroll in the course."
        );
        toastError("Course Enrollment Required", "You are not registered yet for any course. Please contact administrator to enroll in the course.");
      } else {
        toastError("Scan Error", errMsg);
      }
      stopCamera();
    },
  });

  // Start Live Camera QR Code Scanner
  const startCamera = async () => {
    setCameraError(null);
    setScanResult(null);
    setNotEnrolledError(null);

    try {
      if (!scannerRef.current) {
        scannerRef.current = new Html5Qrcode(scannerContainerId, {
          formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE],
          verbose: false,
        });
      }

      setIsCameraActive(true);

      const config = {
        fps: 15,
        qrbox: { width: 250, height: 250 },
        aspectRatio: 1.0,
      };

      await scannerRef.current.start(
        { facingMode: "environment" },
        config,
        (decodedText) => {
          handleDecodedQR(decodedText);
        },
        () => {
          // Frame parse error / scanning
        }
      );
    } catch (err: any) {
      setIsCameraActive(false);
      const msg =
        err?.message ||
        "Unable to access camera. Please check camera permissions in your browser or try file upload / manual code.";
      setCameraError(msg);
      toastError("Camera Access Failed", msg);
    }
  };

  // Stop Live Camera
  const stopCamera = async () => {
    if (scannerRef.current && isCameraActive) {
      try {
        await scannerRef.current.stop();
      } catch (err) {
        // Ignore stop error
      }
      setIsCameraActive(false);
    }
  };

  // Handle QR Decoding
  const handleDecodedQR = (decodedText: string) => {
    if (!decodedText || scanMutation.isPending) return;

    // Check if student has active course
    if (attendanceData?.student && !attendanceData.student.has_enrollments) {
      setNotEnrolledError(
        "You are not registered yet for any course. Please contact administrator to enroll in the course."
      );
      toastError(
        "Registration Missing",
        "You are not registered yet for any course. Please contact administrator to enroll in the course."
      );
      stopCamera();
      return;
    }

    scanMutation.mutate({ qr_data: decodedText });
  };

  // Handle Image File Upload Scan
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setCameraError(null);
    setScanResult(null);
    setNotEnrolledError(null);

    try {
      const html5QrCode = new Html5Qrcode("gqt-qr-file-reader");
      const decodedText = await html5QrCode.scanFile(file, true);
      handleDecodedQR(decodedText);
    } catch (err: any) {
      toastError("QR Not Recognized", "Could not find a valid QR Code in the uploaded image.");
    }
  };

  // Handle Manual Code Submit
  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualCode.trim()) return;

    if (attendanceData?.student && !attendanceData.student.has_enrollments) {
      setNotEnrolledError(
        "You are not registered yet for any course. Please contact administrator to enroll in the course."
      );
      toastError(
        "Enrollment Required",
        "You are not registered yet for any course. Please contact administrator to enroll in the course."
      );
      return;
    }

    scanMutation.mutate({ qr_data: manualCode.trim(), session_code: manualCode.trim() });
    setManualCode("");
  };

  // Copy Digital ID QR Data
  const copyQRData = () => {
    if (attendanceData?.student_qr_data) {
      navigator.clipboard.writeText(attendanceData.student_qr_data);
      setIsCopied(true);
      toastSuccess("Copied", "Digital ID QR payload copied to clipboard.");
      setTimeout(() => setIsCopied(false), 2000);
    }
  };

  // Clean up camera on unmount
  useEffect(() => {
    return () => {
      if (scannerRef.current && scannerRef.current.isScanning) {
        scannerRef.current.stop().catch(() => {});
      }
    };
  }, []);

  // Filter attendance records
  const filteredRecords = (attendanceData?.records || []).filter((r) => {
    const matchesSearch =
      r.session_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.date.includes(searchQuery) ||
      (r.remarks && r.remarks.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesStatus = statusFilter === "ALL" || r.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const studentName =
    attendanceData?.student?.full_name ||
    studentProfile?.full_name ||
    user?.email ||
    "Student";

  const studentId =
    attendanceData?.student?.student_id ||
    studentProfile?.student_id_number ||
    "GQT-STUDENT";

  const batchCode =
    attendanceData?.student?.batch_code ||
    studentProfile?.batch_code ||
    "BATCH-2026";

  const courseName =
    attendanceData?.student?.course_name ||
    (studentProfile as any)?.course_opted ||
    (studentProfile as any)?.course_name ||
    "Full Stack Software Development";

  const attendancePct = attendanceData?.attendance_percentage ?? 100.0;
  const isAttendanceHealthy = attendancePct >= 75.0;

  // Demo session QR payload for testing faculty projection
  const demoQrPayload = JSON.stringify({
    type: "GQT_CLASS_SESSION",
    session_title: demoSessionTitle,
    course_name: courseName,
    date: new Date().toISOString().split("T")[0],
    code: `GQT-${Date.now().toString(36).toUpperCase()}`,
  });

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* 1. Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand-500/10 text-brand-600 dark:text-brand-400">
              <QrCode className="h-5 w-5" />
            </span>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              QR Code Attendance
            </h1>
          </div>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Scan lecture QR codes to mark class attendance, display your student ID, and track attendance streaks.
          </p>
        </div>

        {/* Tab Selector */}
        <div className="flex rounded-2xl bg-slate-100 dark:bg-surface-900 p-1.5 border border-slate-200 dark:border-surface-800">
          <button
            onClick={() => {
              setActiveTab("scan");
              stopCamera();
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === "scan"
                ? "bg-white dark:bg-surface-800 text-brand-600 dark:text-brand-400 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <Camera className="h-4 w-4" />
            <span>Scan QR Code</span>
          </button>

          <button
            onClick={() => {
              setActiveTab("pass");
              stopCamera();
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === "pass"
                ? "bg-white dark:bg-surface-800 text-brand-600 dark:text-brand-400 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <ShieldCheck className="h-4 w-4" />
            <span>My Digital Pass</span>
          </button>

          <button
            onClick={() => {
              setActiveTab("history");
              stopCamera();
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === "history"
                ? "bg-white dark:bg-surface-800 text-brand-600 dark:text-brand-400 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <Calendar className="h-4 w-4" />
            <span>Attendance Logs</span>
          </button>
        </div>
      </div>

      {/* 2. Top Stats Overview Bar */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Attendance Percentage */}
        <Card className="p-5 relative overflow-hidden bg-gradient-to-br from-white to-slate-50 dark:from-surface-900 dark:to-surface-950 border-slate-200 dark:border-surface-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Attendance Rate
            </span>
            <Badge variant={isAttendanceHealthy ? "success" : "danger"} size="sm">
              {isAttendanceHealthy ? "Above Target" : "Below 75%"}
            </Badge>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
              {attendancePct.toFixed(1)}%
            </span>
            <span className="text-xs text-slate-500">Target: 75%</span>
          </div>
          <div className="mt-3 h-2 w-full rounded-full bg-slate-100 dark:bg-surface-800 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                isAttendanceHealthy ? "bg-emerald-500" : "bg-rose-500"
              }`}
              style={{ width: `${Math.min(100, Math.max(0, attendancePct))}%` }}
            />
          </div>
        </Card>

        {/* Total Classes Attended */}
        <Card className="p-5 bg-gradient-to-br from-white to-slate-50 dark:from-surface-900 dark:to-surface-950 border-slate-200 dark:border-surface-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Classes Attended
            </span>
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-500">
              <CheckCircle2 className="h-4 w-4" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 dark:text-white">
              {attendanceData?.attended_classes ?? 0}
            </span>
            <span className="text-xs text-slate-500">
              / {attendanceData?.total_classes ?? 0} Total Sessions
            </span>
          </div>
          <p className="mt-2 text-[11px] text-slate-500 dark:text-slate-400">
            Verified classroom & lab sessions
          </p>
        </Card>

        {/* Current Active Streak */}
        <Card className="p-5 bg-gradient-to-br from-white to-slate-50 dark:from-surface-900 dark:to-surface-950 border-slate-200 dark:border-surface-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Daily Streak
            </span>
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-500/10 text-amber-500">
              <Flame className="h-4 w-4 fill-amber-500 animate-pulse" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 dark:text-white">
              {attendanceData?.current_streak_days ?? studentProfile?.current_streak_days ?? 0}
            </span>
            <span className="text-xs text-slate-500">Days Active</span>
          </div>
          <p className="mt-2 text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
            +5 Points per consecutive attendance
          </p>
        </Card>

        {/* Registered Course Track */}
        <Card className="p-5 bg-gradient-to-br from-white to-slate-50 dark:from-surface-900 dark:to-surface-950 border-slate-200 dark:border-surface-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Registered Course
            </span>
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-500">
              <BookOpen className="h-4 w-4" />
            </span>
          </div>
          <div className="mt-3">
            <div className="font-bold text-sm text-slate-900 dark:text-white truncate" title={courseName}>
              {courseName}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Batch: <span className="font-mono font-semibold text-brand-600 dark:text-brand-400">{batchCode}</span>
            </div>
          </div>
        </Card>
      </div>

      {/* 3. Not Registered / No Course Warning Notice */}
      {notEnrolledError && (
        <div className="rounded-3xl border-2 border-rose-500/40 bg-rose-50/90 dark:bg-rose-950/40 p-6 shadow-xl shadow-rose-500/5 backdrop-blur-md animate-bounceOnce">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-rose-500/15 text-rose-600 dark:text-rose-400">
                <AlertCircle className="h-7 w-7" />
              </div>
              <div>
                <h2 className="text-base font-bold text-rose-900 dark:text-rose-200">
                  Course Enrollment Required
                </h2>
                <p className="mt-1 text-sm text-rose-700 dark:text-rose-300 font-medium">
                  {notEnrolledError}
                </p>
                <p className="mt-2 text-xs text-rose-600/80 dark:text-rose-400/80">
                  Only enrolled students with verified batch access can log attendance for scheduled classroom sessions.
                </p>
              </div>
            </div>

            <Link to="/contact">
              <Button variant="danger" className="shrink-0 shadow-lg shadow-rose-600/20">
                <span>Contact Administrator</span>
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      )}

      {/* 4. TAB 1: Live QR Scanner & Manual Verification */}
      {activeTab === "scan" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Main Scanner Card (Left Column) */}
          <div className="lg:col-span-7 space-y-6">
            <Card className="p-6 sm:p-8 bg-white dark:bg-surface-900 border-slate-200 dark:border-surface-800 shadow-xl shadow-brand-500/5">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <Camera className="h-5 w-5 text-brand-600 dark:text-brand-400" />
                    <span>Live QR Code Scanner</span>
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Align the instructor or lecture projector QR code within the frame
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <Badge variant={isCameraActive ? "success" : "neutral"}>
                    {isCameraActive ? "Camera Active" : "Standby"}
                  </Badge>
                </div>
              </div>

              {/* Viewport Area */}
              <div className="relative rounded-2xl border-2 border-dashed border-slate-300 dark:border-surface-700 bg-slate-950 overflow-hidden flex flex-col items-center justify-center min-h-[320px]">
                {/* HTML5 QR Camera Element */}
                <div id={scannerContainerId} className={`w-full ${isCameraActive ? "block" : "hidden"}`} />

                {/* Hidden image file reader container */}
                <div id="gqt-qr-file-reader" className="hidden" />

                {/* Standby State UI */}
                {!isCameraActive && !scanMutation.isPending && (
                  <div className="text-center p-8 space-y-4">
                    <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-brand-500/10 text-brand-500 ring-8 ring-brand-500/5">
                      <QrCode className="h-8 w-8" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white">Camera is currently paused</h4>
                      <p className="mt-1 text-xs text-slate-400 max-w-xs mx-auto">
                        Click below to launch your device camera and scan the classroom attendance QR code.
                      </p>
                    </div>
                    <Button onClick={startCamera} className="shadow-lg shadow-brand-600/30">
                      <Camera className="h-4 w-4 mr-2" />
                      <span>Start Camera Scanner</span>
                    </Button>
                  </div>
                )}

                {/* Loading State when decoding */}
                {scanMutation.isPending && (
                  <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-slate-950/80 backdrop-blur-sm p-6 text-center space-y-3">
                    <RefreshCw className="h-10 w-10 animate-spin text-brand-500" />
                    <div className="text-white font-bold text-sm">Verifying QR & Recording Attendance...</div>
                    <p className="text-xs text-slate-400">Validating student profile and course registration</p>
                  </div>
                )}

                {/* Camera Active Controls Bar */}
                {isCameraActive && (
                  <div className="absolute bottom-4 inset-x-4 z-20 flex items-center justify-between rounded-xl bg-slate-900/90 p-2.5 backdrop-blur-md text-xs text-white">
                    <span className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
                      Scanning for QR code...
                    </span>
                    <button
                      onClick={stopCamera}
                      className="px-3 py-1 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-medium transition-colors"
                    >
                      Stop Camera
                    </button>
                  </div>
                )}
              </div>

              {/* Camera Error Display */}
              {cameraError && (
                <div className="mt-4 flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-50 dark:bg-amber-950/30 p-3.5 text-xs text-amber-800 dark:text-amber-200">
                  <AlertCircle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold">Camera issue:</span> {cameraError}
                  </div>
                </div>
              )}

              {/* Alternative Input Options: File Upload & Manual Code */}
              <div className="mt-6 pt-6 border-t border-slate-200 dark:border-surface-800 grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* File Upload Option */}
                <label className="flex flex-col items-center justify-center p-4 rounded-2xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-950/60 hover:bg-slate-100 dark:hover:bg-surface-800/80 cursor-pointer transition-colors text-center group">
                  <Upload className="h-5 w-5 text-slate-500 dark:text-slate-400 group-hover:text-brand-500 mb-1.5 transition-colors" />
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                    Upload QR Screenshot
                  </span>
                  <span className="text-[10px] text-slate-500">Scan from saved photo/gallery</span>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </label>

                {/* Faculty Projector Mode Simulation */}
                <button
                  type="button"
                  onClick={() => setShowDemoProjector((prev) => !prev)}
                  className="flex flex-col items-center justify-center p-4 rounded-2xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-950/60 hover:bg-slate-100 dark:hover:bg-surface-800/80 transition-colors text-center group"
                >
                  <Sparkles className="h-5 w-5 text-indigo-500 mb-1.5 transition-colors" />
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                    {showDemoProjector ? "Hide Test QR" : "Show Session QR"}
                  </span>
                  <span className="text-[10px] text-slate-500">Project class session code</span>
                </button>
              </div>

              {/* Manual Session Code Input */}
              <form onSubmit={handleManualSubmit} className="mt-4 pt-4 border-t border-slate-200 dark:border-surface-800 flex gap-2">
                <input
                  type="text"
                  value={manualCode}
                  onChange={(e) => setManualCode(e.target.value)}
                  placeholder="Or enter Session Code (e.g. GQT-CLASS-2026)"
                  className="flex-1 rounded-xl border border-slate-300 dark:border-surface-700 bg-white dark:bg-surface-950 px-3.5 py-2 text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                />
                <Button type="submit" variant="secondary" size="sm" isLoading={scanMutation.isPending}>
                  Submit Code
                </Button>
              </form>
            </Card>

            {/* Simulated Session Projector QR (For Classroom Display / Instant Testing) */}
            {showDemoProjector && (
              <Card className="p-6 bg-gradient-to-br from-indigo-900/10 via-white to-brand-50 dark:from-indigo-950/40 dark:via-surface-900 dark:to-brand-950/40 border-indigo-200 dark:border-indigo-900/50 shadow-xl animate-fadeIn">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600 text-white text-xs font-bold">
                      QR
                    </span>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                        Classroom Session QR Broadcast
                      </h3>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400">
                        Scan with your phone or camera to test instant attendance marking
                      </p>
                    </div>
                  </div>
                  <Badge variant="indigo" size="sm">
                    Live Broadcast
                  </Badge>
                </div>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-6 p-4 rounded-2xl bg-white dark:bg-surface-950 border border-slate-200 dark:border-surface-800">
                  <div className="p-3 bg-white rounded-2xl shadow-md ring-1 ring-slate-200">
                    <QRCodeSVG
                      value={demoQrPayload}
                      size={160}
                      level="H"
                      includeMargin={false}
                    />
                  </div>
                  <div className="space-y-2 text-center sm:text-left text-xs">
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Session</span>
                      <span className="font-semibold text-slate-900 dark:text-white">{demoSessionTitle}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Course</span>
                      <span className="font-semibold text-brand-600 dark:text-brand-400">{courseName}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Batch</span>
                      <span className="font-mono text-slate-700 dark:text-slate-300 font-bold">{batchCode}</span>
                    </div>
                    <Button
                      size="sm"
                      onClick={() => handleDecodedQR(demoQrPayload)}
                      isLoading={scanMutation.isPending}
                      className="mt-2 text-xs"
                    >
                      <Zap className="h-3.5 w-3.5 mr-1.5" />
                      <span>One-Click Self Mark</span>
                    </Button>
                  </div>
                </div>
              </Card>
            )}
          </div>

          {/* Right Column: Scan Result Confirmation or Student Summary Card */}
          <div className="lg:col-span-5 space-y-6">
            {/* Scan Success Celebration Card */}
            {scanResult ? (
              <Card className="p-6 sm:p-8 bg-gradient-to-b from-emerald-500/10 via-white to-slate-50 dark:from-emerald-950/30 dark:via-surface-900 dark:to-surface-950 border-emerald-500/30 shadow-2xl shadow-emerald-500/10 animate-bounceOnce">
                <div className="text-center space-y-3">
                  <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-emerald-500 text-white shadow-lg shadow-emerald-500/30 animate-pulse">
                    <CheckCircle2 className="h-9 w-9" />
                  </div>
                  <Badge variant="success" size="md" className="px-4 py-1 text-sm font-bold">
                    MARKED AS {scanResult.attendance.status}
                  </Badge>
                  <h3 className="text-xl font-extrabold text-slate-900 dark:text-white">
                    Attendance Recorded!
                  </h3>
                  <p className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                    {scanResult.message}
                  </p>
                </div>

                {/* Verified Telemetry Details */}
                <div className="mt-6 space-y-3 rounded-2xl bg-white/80 dark:bg-surface-950/80 p-4 border border-slate-200 dark:border-surface-800 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-100 dark:border-surface-800">
                    <span className="text-slate-500">Student Name:</span>
                    <span className="font-bold text-slate-900 dark:text-white">{scanResult.student.full_name}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100 dark:border-surface-800">
                    <span className="text-slate-500">Student ID / USN:</span>
                    <span className="font-mono font-bold text-brand-600 dark:text-brand-400">{scanResult.student.student_id}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100 dark:border-surface-800">
                    <span className="text-slate-500">Batch Code:</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">{scanResult.student.batch_code}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100 dark:border-surface-800">
                    <span className="text-slate-500">Course Opted:</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200 truncate max-w-[180px]">{scanResult.student.course_name}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100 dark:border-surface-800">
                    <span className="text-slate-500">Session Name:</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">{scanResult.attendance.session_title}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Logged Timestamp:</span>
                    <span className="font-mono text-slate-700 dark:text-slate-300">{scanResult.attendance.timestamp}</span>
                  </div>
                </div>

                <Button
                  onClick={() => setScanResult(null)}
                  variant="outline"
                  className="w-full mt-5"
                >
                  <span>Scan Another Class</span>
                </Button>
              </Card>
            ) : (
              /* Student Attendance Verification Summary */
              <Card className="p-6 bg-white dark:bg-surface-900 border-slate-200 dark:border-surface-800 shadow-xl shadow-brand-500/5 space-y-6">
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">
                    Attendance Policy & Guidelines
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Global Quest Technologies Academic Integrity
                  </p>
                </div>

                <div className="space-y-3 text-xs text-slate-600 dark:text-slate-300">
                  <div className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-50 dark:bg-surface-950/60 border border-slate-200 dark:border-surface-800">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                    <span>
                      <strong className="text-slate-900 dark:text-white">75% Mandatory Attendance:</strong> Required for placement drive eligibility and certification.
                    </span>
                  </div>

                  <div className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-50 dark:bg-surface-950/60 border border-slate-200 dark:border-surface-800">
                    <Flame className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                    <span>
                      <strong className="text-slate-900 dark:text-white">Consecutive Streaks:</strong> Daily class attendance accumulates streak multiplier points on the leaderboard.
                    </span>
                  </div>

                  <div className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-50 dark:bg-surface-950/60 border border-slate-200 dark:border-surface-800">
                    <ShieldCheck className="h-4 w-4 text-indigo-500 shrink-0 mt-0.5" />
                    <span>
                      <strong className="text-slate-900 dark:text-white">Single Verification:</strong> Each lecture session is marked once per student per day.
                    </span>
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-gradient-to-br from-brand-50 to-indigo-50 dark:from-brand-950/40 dark:to-surface-950 p-4 text-center">
                  <p className="text-xs font-semibold text-brand-700 dark:text-brand-300">
                    Need attendance adjustment or leave approval?
                  </p>
                  <Link to="/contact" className="inline-block mt-2 text-xs font-bold text-brand-600 dark:text-brand-400 hover:underline">
                    Submit Leave Request / Support Ticket &rarr;
                  </Link>
                </div>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* 5. TAB 2: Student Digital Pass & Personal ID QR */}
      {activeTab === "pass" && (
        <div className="max-w-2xl mx-auto space-y-6">
          <Card className="p-8 bg-gradient-to-b from-white via-slate-50 to-slate-100 dark:from-surface-900 dark:via-surface-900 dark:to-surface-950 border-slate-200 dark:border-surface-800 shadow-2xl relative overflow-hidden">
            {/* Ambient card top glow */}
            <div className="absolute top-0 inset-x-0 h-2 bg-gradient-to-r from-brand-500 via-indigo-500 to-emerald-500" />

            {/* Pass Header */}
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-surface-800 pb-5">
              <BrandLogo variant="full" size="md" subtitle="Official Student Identity" />
              <Badge variant="indigo" size="md" className="font-mono font-bold">
                {batchCode}
              </Badge>
            </div>

            {/* Main Pass Content */}
            <div className="mt-8 flex flex-col sm:flex-row items-center gap-8">
              {/* Crisp High-Res QR Code Card */}
              <div className="p-4 bg-white rounded-3xl shadow-xl ring-1 ring-slate-200/80 shrink-0 text-center space-y-2">
                <QRCodeSVG
                  value={attendanceData?.student_qr_data || JSON.stringify({ id: studentId, name: studentName, batch: batchCode })}
                  size={190}
                  level="H"
                  includeMargin={true}
                />
                <span className="text-[10px] font-mono text-slate-500 font-bold block">
                  SCAN FOR VERIFICATION
                </span>
              </div>

              {/* Student Metadata */}
              <div className="space-y-4 flex-1 text-center sm:text-left">
                <div>
                  <span className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Student Name</span>
                  <h2 className="text-xl font-extrabold text-slate-900 dark:text-white">
                    {studentName}
                  </h2>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Student ID</span>
                    <p className="font-mono font-bold text-brand-600 dark:text-brand-400">{studentId}</p>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Batch</span>
                    <p className="font-bold text-slate-800 dark:text-slate-200">{batchCode}</p>
                  </div>
                </div>

                <div>
                  <span className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Enrolled Track</span>
                  <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">{courseName}</p>
                </div>

                <div>
                  <span className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Institution / College</span>
                  <p className="text-xs text-slate-600 dark:text-slate-300">
                    {attendanceData?.student?.college_name || studentProfile?.college_name || "Global Quest Technologies Academy"}
                  </p>
                </div>
              </div>
            </div>

            {/* Pass Footer Actions */}
            <div className="mt-8 pt-5 border-t border-slate-200 dark:border-surface-800 flex items-center justify-between text-xs">
              <div className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-medium">
                <ShieldCheck className="h-4 w-4" />
                <span>Verified GQT Student Credential</span>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={copyQRData}
              >
                {isCopied ? <Check className="h-3.5 w-3.5 mr-1 text-emerald-500" /> : <Copy className="h-3.5 w-3.5 mr-1" />}
                <span>{isCopied ? "Copied!" : "Copy Token"}</span>
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* 6. TAB 3: Attendance History Logs */}
      {activeTab === "history" && (
        <Card className="p-6 bg-white dark:bg-surface-900 border-slate-200 dark:border-surface-800 shadow-xl shadow-brand-500/5 space-y-6">
          {/* Header & Search Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                Session Attendance History
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Complete verifiable record of all marked sessions and timestamps
              </p>
            </div>

            {/* Filters */}
            <div className="flex items-center gap-3">
              {/* Search Bar */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search session or date..."
                  className="rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 pl-9 pr-3 py-1.5 text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                />
              </div>

              {/* Status filter */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 px-3 py-1.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-none"
              >
                <option value="ALL">All Statuses</option>
                <option value="PRESENT">Present</option>
                <option value="LATE">Late</option>
                <option value="ABSENT">Absent</option>
                <option value="EXCUSED">Excused</option>
              </select>

              <Button
                variant="outline"
                size="sm"
                onClick={() => refetchAttendance()}
                isLoading={isLoadingData}
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>

          {/* Records Table */}
          <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-surface-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-surface-950/80 text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-surface-800 font-semibold">
                <tr>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Session Title</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Verification Remarks</th>
                  <th className="py-3 px-4 text-right">Recorded Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-surface-800 text-slate-700 dark:text-slate-300">
                {filteredRecords.length > 0 ? (
                  filteredRecords.map((rec) => (
                    <tr key={rec.id} className="hover:bg-slate-50/80 dark:hover:bg-surface-800/40 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-medium text-slate-900 dark:text-white">
                        {rec.date}
                      </td>
                      <td className="py-3.5 px-4 font-semibold text-slate-900 dark:text-slate-100">
                        {rec.session_title}
                      </td>
                      <td className="py-3.5 px-4">
                        <Badge
                          variant={
                            rec.status === "PRESENT"
                              ? "success"
                              : rec.status === "LATE"
                              ? "warning"
                              : rec.status === "EXCUSED"
                              ? "cyan"
                              : "danger"
                          }
                          size="sm"
                        >
                          {rec.status}
                        </Badge>
                      </td>
                      <td className="py-3.5 px-4 text-slate-500 dark:text-slate-400">
                        {rec.remarks || "Standard check-in"}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono text-[11px] text-slate-400">
                        {new Date(rec.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-slate-400">
                      <Calendar className="h-8 w-8 mx-auto mb-2 opacity-40" />
                      <p className="font-semibold">No attendance records found</p>
                      <p className="text-xs mt-1">Scan a lecture QR code to mark your first class attendance.</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};
