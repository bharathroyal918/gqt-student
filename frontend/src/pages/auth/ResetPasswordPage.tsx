import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, useNavigate } from "react-router-dom";
import { KeyRound, Lock, ArrowLeft, Sun, Moon } from "lucide-react";

import { authApi } from "../../api/authApi";
import { useThemeStore } from "../../store/themeStore";
import { Button } from "../../components/ui/Button";
import { FormField, Input } from "../../components/ui/Form";
import { useToast } from "../../context/ToastContext";

const resetSchema = z
  .object({
    token: z.string().min(1, "Reset token is required"),
    new_password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string().min(1, "Please confirm password"),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type ResetFormData = z.infer<typeof resetSchema>;

export const ResetPasswordPage: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const { theme, toggleTheme } = useThemeStore();
  const { success, error: toastError } = useToast();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetFormData>({
    resolver: zodResolver(resetSchema),
  });

  const onSubmit = async (data: ResetFormData) => {
    setIsLoading(true);
    try {
      await authApi.resetPassword(data.token, data.new_password);
      success("Password Reset Complete", "You may now sign in using your new credentials.");
      navigate("/login");
    } catch (err: any) {
      const apiMsg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.message ||
        "Invalid or expired password reset token.";
      toastError("Reset Failed", apiMsg);
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
        <div className="rounded-3xl border border-slate-200 dark:border-surface-800 bg-white/95 dark:bg-surface-900/80 p-8 shadow-2xl shadow-brand-500/5 dark:shadow-black/60 backdrop-blur-xl">
          <div className="flex items-center justify-between mb-6">
            <Link
              to="/login"
              className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to login
            </Link>
            <Link
              to="/forgot-password"
              className="text-xs font-medium text-brand-600 dark:text-brand-400 hover:underline"
            >
              Use OTP Flow &rarr;
            </Link>
          </div>

          <div className="text-left mb-6">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Reset Password</h1>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Provide your token and choose a secure 8+ character password.
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" method="POST">
            <FormField label="Reset Token" error={errors.token?.message} required>
              <div className="relative">
                <KeyRound className="absolute left-3.5 top-3 h-4 w-4 text-slate-400 pointer-events-none" />
                <Input
                  {...register("token")}
                  autoComplete="one-time-code"
                  placeholder="Paste reset token here"
                  className="pl-10 font-mono text-xs"
                  error={!!errors.token}
                  disabled={isLoading}
                />
              </div>
            </FormField>

            <FormField label="New Password" error={errors.new_password?.message} required>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-400 pointer-events-none" />
                <Input
                  {...register("new_password")}
                  type="password"
                  autoComplete="new-password"
                  placeholder="At least 8 characters"
                  className="pl-10"
                  error={!!errors.new_password}
                  disabled={isLoading}
                />
              </div>
            </FormField>

            <FormField label="Confirm Password" error={errors.confirm_password?.message} required>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-400 pointer-events-none" />
                <Input
                  {...register("confirm_password")}
                  type="password"
                  autoComplete="new-password"
                  placeholder="Re-enter password"
                  className="pl-10"
                  error={!!errors.confirm_password}
                  disabled={isLoading}
                />
              </div>
            </FormField>

            <Button type="submit" className="w-full mt-2" isLoading={isLoading}>
              Update Password
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};

