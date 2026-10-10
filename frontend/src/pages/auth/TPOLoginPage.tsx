import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, useNavigate } from "react-router-dom";
import { ShieldAlert, Sun, Moon } from "lucide-react";

import { authApi } from "../../api/authApi";
import { useAuthStore } from "../../store/authStore";
import { useThemeStore } from "../../store/themeStore";
import { Button } from "../../components/ui/Button";
import { FormField, Input } from "../../components/ui/Form";
import { useToast } from "../../context/ToastContext";
import { BrandLogo } from "../../components/common/BrandLogo";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid official email address"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export const TPOLoginPage: React.FC = () => {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { setAuth } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();
  const { success, error: toastError } = useToast();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const result = await authApi.loginTPO(data.email, data.password);

      if (result.user.role !== "TPO") {
        setErrorMessage("Access denied. The TPO Portal is restricted to authorized placement officers.");
        toastError("Access Denied", "Your account does not possess TPO privileges.");
        setIsLoading(false);
        return;
      }

      setAuth(result.user, { access: result.access, refresh: result.refresh });
      success("Welcome Back", "Successfully authenticated to the TPO Portal.");
      navigate("/tpo/dashboard", { replace: true });
    } catch (err: any) {
      const apiMsg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.message ||
        "Invalid TPO credentials. Please verify your email and password.";

      setErrorMessage(apiMsg);
      toastError("Authentication Failed", apiMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-slate-50 dark:bg-surface-950 p-4 sm:p-6 lg:p-8 font-sans text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* Background aesthetics */}
      <div className="pointer-events-none fixed inset-0 flex items-center justify-center overflow-hidden">
        <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-brand-500/10 dark:bg-brand-500/15 blur-[128px]" />
        <div className="absolute -bottom-40 -left-40 h-96 w-96 rounded-full bg-emerald-500/10 dark:bg-emerald-500/15 blur-[128px]" />
      </div>

      {/* Floating Theme Toggle Top Right */}
      <div className="absolute top-4 right-4 sm:top-6 sm:right-6 z-20">
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

      {/* Login Card */}
      <div className="relative w-full max-w-md">
        <div className="rounded-3xl border border-slate-200 dark:border-surface-800 bg-white/95 dark:bg-surface-900/85 p-8 shadow-2xl shadow-brand-500/5 dark:shadow-black/60 backdrop-blur-2xl sm:p-10 transition-colors">
          {/* Header */}
          <div className="flex flex-col items-center text-center">
            <BrandLogo
              variant="full"
              badge="TPO Portal"
              badgeVariant="admin"
              subtitle="Training & Placement Officer Access"
            />
            <h1 className="mt-6 text-xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-2xl">
              Officer Sign In
            </h1>
            <p className="mt-2 text-xs text-slate-500 dark:text-slate-400 max-w-sm leading-relaxed">
              Sign in with your institutional credentials to access student directories and placement analytics.
            </p>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div className="mt-6 flex items-start gap-3 rounded-2xl border border-rose-200 dark:border-rose-500/20 bg-rose-50 dark:bg-rose-500/10 p-3.5 text-xs text-rose-700 dark:text-rose-300">
              <ShieldAlert className="h-4 w-4 shrink-0 text-rose-500 dark:text-rose-400 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
            <FormField label="Official Email" error={errors.email?.message} required>
              <Input
                {...register("email")}
                type="email"
                placeholder="tpo.officer@institution.edu"
                autoComplete="email"
              />
            </FormField>

            <FormField label="Password" error={errors.password?.message} required>
              <Input
                {...register("password")}
                type="password"
                placeholder="••••••••••••"
                autoComplete="current-password"
              />
            </FormField>

            <div className="pt-2">
              <Button
                type="submit"
                isLoading={isLoading}
                className="w-full h-11 text-sm font-semibold shadow-lg shadow-brand-500/25"
              >
                Sign In to TPO Portal
              </Button>
            </div>
          </form>

          {/* Dedicated TPO Registration Navigation Footer */}
          <div className="mt-8 border-t border-slate-200 dark:border-surface-800 pt-6 text-center text-xs text-slate-500 dark:text-slate-400">
            <span>New Placement Officer or Institution? </span>
            <div className="mt-2 flex justify-center items-center gap-2">
              <Link
                to="/tpo/register"
                className="font-semibold text-brand-600 dark:text-brand-400 hover:text-brand-700 dark:hover:text-brand-300 hover:underline transition-colors"
              >
                Register TPO Account & Select College →
              </Link>
            </div>
            <p className="mt-3 text-[11px] text-slate-400 dark:text-slate-500">
              * Note: Newly registered TPO accounts require institutional administrative approval before student records become accessible.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
