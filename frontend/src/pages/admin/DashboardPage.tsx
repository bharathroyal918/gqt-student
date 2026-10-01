import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Users,
  Award,
  CheckCircle,
  FileCode,
  Flame,
  TrendingUp,
  Activity,
  ArrowUpRight,
} from "lucide-react";
import { Link } from "react-router-dom";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

import { adminApi } from "../../api/adminApi";
import { Card } from "../../components/ui/Card";
import { ChartCard } from "../../components/ui/ChartCard";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";

export const DashboardPage: React.FC = () => {
  const {
    data: dashboardData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["admin", "dashboard"],
    queryFn: () => adminApi.getAnalyticsDashboard(),
    staleTime: 30000,
  });

  const { data: activityData } = useQuery({
    queryKey: ["admin", "reports", "monthly-activity", 7],
    queryFn: () => adminApi.getMonthlyActivityReport(7),
    staleTime: 60000,
  });

  if (isLoading) {
    return <LoadingState message="Aggregating platform metrics..." />;
  }

  if (isError) {
    return (
      <ErrorState
        title="Dashboard Offline"
        message={error instanceof Error ? error.message : "Failed to load dashboard metrics"}
        onRetry={refetch}
      />
    );
  }

  if (!dashboardData) return null;

  const statCards = [
    {
      title: "Total Students",
      value: dashboardData.total_students,
      subtitle: `${dashboardData.active_students} active accounts`,
      icon: Users,
      color: "text-brand-400 bg-brand-500/10",
      link: "/admin/students",
    },
    {
      title: "Curriculum Completion",
      value: `${dashboardData.module_completion_rate}%`,
      subtitle: "Avg. across all modules",
      icon: CheckCircle,
      color: "text-emerald-400 bg-emerald-500/10",
      link: "/admin/courses",
    },
    {
      title: "Code Submissions",
      value: dashboardData.assignment_statistics.total_submissions,
      subtitle: `${dashboardData.assignment_statistics.acceptance_rate}% pass rate`,
      icon: FileCode,
      color: "text-cyan-400 bg-cyan-500/10",
      link: "/admin/assignments",
    },
    {
      title: "Today's Activity",
      value: dashboardData.today_activity.submissions_count,
      subtitle: `${dashboardData.today_activity.active_students_count} active coders today`,
      icon: Activity,
      color: "text-amber-400 bg-amber-500/10",
      link: "/admin/analytics",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Title & Quick Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Institutional Dashboard</h1>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Real-time platform overview &bull; Live operational metrics and academic telemetry
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/admin/reports"
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 dark:border-surface-700 bg-white dark:bg-surface-900 px-3.5 py-2 text-xs font-medium text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-surface-800 transition-colors shadow-sm"
          >
            Generate Reports
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <Link key={card.title} to={card.link}>
              <Card className="hover:border-brand-500/40 transition-all duration-200">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-500 dark:text-slate-400">{card.title}</span>
                  <div className={`flex h-9 w-9 items-center justify-center rounded-xl ${card.color}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                </div>
                <div className="mt-3">
                  <span className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">{card.value}</span>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{card.subtitle}</p>
                </div>
              </Card>
            </Link>
          );
        })}
      </div>

      {/* Charts & Top Performers Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Weekly Activity Trends */}
        <div className="lg:col-span-2">
          <ChartCard
            title="Weekly Submissions Volume"
            subtitle="7-day coding activity and execution frequency"
          >
            {activityData?.timeline ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={activityData.timeline} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                  <XAxis
                    dataKey="date"
                    stroke="#64748b"
                    fontSize={11}
                    tickFormatter={(val) => val.slice(5)}
                  />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#1e293b",
                      borderRadius: "12px",
                      color: "#f8fafc",
                      fontSize: "12px",
                    }}
                  />
                  <Bar dataKey="submissions_count" name="Submissions" fill="#6366f1" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="active_students" name="Active Students" fill="#06b6d4" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-slate-500">No telemetry recorded this week.</div>
            )}
          </ChartCard>
        </div>

        {/* Top Performers Leaderboard Card */}
        <Card className="flex flex-col">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-surface-800 pb-3">
            <div className="flex items-center gap-2">
              <Award className="h-4 w-4 text-amber-500" />
              <h3 className="font-semibold text-slate-900 dark:text-white tracking-tight text-base">Top Performers</h3>
            </div>
            <Link to="/admin/students" className="text-xs font-semibold text-brand-600 dark:text-brand-400 hover:underline">
              View All
            </Link>
          </div>

          <div className="mt-3 divide-y divide-slate-200/80 dark:divide-surface-800/60 flex-1">
            {dashboardData.top_performers.length === 0 ? (
              <p className="py-8 text-center text-xs text-slate-500">No student scores recorded yet.</p>
            ) : (
              dashboardData.top_performers.map((student, idx) => (
                <div key={student.id} className="py-2.5 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span
                      className={`flex h-6 w-6 items-center justify-center rounded-lg text-xs font-bold ${
                        idx === 0
                          ? "bg-amber-500/20 text-amber-500"
                          : idx === 1
                          ? "bg-slate-200 dark:bg-slate-300/20 text-slate-700 dark:text-slate-300"
                          : idx === 2
                          ? "bg-amber-700/20 text-amber-600"
                          : "bg-slate-100 dark:bg-surface-800 text-slate-600 dark:text-slate-400"
                      }`}
                    >
                      {idx + 1}
                    </span>
                    <div>
                      <p className="text-xs font-semibold text-slate-900 dark:text-white">{student.full_name}</p>
                      <p className="text-[10px] text-slate-500 dark:text-slate-400">
                        {student.student_id_number} &bull; {student.batch_code}
                      </p>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-xs font-bold text-slate-900 dark:text-white">{student.total_points}</span>
                    <div className="flex items-center gap-1 justify-end text-[10px] text-amber-500">
                      <Flame className="h-3 w-3" />
                      <span>{student.current_streak_days}d</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* Operational Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-500">
            <TrendingUp className="h-6 w-6" />
          </div>
          <div>
            <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Pass Rate</h4>
            <p className="text-xl font-bold text-slate-900 dark:text-white">
              {dashboardData.assignment_statistics.acceptance_rate}%
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {dashboardData.assignment_statistics.accepted_submissions} accepted submissions
            </p>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-500">
            <Users className="h-6 w-6" />
          </div>
          <div>
            <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Active Enrollment</h4>
            <p className="text-xl font-bold text-slate-900 dark:text-white">
              {dashboardData.active_students} Students
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {Math.round((dashboardData.active_students / Math.max(dashboardData.total_students, 1)) * 100)}% portal engagement
            </p>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-500/10 text-cyan-500">
            <FileCode className="h-6 w-6" />
          </div>
          <div>
            <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Daily Activity</h4>
            <p className="text-xl font-bold text-slate-900 dark:text-white">
              {dashboardData.today_activity.submissions_count} Runs
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">Automated sandbox grading</p>
          </div>
        </Card>
      </div>
    </div>
  );
};
