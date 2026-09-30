import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { BookOpen, Layers, ArrowRight, CheckCircle2, PlayCircle, RefreshCw } from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import { studentApi, StudentCourseItem } from "../../api/studentApi";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";

export const StudentCoursesPage: React.FC = () => {
  const { user } = useAuthStore();

  const {
    data: courses,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery<StudentCourseItem[]>({
    queryKey: ["student", "courses", user?.id],
    queryFn: studentApi.getCourses,
    enabled: !!user?.id,
    staleTime: 1000 * 60,
  });

  if (isLoading) {
    return (
      <div className="flex h-96 flex-col items-center justify-center space-y-4">
        <LoadingState message="Loading your enrolled curriculum tracks..." />
      </div>
    );
  }

  if (isError || !courses) {
    return (
      <ErrorState
        title="Unable to load courses"
        message={error instanceof Error ? error.message : "Failed to load courses from server."}
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <BookOpen className="h-6 w-6 text-brand-500" />
            Curriculum Tracks & Courses
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Complete sequential module milestones and master each core programming concept.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-1.5 self-start sm:self-auto"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin text-brand-500" : ""}`} />
          <span>Refresh Tracks</span>
        </Button>
      </div>

      {courses.length === 0 ? (
        <Card className="p-12 text-center">
          <BookOpen className="h-12 w-12 text-slate-400 mx-auto mb-3 opacity-60" />
          <h3 className="text-base font-semibold text-slate-900 dark:text-white">
            No Enrolled Courses Found
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto mt-1">
            Your cohort administrator has not yet assigned a course track to your account.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {courses.map((course) => {
            const isCompleted = course.progress_percentage === 100;
            const continueUrl = course.continue_module_id
              ? `/modules/${course.continue_module_id}`
              : `/courses/${course.id}`;

            return (
              <Card
                key={course.id}
                className="p-6 flex flex-col justify-between hover:border-brand-500/40 transition-colors shadow-sm"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-500 border border-brand-500/20">
                      <BookOpen className="h-6 w-6" />
                    </div>
                    {course.is_enrolled ? (
                      <Badge variant={isCompleted ? "success" : "emerald"} size="sm">
                        {isCompleted ? "Completed" : "Active Enrollment"}
                      </Badge>
                    ) : (
                      <Badge variant="neutral" size="sm">
                        Not Enrolled
                      </Badge>
                    )}
                  </div>

                  <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                    {course.title}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 line-clamp-3 leading-relaxed">
                    {course.description || "Structured sequential learning modules with coding labs and lecture notes."}
                  </p>

                  {/* Progress Bar & Module Counter */}
                  {course.is_enrolled && (
                    <div className="mt-5 space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-500 dark:text-slate-400">Curriculum Progress</span>
                        <span className="font-bold text-slate-900 dark:text-white">
                          {course.progress_percentage}%
                        </span>
                      </div>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-surface-800">
                        <div
                          className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min(course.progress_percentage, 100)}%` }}
                        />
                      </div>
                      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                        <span>{course.completed_modules} of {course.total_modules} modules completed</span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="mt-6 pt-4 border-t border-slate-200 dark:border-surface-800 flex items-center justify-between">
                  <Link
                    to={`/courses/${course.id}`}
                    className="text-xs font-semibold text-brand-600 dark:text-brand-400 hover:underline flex items-center gap-1"
                  >
                    <Layers className="h-3.5 w-3.5" />
                    <span>View Roadmap</span>
                  </Link>

                  {course.is_enrolled ? (
                    <Link to={continueUrl}>
                      <Button size="sm" className="flex items-center gap-1.5">
                        {isCompleted ? (
                          <>
                            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                            <span>Review</span>
                          </>
                        ) : (
                          <>
                            <PlayCircle className="h-3.5 w-3.5" />
                            <span>Continue</span>
                          </>
                        )}
                        <ArrowRight className="h-3.5 w-3.5" />
                      </Button>
                    </Link>
                  ) : (
                    <Button size="sm" disabled variant="outline">
                      Contact Admin
                    </Button>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};
