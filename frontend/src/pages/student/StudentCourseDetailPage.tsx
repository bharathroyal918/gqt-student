import React from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  BookOpen,
  Layers,
  Lock,
  Play,
  CheckCircle2,
  Circle,
  ChevronRight,
  Trophy,
  ArrowRight,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import { studentApi, StudentModuleItem } from "../../api/studentApi";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";

/** Determine visual styling and icon based on module status */
function getModuleVisuals(mod: StudentModuleItem) {
  switch (mod.status) {
    case "COMPLETED":
      return {
        icon: CheckCircle2,
        iconColor: "text-emerald-600 dark:text-emerald-400",
        bgColor: "bg-emerald-50 dark:bg-emerald-500/10",
        borderColor: "border-emerald-200 dark:border-emerald-500/20",
        textColor: "text-emerald-700 dark:text-emerald-400",
        label: "Completed",
        badgeVariant: "success" as const,
      };
    case "IN_PROGRESS":
      return {
        icon: Play,
        iconColor: "text-brand-600 dark:text-brand-400",
        bgColor: "bg-brand-50 dark:bg-brand-500/10",
        borderColor: "border-brand-200 dark:border-brand-500/25",
        textColor: "text-brand-700 dark:text-brand-400",
        label: "In Progress",
        badgeVariant: "brand" as const,
      };
    case "UNLOCKED":
      return {
        icon: Circle,
        iconColor: "text-amber-600 dark:text-amber-400",
        bgColor: "bg-amber-50 dark:bg-amber-500/10",
        borderColor: "border-amber-200 dark:border-amber-500/20",
        textColor: "text-amber-700 dark:text-amber-400",
        label: "Unlocked",
        badgeVariant: "amber" as const,
      };
    case "LOCKED":
    default:
      return {
        icon: Lock,
        iconColor: "text-slate-400 dark:text-slate-500",
        bgColor: "bg-slate-100 dark:bg-surface-800/50",
        borderColor: "border-slate-200 dark:border-surface-700/40",
        textColor: "text-slate-500 dark:text-slate-400",
        label: "Locked",
        badgeVariant: "slate" as const,
      };
  }
}

