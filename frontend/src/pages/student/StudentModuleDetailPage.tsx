import React, { useState, useMemo } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Code2,
  Lock,
  Sparkles,
  Trophy,
  FileText,
} from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import { studentApi } from "../../api/studentApi";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { useToast } from "../../context/ToastContext";

/** Render markdown-like lecture_content as structured HTML */
function LectureRenderer({ content }: { content: string }) {
  const sections = useMemo(() => {
    if (!content) return [];
    const lines = content.split("\n");
    const result: Array<{ type: "h1" | "h2" | "h3" | "p" | "code" | "list"; text: string }> = [];
    let inCode = false;
    let codeBlock: string[] = [];

    for (const line of lines) {
      if (line.trim().startsWith("```")) {
        if (inCode) {
          result.push({ type: "code", text: codeBlock.join("\n") });
          codeBlock = [];
          inCode = false;
        } else {
          inCode = true;
        }
        continue;
      }
      if (inCode) {
        codeBlock.push(line);
        continue;
      }

      const trimmed = line.trim();
      if (!trimmed) continue;

      if (trimmed.startsWith("### ")) {
        result.push({ type: "h3", text: trimmed.slice(4) });
      } else if (trimmed.startsWith("## ")) {
        result.push({ type: "h2", text: trimmed.slice(3) });
      } else if (trimmed.startsWith("# ")) {
        result.push({ type: "h1", text: trimmed.slice(2) });
      } else if (trimmed.startsWith("- ")) {
        result.push({ type: "list", text: trimmed.slice(2) });
      } else {
        result.push({ type: "p", text: trimmed });
      }
    }

    if (codeBlock.length > 0) {
      result.push({ type: "code", text: codeBlock.join("\n") });
    }

    return result;
  }, [content]);

  if (sections.length === 0) {
    return (
      <p className="text-sm text-slate-500 dark:text-slate-400 italic">
        No lecture content available for this module yet.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {sections.map((section, idx) => {
        switch (section.type) {
          case "h1":
            return (
              <h2 key={idx} className="text-xl font-bold text-slate-900 dark:text-white">
                {section.text}
              </h2>
            );
          case "h2":
            return (
              <h3 key={idx} className="text-lg font-semibold text-slate-900 dark:text-white mt-3">
                {section.text}
              </h3>
            );
          case "h3":
            return (
              <h4 key={idx} className="text-base font-semibold text-slate-800 dark:text-slate-200 mt-2">
                {section.text}
              </h4>
            );
          case "list":
            return (
              <li key={idx} className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed ml-4 list-disc">
                <InlineCode text={section.text} />
              </li>
            );
          case "code":
            return (
              <pre
                key={idx}
                className="overflow-x-auto rounded-xl bg-slate-950 dark:bg-surface-950 border border-slate-800 dark:border-surface-800 p-4 text-sm font-mono text-emerald-400 dark:text-emerald-300 leading-relaxed shadow-sm"
              >
                <code>{section.text}</code>
              </pre>
            );
          case "p":
          default:
            return (
              <p key={idx} className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                <InlineCode text={section.text} />
              </p>
            );
        }
      })}
    </div>
  );
}

/** Highlight inline `code` within text */
function InlineCode({ text }: { text: string }) {
  const parts = text.split(/(`[^`]+`)/g);
  return (
    <>
      {parts.map((part, i) =>
        part.startsWith("`") && part.endsWith("`") ? (
          <code
            key={i}
            className="rounded bg-brand-50 dark:bg-brand-500/10 px-1.5 py-0.5 text-[13px] font-mono text-brand-600 dark:text-brand-400 border border-brand-200 dark:border-brand-500/20 font-semibold"
          >
            {part.slice(1, -1)}
          </code>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </>
  );
}

export const StudentModuleDetailPage: React.FC = () => {
  const { moduleId } = useParams<{ moduleId: string }>();
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const { success: toastSuccess, error: toastError } = useToast();
  const [showCompletionSuccess, setShowCompletionSuccess] = useState(false);

  const {
    data: moduleData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["student", "module-detail", moduleId, user?.id],
    queryFn: () => studentApi.getModuleDetail(moduleId!),
    enabled: !!moduleId && !!user?.id,
    staleTime: 1000 * 30,
  });

  const completeMutation = useMutation({
    mutationFn: () => studentApi.completeModule(moduleId!),
    onSuccess: (result) => {
      toastSuccess(
        "Module Completed!",
        `${result.title} marked as complete. Course progress: ${result.course_progress_percentage}%`
      );
      setShowCompletionSuccess(true);

      // Invalidate relevant queries to refresh roadmap, dashboard, etc.
      queryClient.invalidateQueries({ queryKey: ["student", "module-detail", moduleId] });
      queryClient.invalidateQueries({ queryKey: ["student", "course-detail"] });
      queryClient.invalidateQueries({ queryKey: ["student", "courses"] });
      queryClient.invalidateQueries({ queryKey: ["student", "dashboard"] });
    },
    onError: (err: any) => {
      const msg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.message ||
        "Failed to mark module as complete.";
      toastError("Completion Failed", msg);
    },
  });

  if (isLoading) {
    return (
      <div className="flex h-96 flex-col items-center justify-center">
        <LoadingState message="Loading module lecture content..." />
      </div>
    );
  }

  if (isError || !moduleData) {
    // Handle locked module specifically
    const errorCode = (error as any)?.response?.data?.error?.code;
    const errorMsg =
      (error as any)?.response?.data?.error?.message ||
      (error instanceof Error ? error.message : "Failed to load module.");

    if (errorCode === "MODULE_LOCKED") {
      return (
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <Link to="/courses">
              <Button variant="ghost" size="sm" className="flex items-center gap-1.5">
                <ArrowLeft className="h-4 w-4" />
                Back to Courses
              </Button>
            </Link>
          </div>
          <Card className="p-12 text-center">
            <Lock className="h-12 w-12 text-slate-500 mx-auto mb-3 opacity-60" />
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Module Locked
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto mt-2 leading-relaxed">
              {errorMsg}
            </p>
            <Link to="/courses" className="inline-block mt-6">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-3.5 w-3.5 mr-1.5" />
                Return to Course Roadmap
              </Button>
            </Link>
          </Card>
        </div>
      );
    }

    return (
      <ErrorState
        title="Unable to load module"
        message={errorMsg}
        onRetry={() => refetch()}
      />
    );
  }

  const isCompleted = moduleData.status === "COMPLETED";
  const isInProgress = moduleData.status === "IN_PROGRESS";

  return (
    <div className="space-y-6">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
        <Link to="/courses" className="hover:text-slate-900 dark:hover:text-white transition-colors">
          Courses
        </Link>
        <ChevronRight className="h-3.5 w-3.5" />
        <Link
          to={`/courses/${moduleData.course_id}`}
          className="hover:text-slate-900 dark:hover:text-white transition-colors"
        >
          {moduleData.course_title}
        </Link>
        <ChevronRight className="h-3.5 w-3.5" />
        <span className="text-slate-900 dark:text-white font-semibold truncate">
          Module {moduleData.order_index}
        </span>
      </div>

      {/* Module Header Card */}
      <Card className="p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-xs text-brand-600 dark:text-brand-400 font-bold uppercase">
                Module {moduleData.order_index}
              </span>
              <Badge
                variant={
                  isCompleted ? "success" : isInProgress ? "brand" : "amber"
                }
              >
                {isCompleted ? "Completed" : isInProgress ? "In Progress" : "Unlocked"}
              </Badge>
              <Badge variant="indigo" size="sm">
                Passing Score: {moduleData.passing_percentage}%
              </Badge>
            </div>
            <h1 className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
              {moduleData.title}
            </h1>
            <p className="text-sm text-slate-600 dark:text-slate-300 mt-1.5 max-w-xl leading-relaxed">
              {moduleData.summary}
            </p>

            {/* Score display */}
            {moduleData.score_percentage > 0 && (
              <div className="flex items-center gap-3 mt-3">
                <div className="h-2 w-32 overflow-hidden rounded-full bg-slate-200 dark:bg-surface-800">
                  <div
                    className={`h-full rounded-full ${
                      moduleData.score_percentage >= moduleData.passing_percentage
                        ? "bg-emerald-500"
                        : "bg-amber-500"
                    }`}
                    style={{ width: `${Math.min(moduleData.score_percentage, 100)}%` }}
                  />
                </div>
                <span className="text-sm font-bold text-slate-900 dark:text-white">
                  {moduleData.score_percentage}%
                </span>
                {isCompleted && moduleData.completed_at && (
                  <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                    Completed {new Date(moduleData.completed_at).toLocaleDateString()}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Primary Action */}
          <div className="flex gap-2 self-start shrink-0">
            <Link to="/assignments">
              <Button variant="outline" size="sm" className="flex items-center gap-1.5">
                <Code2 className="h-4 w-4" />
                <span className="hidden sm:inline">Coding Assessment</span>
                <span className="sm:hidden">Assess</span>
              </Button>
            </Link>

            {!isCompleted && (
              <Button
                size="sm"
                className="flex items-center gap-1.5"
                onClick={() => completeMutation.mutate()}
                disabled={completeMutation.isPending}
              >
                {completeMutation.isPending ? (
                  <>
                    <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                    <span>Completing...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Mark Complete</span>
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* Completion Success Banner */}
      <AnimatePresence>
        {(showCompletionSuccess || isCompleted) && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <Card className="p-4 border-emerald-300 dark:border-emerald-500/30 bg-emerald-50 dark:bg-emerald-950/20">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">
                    <Trophy className="h-4.5 w-4.5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-emerald-700 dark:text-emerald-400 text-sm">Module Completed!</h3>
                    <p className="text-xs text-slate-600 dark:text-slate-300 mt-0.5">
                      You've mastered {moduleData.title}.
                      {completeMutation.data?.next_module
                        ? ` Next: ${completeMutation.data.next_module.title}`
                        : " You've completed all modules!"}
                    </p>
                  </div>
                </div>

                {completeMutation.data?.next_module && (
                  <Link to={`/modules/${completeMutation.data.next_module.id}`}>
                    <Button size="sm" className="flex items-center gap-1.5">
                      <Sparkles className="h-3.5 w-3.5" />
                      <span className="hidden sm:inline">Next Module</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Button>
                  </Link>
                )}
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Lecture Content */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-5">
          <FileText className="h-4.5 w-4.5 text-brand-600 dark:text-brand-400" />
          <h2 className="text-base font-bold text-slate-900 dark:text-white">Lecture Notes & Content</h2>
        </div>
        <div className="border-t border-slate-200 dark:border-surface-800 pt-5">
          <LectureRenderer content={moduleData.lecture_content} />
        </div>
      </Card>

      {/* Module Navigation */}
      <div className="flex items-center justify-between gap-4">
        {moduleData.prev_module_id ? (
          <Link to={`/modules/${moduleData.prev_module_id}`}>
            <Button variant="outline" size="sm" className="flex items-center gap-1.5">
              <ChevronLeft className="h-4 w-4" />
              Previous Module
            </Button>
          </Link>
        ) : (
          <div />
        )}

        <Link to={`/courses/${moduleData.course_id}`}>
          <Button variant="ghost" size="sm" className="flex items-center gap-1.5">
            <BookOpen className="h-3.5 w-3.5" />
            Course Roadmap
          </Button>
        </Link>

        {moduleData.next_module_id ? (
          moduleData.is_next_unlocked ? (
            <Link to={`/modules/${moduleData.next_module_id}`}>
              <Button size="sm" className="flex items-center gap-1.5">
                Next Module
                <ChevronRight className="h-4 w-4" />
              </Button>
            </Link>
          ) : (
            <Button variant="outline" size="sm" disabled className="flex items-center gap-1.5">
              <Lock className="h-3.5 w-3.5" />
              Next Module Locked
            </Button>
          )
        ) : (
          <div />
        )}
      </div>
    </div>
  );
};
