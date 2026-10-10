import React from "react";
import { Menu, Sun, Moon, Building2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "../../store/authStore";
import { useThemeStore } from "../../store/themeStore";
import { tpoApi } from "../../api/tpoApi";
import { UserAvatar } from "../ui/UserAvatar";

interface TPOHeaderProps {
  onToggleMobileSidebar: () => void;
}

export const TPOHeader: React.FC<TPOHeaderProps> = ({ onToggleMobileSidebar }) => {
  const { user } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();

  const { data: profile } = useQuery({
    queryKey: ["tpo-profile-me", user?.id],
    queryFn: tpoApi.getMe,
    staleTime: 60 * 1000,
  });

  const tpoName = profile?.full_name || user?.email || "TPO Officer";
  const college = profile?.college;

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 dark:border-surface-800 bg-white/90 dark:bg-surface-950/90 px-4 sm:px-6 backdrop-blur-md">
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
          <span className="font-bold text-xs text-slate-900 dark:text-white">TPO Portal</span>
        </div>

        {college && (
          <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 dark:bg-surface-900 border border-slate-200 dark:border-surface-800 text-xs text-slate-700 dark:text-slate-300">
            <Building2 className="h-3.5 w-3.5 text-brand-500 shrink-0" />
            <span className="font-semibold">{college.name}</span>
            {college.code && (
              <span className="text-slate-400">({college.code})</span>
            )}
          </div>
        )}
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

        {/* User profile quick view */}
        <div className="flex items-center gap-2.5 pl-2 border-l border-slate-200 dark:border-surface-800">
          <UserAvatar
            src={profile?.avatar_url}
            name={tpoName}
            initials={tpoName.slice(0, 2).toUpperCase()}
            size="sm"
          />
          <div className="hidden md:block text-left">
            <p className="text-xs font-semibold text-slate-900 dark:text-white leading-tight">
              {tpoName}
            </p>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 font-medium">
              {profile?.designation || "TPO"}
            </p>
          </div>
        </div>
      </div>
    </header>
  );
};
