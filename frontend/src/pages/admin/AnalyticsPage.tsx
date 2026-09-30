import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  TrendingUp,
  CheckCircle2,
  Flame,
  FolderGit2,
  Filter,
  RefreshCw,
  Star,
} from "lucide-react";
import { adminApi } from "../../api/adminApi";
import { CourseItem } from "../../types/admin";
import { Card } from "../../components/ui/Card";
import { ChartCard } from "../../components/ui/ChartCard";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Select } from "../../components/ui/Form";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: "#10b981",
  medium: "#f59e0b",
  hard: "#ef4444",
};

const SCORE_COLORS = ["#6366f1", "#3b82f6", "#0ea5e9", "#10b981", "#f59e0b"];

export const AnalyticsPage: React.FC = () => {
  const [activityDays, setActivityDays] = useState<number>(30);
  const [selectedCourse, setSelectedCourse] = useState<string>("");
  const [selectedBatch, setSelectedBatch] = useState<string>("");

  // Query Courses for Filter
  const { data: coursesData } = useQuery({
    queryKey: ["admin-courses-options"],
    queryFn: () => adminApi.getCourses({ page_size: 50 }),
  });

  // Query Dashboard Telemetry with Caching
  const {
    data: analytics,
    isLoading: isAnalyticsLoading,
    isError: isAnalyticsError,
    isFetching,
    refetch: refetchAnalytics,
  } = useQuery({
    queryKey: ["admin-analytics-dashboard", selectedCourse, selectedBatch, activityDays],
    queryFn: () =>
      adminApi.getAnalyticsDashboard({
        course_id: selectedCourse || undefined,
        batch_code: selectedBatch || undefined,
        days: activityDays,
      }),
  });

  if (isAnalyticsLoading) {
    return <LoadingState message="Aggregating platform telemetry and metrics..." />;
  }

  if (isAnalyticsError || !analytics) {
    return (
      <ErrorState
        title="Analytics Offline"
        message="Unable to compute analytics data. Check server telemetry logs."
        onRetry={() => refetchAnalytics()}
      />
    );
  }

  const timelineData = analytics.activity_timeline || [];
  const scoreData = analytics.score_distribution || [];
  const diffData = analytics.assignment_statistics?.difficulty_distribution
    ? [
        { name: "Easy", count: analytics.assignment_statistics.difficulty_distribution.easy, color: DIFFICULTY_COLORS.easy },
        { name: "Medium", count: analytics.assignment_statistics.difficulty_distribution.medium, color: DIFFICULTY_COLORS.medium },
        { name: "Hard", count: analytics.assignment_statistics.difficulty_distribution.hard, color: DIFFICULTY_COLORS.hard },
      ]
    : [];

  const coursesList = coursesData?.data || [];

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <TrendingUp className="h-6 w-6 text-brand-400" />
            Analytics & Platform Telemetry
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time curriculum progression, sandbox execution metrics, and cohort score distributions.
          </p>
        </div>

        {/* Global Action */}
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetchAnalytics()}
            disabled={isFetching}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Multi-Dimensional Filters Bar */}
      <Card className="p-4 bg-surface-900/60 border-surface-800">
        <div className="flex flex-col sm:flex-row items-center gap-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 shrink-0">
            <Filter className="h-4 w-4 text-brand-400" />
            Filters:
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full">
            {/* Timeline Filter */}
            <div>
              <Select
                value={activityDays}
                onChange={(e) => setActivityDays(Number(e.target.value))}
              >
                <option value={7}>Timeline: Last 7 Days</option>
                <option value={14}>Timeline: Last 14 Days</option>
                <option value={30}>Timeline: Last 30 Days</option>
                <option value={60}>Timeline: Last 60 Days</option>
                <option value={90}>Timeline: Last 90 Days</option>
              </Select>
            </div>

            {/* Course Filter */}
            <div>
              <Select
                value={selectedCourse}
                onChange={(e) => setSelectedCourse(e.target.value)}
              >
                <option value="">All Course Tracks</option>
                {coursesList.map((c: CourseItem) => (
                  <option key={c.id} value={c.id}>
                    {c.title}
                  </option>
                ))}
              </Select>
            </div>

            {/* Batch Filter */}
            <div>
              <Select
                value={selectedBatch}
                onChange={(e) => setSelectedBatch(e.target.value)}
              >
                <option value="">All Cohorts / Batches</option>
                <option value="BATCH-2025-A">BATCH-2025-A</option>
                <option value="BATCH-2025-B">BATCH-2025-B</option>
                <option value="BATCH-2026-A">BATCH-2026-A</option>
              </Select>
            </div>
          </div>

          {(selectedCourse || selectedBatch || activityDays !== 30) && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setSelectedCourse("");
                setSelectedBatch("");
                setActivityDays(30);
              }}
              className="text-xs shrink-0"
            >
              Reset
            </Button>
          )}
        </div>
      </Card>

      {/* Summary KPI Cards Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="p-5 bg-gradient-to-br from-surface-900 to-emerald-950/20 border-emerald-500/20">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Curriculum Completion</span>
            <div className="h-8 w-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <CheckCircle2 className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-2xl font-bold text-white">
            {analytics.module_completion_rate}%
          </div>
          <div className="mt-1 text-xs text-slate-400">
            {analytics.completed_modules_count} module completions logged
          </div>
        </Card>

        <Card className="p-5 bg-gradient-to-br from-surface-900 to-indigo-950/20 border-indigo-500/20">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Coding Pass Rate</span>
            <div className="h-8 w-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
              <TrendingUp className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-2xl font-bold text-indigo-400">
            {analytics.assignment_statistics?.acceptance_rate || 0}%
          </div>
          <div className="mt-1 text-xs text-slate-400">
            {analytics.assignment_statistics?.accepted_submissions || 0} accepted of{" "}
            {analytics.assignment_statistics?.total_submissions || 0}
          </div>
        </Card>

        <Card className="p-5 bg-gradient-to-br from-surface-900 to-amber-950/20 border-amber-500/20">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Capstone Project Approvals</span>
            <div className="h-8 w-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center">
              <FolderGit2 className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-2xl font-bold text-amber-400">
            {analytics.project_statistics?.approval_rate || 0}%
          </div>
          <div className="mt-1 text-xs text-slate-400">
            {analytics.project_statistics?.approved_submissions || 0} approved submissions
          </div>
        </Card>

        <Card className="p-5 bg-gradient-to-br from-surface-900 to-rose-950/20 border-rose-500/20">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Active Learners</span>
            <div className="h-8 w-8 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center">
              <Flame className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 text-2xl font-bold text-rose-400">
            {analytics.active_students}
          </div>
          <div className="mt-1 text-xs text-slate-400">
            Out of {analytics.total_students} registered students
          </div>
        </Card>
      </div>

      {/* Main Charts Section */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Activity Timeline Chart (2 cols) */}
        <div className="lg:col-span-2">
          <ChartCard
            title={`Daily Activity Timeline (Past ${activityDays} Days)`}
            description="Active learners and total evaluated code submissions over time"
          >
            <div className="h-80 w-full pt-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={timelineData}
                  margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="colorStudents" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="colorSubmissions" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    dataKey="label"
                    stroke="#64748b"
                    fontSize={11}
                  />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      borderRadius: "0.75rem",
                      fontSize: "12px",
                      color: "#fff",
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "12px" }} />
                  <Area
                    type="monotone"
                    dataKey="active_students"
                    name="Active Learners"
                    stroke="#6366f1"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorStudents)"
                  />
                  <Area
                    type="monotone"
                    dataKey="submissions_count"
                    name="Code Submissions"
                    stroke="#10b981"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorSubmissions)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>
        </div>

        {/* Question Difficulty Breakdown */}
        <div className="lg:col-span-1">
          <ChartCard
            title="Question Difficulty Mix"
            description="Active algorithmic challenges"
          >
            <div className="h-80 w-full pt-4 flex flex-col items-center justify-center">
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={diffData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="count"
                  >
                    {diffData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      borderRadius: "0.75rem",
                      fontSize: "12px",
                      color: "#fff",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex gap-4 text-xs mt-2">
                {diffData.map((d) => (
                  <div key={d.name} className="flex items-center gap-1.5">
                    <div className="h-3 w-3 rounded-full" style={{ backgroundColor: d.color }} />
                    <span className="text-slate-300">
                      {d.name}: <strong className="text-white">{d.count}</strong>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </ChartCard>
        </div>
      </div>

      {/* Second Row Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Score Distribution BarChart */}
        <ChartCard
          title="Cohort Score Distribution"
          description="Number of students in each points bracket"
        >
          <div className="h-72 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoreData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="bracket" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#334155",
                    borderRadius: "0.75rem",
                    fontSize: "12px",
                    color: "#fff",
                  }}
                />
                <Bar dataKey="count" name="Students" radius={[6, 6, 0, 0]}>
                  {scoreData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={SCORE_COLORS[index % SCORE_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        {/* Top Performers Widget */}
        <Card className="p-6 border-surface-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-surface-800 pb-4">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Star className="h-4 w-4 text-amber-400 fill-amber-400" />
                  Top Cohort Performers
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Leading students by accumulated assessment points
                </p>
              </div>
              <Badge variant="amber" size="sm">
                Top 5
              </Badge>
            </div>

            <div className="mt-4 divide-y divide-surface-800/60">
              {analytics.top_performers?.length === 0 ? (
                <div className="py-8 text-center text-xs text-slate-500">
                  No active student scores logged yet.
                </div>
              ) : (
                analytics.top_performers.map((student, idx) => (
                  <div key={student.id} className="py-3 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-surface-800 font-bold text-xs text-slate-300">
                        #{idx + 1}
                      </div>
                      <div>
                        <div className="text-xs font-semibold text-white">
                          {student.full_name}
                        </div>
                        <div className="text-[11px] text-slate-400">
                          {student.student_id_number} • {student.batch_code}
                        </div>
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="text-xs font-bold text-amber-300">
                        {student.total_points.toLocaleString()} pts
                      </div>
                      <div className="text-[11px] text-rose-400 flex items-center justify-end gap-1">
                        <Flame className="h-3 w-3" />
                        {student.current_streak_days}d streak
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
