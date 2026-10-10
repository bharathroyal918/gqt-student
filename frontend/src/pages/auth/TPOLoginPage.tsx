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
    <div className="relative flex min-h-screen flex-col items-center justify-center bg-slate-900 p-4 sm:p-6 lg:p-8 font-sans text-slate-100">
      {/* Background aesthetics */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-brand-500/10 blur-[128px]" />
        <div className="absolute -bottom-40 -left-40 h-96 w-96 rounded-full bg-emerald-500/10 blur-[128px]" />
      </div>

      {/* Theme Toggle Top Right */}
      <div className="absolute top-4 right-4 sm:top-6 sm:right-6">
        <button
          onClick={toggleTheme}
          className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-700/60 bg-slate-800/80 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors shadow-lg"
          aria-label="Toggle Theme"
        >
          {theme === "dark" ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-indigo-400" />}
        </button>
      </div>

      {/* Login Card */}
      <div className="relative w-full max-w-md">
        <div className="rounded-3xl border border-slate-800/80 bg-slate-950/80 p-8 shadow-2xl backdrop-blur-xl sm:p-10">
          {/* Header */}
          <div className="flex flex-col items-center text-center">
            <BrandLogo
              variant="full"
              badge="TPO Portal"
              badgeVariant="admin"
              subtitle="Training & Placement Officer Access"
            />
            <h1 className="mt-6 text-xl font-bold tracking-tight text-white sm:text-2xl">
              Officer Sign In
            </h1>
            <p className="mt-2 text-xs text-slate-400 max-w-sm leading-relaxed">
              Sign in with your institutional credentials to access student directories and placement analytics.
            </p>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div className="mt-6 flex items-start gap-3 rounded-2xl border border-rose-500/20 bg-rose-500/10 p-3.5 text-xs text-rose-300">
              <ShieldAlert className="h-4 w-4 shrink-0 text-rose-400 mt-0.5" />
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

          {/* Alternate Logins Footer */}
          <div className="mt-8 border-t border-slate-800/80 pt-6 text-center text-xs text-slate-500">
            <span>Are you a student or platform administrator? </span>
            <div className="mt-2 flex justify-center gap-4 text-xs font-semibold">
              <Link to="/login" className="text-brand-400 hover:text-brand-300 hover:underline">
                Student Portal
              </Link>
              <span>•</span>
              <Link to="/admin/login" className="text-brand-400 hover:text-brand-300 hover:underline">
                Admin Portal
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
