import React, { useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import {
  QrCode,
  Check,
  Copy,
  Download,
  AlertCircle,
  X,
  Mail,
  User,
} from "lucide-react";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { useAuthStore } from "../../store/authStore";
import { StudentAttendanceData } from "../../api/studentApi";

interface StudentQRCodeModalProps {
  isOpen: boolean;
  onClose: () => void;
  attendanceData?: StudentAttendanceData | null;
}

export const StudentQRCodeModal: React.FC<StudentQRCodeModalProps> = ({
  isOpen,
  onClose,
  attendanceData,
}) => {
  const { user, studentProfile } = useAuthStore();
  const [copied, setCopied] = useState(false);

  // Student Details Resolution
  const fullName = attendanceData?.student?.full_name || studentProfile?.full_name || "Enrolled Student";
  const studentId = attendanceData?.student?.student_id || studentProfile?.student_id_number || "GQT-STUDENT";
  const batchCode = attendanceData?.student?.batch_code || studentProfile?.batch_code || "BATCH-2026";
  const collegeName = attendanceData?.student?.college_name || studentProfile?.college_name || "GQT Institute";
  const email = user?.email || "";

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
    (hasCourse ? "Full Stack Software Development" : "Not Enrolled");

  // QR Code Payload for Classroom Scanner / Admin Terminal
  const qrPayload = JSON.stringify({
    type: "STUDENT_ATTENDANCE_ID",
    student_id: studentId,
    full_name: fullName,
    batch_code: batchCode,
    course: courseName,
    college: collegeName,
    email: email,
  });

  const handleCopyId = () => {
    navigator.clipboard.writeText(studentId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadQR = () => {
    const svgElement = document.getElementById("student-attendance-qrcode-svg");
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

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="md" title="Student Attendance QR">
      <div className="relative p-6 sm:p-7 space-y-6 text-center">
        {/* Header Badge & Close */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand-500/10 text-brand-600 dark:text-brand-400">
              <QrCode className="h-4 w-4" />
            </span>
            <div className="text-left">
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Student Attendance QR
              </h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                Present this code to the instructor or scanner terminal
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-surface-800 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* NOT ENROLLED IN ANY COURSE GUARD */}
        {!hasCourse ? (
          <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-6 text-left space-y-4 animate-shake">
            <div className="flex items-start gap-3.5">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rose-500 text-white shadow-lg shadow-rose-500/30">
                <AlertCircle className="h-6 w-6" />
              </div>
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-rose-600 dark:text-rose-400">
                  Course Registration Required
                </h4>
                <p className="text-xs text-rose-700 dark:text-rose-300 font-medium leading-relaxed">
                  You are not registered yet for any course. Please contact administrator to enroll in the course.
                </p>
              </div>
            </div>

            <div className="rounded-xl bg-white/80 dark:bg-surface-900/80 p-3.5 border border-rose-200 dark:border-rose-900/50 text-xs space-y-1 text-slate-700 dark:text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-500">Student Name:</span>
                <span className="font-semibold">{fullName}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Student ID / USN:</span>
                <span className="font-mono font-bold text-rose-600 dark:text-rose-400">{studentId}</span>
              </div>
            </div>

            <div className="pt-2">
              <a href="mailto:admin@gqt.com?subject=Enrollment%20Request">
                <Button variant="danger" className="w-full">
                  <Mail className="h-4 w-4 mr-2" />
                  <span>Contact Administrator</span>
                </Button>
              </a>
            </div>
          </div>
        ) : (
          /* VERIFIED ENROLLED STUDENT QR CODE CARD */
          <div className="space-y-5">
            {/* High Definition QR Code Container */}
            <div className="relative mx-auto inline-block rounded-3xl p-5 bg-white border-2 border-slate-200 dark:border-surface-700 shadow-xl shadow-brand-500/10">
              <div className="relative">
                <QRCodeSVG
                  id="student-attendance-qrcode-svg"
                  value={qrPayload}
                  size={220}
                  level="H"
                  includeMargin={false}
                  bgColor="#ffffff"
                  fgColor="#0f172a"
                />
              </div>

              {/* Glowing Corner Scanner Markers */}
              <div className="pointer-events-none absolute -top-1.5 -left-1.5 h-6 w-6 border-t-4 border-l-4 border-brand-500 rounded-tl-lg" />
              <div className="pointer-events-none absolute -top-1.5 -right-1.5 h-6 w-6 border-t-4 border-r-4 border-brand-500 rounded-tr-lg" />
              <div className="pointer-events-none absolute -bottom-1.5 -left-1.5 h-6 w-6 border-b-4 border-l-4 border-brand-500 rounded-bl-lg" />
              <div className="pointer-events-none absolute -bottom-1.5 -right-1.5 h-6 w-6 border-b-4 border-r-4 border-brand-500 rounded-br-lg" />
            </div>

            {/* Verified Student Metadata */}
            <div className="rounded-2xl bg-slate-50 dark:bg-surface-900/80 p-4 border border-slate-200 dark:border-surface-800 text-left space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <User className="h-3.5 w-3.5 text-brand-500" />
                  <span className="font-bold text-slate-900 dark:text-white text-xs">{fullName}</span>
                </div>
                <Badge variant="indigo" size="sm" className="font-mono text-[10px]">
                  {batchCode}
                </Badge>
              </div>

              <div className="flex items-center justify-between pt-1 border-t border-slate-200/60 dark:border-surface-800/60 text-[11px]">
                <span className="text-slate-500">Student ID / USN:</span>
                <span className="font-mono font-bold text-brand-600 dark:text-brand-400">{studentId}</span>
              </div>

              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-500">Enrolled Course:</span>
                <span className="font-medium text-slate-900 dark:text-slate-200 truncate max-w-[200px]">
                  {courseName}
                </span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopyId}
                className="flex-1 flex items-center justify-center gap-1.5 text-xs"
              >
                {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                <span>{copied ? "Copied ID!" : "Copy ID"}</span>
              </Button>

              <Button
                variant="primary"
                size="sm"
                onClick={handleDownloadQR}
                className="flex-1 flex items-center justify-center gap-1.5 text-xs shadow-md shadow-brand-500/20"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Save QR Code</span>
              </Button>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};
