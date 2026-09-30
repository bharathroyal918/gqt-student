import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Trophy,
  Award,
  Flame,
  CheckCircle2,
  Plus,
  ShieldCheck,
  ShieldAlert,
  UserCheck,
  UserX,
  Calendar,
  Building,
  GraduationCap,
  Code2,
} from "lucide-react";
import { adminApi } from "../../api/adminApi";
import { CourseItem } from "../../types/admin";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { StatusDot } from "../../components/ui/StatusDot";
import { Card } from "../../components/ui/Card";
import { Modal } from "../../components/ui/Modal";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { useToast } from "../../context/ToastContext";

export const StudentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [activeTab, setActiveTab] = useState<"overview" | "progress" | "scores" | "rank">("overview");
  const [isEnrollModalOpen, setIsEnrollModalOpen] = useState(false);
  const [selectedCourseIds, setSelectedCourseIds] = useState<string[]>([]);

  // Queries
  const {
    data: student,
    isLoading: isStudentLoading,
    isError: isStudentError,
    refetch: refetchStudent,
  } = useQuery({
    queryKey: ["admin-student-detail", id],
    queryFn: () => adminApi.getStudentDetail(id!),
    enabled: Boolean(id),
  });

  const { data: progress } = useQuery({
    queryKey: ["admin-student-progress", id],
    queryFn: () => adminApi.getStudentProgress(id!),
    enabled: Boolean(id) && activeTab === "progress",
  });

  const { data: scores } = useQuery({
    queryKey: ["admin-student-scores", id],
    queryFn: () => adminApi.getStudentScores(id!),
    enabled: Boolean(id) && activeTab === "scores",
  });

  const { data: rank } = useQuery({
    queryKey: ["admin-student-rank", id],
    queryFn: () => adminApi.getStudentRank(id!),
    enabled: Boolean(id) && activeTab === "rank",
  });

  const { data: coursesData } = useQuery({
    queryKey: ["admin-all-courses-select"],
    queryFn: () => adminApi.getCourses({ page_size: 100 }),
    enabled: isEnrollModalOpen,
  });

  // Mutations
  const updateMutation = useMutation({
    mutationFn: (payload: any) => adminApi.updateStudent(id!, payload),
    onSuccess: () => {
      success("Status Updated", "Student profile updated successfully.");
      queryClient.invalidateQueries({ queryKey: ["admin-student-detail", id] });
      queryClient.invalidateQueries({ queryKey: ["admin-students"] });
    },
    onError: () => toastError("Update Failed", "Could not update student status."),
  });

  const enrollMutation = useMutation({
    mutationFn: (courseIds: string[]) => adminApi.assignCourses(id!, courseIds),
    onSuccess: () => {
      success("Enrollments Updated", "Courses have been assigned to student.");
      setIsEnrollModalOpen(false);
      setSelectedCourseIds([]);
      queryClient.invalidateQueries({ queryKey: ["admin-student-detail", id] });
    },
    onError: () => toastError("Enrollment Failed", "Could not update course enrollments."),
  });

  if (isStudentLoading) {
    return <LoadingState message="Loading student records..." />;
  }

  if (isStudentError || !student) {
    return (
      <ErrorState
        title="Student Not Found"
        message="Unable to locate student details. The account might have been removed."
        onRetry={() => refetchStudent()}
      />
    );
  }

  const handleToggleCourseSelect = (courseId: string) => {
    setSelectedCourseIds((prev) =>
      prev.includes(courseId) ? prev.filter((c) => c !== courseId) : [...prev, courseId]
    );
  };

  const openEnrollModal = () => {
    const existing = student.enrollments.map((e) => e.course_id);
    setSelectedCourseIds(existing);
    setIsEnrollModalOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Top back navigation */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate("/admin/students")}>
          <ArrowLeft className="h-4 w-4 mr-1.5" />
          Back to Students
        </Button>
      </div>

      {/* Header Profile Card */}
      <Card className="p-6">
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-indigo-600 text-2xl font-black text-white shadow-xl shadow-brand-500/20">
              {student.full_name.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl font-bold text-white">{student.full_name}</h1>
                <Badge variant="indigo">{student.batch_code}</Badge>
                <Badge
                  variant={
                    student.onboarding_status === "ACTIVE"
                      ? "emerald"
                      : student.onboarding_status === "PENDING_ACTIVATION"
                      ? "amber"
                      : "rose"
                  }
                >
                  {student.onboarding_status}
                </Badge>
              </div>

              <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-slate-400">
                <span className="font-mono text-slate-300">ID: {student.student_id_number}</span>
                <span>•</span>
                <span>{student.email || "No email"}</span>
                <span>•</span>
                <span>{student.mobile_number || "No mobile"}</span>
              </div>

              <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-slate-400">
                {student.college_name && (
                  <span className="flex items-center gap-1 text-slate-300">
                    <Building className="h-3.5 w-3.5" />
                    {student.college_name}
                  </span>
                )}
                {student.graduation_year && (
                  <span className="flex items-center gap-1">
                    <GraduationCap className="h-3.5 w-3.5" />
                    Class of {student.graduation_year}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Quick Action Badges / Controls */}
          <div className="flex flex-wrap items-center gap-2">
            <Button
              size="sm"
              variant="secondary"
              onClick={() =>
                updateMutation.mutate({
                  onboarding_status: student.onboarding_status === "ACTIVE" ? "SUSPENDED" : "ACTIVE",
                })
              }
              isLoading={updateMutation.isPending}
            >
              {student.onboarding_status === "ACTIVE" ? (
                <>
                  <ShieldAlert className="h-4 w-4 mr-1.5 text-amber-400" />
                  Revoke Access
                </>
              ) : (
                <>
                  <ShieldCheck className="h-4 w-4 mr-1.5 text-emerald-400" />
                  Grant Access
                </>
              )}
            </Button>

            <Button
              size="sm"
              variant="secondary"
              onClick={() => updateMutation.mutate({ is_active: !student.is_active })}
              isLoading={updateMutation.isPending}
            >
              {student.is_active ? (
                <>
                  <UserX className="h-4 w-4 mr-1.5 text-rose-400" />
                  Deactivate
                </>
              ) : (
                <>
                  <UserCheck className="h-4 w-4 mr-1.5 text-emerald-400" />
                  Activate
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Quick Highlights Bar */}
        <div className="mt-6 grid grid-cols-2 gap-4 border-t border-surface-800 pt-4 sm:grid-cols-4">
          <div className="rounded-xl bg-surface-900/60 p-3">
            <div className="text-xs text-slate-400">Total Points</div>
            <div className="text-lg font-bold text-amber-400">
              {parseFloat(student.total_points || "0").toLocaleString()} pts
            </div>
          </div>
          <div className="rounded-xl bg-surface-900/60 p-3">
            <div className="text-xs text-slate-400">Streak</div>
            <div className="text-lg font-bold text-rose-400 flex items-center gap-1">
              <Flame className="h-5 w-5" />
              {student.current_streak_days} days
            </div>
          </div>
          <div className="rounded-xl bg-surface-900/60 p-3">
            <div className="text-xs text-slate-400">Enrolled Courses</div>
            <div className="text-lg font-bold text-brand-400">
              {student.enrollments?.length || 0}
            </div>
          </div>
          <div className="rounded-xl bg-surface-900/60 p-3">
            <div className="text-xs text-slate-400">Account Status</div>
            <div className="text-sm font-semibold text-white flex items-center gap-1.5 mt-1">
              <StatusDot status={student.is_active ? "online" : "offline"} pulse={student.is_active} />
              {student.is_active ? "Active" : "Inactive"}
            </div>
          </div>
        </div>
      </Card>

      {/* Navigation Tabs */}
      <div className="flex border-b border-surface-800">
        <button
          onClick={() => setActiveTab("overview")}
          className={`px-5 py-3 text-sm font-medium border-b-2 transition-all ${
            activeTab === "overview"
              ? "border-brand-500 text-brand-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          Enrolled Courses
        </button>
        <button
          onClick={() => setActiveTab("progress")}
          className={`px-5 py-3 text-sm font-medium border-b-2 transition-all ${
            activeTab === "progress"
              ? "border-brand-500 text-brand-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          Curriculum Progress
        </button>
        <button
          onClick={() => setActiveTab("scores")}
          className={`px-5 py-3 text-sm font-medium border-b-2 transition-all ${
            activeTab === "scores"
              ? "border-brand-500 text-brand-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          Scores & Points Ledger
        </button>
        <button
          onClick={() => setActiveTab("rank")}
          className={`px-5 py-3 text-sm font-medium border-b-2 transition-all ${
            activeTab === "rank"
              ? "border-brand-500 text-brand-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          Leaderboard & Rank
        </button>
      </div>

      {/* Tab 1: Overview & Enrolled Courses */}
      {activeTab === "overview" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Assigned Course Track</h2>
            <Button size="sm" onClick={openEnrollModal}>
              <Plus className="h-4 w-4 mr-1.5" />
              Manage Enrollments
            </Button>
          </div>

          {student.enrollments.length === 0 ? (
            <EmptyState
              title="No Courses Assigned"
              description="This student is not currently enrolled in any curriculum tracks."
              actionLabel="Assign Courses"
              onAction={openEnrollModal}
            />
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {student.enrollments.map((enr) => (
                <Card key={enr.id} className="p-4 flex flex-col justify-between">
                  <div>
                    <div className="flex items-start justify-between gap-2">
                      <div className="font-semibold text-white text-base">{enr.course_title}</div>
                      <Badge
                        variant={enr.status === "ACTIVE" ? "emerald" : enr.status === "COMPLETED" ? "indigo" : "amber"}
                        size="sm"
                      >
                        {enr.status}
                      </Badge>
                    </div>
                    <div className="mt-3 text-xs text-slate-400 space-y-1">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="h-3.5 w-3.5 text-slate-500" />
                        <span>Enrolled: {new Date(enr.enrolled_at).toLocaleDateString()}</span>
                      </div>
                      {enr.completed_at && (
                        <div className="flex items-center gap-1.5 text-emerald-400">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          <span>Completed: {new Date(enr.completed_at).toLocaleDateString()}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Progress */}
      {activeTab === "progress" && (
        <div className="space-y-6">
          {progress ? (
            <>
              {/* Summary KPIs */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <Card className="p-4">
                  <div className="text-xs text-slate-400">Module Completion</div>
                  <div className="text-2xl font-bold text-white mt-1">
                    {progress.overview.module_completion_rate}%
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    {progress.overview.completed_modules} of {progress.overview.total_modules} modules
                  </div>
                </Card>

                <Card className="p-4">
                  <div className="text-xs text-slate-400">Question Solve Rate</div>
                  <div className="text-2xl font-bold text-emerald-400 mt-1">
                    {progress.overview.question_solve_rate}%
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    {progress.overview.solved_questions} of {progress.overview.total_questions} problems
                  </div>
                </Card>
              </div>

              {/* Modules breakdown */}
              <div className="space-y-3">
                <h3 className="text-base font-semibold text-white">Module Progression</h3>
                <div className="divide-y divide-surface-800 rounded-2xl border border-surface-800 bg-surface-900/60 overflow-hidden">
                  {progress.modules.map((m) => (
                    <div key={m.module_id} className="p-4 flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-white text-sm">{m.module_title}</div>
                        <div className="text-xs text-slate-400">{m.course_title}</div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-xs text-slate-300 font-mono">Score: {m.score_percentage}%</span>
                        <Badge
                          variant={
                            m.status === "COMPLETED"
                              ? "emerald"
                              : m.status === "IN_PROGRESS"
                              ? "indigo"
                              : "slate"
                          }
                          size="sm"
                        >
                          {m.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                  {progress.modules.length === 0 && (
                    <div className="p-6 text-center text-sm text-slate-400">No module records found.</div>
                  )}
                </div>
              </div>

              {/* Questions solved list */}
              <div className="space-y-3">
                <h3 className="text-base font-semibold text-white">Coding Assessment Progress</h3>
                <div className="divide-y divide-surface-800 rounded-2xl border border-surface-800 bg-surface-900/60 overflow-hidden">
                  {progress.questions.map((q) => (
                    <div key={q.question_id} className="p-4 flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-white text-sm flex items-center gap-2">
                          <Code2 className="h-4 w-4 text-brand-400" />
                          {q.question_title}
                        </div>
                        <div className="text-xs text-slate-400">{q.module_title}</div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-xs text-slate-400">Attempts: {q.attempts_count}</span>
                        <Badge variant={q.is_solved ? "emerald" : "amber"} size="sm">
                          {q.is_solved ? `Solved (${q.best_score} pts)` : "Pending"}
                        </Badge>
                      </div>
                    </div>
                  ))}
                  {progress.questions.length === 0 && (
                    <div className="p-6 text-center text-sm text-slate-400">No question attempts logged yet.</div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <LoadingState message="Loading progress records..." />
          )}
        </div>
      )}

      {/* Tab 3: Scores */}
      {activeTab === "scores" && (
        <div className="space-y-6">
          {scores ? (
            <>
              {/* Category Breakdown */}
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                {Object.entries(scores.breakdown_by_source).map(([source, pts]) => (
                  <Card key={source} className="p-4">
                    <div className="text-xs text-slate-400 capitalize">{source.replace("_", " ").toLowerCase()}</div>
                    <div className="text-xl font-bold text-amber-400 mt-1">
                      {parseFloat(pts).toLocaleString()} pts
                    </div>
                  </Card>
                ))}
              </div>

              {/* Records Ledger */}
              <div className="space-y-3">
                <h3 className="text-base font-semibold text-white">Score Event Log</h3>
                <div className="divide-y divide-surface-800 rounded-2xl border border-surface-800 bg-surface-900/60 overflow-hidden">
                  {scores.records.map((r) => (
                    <div key={r.id} className="p-4 flex items-center justify-between text-xs">
                      <div>
                        <Badge variant="indigo" size="sm">{r.source_type}</Badge>
                        <div className="text-slate-400 mt-1 font-mono">{r.policy_applied}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-amber-400 text-sm">+{parseFloat(r.points).toFixed(1)} pts</div>
                        <div className="text-slate-500 mt-0.5">{new Date(r.awarded_at).toLocaleString()}</div>
                      </div>
                    </div>
                  ))}
                  {scores.records.length === 0 && (
                    <div className="p-6 text-center text-sm text-slate-400">No score events awarded yet.</div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <LoadingState message="Loading score ledger..." />
          )}
        </div>
      )}

      {/* Tab 4: Leaderboard & Rank */}
      {activeTab === "rank" && (
        <div className="space-y-6">
          {rank ? (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <Card className="p-6 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
                    <Trophy className="h-5 w-5" />
                    Global Standings
                  </div>
                  <div className="mt-4">
                    <div className="text-5xl font-black text-white">#{rank.global_rank}</div>
                    <p className="text-xs text-slate-400 mt-2">
                      Out of {rank.total_students_global} students platform-wide
                    </p>
                  </div>
                </div>
                <div className="mt-6 pt-4 border-t border-surface-800 text-xs text-slate-400">
                  Total Points: <span className="font-bold text-amber-400">{parseFloat(rank.total_points).toLocaleString()}</span>
                </div>
              </Card>

              <Card className="p-6 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 text-brand-400 font-semibold text-sm">
                    <Award className="h-5 w-5" />
                    Batch Standings ({rank.batch_code})
                  </div>
                  <div className="mt-4">
                    <div className="text-5xl font-black text-white">#{rank.batch_rank}</div>
                    <p className="text-xs text-slate-400 mt-2">
                      Out of {rank.total_students_batch} students in this cohort
                    </p>
                  </div>
                </div>
                <div className="mt-6 pt-4 border-t border-surface-800 text-xs text-slate-400 flex items-center justify-between">
                  <span>Current Streak: {rank.current_streak_days} days</span>
                  <span>Record Streak: {rank.highest_streak_days} days</span>
                </div>
              </Card>
            </div>
          ) : (
            <LoadingState message="Loading leaderboard ranking..." />
          )}
        </div>
      )}

      {/* Enroll Courses Modal */}
      <Modal
        isOpen={isEnrollModalOpen}
        onClose={() => setIsEnrollModalOpen(false)}
        title="Manage Course Enrollments"
        description="Select the curriculum tracks this student is granted access to."
        size="md"
      >
        <div className="space-y-4">
          <div className="max-h-60 overflow-y-auto space-y-2 border border-surface-800 rounded-xl p-3 bg-surface-900/50">
            {coursesData?.data.map((c: CourseItem) => {
              const isSelected = selectedCourseIds.includes(c.id);
              return (
                <div
                  key={c.id}
                  onClick={() => handleToggleCourseSelect(c.id)}
                  className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? "border-brand-500 bg-brand-500/10 text-white"
                      : "border-surface-800 bg-surface-900/40 text-slate-300 hover:border-surface-700"
                  }`}
                >
                  <div className="font-medium text-sm">{c.title}</div>
                  <div className="h-5 w-5 rounded border flex items-center justify-center border-surface-700 bg-surface-950">
                    {isSelected && <CheckCircle2 className="h-4 w-4 text-brand-400" />}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-surface-800">
            <Button variant="secondary" onClick={() => setIsEnrollModalOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => enrollMutation.mutate(selectedCourseIds)}
              isLoading={enrollMutation.isPending}
            >
              Save Enrollments
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
