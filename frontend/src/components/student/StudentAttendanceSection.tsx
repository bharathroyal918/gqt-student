import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  QrCode,
  CheckCircle2,
  XCircle,
  Clock,
  Calendar,
  Layers,
  TrendingUp,
} from "lucide-react";
import { studentApi, StudentAttendanceData } from "../../api/studentApi";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { StudentQRCodeModal } from "./StudentQRCodeModal";

interface StudentAttendanceSectionProps {
  className?: string;
}

export const StudentAttendanceSection: React.FC<StudentAttendanceSectionProps> = ({
  className = "",
}) => {
  const [selectedTech, setSelectedTech] = useState<string>("ALL");
  const [isQRModalOpen, setIsQRModalOpen] = useState(false);

  // Fetch student attendance telemetry
  const { data: attendanceData } = useQuery<StudentAttendanceData>({
    queryKey: ["student", "attendance"],
    queryFn: studentApi.getAttendanceTelemetry,
    staleTime: 1000 * 30, // 30s fresh
  });

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

  // Filter records based on selected technology
  const filteredRecords = allRecords.filter((rec) => {
    if (selectedTech === "ALL") return true;
    const tech = rec.technology || rec.session_title || "";
    return (
      tech.toLowerCase().includes(selectedTech.toLowerCase()) ||
      selectedTech.toLowerCase().includes(tech.toLowerCase())
    );
  });

  // Calculate statistics for selected technology
  const totalClasses =
    filteredRecords.length > 0
      ? filteredRecords.length
      : selectedTech === "ALL"
      ? attendanceData?.total_classes || 0
      : 0;
  const presentClasses = filteredRecords.filter((r) => r.status === "PRESENT").length;
  const absentClasses = filteredRecords.filter((r) => r.status === "ABSENT").length;
  const lateClasses = filteredRecords.filter((r) => r.status === "LATE").length;

  const attendancePercentage =
    totalClasses > 0
      ? Math.round(((presentClasses + lateClasses) / totalClasses) * 1000) / 10
      : selectedTech === "ALL"
      ? attendanceData?.attendance_percentage ?? 100.0
      : 100.0;

  const isHealthy = attendancePercentage >= 75.0;

  return (
    <div className={`space-y-6 ${className}`}>
      {/* QR Code Popup Modal */}
      <StudentQRCodeModal
        isOpen={isQRModalOpen}
        onClose={() => setIsQRModalOpen(false)}
        attendanceData={attendanceData}
      />

      <Card className="p-6 sm:p-7 bg-white dark:bg-surface-900 border-slate-200 dark:border-surface-800 shadow-xl shadow-brand-500/5">
        {/* Module Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6 pb-5 border-b border-slate-200/80 dark:border-surface-800/80">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500/10 text-brand-600 dark:text-brand-400">
                <Calendar className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span>Daily Attendance & Technology Log</span>
                  <Badge
                    variant={isHealthy ? "success" : "warning"}
                    size="sm"
                    className="font-semibold text-[11px]"
                  >
                    {isHealthy ? "Eligible (>75%)" : "Low Attendance"}
                  </Badge>
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Real-time session records verified via QR Attendance scanning
                </p>
              </div>
            </div>
          </div>

          {/* Quick Action: Open Attendance QR Code Modal */}
          <div className="flex items-center gap-3">
            <Button
              onClick={() => setIsQRModalOpen(true)}
              className="flex items-center gap-2 shadow-md shadow-brand-500/20"
              size="sm"
            >
              <QrCode className="h-4 w-4" />
              <span>Show My Attendance QR</span>
            </Button>
          </div>
        </div>

        {/* Technology Filter Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none mb-6">
          {availableTechnologies.map((tech) => {
            const isSelected = selectedTech === tech.id;
            return (
              <button
                key={tech.id}
                onClick={() => setSelectedTech(tech.id)}
                className={`whitespace-nowrap px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5 ${
                  isSelected
                    ? "bg-brand-600 text-white shadow-md shadow-brand-600/25"
                    : "bg-slate-100 dark:bg-surface-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-surface-700"
                }`}
              >
                <Layers className={`h-3.5 w-3.5 ${isSelected ? "text-white" : "text-slate-400"}`} />
                <span>{tech.name}</span>
              </button>
            );
          })}
        </div>

        {/* KPI Stat Strip for Selected Technology */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 mb-6">
          {/* Present Count (✓) */}
          <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 dark:bg-emerald-950/20 p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">
                Present (✓)
              </span>
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-emerald-600 dark:text-emerald-400 font-mono">
                {presentClasses}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">Days</span>
            </div>
          </div>

          {/* Absent Count (✗) */}
          <div className="rounded-2xl border border-rose-500/20 bg-rose-500/5 dark:bg-rose-950/20 p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-rose-600 dark:text-rose-400 uppercase tracking-wider">
                Absent (✗)
              </span>
              <XCircle className="h-4 w-4 text-rose-500" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-rose-600 dark:text-rose-400 font-mono">
                {absentClasses}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">Days</span>
            </div>
          </div>

          {/* Total Classes */}
          <div className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900/50 p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                Total Sessions
              </span>
              <Calendar className="h-4 w-4 text-slate-400" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-slate-900 dark:text-white font-mono">
                {totalClasses}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">Recorded</span>
            </div>
          </div>

          {/* Attendance Percentage */}
          <div className="rounded-2xl border border-brand-500/20 bg-brand-500/5 dark:bg-brand-950/20 p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-brand-600 dark:text-brand-400 uppercase tracking-wider">
                Attendance Rate
              </span>
              <TrendingUp className="h-4 w-4 text-brand-500" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-brand-600 dark:text-brand-400 font-mono">
                {attendancePercentage}%
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">Average</span>
            </div>
          </div>
        </div>

        {/* Daily Attendance Grid & Table */}
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-surface-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-surface-950/80 text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-surface-800 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Technology / Subject</th>
                <th className="py-3 px-4">Session Title</th>
                <th className="py-3 px-4">Attendance Status</th>
                <th className="py-3 px-4 text-right">Remarks</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-surface-800 text-slate-700 dark:text-slate-300">
              {filteredRecords.length > 0 ? (
                filteredRecords.map((rec) => (
                  <tr key={rec.id} className="hover:bg-slate-50/80 dark:hover:bg-surface-800/40 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-medium text-slate-900 dark:text-white whitespace-nowrap">
                      {rec.date}
                    </td>

                    <td className="py-3.5 px-4 font-semibold text-slate-900 dark:text-slate-100">
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg text-[11px] bg-brand-500/10 text-brand-600 dark:text-brand-400 font-medium">
                        {rec.technology || "Full Stack Development"}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-slate-600 dark:text-slate-300">
                      {rec.session_title}
                    </td>

                    <td className="py-3.5 px-4">
                      {rec.status === "PRESENT" && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                          <span>✓ Present</span>
                        </span>
                      )}
                      {rec.status === "ABSENT" && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30">
                          <XCircle className="h-3.5 w-3.5 text-rose-500" />
                          <span>✗ Absent</span>
                        </span>
                      )}
                      {rec.status === "LATE" && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
                          <Clock className="h-3.5 w-3.5 text-amber-500" />
                          <span>Late</span>
                        </span>
                      )}
                      {rec.status === "EXCUSED" && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border border-cyan-500/30">
                          <span>Excused</span>
                        </span>
                      )}
                    </td>

                    <td className="py-3.5 px-4 text-right text-slate-500 dark:text-slate-400 italic">
                      {rec.remarks || "Verified via QR Terminal"}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-slate-500 dark:text-slate-400">
                    <Calendar className="h-8 w-8 mx-auto mb-2 text-slate-300 dark:text-slate-600" />
                    <p className="font-semibold text-sm text-slate-700 dark:text-slate-300">
                      No attendance records found for {selectedTech === "ALL" ? "your account" : selectedTech}.
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      Present your attendance QR code during classroom sessions to log your daily record.
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
