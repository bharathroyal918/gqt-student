import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  TrendingUp,
  Award,
  Code2,
  RefreshCw,
  Info,
  Calendar,
} from "lucide-react";
import { tpoApi } from "../../api/tpoApi";
import { useAuthStore } from "../../store/authStore";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";

export const TPOPerformanceTrendsPage: React.FC = () => {
  const { user } = useAuthStore();

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ["tpo-performance-trends", user?.id],
    queryFn: tpoApi.getPerformanceTrends,
    staleTime: 60 * 1000,
  });

  if (isLoading) {
    return <LoadingState message="Extracting timestamped historical performance trend lines..." />;
  }

  if (isError || !data) {
    return (
      <ErrorState
        title="Failed to Load Performance Trends"
        message={
          (error as any)?.response?.data?.error?.message ||
          "Could not retrieve historical trend metrics for your assigned college."
        }
        onRetry={() => refetch()}
      />
    );
  }

  const lastUpdated = dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString() : "";

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-6 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20 shadow-inner">
            <TrendingUp className="h-7 w-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-sky-600 dark:text-sky-400">
                Longitudinal Analytics
              </span>
              <Badge variant="brand" size="sm">
                Verified Timestamps
              </Badge>
            </div>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Student Performance Trends
            </h1>
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
              Historical score distributions and submission acceptance rates over time
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 self-start sm:self-center">
          <div className="text-right hidden md:block">
            <span className="text-[10px] text-slate-400 block font-medium">Last Synced</span>
            <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              {lastUpdated || "Live"}
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Verification Notice */}
      <div className="flex items-start gap-3 p-4 rounded-xl bg-sky-50 dark:bg-surface-900/60 border border-sky-500/20 text-xs text-sky-800 dark:text-sky-200">
        <Info className="h-4 w-4 shrink-0 text-sky-600 dark:text-sky-400 mt-0.5" />
        <div>
          <span className="font-bold">Strict Historical Integrity Rule: </span>
          All data points shown here are computed directly from verified, immutable timestamped records (
          <code className="font-mono bg-sky-500/10 px-1 py-0.5 rounded">ScoreRecord.awarded_at</code> and{" "}
          <code className="font-mono bg-sky-500/10 px-1 py-0.5 rounded">CodeSubmission.submitted_at</code>
          ). If insufficient history exists for a period, an honest unavailable state is displayed instead of fabricated values.
        </div>
      </div>

      {!data.has_sufficient_history ? (
        <Card className="p-12 text-center text-slate-400">
          <Calendar className="h-12 w-12 mx-auto mb-3 text-slate-300 dark:text-surface-700" />
          <h3 className="text-base font-bold text-slate-900 dark:text-white">
            Insufficient Historical Records
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto mt-1">
            {data.unavailable_reason ||
              "No historical timestamped records are available yet to plot monthly trend lines for your institution."}
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Monthly Score Trend Table & Bars */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Award className="h-5 w-5 text-amber-500" />
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Monthly Points & Awards Volume
                </h3>
              </div>
              <Badge variant="brand" size="sm">
                Score Accumulation
              </Badge>
            </div>

            {data.monthly_score_trends.length === 0 ? (
              <div className="p-8 text-center text-slate-400">
                <p className="text-xs">No points awarded in previous periods.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {data.monthly_score_trends.map((item) => {
                  const maxPts = Math.max(...data.monthly_score_trends.map((t) => t.total_points), 1);
                  const pct = Math.round((item.total_points / maxPts) * 100);

                  return (
                    <div key={item.period} className="space-y-1.5 p-3 rounded-xl bg-slate-50 dark:bg-surface-900/60 border border-slate-100 dark:border-surface-800/60">
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-bold text-slate-900 dark:text-white">
                          {item.period}
                        </span>
                        <div className="flex items-center gap-3">
                          <span className="text-slate-400 text-[11px]">
                            {item.awards_count} awards logged
                          </span>
                          <span className="font-bold text-amber-600 dark:text-amber-400">
                            +{item.total_points.toFixed(0)} pts
                          </span>
                        </div>
                      </div>
                      <div className="h-2 w-full rounded-full bg-slate-100 dark:bg-surface-800 overflow-hidden">
                        <div
                          className="h-full bg-amber-500 rounded-full transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>

          {/* Monthly Coding Submissions Trend */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Code2 className="h-5 w-5 text-violet-500" />
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Monthly Coding Submissions & Pass Rate
                </h3>
              </div>
              <Badge variant="brand" size="sm">
                Code Acceptance
              </Badge>
            </div>

            {data.monthly_submission_trends.length === 0 ? (
              <div className="p-8 text-center text-slate-400">
                <p className="text-xs">No coding submissions recorded in previous periods.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {data.monthly_submission_trends.map((item) => (
                  <div
                    key={item.period}
                    className="space-y-1.5 p-3 rounded-xl bg-slate-50 dark:bg-surface-900/60 border border-slate-100 dark:border-surface-800/60"
                  >
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-bold text-slate-900 dark:text-white">
                        {item.period}
                      </span>
                      <div className="flex items-center gap-3">
                        <span className="text-slate-400 text-[11px]">
                          {item.accepted_submissions}/{item.total_submissions} accepted
                        </span>
                        <span className="font-bold text-emerald-600 dark:text-emerald-400">
                          {item.pass_rate}%
                        </span>
                      </div>
                    </div>
                    <div className="h-2 w-full rounded-full bg-slate-100 dark:bg-surface-800 overflow-hidden">
                      <div
                        className="h-full bg-violet-500 rounded-full transition-all duration-500"
                        style={{ width: `${item.pass_rate}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
};
