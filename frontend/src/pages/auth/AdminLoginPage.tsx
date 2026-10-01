import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, useNavigate } from "react-router-dom";
import { Lock, Mail, ShieldAlert, Sun, Moon } from "lucide-react";

import { authApi } from "../../api/authApi";
import { useAuthStore } from "../../store/authStore";
import { useThemeStore } from "../../store/themeStore";
import { Button } from "../../components/ui/Button";
import { FormField, Input } from "../../components/ui/Form";
import { useToast } from "../../context/ToastContext";
import { BrandLogo } from "../../components/common/BrandLogo";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid administrative email address"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export const AdminLoginPage: React.FC = () => {
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
      const result = await authApi.loginAdmin(data.email, data.password);

      if (result.user.role !== "ADMIN") {
        setErrorMessage("Access denied. The Admin Portal is restricted to authorized staff.");
        toastError("Access Denied", "Your account does not possess administrative privileges.");
        setIsLoading(false);
        return;
      }

      setAuth(result.user, { access: result.access, refresh: result.refresh });
      success("Welcome Back", "Successfully authenticated as Administrator.");
      navigate("/admin/dashboard", { replace: true });
    } catch (err: any) {
      const apiMsg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.message ||
        "Invalid administrative credentials. Please verify your email and password.";
      setErrorMessage(apiMsg);
      toastError("Authentication Failed", apiMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-slate-50 dark:bg-surface-950 p-4 font-sans text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* Background ambient glow */}
      <div className="pointer-events-none fixed inset-0 flex items-center justify-center">
        <div className="h-[500px] w-[500px] rounded-full bg-brand-500/10 blur-[120px]" />
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

      <div className="w-full max-w-md">
        {/* Brand Card */}
        <div className="rounded-3xl border border-slate-200 dark:border-surface-800 bg-white/95 dark:bg-surface-900/80 p-8 shadow-2xl shadow-brand-500/5 dark:shadow-black/60 backdrop-blur-xl">
          <div className="text-center mb-8">
            <BrandLogo variant="image-card" className="mb-4" />
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Admin Portal</h1>
            <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
              Sign in with institutional credentials to manage curriculum and students
            </p>
          </div>

          {errorMessage && (
            <div className="mb-6 flex items-start gap-3 rounded-xl border border-rose-500/30 bg-rose-50 dark:bg-rose-950/40 p-3.5 text-xs text-rose-700 dark:text-rose-200">
              <ShieldAlert className="h-4 w-4 shrink-0 text-rose-500 dark:text-rose-400 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <FormField label="Admin Email" error={errors.email?.message} required>
              <div className="relative">
                <Mail className="absolute left-3.5 top-3 h-4 w-4 text-slate-400 pointer-events-none" />
                <Input
                  {...register("email")}
                  type="email"
                  placeholder="admin@gqt.edu"
                  className="pl-10"
                  error={!!errors.email}
                  disabled={isLoading}
                />
              </div>
            </FormField>

            <FormField label="Password" error={errors.password?.message} required>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-400 pointer-events-none" />
                <Input
                  {...register("password")}
                  type="password"
                  placeholder="••••••••••••"
                  className="pl-10"
                  error={!!errors.password}
                  disabled={isLoading}
                />
              </div>
            </FormField>

            <div className="flex items-center justify-between">
              <Link
                to="/login"
                className="text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-300 transition-colors"
              >
                &larr; Student Portal
              </Link>
              <Link
                to="/auth/forgot-password"
                className="text-xs font-medium text-brand-600 dark:text-brand-400 hover:text-brand-700 dark:hover:text-brand-300 transition-colors"
              >
                Forgot password?
              </Link>
            </div>

            <Button type="submit" className="w-full mt-2" isLoading={isLoading}>
              Sign In to Management
            </Button>
          </form>
        </div>

        <p className="mt-6 text-center text-xs text-slate-500">
          GQT Student Learning & Assessment System &bull; Secure Access
        </p>
      </div>
    </div>
  );
};

