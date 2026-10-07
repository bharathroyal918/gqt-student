import React from "react";
import { Menu, Sun, Moon, LogOut } from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import { useThemeStore } from "../../store/themeStore";
import { authApi } from "../../api/authApi";
import { useNavigate } from "react-router-dom";
import { UserAvatar } from "../ui/UserAvatar";

interface AdminHeaderProps {
  onToggleMobileSidebar: () => void;
}

export const AdminHeader: React.FC<AdminHeaderProps> = ({ onToggleMobileSidebar }) => {
  const { user, clearAuth } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    const refreshToken = localStorage.getItem("gqt_refresh_token");
    if (refreshToken) {
      try {
        await authApi.logout(refreshToken);
      } catch (e) {
        // Silently clear local auth even if network request fails
      }
    }
    clearAuth();
    navigate("/auth/login");
  };

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 dark:border-surface-800 bg-white/90 dark:bg-surface-950/90 px-4 sm:px-6 backdrop-blur-md transition-colors duration-200">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMobileSidebar}
          className="rounded-lg p-2 text-slate-500 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-surface-800 hover:text-slate-900 dark:hover:text-white lg:hidden transition-colors"
          aria-label="Toggle navigation"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-2 lg:hidden">
          <img src="/gqt-icon.svg" alt="GQT" className="h-6 w-6 rounded-md object-contain" />
          <span className="font-bold text-xs text-slate-900 dark:text-white">GQT Admin</span>
        </div>

        <span className="hidden sm:inline-block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
          Institutional Administration
        </span>
      </div>

      <div className="flex items-center gap-3">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-100 dark:bg-surface-900 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-surface-800 transition-colors"
          aria-label="Toggle dark/light theme"
        >
          {theme === "dark" ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-indigo-600" />}
        </button>

        {/* User profile link */}
        {(() => {
          const adminProfile = (user as any)?.admin_profile;
          const adminName = adminProfile?.full_name || user?.email || "Admin User";
          const adminAvatar = adminProfile?.avatar_url;
          const adminInitials = adminName.slice(0, 2).toUpperCase();

          return (
            <button
              onClick={() => navigate("/admin/profile")}
              className="flex items-center gap-2.5 rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900 p-1.5 sm:px-3 sm:py-1.5 hover:bg-slate-100 dark:hover:bg-surface-800 hover:border-brand-500/30 transition-all text-left group"
              title="View & Edit Admin Profile"
            >
              <UserAvatar
                src={adminAvatar}
                name={adminName}
                initials={adminInitials}
                size="sm"
                className="group-hover:scale-105 transition-transform"
              />
              <div className="hidden sm:block text-left text-xs">
                <p className="font-semibold text-slate-900 dark:text-white truncate max-w-[140px]">
                  {adminName}
                </p>
                <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate max-w-[140px]">
                  {adminProfile?.designation || "Administrator"}
                </p>
              </div>
            </button>
          );
        })()}

        {/* Logout button */}
        <button
          onClick={handleLogout}
          className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-100 dark:bg-surface-900 text-slate-600 dark:text-slate-300 hover:text-rose-500 hover:bg-rose-500/10 transition-colors"
          title="Sign out"
          aria-label="Sign out"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
};
