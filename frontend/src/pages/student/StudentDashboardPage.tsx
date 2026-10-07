import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Trophy,
  Flame,
  Award,
  Code2,
  CalendarCheck,
  Bell,
  RefreshCw,
  Sparkles,
  ArrowRight,
  TrendingUp,
  Clock,
  Star,
  QrCode,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";
import { useAuthStore } from "../../store/authStore";
import { studentApi, StudentDashboardData } from "../../api/studentApi";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { StreakHeatmap } from "../../components/dashboard/StreakHeatmap";
import { UserAvatar } from "../../components/ui/UserAvatar";
import { StudentAttendanceSection } from "../../components/student/StudentAttendanceSection";
import { StudentQRCodeModal } from "../../components/student/StudentQRCodeModal";

export const StudentDashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"submissions" | "tasks" | "achievements" | "notifications">("submissions");
  const [isQRModalOpen, setIsQRModalOpen] = useState(false);

  // User-aware query key ensures zero crosstalk between student sessions
  const {
    data: dashboardData,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery<StudentDashboardData>({
    queryKey: ["student", "dashboard", user?.id],
    queryFn: studentApi.getDashboard,
    enabled: !!user?.id,
    staleTime: 1000 * 30, // 30 seconds
    refetchOnWindowFocus: true,
  });

  if (isLoading) {
    return (
      <div className="flex h-96 flex-col items-center justify-center space-y-4">
        <LoadingState message="Loading your personalized academic telemetry..." />
      </div>
    );
  }

  if (isError || !dashboardData) {
    return (
      <ErrorState
        title="Unable to load dashboard"
        message={error instanceof Error ? error.message : "Failed to load live student telemetry from the backend."}
        onRetry={() => refetch()}
      />
    );
  }

  const { profile, leaderboard, progress, activity } = dashboardData;
  const isOutsideTop10 = !leaderboard.current_student.is_in_top_10;

  return (
    <div className="space-y-8 pb-12">
      {/* =========================================================================
          0. ACCESS AUTHORIZATION STATUS BANNER
         ========================================================================= */}
      {user?.onboarding_status === "PENDING_ACTIVATION" && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-5 backdrop-blur-md flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
        >
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-500/20 text-amber-500 text-lg font-bold">
              ⏳
            </div>
            <div>
              <h3 className="text-sm font-bold text-amber-900 dark:text-amber-300">
                Institutional Access Authorization Pending
              </h3>
              <p className="text-xs text-amber-800/90 dark:text-amber-300/80 mt-0.5">
                Your registered email (<strong>{user?.email}</strong>) has been submitted to the administration. Once an administrator approves your account, your full curriculum modules, daily live attendance, and coding assessments will be unlocked.
              </p>
            </div>
          </div>
          <Badge variant="amber" size="md" className="shrink-0 font-semibold">
            Awaiting Admin Approval
          </Badge>
        </motion.div>
      )}

      {/* =========================================================================
          1. PROFILE BANNER & HERO CARD
         ========================================================================= */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="relative overflow-hidden rounded-3xl border border-slate-200 dark:border-surface-800 bg-gradient-to-br from-brand-500/10 via-white dark:via-surface-900 to-white dark:to-surface-950 p-6 sm:p-8 shadow-sm backdrop-blur-xl"
      >
        <div className="relative z-10 flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          {/* Avatar & Identification */}
          <div className="flex items-center gap-5">
            <div className="relative">
              {profile.avatar_url ? (
                <img
                  src={profile.avatar_url}
                  alt={profile.full_name}
                  className="h-20 w-20 rounded-2xl object-cover ring-4 ring-brand-500/20 shadow-md"
                />
              ) : (
                <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600 to-indigo-600 text-2xl font-bold text-white shadow-md ring-4 ring-brand-500/20">
                  {profile.full_name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .slice(0, 2)
                    .toUpperCase()}
                </div>
              )}
              <span className="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500 ring-2 ring-white dark:ring-surface-900 text-[10px] font-bold text-white">
                ✓
              </span>
            </div>

            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
                  {profile.full_name}
                </h1>
                <Badge variant="indigo" size="sm">
                  {profile.batch_code}
                </Badge>
                <Badge variant="neutral" size="sm">
                  {profile.student_id_number}
                </Badge>
              </div>

              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                {profile.course}
              </p>

              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 dark:text-slate-400 pt-1">
                <span className="flex items-center gap-1 font-semibold text-rose-500 dark:text-rose-400">
                  <Flame className="h-4 w-4 fill-current" />
                  {profile.current_streak_days} Day Streak (Best: {profile.highest_streak_days})
                </span>
                <span>•</span>
                <span>{profile.college_name || "GQT Engineering Academy"}</span>
              </div>
            </div>
          </div>

          {/* Quick Actions & Refetch Trigger */}
          <div className="flex flex-wrap items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isFetching}
              className="flex items-center gap-1.5"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin text-brand-500" : ""}`} />
              <span>{isFetching ? "Refetching..." : "Live Sync"}</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsQRModalOpen(true)}
              className="flex items-center gap-1.5 border-brand-500/30 text-brand-600 dark:text-brand-400 hover:bg-brand-50 dark:hover:bg-brand-950/30 shadow-sm"
            >
              <QrCode className="h-3.5 w-3.5" />
              <span>My Attendance QR</span>
            </Button>

            <Link to="/courses">
              <Button size="sm" className="flex items-center gap-1.5">
                <span>Continue Study</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>
        </div>

        {/* Hero KPI Stat Strip */}
        <div className="mt-8 grid grid-cols-2 gap-4 border-t border-slate-200/80 dark:border-surface-800/80 pt-6 sm:grid-cols-4">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Total Score</span>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-slate-900 dark:text-white">
                {profile.total_score.toLocaleString()}
              </span>
              <span className="text-xs font-semibold text-brand-500">pts</span>
            </div>
          </div>

          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Current Rank</span>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-amber-500">
                #{profile.current_rank}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">of {profile.total_students}</span>
            </div>
          </div>

          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Completed Modules</span>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-slate-900 dark:text-white">
                {profile.completed_modules}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">/ {profile.total_modules}</span>
            </div>
          </div>

          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Curriculum Progress</span>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-emerald-500">
                {profile.overall_progress}%
              </span>
            </div>
            {/* Progress bar */}
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-surface-800">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(profile.overall_progress, 100)}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="h-full bg-emerald-500 rounded-full"
              />
            </div>
          </div>
        </div>
      </motion.div>

      {/* =========================================================================
          2. LEADERBOARD & COHORT STANDINGS
         ========================================================================= */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <div className="lg:col-span-12">
          <Card className="p-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Trophy className="h-5 w-5 text-amber-500" />
                  Cohort Leaderboard
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Live rankings based on verified coding questions, daily tasks, and capstone project performance.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Badge variant="warning" size="sm" className="flex items-center gap-1 font-semibold">
                  <Star className="h-3 w-3 fill-current" />
                  Top 3 Highlighted
                </Badge>
              </div>
            </div>

            {/* Top 3 Podium Cards */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 mb-6">
              {leaderboard.top_10.slice(0, 3).map((student, idx) => {
                const podiumColors = [
                  {
                    border: "border-amber-400/60 dark:border-amber-500/40",
                    bg: "bg-gradient-to-b from-amber-500/10 via-amber-500/5 to-transparent",
                    text: "text-amber-600 dark:text-amber-400",
                    badge: "1st Place",
                    icon: Trophy,
                  },
                  {
                    border: "border-slate-300 dark:border-slate-700/60",
                    bg: "bg-gradient-to-b from-slate-400/10 via-slate-400/5 to-transparent",
                    text: "text-slate-600 dark:text-slate-300",
                    badge: "2nd Place",
                    icon: Award,
                  },
                  {
                    border: "border-amber-700/30 dark:border-amber-700/40",
                    bg: "bg-gradient-to-b from-amber-700/10 via-amber-700/5 to-transparent",
                    text: "text-amber-800 dark:text-amber-500",
                    badge: "3rd Place",
                    icon: Award,
                  },
                ][idx];

                const IconComponent = podiumColors.icon;

                return (
                  <motion.div
                    key={student.student_id}
                    initial={{ scale: 0.95, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: idx * 0.1 }}
                    className={`relative rounded-2xl border ${podiumColors.border} ${podiumColors.bg} p-5 flex flex-col justify-between shadow-sm transition-all hover:scale-[1.02] ${
                      student.is_current_student ? "ring-2 ring-brand-500" : ""
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <span className={`text-xs font-bold uppercase tracking-wider ${podiumColors.text}`}>
                          {podiumColors.badge}
                        </span>
                        <IconComponent className={`h-5 w-5 ${podiumColors.text}`} />
                      </div>

                      <div className="flex items-center gap-3">
                        <UserAvatar
                          src={student.avatar_url}
                          name={student.full_name}
                          size="lg"
                          className="!h-12 !w-12 rounded-xl ring-2 ring-slate-200 dark:ring-surface-700 shadow-sm shrink-0"
                        />

                        <div className="overflow-hidden">
                          <p className="font-bold text-slate-900 dark:text-white truncate">
                            {student.full_name}
                            {student.is_current_student && (
                              <span className="ml-1.5 text-[10px] text-brand-600 dark:text-brand-400 font-semibold">(You)</span>
                            )}
                          </p>
                          <span className="text-xs text-slate-500 dark:text-slate-400">{student.batch_code}</span>
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-200/60 dark:border-surface-800/80 flex items-center justify-between">
                      <span className="text-xs text-slate-500 dark:text-slate-400">Verified Points</span>
                      <span className="text-sm font-black text-slate-900 dark:text-white">
                        {student.total_points.toLocaleString()} pts
                      </span>
                    </div>
                  </motion.div>
                );
              })}
            </div>

            {/* Ranks 4 to 10 Table */}
            <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-surface-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 dark:bg-surface-900/80 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Rank</th>
                    <th className="px-4 py-3">Student</th>
                    <th className="px-4 py-3">Cohort Batch</th>
                    <th className="px-4 py-3 text-right">Total Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-surface-800">
                  {leaderboard.top_10.slice(3).map((item) => (
                    <tr
                      key={item.student_id}
                      className={`transition-colors hover:bg-slate-50/50 dark:hover:bg-surface-800/40 ${
                        item.is_current_student
                          ? "bg-brand-500/10 font-bold dark:bg-brand-500/15"
                          : ""
                      }`}
                    >
                      <td className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">
                        #{item.rank}
                      </td>
                      <td className="px-4 py-3 flex items-center gap-2.5">
                        <UserAvatar
                          src={item.avatar_url}
                          name={item.full_name}
                          size="sm"
                          className="!h-7 !w-7 rounded-lg shadow-sm shrink-0"
                        />
                        <span className="text-slate-900 dark:text-white">
                          {item.full_name}
                          {item.is_current_student && (
                            <Badge variant="indigo" size="sm" className="ml-2">
                              You
                            </Badge>
                          )}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-500 dark:text-slate-400">
                        {item.batch_code}
                      </td>
                      <td className="px-4 py-3 text-right font-mono font-bold text-slate-900 dark:text-white">
                        {item.total_points.toLocaleString()} pts
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pinned Card If Student Is Outside Top 10 */}
            {isOutsideTop10 && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 flex flex-col sm:flex-row items-center justify-between rounded-xl border border-brand-500/30 bg-brand-500/10 px-5 py-3.5 text-sm"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-500 text-white font-bold text-xs">
                    #{leaderboard.current_student.rank}
                  </div>
                  <div>
                    <span className="font-bold text-slate-900 dark:text-white">
                      Your Global Cohort Position
                    </span>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      Currently ranked #{leaderboard.current_student.rank} of {profile.total_students} students
                    </p>
                  </div>
                </div>

                <div className="mt-2 sm:mt-0 flex items-center gap-3">
                  <span className="font-mono font-bold text-brand-600 dark:text-brand-400">
                    {leaderboard.current_student.total_points.toLocaleString()} pts
                  </span>
                  <Link to="/assignments">
                    <Button size="sm">
                      <span>Solve Problems to Climb</span>
                      <ArrowRight className="h-3.5 w-3.5 ml-1" />
                    </Button>
                  </Link>
                </div>
              </motion.div>
            )}
          </Card>
        </div>
      </div>

      {/* =========================================================================
          2.5 LEETCODE-STYLE STREAK & YEARLY ACTIVITY HEATMAP
         ========================================================================= */}
      <StreakHeatmap data={dashboardData.activity_heatmap} />

      {/* =========================================================================
          3. PROGRESS & ANALYTICS CHARTS
         ========================================================================= */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Weekly Score Trend Area Chart */}
        <div className="lg:col-span-7">
          <Card className="p-6 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-brand-500" />
                    Score History (Last 7 Days)
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Live chronological delta points accumulated each day
                  </p>
                </div>
                <Badge variant="indigo" size="sm">
                  Live Trend
                </Badge>
              </div>

              <div className="h-64 w-full pt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={progress.chart_history}>
                    <defs>
                      <linearGradient id="scoreGlow" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.6} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <XAxis
                      dataKey="date"
                      stroke="#94a3b8"
                      fontSize={11}
                      tickLine={false}
                      axisLine={{ stroke: "#334155", strokeWidth: 0.5 }}
                    />
                    <YAxis
                      stroke="#94a3b8"
                      fontSize={11}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div className="rounded-xl border border-surface-700 bg-surface-900 p-2.5 shadow-xl text-xs text-white">
                              <p className="font-semibold text-brand-400">{data.full_date}</p>
                              <p className="font-bold text-sm mt-0.5">+{data.points} Points Earned</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="points"
                      stroke="#6366f1"
                      strokeWidth={2.5}
                      fillOpacity={1}
                      fill="url(#scoreGlow)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* 3 Metric Cards for Module, Assignment, Project */}
            <div className="grid grid-cols-3 gap-3 pt-4 border-t border-slate-200 dark:border-surface-800 mt-4 text-center">
              <div>
                <span className="text-[11px] text-slate-500 dark:text-slate-400 uppercase font-semibold">
                  Modules
                </span>
                <p className="text-base font-bold text-slate-900 dark:text-white mt-0.5">
                  {progress.module_completion.completed}/{progress.module_completion.total}
                </p>
                <span className="text-[10px] text-emerald-500 font-semibold">
                  {progress.module_completion.percentage}% Done
                </span>
              </div>

              <div>
                <span className="text-[11px] text-slate-500 dark:text-slate-400 uppercase font-semibold">
                  Problems Solved
                </span>
                <p className="text-base font-bold text-slate-900 dark:text-white mt-0.5">
                  {progress.assignment_progress.solved}/{progress.assignment_progress.total}
                </p>
                <span className="text-[10px] text-brand-500 font-semibold">
                  {progress.assignment_progress.total_points} pts
                </span>
              </div>

              <div>
                <span className="text-[11px] text-slate-500 dark:text-slate-400 uppercase font-semibold">
                  Projects Approved
                </span>
                <p className="text-base font-bold text-slate-900 dark:text-white mt-0.5">
                  {progress.project_score.approved}/{progress.project_score.submitted}
                </p>
                <span className="text-[10px] text-indigo-500 font-semibold">
                  {progress.project_score.total_score} pts
                </span>
              </div>
            </div>
          </Card>
        </div>

        {/* Skills Mastery Radar Chart */}
        <div className="lg:col-span-5">
          <Card className="p-6 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-indigo-500" />
                  Skills Mastery Matrix
                </h3>
                <Badge variant="neutral" size="sm">
                  Full Spectrum
                </Badge>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">
                Evaluation across coursework, daily tasks, labs, and streak persistence.
              </p>

              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={progress.skills_radar} outerRadius="75%">
                    <PolarGrid stroke="#334155" />
                    <PolarAngleAxis
                      dataKey="skill"
                      tick={{ fill: "#94a3b8", fontSize: 10 }}
                    />
                    <PolarRadiusAxis
                      angle={30}
                      domain={[0, 100]}
                      tick={{ fill: "#64748b", fontSize: 9 }}
                    />
                    <Radar
                      name="Student Mastery"
                      dataKey="score"
                      stroke="#818cf8"
                      fill="#6366f1"
                      fillOpacity={0.45}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900/60 p-3 mt-4 flex items-center justify-between text-xs">
              <span className="text-slate-600 dark:text-slate-400">Daily Task Completions:</span>
              <span className="font-bold text-slate-900 dark:text-white">
                {progress.task_progress.completed} Tasks ({progress.task_progress.total_points} pts)
              </span>
            </div>
          </Card>
        </div>
      </div>

      {/* =========================================================================
          4. TABBED ACTIVITY & NOTIFICATIONS GRID
         ========================================================================= */}
      <Card className="p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 dark:border-surface-800 pb-4 mb-6">
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Clock className="h-5 w-5 text-brand-500" />
              Activity Stream & Alerts
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
              Live audit trail of your code runs, daily challenge completions, badges, and alerts.
            </p>
          </div>

          {/* Navigation Pill Tabs */}
          <div className="flex flex-wrap items-center gap-1.5 rounded-xl border border-slate-200 dark:border-surface-800 p-1 bg-slate-50 dark:bg-surface-900">
            <button
              onClick={() => setActiveTab("submissions")}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                activeTab === "submissions"
                  ? "bg-brand-600 text-white shadow-sm font-bold"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              Code Runs ({activity.recent_submissions.length})
            </button>
            <button
              onClick={() => setActiveTab("tasks")}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                activeTab === "tasks"
                  ? "bg-brand-600 text-white shadow-sm font-bold"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              Daily Tasks ({activity.recent_tasks.length})
            </button>
            <button
              onClick={() => setActiveTab("achievements")}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                activeTab === "achievements"
                  ? "bg-brand-600 text-white shadow-sm font-bold"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              Badges ({activity.recent_achievements.length})
            </button>
            <button
              onClick={() => setActiveTab("notifications")}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                activeTab === "notifications"
                  ? "bg-brand-600 text-white shadow-sm font-bold"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              Notifications ({activity.notifications.length})
            </button>
          </div>
        </div>

        {/* Tab Content Panes */}
        <AnimatePresence mode="wait">
          {activeTab === "submissions" && (
            <motion.div
              key="submissions"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="space-y-3"
            >
              {activity.recent_submissions.length === 0 ? (
                <div className="py-12 text-center text-xs text-slate-500 dark:text-slate-400">
                  <Code2 className="h-8 w-8 mx-auto mb-2 text-slate-400 dark:text-slate-600 opacity-60" />
                  No code submissions recorded yet. Head over to Coding Labs to get started!
                </div>
              ) : (
                activity.recent_submissions.map((sub) => (
                  <div
                    key={sub.id}
                    className="flex flex-col sm:flex-row sm:items-center sm:justify-between rounded-xl border border-slate-200 dark:border-surface-800 p-4 transition-colors hover:border-brand-500/40"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500/10 text-brand-600 dark:text-brand-400 font-bold">
                        <Code2 className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="font-semibold text-slate-900 dark:text-white text-sm">
                          {sub.question_title}
                        </p>
                        <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                          <span className="uppercase font-semibold text-slate-600 dark:text-slate-400">{sub.language}</span>
                          <span>•</span>
                          <span>{sub.execution_time_ms ? `${sub.execution_time_ms}ms` : "N/A"}</span>
                          <span>•</span>
                          <span>{new Date(sub.submitted_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>

                    <div className="mt-3 sm:mt-0 flex items-center gap-3">
                      <Badge
                        variant={
                          sub.status === "ACCEPTED"
                            ? "success"
                            : sub.status === "WRONG_ANSWER"
                            ? "danger"
                            : "neutral"
                        }
                      >
                        {sub.status.replace("_", " ")}
                      </Badge>
                      <span className="font-mono font-bold text-sm text-slate-900 dark:text-white">
                        +{sub.score_awarded} pts
                      </span>
                    </div>
                  </div>
                ))
              )}
            </motion.div>
          )}

          {activeTab === "tasks" && (
            <motion.div
              key="tasks"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="space-y-3"
            >
              {activity.recent_tasks.length === 0 ? (
                <div className="py-12 text-center text-xs text-slate-500 dark:text-slate-400">
                  <CalendarCheck className="h-8 w-8 mx-auto mb-2 text-slate-400 dark:text-slate-600 opacity-60" />
                  No completed daily tasks recorded yet. Maintain your streak on the Tasks page!
                </div>
              ) : (
                activity.recent_tasks.map((task) => (
                  <div
                    key={task.id}
                    className="flex flex-col sm:flex-row sm:items-center sm:justify-between rounded-xl border border-slate-200 dark:border-surface-800 p-4 transition-colors hover:border-brand-500/40"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/10 text-rose-500 font-bold">
                        <Flame className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="font-semibold text-slate-900 dark:text-white text-sm">
                          {task.task_title}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                          Scheduled for: {task.scheduled_date} • Completed: {new Date(task.completed_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>

                    <div className="mt-3 sm:mt-0 flex items-center gap-3">
                      <Badge variant="success">Completed</Badge>
                      <span className="font-mono font-bold text-sm text-slate-900 dark:text-white">
                        +{task.score_awarded} pts
                      </span>
                    </div>
                  </div>
                ))
              )}
            </motion.div>
          )}

          {activeTab === "achievements" && (
            <motion.div
              key="achievements"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="grid grid-cols-1 gap-4 sm:grid-cols-2"
            >
              {activity.recent_achievements.length === 0 ? (
                <div className="col-span-2 py-12 text-center text-xs text-slate-500 dark:text-slate-400">
                  <Award className="h-8 w-8 mx-auto mb-2 text-slate-400 dark:text-slate-600 opacity-60" />
                  No badges unlocked yet. Keep solving assignments and building your streak!
                </div>
              ) : (
                activity.recent_achievements.map((ach) => (
                  <div
                    key={ach.id}
                    className="flex items-start gap-3.5 rounded-xl border border-slate-200 dark:border-surface-800 p-4"
                  >
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-amber-500/10 text-amber-500 font-bold">
                      <Award className="h-6 w-6" />
                    </div>
                    <div>
                      <h4 className="font-bold text-slate-900 dark:text-white text-sm">
                        {ach.badge_name}
                      </h4>
                      <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                        {ach.badge_description}
                      </p>
                      <span className="text-[10px] text-slate-500 dark:text-slate-400 block mt-2">
                        Unlocked on {new Date(ach.awarded_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </motion.div>
          )}

          {activeTab === "notifications" && (
            <motion.div
              key="notifications"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="space-y-3"
            >
              {activity.notifications.length === 0 ? (
                <div className="py-12 text-center text-xs text-slate-500 dark:text-slate-400">
                  <Bell className="h-8 w-8 mx-auto mb-2 text-slate-400 dark:text-slate-600 opacity-60" />
                  You're all caught up! No unread notifications.
                </div>
              ) : (
                activity.notifications.map((notif) => (
                  <div
                    key={notif.id}
                    className={`flex items-start gap-3.5 rounded-xl border p-4 transition-colors ${
                      notif.is_read
                        ? "border-slate-200 dark:border-surface-800 bg-transparent"
                        : "border-brand-500/40 bg-brand-500/5 dark:bg-brand-500/10"
                    }`}
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-500/10 text-brand-600 dark:text-brand-400 font-bold">
                      <Bell className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h4 className="font-semibold text-slate-900 dark:text-white text-sm">
                          {notif.title}
                        </h4>
                        <span className="text-[10px] text-slate-500 dark:text-slate-400">
                          {new Date(notif.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 leading-relaxed">
                        {notif.body}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </Card>

      {/* =========================================================================
          5. DAILY ATTENDANCE & TECHNOLOGY BREAKDOWN MODULE
         ========================================================================= */}
      <StudentAttendanceSection />

      {/* Global QR Code Modal */}
      <StudentQRCodeModal
        isOpen={isQRModalOpen}
        onClose={() => setIsQRModalOpen(false)}
      />
    </div>
  );
};
