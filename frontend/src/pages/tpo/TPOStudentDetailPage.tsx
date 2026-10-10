import React from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  BookOpen,
  Calendar,
  Code2,
  Flame,
  FolderKanban,
  Percent,
} from "lucide-react";
import { tpoApi } from "../../api/tpoApi";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { UserAvatar } from "../../components/ui/UserAvatar";

export const TPOStudentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const {
    data: student,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["tpo-student-detail", id],
    queryFn: () => tpoApi.getStudentDetail(id!),
    enabled: !!id,
    staleTime: 60 * 1000,
  });

  if (isLoading) {
    return <LoadingState message="Loading student performance dossier..." />;
  }

  if (isError || !student) {
    return (
      <ErrorState
        title="Student Record Inaccessible"
        message={
          (error as any)?.response?.data?.error?.message ||
          "Student does not exist or does not belong to your assigned college."
        }
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Back Button */}
      <div>
        <Link
          to="/tpo/students"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white transition-colors"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Student Directory
        </Link>
      </div>

      {/* -------------------------------------------------------------------------- */}
      {/* 1. STUDENT PROFILE SUMMARY BANNER */}
      {/* -------------------------------------------------------------------------- */}
      <div className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <UserAvatar
              src={student.avatar_url}
              name={student.full_name}
              initials={student.full_name.slice(0, 2).toUpperCase()}
              size="lg"
            />
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
                  {student.full_name}
                </h1>
                <Badge variant={student.is_active ? "success" : "neutral"} size="sm">
                  {student.is_active ? "Active Student" : "Inactive / Suspended"}
                </Badge>
              </div>

              <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 dark:text-slate-400 font-medium">
                <span className="font-mono text-brand-600 dark:text-brand-400 font-bold">
                  {student.student_id_number}
                </span>
                <span>•</span>
                <span>{student.email}</span>
                <span>•</span>
                <span>{student.branch}</span>
                {student.graduation_year && (
                  <>
                    <span>•</span>
                    <span>Class of {student.graduation_year}</span>
                  </>
                )}
              </div>

              <div className="mt-2 text-xs text-slate-400">
                <span className="font-semibold text-slate-700 dark:text-slate-300">Track:</span>{" "}
                {student.course_opted} ({student.batch_code})
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4 bg-slate-50 dark:bg-surface-950 p-4 rounded-xl border border-slate-100 dark:border-surface-800">
            <div className="text-center px-2">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">
                Total Points
              </span>
              <span className="text-xl font-bold text-slate-900 dark:text-white">
                {student.total_points.toFixed(0)}
              </span>
            </div>
            <div className="h-8 w-px bg-slate-200 dark:bg-surface-800" />
            <div className="text-center px-2">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">
                Attendance
              </span>
              <span
                className={`text-xl font-bold ${
                  student.attendance_percentage >= 75
                    ? "text-emerald-600 dark:text-emerald-400"
                    : "text-rose-600 dark:text-rose-400"
                }`}
              >
                {student.attendance_percentage}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* -------------------------------------------------------------------------- */}
      {/* 2. STATS OVERVIEW CARDS */}
      {/* -------------------------------------------------------------------------- */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Streak */}
        <Card className="p-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase">
            <Flame className="h-4 w-4 text-amber-500" /> Current Streak
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900 dark:text-white">
              {student.current_streak_days}
            </span>
            <span className="text-xs text-slate-400">
              days (best: {student.highest_streak_days}d)
            </span>
          </div>
        </Card>

        {/* Classes Attended */}
        <Card className="p-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase">
            <Percent className="h-4 w-4 text-emerald-500" /> Classes Record
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900 dark:text-white">
              {student.attended_classes}
            </span>
            <span className="text-xs text-slate-400">/ {student.total_classes} attended</span>
          </div>
        </Card>

        {/* Assignments Score */}
        <Card className="p-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase">
            <Code2 className="h-4 w-4 text-blue-500" /> Assignment Pts
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900 dark:text-white">
              {student.score_breakdown?.ASSIGNMENT?.toFixed(0) || "0"}
            </span>
            <span className="text-xs text-slate-400">pts awarded</span>
          </div>
        </Card>

        {/* Projects Score */}
        <Card className="p-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 uppercase">
            <FolderKanban className="h-4 w-4 text-violet-500" /> Project Pts
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900 dark:text-white">
              {student.score_breakdown?.PROJECT?.toFixed(0) || "0"}
            </span>
            <span className="text-xs text-slate-400">pts awarded</span>
          </div>
        </Card>
      </div>

      {/* -------------------------------------------------------------------------- */}
      {/* 3. ENROLLED COURSES & RECENT SUBMISSIONS */}
      {/* -------------------------------------------------------------------------- */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Enrolled Courses */}
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <BookOpen className="h-4 w-4 text-brand-500" />
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Enrolled Curriculum Courses ({student.enrollments.length})
            </h3>
          </div>
          {student.enrollments.length === 0 ? (
            <p className="text-xs text-slate-400">No active course enrollments.</p>
          ) : (
            <div className="space-y-3">
              {student.enrollments.map((enr) => (
                <div
                  key={enr.id}
                  className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-surface-900/60 border border-slate-100 dark:border-surface-800/60 text-xs"
                >
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-white">
                      {enr.course_title}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      Enrolled: {new Date(enr.enrolled_at).toLocaleDateString()}
                    </div>
                  </div>
                  <Badge variant={enr.status === "ACTIVE" ? "brand" : "neutral"} size="sm">
                    {enr.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Recent Code Submissions */}
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <Code2 className="h-4 w-4 text-brand-500" />
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Recent Lab Submissions ({student.recent_submissions.length})
            </h3>
          </div>
          {student.recent_submissions.length === 0 ? (
            <p className="text-xs text-slate-400">No coding submissions recorded yet.</p>
          ) : (
            <div className="space-y-2.5">
              {student.recent_submissions.map((sub) => (
                <div
                  key={sub.id}
                  className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-surface-900/60 border border-slate-100 dark:border-surface-800/60 text-xs"
                >
                  <div className="min-w-0 flex-1 pr-3">
                    <div className="font-semibold text-slate-900 dark:text-white truncate">
                      {sub.question_title}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-2">
                      <span className="uppercase font-mono font-bold text-[10px] text-slate-500">
                        {sub.language}
                      </span>
                      <span>•</span>
                      <span>
                        {sub.passed_test_cases}/{sub.total_test_cases} tests passed
                      </span>
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                        sub.status === "ACCEPTED"
                          ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                          : "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                      }`}
                    >
                      {sub.status} (+{sub.score_awarded} pts)
                    </span>
                    <div className="text-[10px] text-slate-400 mt-1">
                      {new Date(sub.submitted_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* -------------------------------------------------------------------------- */}
      {/* 4. RECENT ATTENDANCE SESSIONS LOG */}
      {/* -------------------------------------------------------------------------- */}
      <Card className="p-5">
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="h-4 w-4 text-brand-500" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
            Recent Attendance Log ({student.recent_attendance.length} sessions)
          </h3>
        </div>
        {student.recent_attendance.length === 0 ? (
          <p className="text-xs text-slate-400">No session attendance records available.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
              <thead className="border-b border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-950 font-semibold uppercase text-slate-400">
                <tr>
                  <th className="px-4 py-2.5">Date</th>
                  <th className="px-4 py-2.5">Session / Module</th>
                  <th className="px-4 py-2.5">Technology</th>
                  <th className="px-4 py-2.5">Status</th>
                  <th className="px-4 py-2.5">Remarks</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-surface-800">
                {student.recent_attendance.map((att) => (
                  <tr key={att.id} className="hover:bg-slate-50 dark:hover:bg-surface-800/40">
                    <td className="px-4 py-3 font-mono font-medium">{att.date}</td>
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                      {att.session_title}
                    </td>
                    <td className="px-4 py-3 text-slate-500">{att.technology}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold ${
                          att.status === "PRESENT"
                            ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                            : att.status === "LATE"
                            ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                            : "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                        }`}
                      >
                        {att.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400">{att.remarks || "—"}</td>
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
