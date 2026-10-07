import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Menu,
  Bell,
  Sun,
  Moon,
  Flame,
  Award,
  User as UserIcon,
  LogOut,
  ChevronDown,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "../../store/authStore";
import { useThemeStore } from "../../store/themeStore";
import { authApi } from "../../api/authApi";
import { studentApi } from "../../api/studentApi";
import { UserAvatar } from "../ui/UserAvatar";
import { Breadcrumbs } from "../ui/Breadcrumbs";

interface StudentHeaderProps {
  onToggleMobileSidebar: () => void;
}

export const StudentHeader: React.FC<StudentHeaderProps> = ({ onToggleMobileSidebar }) => {
  const { user, studentProfile, clearAuth } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();
  const navigate = useNavigate();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const { data: unreadCount = 0 } = useQuery({
    queryKey: ["student", "notifications", "unread-count"],
    queryFn: studentApi.getUnreadNotificationsCount,
    refetchInterval: 30000,
    enabled: !!user,
  });

  const { data: dashboardData } = useQuery({
    queryKey: ["student", "dashboard"],
    queryFn: studentApi.getDashboard,
    enabled: !!user && user.role === "STUDENT",
    staleTime: 10000,
  });

  const handleLogout = async () => {
    try {
      const refreshToken = localStorage.getItem("gqt_refresh_token");
      if (refreshToken) {
        await authApi.logout(refreshToken);
      }
    } catch {
      // Continue client cleanup even if API fails
    } finally {
      clearAuth();
      navigate("/login");
    }
  };

  const effectiveStreak =
    dashboardData?.profile?.current_streak_days ??
    studentProfile?.current_streak_days ??
    0;

  const effectivePoints =
    dashboardData?.profile?.total_score ??
    studentProfile?.total_points ??
    0;

  const pointsFormatted = Number(effectivePoints).toLocaleString();
  const solvedToday = dashboardData?.activity_heatmap?.solved_today ?? false;
  const displayName = dashboardData?.profile?.full_name || studentProfile?.full_name || user?.email || "Student";
  const avatarUrl = dashboardData?.profile?.avatar_url || studentProfile?.avatar_url;
  const initials = displayName.slice(0, 2).toUpperCase();

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 dark:border-surface-800 bg-white/90 dark:bg-surface-950/90 px-4 sm:px-6 lg:px-8 backdrop-blur-md z-30 transition-colors duration-200">
      {/* Left: Mobile Toggle & Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMobileSidebar}
          className="rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-100 dark:bg-surface-900 p-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-surface-800 lg:hidden transition-colors"
          aria-label="Toggle navigation menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-2 lg:hidden">
          <img src="/gqt-icon.svg" alt="GQT" className="h-6 w-6 rounded-md object-contain" />
          <span className="font-bold text-xs text-slate-900 dark:text-white">GQT Portal</span>
        </div>

        <div className="hidden sm:block">
          <Breadcrumbs />
        </div>
      </div>

      {/* Right: Telemetry (Streak, Points) & Actions */}
      <div className="flex items-center gap-2.5 sm:gap-4">
        {/* Streak Counter Pill */}
        {user?.role === "STUDENT" && (
          <Link
            to="/dashboard"
            className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-bold transition-all ${
              effectiveStreak > 0
                ? solvedToday
                  ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/20 shadow-sm"
                  : "border-rose-500/30 bg-rose-500/10 text-rose-600 dark:text-rose-400 hover:bg-rose-500/20 shadow-sm"
                : "border-slate-200 dark:border-surface-700 bg-slate-100 dark:bg-surface-800/80 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
            }`}
            title={
              effectiveStreak > 0
                ? `${effectiveStreak} Day Streak - ${solvedToday ? "Solved today!" : "Solve a problem today to keep streak going!"}`
                : "Start your daily problem solving streak!"
            }
          >
            <Flame className={`h-4 w-4 ${effectiveStreak > 0 ? "animate-pulse fill-rose-500 text-rose-500" : "text-slate-400"}`} />
            <span>{effectiveStreak} {effectiveStreak === 1 ? "day" : "days"}</span>
            {solvedToday && (
              <span className="flex h-1.5 w-1.5 rounded-full bg-emerald-500 ring-2 ring-white dark:ring-surface-950" />
            )}
          </Link>
        )}

        {/* Points Pill */}
        {user?.role === "STUDENT" && (
          <Link
            to="/dashboard"
            className="hidden sm:flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-bold text-amber-600 dark:text-amber-300 hover:bg-amber-500/20 transition-all"
            title="Total Score Points"
          >
            <Award className="h-4 w-4" />
            <span>{pointsFormatted} pts</span>
          </Link>
        )}

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          className="rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-100 dark:bg-surface-900 p-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-surface-800 transition-colors"
          title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          {theme === "dark" ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-indigo-600" />}
        </button>

        {/* Notifications Icon Button */}
        <Link
          to="/notifications"
          className="relative rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-100 dark:bg-surface-900 p-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-surface-800 transition-colors"
          title="Notifications"
        >
          <Bell className="h-4 w-4" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-brand-500 px-1 text-[10px] font-bold text-white shadow-sm">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </Link>

        {/* User Profile Dropdown */}
        {user && (
          <div className="relative">
            <button
              onClick={() => setIsDropdownOpen((prev) => !prev)}
              className="flex items-center gap-2 rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900/80 p-1.5 pr-3 text-left hover:bg-slate-100 dark:hover:bg-surface-800 transition-colors group"
            >
              <UserAvatar
                src={avatarUrl}
                name={displayName}
                initials={initials}
                size="sm"
                className="group-hover:scale-105 transition-transform"
              />
              <div className="hidden md:block">
                <div className="text-xs font-semibold text-slate-900 dark:text-white leading-none truncate max-w-[130px]">{displayName}</div>
                <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5 truncate max-w-[130px]">{studentProfile?.student_id_number || "Student"}</div>
              </div>
              <ChevronDown className="h-3 w-3 text-slate-400 ml-1" />
            </button>

            {/* Dropdown Menu */}
            {isDropdownOpen && (
              <>
                <div
                  className="fixed inset-0 z-30"
                  onClick={() => setIsDropdownOpen(false)}
                />
                <div className="absolute right-0 mt-2 w-52 rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-2 shadow-2xl z-40">
                  <div className="px-3 py-2 border-b border-slate-100 dark:border-surface-800 mb-1">
                    <p className="text-xs font-semibold text-slate-900 dark:text-white truncate">{displayName}</p>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">{user.email || user.mobile_number}</p>
                  </div>

                  <Link
                    to="/profile"
                    onClick={() => setIsDropdownOpen(false)}
                    className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-surface-800 hover:text-slate-900 dark:hover:text-white transition-colors"
                  >
                    <UserIcon className="h-4 w-4 text-slate-400" />
                    <span>My Profile</span>
                  </Link>

                  <button
                    onClick={() => {
                      setIsDropdownOpen(false);
                      handleLogout();
                    }}
                    className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-rose-500 hover:bg-rose-500/10 hover:text-rose-600 dark:hover:text-rose-300 transition-colors"
                  >
                    <LogOut className="h-4 w-4" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </header>
  );
};
