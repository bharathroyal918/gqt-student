import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  CalendarCheck,
  Flame,
  Calendar,
  CheckCircle2,
  Clock,
  Code2,
  Search,
  Award,
  Sparkles,
  Loader2,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Modal } from "../../components/ui/Modal";
import { Textarea } from "../../components/ui/Form";
import { studentApi, StudentTaskItem } from "../../api/studentApi";
import { useToast } from "../../context/ToastContext";
import { useAuthStore } from "../../store/authStore";

export const StudentTasksPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();
  const { hydrateAuth } = useAuthStore();

  const [activeTab, setActiveTab] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTaskForComplete, setSelectedTaskForComplete] = useState<StudentTaskItem | null>(null);
  const [submissionNotes, setSubmissionNotes] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["student", "tasks", activeTab],
    queryFn: () =>
      studentApi.getTasks(activeTab !== "ALL" ? { status: activeTab.toLowerCase() } : undefined),
  });

  const completeMutation = useMutation({
    mutationFn: ({ taskId, notes }: { taskId: string; notes: string }) =>
      studentApi.completeTask(taskId, { submission_notes: notes }),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ["student", "tasks"] });
      queryClient.invalidateQueries({ queryKey: ["student", "dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["student", "profile"] });
      hydrateAuth(true);
      success("Task Completed!", `Earned +${res.score_awarded || 10} points on your profile!`);
      setSelectedTaskForComplete(null);
      setSubmissionNotes("");
    },
    onError: (err: any) => {
      toastError("Completion Failed", err?.response?.data?.message || "Failed to mark task complete.");
    },
  });

  const tasks = data?.tasks || [];
  const filteredTasks = tasks.filter((t) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      t.title.toLowerCase().includes(q) ||
      (t.description && t.description.toLowerCase().includes(q)) ||
      (t.course_title && t.course_title.toLowerCase().includes(q))
    );
  });

  const completedCount = tasks.filter((t) => t.is_completed).length;
  const pendingCount = tasks.filter((t) => !t.is_completed).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            Daily Practice Challenges
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Complete assigned daily coding exercises to maintain consistency streaks and earn leaderboard points.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-2xl border border-brand-500/20 bg-brand-500/10 px-4 py-2 text-brand-600 dark:text-brand-400 font-bold text-xs">
            <Award className="h-4 w-4 text-brand-500" />
            <span>{completedCount} Completed</span>
          </div>
          <div className="flex items-center gap-2 rounded-2xl border border-rose-500/20 bg-rose-500/10 px-4 py-2 text-rose-600 dark:text-rose-400 font-bold text-xs">
            <Flame className="h-4 w-4" />
            <span>Daily Streak Active</span>
          </div>
        </div>
      </div>

      {/* Filter Tabs & Search */}
      <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between border-b border-slate-200 dark:border-surface-800 pb-3">
        <div className="flex flex-wrap gap-2">
          {[
            { key: "ALL", label: "All Tasks" },
            { key: "PENDING", label: `Pending (${pendingCount})` },
            { key: "COMPLETED", label: `Completed (${completedCount})` },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${activeTab === tab.key
                  ? "bg-brand-600 text-white shadow-md shadow-brand-500/20"
                  : "bg-slate-100 dark:bg-surface-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="relative min-w-[240px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search daily challenges..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-surface-700 bg-white dark:bg-surface-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>
      </div>

      {/* Tasks List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-24">
          <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
        </div>
      ) : filteredTasks.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20">
            <CalendarCheck className="h-7 w-7" />
          </div>
          <h3 className="mt-4 text-base font-bold text-slate-900 dark:text-white">
            No challenges found
          </h3>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
            {activeTab === "PENDING"
              ? "Awesome work! You have completed all assigned daily practice challenges."
              : "No challenges match your current filter criteria."}
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredTasks.map((task) => (
            <Card
              key={task.id}
              className={`p-5 transition-all hover:border-brand-500/40 ${task.is_completed
                  ? "bg-slate-50/50 dark:bg-surface-900/40 border-emerald-500/20"
                  : "hover:shadow-md"
                }`}
            >
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="flex items-start gap-4">
                  <div
                    className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border ${task.is_completed
                        ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                        : "bg-brand-500/10 text-brand-600 dark:text-brand-400 border-brand-500/20"
                      }`}
                  >
                    {task.is_completed ? (
                      <CheckCircle2 className="h-5 w-5" />
                    ) : (
                      <CalendarCheck className="h-5 w-5" />
                    )}
                  </div>

                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-bold text-slate-900 dark:text-white text-sm sm:text-base">
                        {task.title}
                      </h3>
                      {task.is_completed ? (
                        <Badge variant="emerald" size="sm">
                          Completed (+{task.score_awarded || task.points} pts)
                        </Badge>
                      ) : (
                        <Badge variant="amber" size="sm">
                          Pending (+{task.points} pts)
                        </Badge>
                      )}
                      {task.course_title && (
                        <span className="text-[11px] font-medium text-slate-400">
                          • {task.course_title}
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed max-w-2xl">
                      {task.description || "Practice problem to sharpen foundational programming concepts."}
                    </p>

                    <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-500 dark:text-slate-400 pt-1">
                      {task.scheduled_date && (
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3.5 w-3.5 text-slate-400" />
                          Assigned: {task.scheduled_date}
                        </span>
                      )}
                      {task.deadline && (
                        <span className="flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5 text-slate-400" />
                          Deadline: {new Date(task.deadline).toLocaleDateString()}
                        </span>
                      )}
                      {task.completed_at && (
                        <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Completed on {new Date(task.completed_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>

                    {task.submission_notes && (
                      <div className="mt-2 rounded-xl bg-slate-100 dark:bg-surface-800 p-2.5 text-xs text-slate-600 dark:text-slate-300 font-mono">
                        <span className="font-semibold text-slate-900 dark:text-white">Submission Notes: </span>
                        {task.submission_notes}
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                  {task.question_id && (
                    <Link to={`/assignments`}>
                      <Button variant="secondary" size="sm">
                        <Code2 className="h-3.5 w-3.5 mr-1" />
                        Solve in IDE
                      </Button>
                    </Link>
                  )}

                  {!task.is_completed ? (
                    <Button
                      size="sm"
                      onClick={() => {
                        setSelectedTaskForComplete(task);
                        setSubmissionNotes("");
                      }}
                    >
                      <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                      Mark Done
                    </Button>
                  ) : (
                    <div className="px-3 py-1 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-bold border border-emerald-500/20">
                      ✓ Done
                    </div>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Complete Task Modal */}
      {selectedTaskForComplete && (
        <Modal
          isOpen={!!selectedTaskForComplete}
          onClose={() => setSelectedTaskForComplete(null)}
          title="Complete Practice Challenge"
        >
          <div className="space-y-4 py-2">
            <div>
              <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                {selectedTaskForComplete.title}
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                {selectedTaskForComplete.description}
              </p>
            </div>

            <div className="rounded-xl bg-brand-500/10 border border-brand-500/20 p-3 text-xs text-brand-700 dark:text-brand-300 flex items-center gap-2">
              <Sparkles className="h-4 w-4 shrink-0 text-brand-500" />
              <span>
                Marking this challenge complete will reward you with <strong>+{selectedTaskForComplete.points} points</strong> on the leaderboard!
              </span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Submission Notes / GitHub URL (Optional)
              </label>
              <Textarea
                rows={3}
                placeholder="E.g., Solved with O(N) dynamic programming; repo: https://github.com/..."
                value={submissionNotes}
                onChange={(e) => setSubmissionNotes(e.target.value)}
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-200 dark:border-surface-800">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setSelectedTaskForComplete(null)}
                disabled={completeMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={() =>
                  completeMutation.mutate({
                    taskId: selectedTaskForComplete.id,
                    notes: submissionNotes,
                  })
                }
                isLoading={completeMutation.isPending}
              >
                <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                Claim +{selectedTaskForComplete.points} Points
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
