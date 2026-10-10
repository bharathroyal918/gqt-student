import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { ShieldX, ArrowRight, LogOut, LayoutDashboard, ShieldCheck, Sun, Moon } from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { useThemeStore } from "../store/themeStore";
import { Button } from "../components/ui/Button";

export const UnauthorizedPage: React.FC = () => {
  const { user, studentProfile, clearAuth } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();
  const navigate = useNavigate();

  const isStudent = user?.role === "STUDENT";
  const isAdmin = user?.role === "ADMIN";
  const isTPO = user?.role === "TPO";

  const handleLogout = () => {
    clearAuth();
    if (isAdmin) {
      navigate("/admin/login");
    } else if (isTPO) {
      navigate("/tpo/login");
    } else {
      navigate("/login");
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-slate-50 dark:bg-surface-950 p-4 text-center font-sans text-slate-900 dark:text-slate-100">
      {/* Background ambient glow */}
      <div className="pointer-events-none fixed inset-0 flex items-center justify-center">
        <div className="h-[450px] w-[450px] rounded-full bg-rose-500/10 blur-[130px]" />
      </div>

      {/* Floating Theme Toggle */}
      <div className="absolute top-4 right-4 z-20">
        <button
          type="button"
          onClick={toggleTheme}
          className="flex h-10 w-10 items-center justify-center rounded-2xl border border-slate-200 dark:border-surface-800 bg-white/90 dark:bg-surface-900/90 text-slate-600 dark:text-slate-300 shadow-md backdrop-blur-md hover:bg-slate-100 dark:hover:bg-surface-800 transition-all"
          title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          aria-label="Toggle Theme"
        >
          {theme === "dark" ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-indigo-600" />}
        </button>
      </div>

      <div className="relative w-full max-w-md rounded-3xl border border-slate-200 dark:border-surface-800 bg-white/95 dark:bg-surface-900/90 p-8 shadow-2xl shadow-brand-500/5 dark:shadow-black/60 backdrop-blur-2xl">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-rose-500/10 text-rose-500 dark:text-rose-400 mb-5 border border-rose-500/20 shadow-inner">
          <ShieldX className="h-8 w-8" />
        </div>

        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">403 — Access Restricted</h1>

        {isStudent ? (
          <>
            <p className="mt-3 text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
              You are signed in as <span className="font-semibold text-brand-600 dark:text-brand-400">{studentProfile?.full_name || user.email}</span> (Student Account).
            </p>
            <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
              Your account does not have authorization to access this area.
            </p>

            <div className="mt-6 space-y-3">
              <Link to="/dashboard" className="block w-full">
                <Button variant="primary" className="w-full">
                  <LayoutDashboard className="h-4 w-4 mr-2" />
                  <span>Go to Student Dashboard</span>
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </Link>

              <Button
                variant="secondary"
                className="w-full text-slate-700 dark:text-slate-300"
                onClick={handleLogout}
              >
                <LogOut className="h-4 w-4 mr-2 text-slate-400" />
                <span>Sign Out</span>
              </Button>
            </div>
          </>
        ) : isTPO ? (
          <>
            <p className="mt-3 text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
              You are signed in as <span className="font-semibold text-brand-600 dark:text-brand-400">{user.email}</span> (TPO Account).
            </p>
            <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
              Your account is authorized for the Training & Placement Officer portal.
            </p>

            <div className="mt-6 space-y-3">
              <Link to="/tpo/dashboard" className="block w-full">
                <Button variant="primary" className="w-full">
                  <LayoutDashboard className="h-4 w-4 mr-2" />
                  <span>Go to TPO Dashboard</span>
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </Link>

              <Button
                variant="secondary"
                className="w-full text-slate-700 dark:text-slate-300"
                onClick={handleLogout}
              >
                <LogOut className="h-4 w-4 mr-2 text-slate-400" />
                <span>Sign Out</span>
              </Button>
            </div>
          </>
        ) : isAdmin ? (
          <>
            <p className="mt-3 text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
              You are signed in with an Administrator profile.
            </p>
            <div className="mt-6 space-y-3">
              <Link to="/admin/dashboard" className="block w-full">
                <Button variant="primary" className="w-full">
                  <ShieldCheck className="h-4 w-4 mr-2" />
                  <span>Go to Admin Dashboard</span>
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </Link>

              <Button
                variant="secondary"
                className="w-full text-slate-700 dark:text-slate-300"
                onClick={handleLogout}
              >
                <LogOut className="h-4 w-4 mr-2 text-slate-400" />
                <span>Sign Out</span>
              </Button>
            </div>
          </>
        ) : (
          <>
            <p className="mt-3 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
              You do not have permission to access this resource. Please sign in with an authorized account.
            </p>

            <div className="mt-6 flex flex-col gap-3">
              <Link to="/login" className="w-full">
                <Button variant="primary" className="w-full">
                  Student Portal Login
                </Button>
              </Link>
              <Link to="/tpo/login" className="w-full">
                <Button variant="secondary" className="w-full">
                  TPO Portal Login
                </Button>
              </Link>
              <Link to="/admin/login" className="w-full">
                <Button variant="secondary" className="w-full">
                  Admin Portal Login
                </Button>
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
};