export const StudentCourseDetailPage: React.FC = () => {
  const { courseId } = useParams<{ courseId: string }>();
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ["student", "course-detail", courseId, user?.id],
    queryFn: () => studentApi.getCourseDetail(courseId!),
    enabled: !!courseId && !!user?.id,
    staleTime: 1000 * 30,
  });

  if (isLoading) {
    return (
      <div className="flex h-96 flex-col items-center justify-center">
        <LoadingState message="Loading course curriculum roadmap..." />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <ErrorState
        title="Unable to load course details"
        message={error instanceof Error ? error.message : "Failed to load course roadmap from server."}
        onRetry={() => refetch()}
      />
    );
  }

  const { course, modules } = data;
  const isCourseComplete = course.progress_percentage === 100;

  return (
    <div className="space-y-6">
      {/* Breadcrumb / Back Navigation */}
      <div className="flex items-center gap-4">
        <Link to="/courses">
          <Button variant="ghost" size="sm" className="flex items-center gap-1.5">
            <ArrowLeft className="h-4 w-4" />
            Back to Courses
          </Button>
        </Link>
      </div>

      {/* Course Header Card */}
      <Card className="p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20">
              <BookOpen className="h-7 w-7" />
            </div>
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{course.title}</h1>
                <Badge variant={isCourseComplete ? "success" : "emerald"}>
                  {isCourseComplete ? "Completed" : "Enrolled"}
                </Badge>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-300 mt-2 max-w-2xl leading-relaxed">
                {course.description || "Sequential curriculum modules. Each module unlocks as you achieve passing scores."}
              </p>
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-1.5 self-start"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin text-brand-500" : ""}`} />
            <span>Refresh</span>
          </Button>
        </div>

        {/* Progress Summary Bar */}
        <div className="mt-6 pt-5 border-t border-slate-200 dark:border-surface-800">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <p className="text-[11px] uppercase font-semibold tracking-wider text-slate-500 dark:text-slate-400">Total Modules</p>
              <p className="text-xl font-bold text-slate-900 dark:text-white mt-0.5">{course.total_modules}</p>
            </div>
            <div>
              <p className="text-[11px] uppercase font-semibold tracking-wider text-slate-500 dark:text-slate-400">Completed</p>
              <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">{course.completed_modules}</p>
            </div>
            <div>
              <p className="text-[11px] uppercase font-semibold tracking-wider text-slate-500 dark:text-slate-400">Remaining</p>
              <p className="text-xl font-bold text-slate-900 dark:text-white mt-0.5">
                {course.total_modules - course.completed_modules}
              </p>
            </div>
            <div>
              <p className="text-[11px] uppercase font-semibold tracking-wider text-slate-500 dark:text-slate-400">Progress</p>
              <p className="text-xl font-bold text-brand-600 dark:text-brand-400 mt-0.5">{course.progress_percentage}%</p>
            </div>
          </div>
          <div className="mt-4 h-2.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-surface-800">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-brand-500 to-emerald-500"
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(course.progress_percentage, 100)}%` }}
              transition={{ duration: 0.8, ease: "easeOut" }}
            />
          </div>
        </div>
      </Card>

      {/* Course Completion Celebration */}
      <AnimatePresence>
        {isCourseComplete && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <Card className="p-5 border-emerald-300 dark:border-emerald-500/30 bg-emerald-50 dark:bg-emerald-950/20">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">
                  <Trophy className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-bold text-emerald-700 dark:text-emerald-400 text-sm">Course Completed!</h3>
                  <p className="text-xs text-slate-600 dark:text-slate-300 mt-0.5">
                    Outstanding! You have mastered all {course.total_modules} modules. Your certificate may be available in your profile.
                  </p>
                </div>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sequential Module Roadmap */}
      <div className="space-y-3">
        <h2 className="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
          <Layers className="h-4 w-4 text-brand-600 dark:text-brand-400" />
          Sequential Curriculum Modules
          <span className="text-xs font-normal text-slate-500 dark:text-slate-400">
            ({course.completed_modules} / {course.total_modules} completed)
          </span>
        </h2>

        <div className="space-y-2">
          <AnimatePresence>
            {modules.map((mod, idx) => {
              const visuals = getModuleVisuals(mod);
              const isClickable = mod.is_accessible;
              const isContinueTarget = course.continue_module_id === mod.id;

              return (
                <motion.div
                  key={mod.id}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.03, duration: 0.25 }}
                >
                  <Card
                    className={`p-4 flex items-center justify-between gap-3 transition-all duration-200 ${
                      isClickable
                        ? "cursor-pointer hover:border-brand-500/40 hover:shadow-sm"
                        : "opacity-60 cursor-not-allowed"
                    } ${isContinueTarget ? "ring-1 ring-brand-500/30 shadow-md shadow-brand-500/5" : ""}`}
                    onClick={() => isClickable && navigate(`/modules/${mod.id}`)}
                  >
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      {/* Module Number */}
                      <div
                        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${visuals.bgColor} border ${visuals.borderColor} font-bold font-mono text-sm ${visuals.textColor}`}
                      >
                        {mod.status === "COMPLETED" ? (
                          <CheckCircle2 className="h-5 w-5" />
                        ) : (
                          `#${mod.order_index}`
                        )}
                      </div>

                      {/* Module Info */}
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3
                            className={`font-semibold text-sm ${
                              mod.status === "LOCKED"
                                ? "text-slate-500 dark:text-slate-500"
                                : "text-slate-900 dark:text-white"
                            }`}
                          >
                            {mod.title}
                          </h3>
                          <Badge variant={visuals.badgeVariant} size="sm">
                            {visuals.label}
                          </Badge>
                          {isContinueTarget && (
                            <Badge variant="brand" size="sm" className="animate-pulse">
                              <Sparkles className="h-2.5 w-2.5 mr-0.5" />
                              Continue
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-1">{mod.summary}</p>

                        {/* Score bar for completed/in-progress modules */}
                        {mod.status !== "LOCKED" && mod.score_percentage > 0 && (
                          <div className="flex items-center gap-2 mt-1.5">
                            <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-200 dark:bg-surface-800">
                              <div
                                className={`h-full rounded-full ${
                                  mod.score_percentage >= mod.passing_percentage
                                    ? "bg-emerald-500"
                                    : "bg-amber-500"
                                }`}
                                style={{ width: `${Math.min(mod.score_percentage, 100)}%` }}
                              />
                            </div>
                            <span className="text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                              {mod.score_percentage}%
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Action / Status */}
                    <div className="shrink-0">
                      {mod.status === "LOCKED" ? (
                        <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 font-medium">
                          <Lock className="h-4 w-4" />
                          <span className="hidden sm:inline">Locked</span>
                        </div>
                      ) : mod.status === "COMPLETED" ? (
                        <div className="flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                          <span className="hidden sm:inline">Review</span>
                          <ChevronRight className="h-4 w-4" />
                        </div>
                      ) : (
                        <Button size="sm" className="flex items-center gap-1">
                          {isContinueTarget ? (
                            <>
                              <Play className="h-3.5 w-3.5" />
                              <span className="hidden sm:inline">Continue</span>
                            </>
                          ) : (
                            <>
                              <ArrowRight className="h-3.5 w-3.5" />
                              <span className="hidden sm:inline">Open</span>
                            </>
                          )}
                        </Button>
                      )}
                    </div>
                  </Card>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};
