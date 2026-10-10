import React from "react";
import { NavLink, Link } from "react-router-dom";
import {
  AlertTriangle,
  BookOpen,
  Building2,
  CalendarCheck,
  Code2,
  FileSpreadsheet,
  LayoutDashboard,
  LogOut,
  TrendingUp,
  UserCheck,
  Users,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { BrandLogo } from "../common/BrandLogo";
import { useAuthStore } from "../../store/authStore";
import { UserAvatar } from "../ui/UserAvatar";
import { tpoApi } from "../../api/tpoApi";
import { authApi } from "../../api/authApi";

interface TPOSidebarProps {
  isOpen: boolean;
  onCloseMobile: () => void;
}

export const TPOSidebar: React.FC<TPOSidebarProps> = ({ isOpen, onCloseMobile }) => {
  const { user, clearAuth } = useAuthStore();

  const { data: profile } = useQuery({
    queryKey: ["tpo-profile-me", user?.id],
    queryFn: tpoApi.getMe,
    staleTime: 60 * 1000,
  });

  const tpoName = profile?.full_name || user?.email || "TPO Officer";
  const tpoAvatar = profile?.avatar_url;
  const tpoInitials = tpoName.slice(0, 2).toUpperCase();
  const college = profile?.college;

  const handleLogout = async () => {
    const refreshToken = localStorage.getItem("gqt_refresh_token");
    if (refreshToken) {
      try {
        await authApi.logout(refreshToken);
      } catch (e) {
        // Silently continue
      }
    }
    clearAuth();
    window.location.href = "/login";
  };

  const navItems = [
    { name: "Overview", href: "/tpo/dashboard", icon: LayoutDashboard },
    { name: "Student Directory", href: "/tpo/students", icon: Users },
    { name: "Learning Progress", href: "/tpo/learning-progress", icon: BookOpen },
    { name: "Assignments & Labs", href: "/tpo/assignments-labs", icon: Code2 },
    { name: "Attendance", href: "/tpo/attendance", icon: CalendarCheck },
    { name: "Performance Trends", href: "/tpo/trends", icon: TrendingUp },
    { name: "Students Needing Support", href: "/tpo/students-needing-support", icon: AlertTriangle },
    { name: "Reports & Exports", href: "/tpo/reports", icon: FileSpreadsheet },
    { name: "Officer Profile", href: "/tpo/profile", icon: UserCheck },
  ];


  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 z-40 bg-black/80 backdrop-blur-sm lg:hidden"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-950 transition-transform duration-300 ease-in-out lg:static lg:translate-x-0 ${isOpen ? "translate-x-0" : "-translate-x-full"
          }`}
      >
        {/* Brand Logo Header */}
        <div className="flex h-16 shrink-0 items-center border-b border-slate-200 dark:border-surface-800 px-5 bg-white dark:bg-surface-950">
          <BrandLogo
            variant="sidebar"
            badge="TPO Portal"
            badgeVariant="admin"
            subtitle="Training & Placement"
          />
        </div>

        {/* Assigned College Banner */}
        {college && (
          <div className="p-3.5 mx-3 mt-3 rounded-xl bg-gradient-to-br from-brand-500/10 to-brand-600/5 border border-brand-500/20">
            <div className="flex items-center gap-2 text-brand-600 dark:text-brand-400 font-semibold text-xs mb-1">
              <Building2 className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">Assigned Institution</span>
            </div>
            <p className="text-xs font-bold text-slate-900 dark:text-white line-clamp-2">
              {college.name}
            </p>
            {college.city && (
              <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
                {college.city}, {college.state}
              </p>
            )}
          </div>
        )}

        {/* Officer Quick Profile Link */}
        <Link
          to="/tpo/profile"
          onClick={onCloseMobile}
          className="p-3 mx-3 my-2 border border-slate-200 dark:border-surface-800 rounded-xl bg-slate-50 dark:bg-surface-900/60 hover:bg-slate-100 dark:hover:bg-surface-900 transition-colors flex items-center gap-3 group"
        >
          <UserAvatar
            src={tpoAvatar}
            name={tpoName}
            initials={tpoInitials}
            size="md"
            className="group-hover:scale-105 transition-transform"
          />
          <div className="min-w-0 flex-1">
            <div className="font-semibold text-slate-900 dark:text-white text-xs truncate group-hover:text-brand-600 dark:group-hover:text-brand-400 transition-colors">
              {tpoName}
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-brand-500/10 text-brand-600 dark:text-brand-400 truncate max-w-[130px]">
                {profile?.designation || "Placement Officer"}
              </span>
            </div>
          </div>
        </Link>

        {/* Navigation Items */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              onClick={onCloseMobile}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${isActive
                  ? "bg-brand-600 text-white shadow-md shadow-brand-500/20 font-semibold"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-surface-900 hover:text-slate-900 dark:hover:text-white"
                }`
              }
            >
              <item.icon className="h-4 w-4 shrink-0" />
              <span>{item.name}</span>
            </NavLink>
          ))}
        </div>

        {/* Footer Logout */}
        <div className="p-3 border-t border-slate-200 dark:border-surface-800">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign Out
          </button>
        </div>
      </aside>
    </>
  );
};
