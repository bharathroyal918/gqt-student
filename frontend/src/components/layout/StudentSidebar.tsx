import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { BrandLogo } from "../common/BrandLogo";
import {
  LayoutDashboard,
  BookOpen,
  Code2,
  CalendarCheck,
  FolderGit2,
  Sparkles,
  Bell,
  User,
  Mail,
  LogOut,
  Flame,
  Sun,
  Moon,
  Briefcase,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "../../store/authStore";
import { useThemeStore } from "../../store/themeStore";
import { authApi } from "../../api/authApi";
import { studentApi } from "../../api/studentApi";
import { Badge } from "../ui/Badge";
import { UserAvatar } from "../ui/UserAvatar";

interface StudentSidebarProps {
  isOpen: boolean;
  onCloseMobile: () => void;
}

export const StudentSidebar: React.FC<StudentSidebarProps> = ({ isOpen, onCloseMobile }) => {
  const { user, studentProfile, clearAuth } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();
  const navigate = useNavigate();

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
      // Continue client cleanup even if API network request fails
    } finally {
      clearAuth();
      navigate("/login");
    }
  };

  const navItems = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Placement Drives", href: "/placements", icon: Briefcase },
    { name: "Courses", href: "/courses", icon: BookOpen },
    { name: "Assignments", href: "/assignments", icon: Code2 },
    { name: "Daily Tasks", href: "/tasks", icon: CalendarCheck },
    { name: "Projects", href: "/projects", icon: FolderGit2 },
    { name: "Help AI", href: "/help-ai", icon: Sparkles },
    { name: "Notifications", href: "/notifications", icon: Bell },
    { name: "Profile", href: "/profile", icon: User },
    { name: "Contact", href: "/contact", icon: Mail },
  ];

  const effectiveStreak =
    dashboardData?.profile?.current_streak_days ??
    studentProfile?.current_streak_days ??
    0;

  const displayName = dashboardData?.profile?.full_name || studentProfile?.full_name || user?.email || "Student";
  const avatarUrl = dashboardData?.profile?.avatar_url || studentProfile?.avatar_url;
  const initials = displayName.slice(0, 2).toUpperCase();

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm lg:hidden"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-950 transition-all duration-300 lg:static lg:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Brand Logo Header */}
        <div className="flex h-16 shrink-0 items-center border-b border-slate-200 dark:border-surface-800 px-5 bg-white dark:bg-surface-950">
          <BrandLogo
            variant="sidebar"
            badge="Student"
            badgeVariant="student"
            subtitle="Learning & Assessment"
          />
        </div>

        {/* Student Profile Quick Banner */}
        {user && (
          <div className="p-4 border-b border-slate-200 dark:border-surface-800/80 bg-slate-50 dark:bg-surface-900/40">
            <div className="flex items-center gap-3">
              <UserAvatar
                src={avatarUrl}
                name={displayName}
                initials={initials}
                size="md"
              />
              <div className="min-w-0 flex-1">
                <div className="font-semibold text-slate-900 dark:text-white text-xs truncate">{displayName}</div>
                <div className="flex items-center gap-2 mt-0.5">
                  {(dashboardData?.profile?.batch_code || studentProfile?.batch_code) && (
                    <Badge variant="indigo" size="sm">
                      {dashboardData?.profile?.batch_code || studentProfile?.batch_code}
                    </Badge>
                  )}
                  <span className="flex items-center gap-0.5 text-[11px] font-bold text-rose-500 dark:text-rose-400">
                    <Flame className={`h-3 w-3 ${effectiveStreak > 0 ? "animate-pulse fill-rose-500" : ""}`} />
                    {effectiveStreak}d
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Navigation links */}
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.name}
                to={item.href}
                onClick={onCloseMobile}
                className={({ isActive }) =>
                  `group flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? "bg-brand-600 text-white shadow-md shadow-brand-500/25 font-semibold"
                      : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-surface-900 hover:text-slate-900 dark:hover:text-white"
                  }`
                }
              >
                <Icon className="h-4 w-4 shrink-0 transition-transform duration-150 group-hover:scale-110" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Footer with Theme toggle & Logout */}
        <div className="border-t border-slate-200 dark:border-surface-800 p-4 space-y-2">
          {/* Quick theme toggle */}
          <button
            onClick={toggleTheme}
            className="flex w-full items-center justify-between rounded-xl px-3 py-2 text-xs font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-surface-900 hover:text-slate-900 dark:hover:text-white transition-colors"
          >
            <span className="flex items-center gap-2">
              {theme === "dark" ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-indigo-600" />}
              <span>{theme === "dark" ? "Light Mode" : "Dark Mode"}</span>
            </span>
            <span className="text-[10px] uppercase font-mono text-slate-400 dark:text-slate-500">{theme}</span>
          </button>

          {/* Logout button */}
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-rose-500 hover:bg-rose-500/10 hover:text-rose-600 dark:hover:text-rose-300 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>
    </>
  );
};
