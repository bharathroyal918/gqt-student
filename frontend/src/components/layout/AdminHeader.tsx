import React from "react";
import { Menu, Sun, Moon, LogOut, User } from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import { useThemeStore } from "../../store/themeStore";
import { authApi } from "../../api/authApi";
import { useNavigate } from "react-router-dom";

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
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-surface-800 bg-surface-950/80 px-4 sm:px-6 backdrop-blur-md">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMobileSidebar}
          className="rounded-lg p-2 text-slate-400 hover:bg-surface-800 hover:text-white lg:hidden transition-colors"
          aria-label="Toggle navigation"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-2 lg:hidden">
          <img src="/gqt-icon.svg" alt="GQT" className="h-6 w-6 rounded-md object-contain" />
          <span className="font-bold text-xs text-white">GQT Admin</span>
        </div>

        <span className="hidden sm:inline-block text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Institutional Administration
        </span>
      </div>

      <div className="flex items-center gap-3">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="flex h-9 w-9 items-center justify-center rounded-xl border border-surface-800 bg-surface-900 text-slate-400 hover:text-white hover:bg-surface-800 transition-colors"
          aria-label="Toggle dark/light theme"
        >
          {theme === "dark" ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-indigo-400" />}
        </button>

        {/* User profile dropdown / info */}
        <div className="flex items-center gap-2.5 rounded-xl border border-surface-800 bg-surface-900/80 px-3 py-1.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-500/20 text-brand-400">
            <User className="h-4 w-4" />
          </div>
          <div className="hidden sm:block text-left text-xs">
            <p className="font-semibold text-white truncate max-w-[140px]">{user?.email || "Admin User"}</p>
            <p className="text-[10px] text-slate-400">Administrator</p>
          </div>
        </div>

        {/* Logout button */}
        <button
          onClick={handleLogout}
          className="flex h-9 w-9 items-center justify-center rounded-xl border border-surface-800 bg-surface-900 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
          title="Sign out"
          aria-label="Sign out"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
};
