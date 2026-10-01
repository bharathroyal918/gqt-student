import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  User,
  Mail,
  Phone,
  Lock,
  Building2,
  GraduationCap,
  ArrowRight,
  Sun,
  Moon,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { authApi } from "../../api/authApi";
import { useAuthStore } from "../../store/authStore";
import { useThemeStore } from "../../store/themeStore";
import { useToast } from "../../context/ToastContext";
import { Button } from "../../components/ui/Button";
import { FormField, Input } from "../../components/ui/Form";
import { BrandLogo } from "../../components/common/BrandLogo";

const registerSchema = z
  .object({
    full_name: z
      .string()
      .min(2, "Full name must be at least 2 characters")
      .max(150, "Full name is too long"),
    email: z.string().email("Please enter a valid email address"),
    mobile_number: z
      .string()
      .min(10, "Mobile number must be at least 10 digits")
      .regex(/^\+?[0-9\s\-]+$/, "Please enter a valid mobile number"),
    college_name: z.string().optional(),
    student_id_number: z.string().optional(),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Za-z]/, "Password must contain at least one letter")
      .regex(/[0-9]/, "Password must contain at least one number"),
    confirm_password: z.string().min(1, "Please confirm your password"),
    agree_terms: z.boolean().refine((val) => val === true, {
      message: "You must agree to the academic terms & code of conduct",
    }),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type RegisterFormValues = z.infer<typeof registerSchema>;

export const StudentRegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();
  const { success, error: toastError } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      agree_terms: false,
    },
  });

  const currentPassword = watch("password", "");

  const getPasswordStrength = (pwd: string) => {
    if (!pwd) return { score: 0, label: "None", color: "bg-slate-300 dark:bg-surface-700" };
    let score = 0;
    if (pwd.length >= 8) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/[0-9]/.test(pwd)) score++;
    if (/[^A-Za-z0-9]/.test(pwd)) score++;

    if (score <= 1) return { score: 25, label: "Weak", color: "bg-rose-500" };
    if (score === 2) return { score: 50, label: "Fair", color: "bg-amber-500" };
    if (score === 3) return { score: 75, label: "Good", color: "bg-blue-500" };
    return { score: 100, label: "Strong", color: "bg-emerald-500" };
  };

  const strength = getPasswordStrength(currentPassword);

  const onSubmit = async (data: RegisterFormValues) => {
    setIsSubmitting(true);
    try {
      const result = await authApi.registerStudent({
        full_name: data.full_name,
        email: data.email,
        mobile_number: data.mobile_number,
        password: data.password,
        college_name: data.college_name || undefined,
        student_id_number: data.student_id_number || undefined,
        batch_code: "BATCH-2026-A",
        graduation_year: 2026,
      });

      setAuth(
        result.user,
        { access: result.access, refresh: result.refresh },
        result.user.student_profile
      );

      success(
        "Registration Successful!",
        `Welcome to GQT Portal, ${result.user.student_profile?.full_name || data.full_name}!`
      );
      navigate("/dashboard", { replace: true });
    } catch (err: any) {
      const apiMsg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.message ||
        "Registration failed. Please check your details and try again.";
      toastError("Registration Error", apiMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-slate-50 dark:bg-surface-950 p-4 py-12 font-sans text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* Ambient background glow */}
      <div className="pointer-events-none fixed inset-0 flex items-center justify-center overflow-hidden">
        <div className="h-[600px] w-[600px] rounded-full bg-brand-500/10 blur-[140px]" />
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
          {theme === "dark" ? (
            <Sun className="h-4 w-4 text-amber-400" />
          ) : (
            <Moon className="h-4 w-4 text-indigo-600" />
          )}
        </button>
      </div>

      <div className="relative w-full max-w-xl">
        {/* Registration Card */}
        <div className="rounded-3xl border border-slate-200 dark:border-surface-800 bg-white/95 dark:bg-surface-900/90 p-8 sm:p-10 shadow-2xl shadow-brand-500/5 dark:shadow-black/70 backdrop-blur-2xl">
          {/* Header */}
          <div className="text-center mb-8">
            <BrandLogo variant="image-card" className="mb-4 mx-auto" />
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-50 dark:bg-brand-950/60 border border-brand-200 dark:border-brand-800/60 text-brand-700 dark:text-brand-300 text-xs font-semibold mb-3">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Student Registration</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              Create Your Student Account
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-2">
              Join the GQT Sequential Learning & Coding Assessment Platform to begin your training.
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Full Name */}
            <FormField label="Full Name" error={errors.full_name?.message} required>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                <Input
                  {...register("full_name")}
                  placeholder="e.g. John Doe"
                  className="pl-10"
                  error={!!errors.full_name}
                  disabled={isSubmitting}
                />
              </div>
            </FormField>

            {/* Email & Mobile in 2 columns on larger screens */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField label="Email Address" error={errors.email?.message} required>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                  <Input
                    {...register("email")}
                    type="email"
                    placeholder="student@example.com"
                    className="pl-10"
                    error={!!errors.email}
                    disabled={isSubmitting}
                  />
                </div>
              </FormField>

              <FormField label="Mobile Number" error={errors.mobile_number?.message} required>
                <div className="relative">
                  <Phone className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                  <Input
                    {...register("mobile_number")}
                    type="tel"
                    placeholder="+91 98765 43210"
                    className="pl-10"
                    error={!!errors.mobile_number}
                    disabled={isSubmitting}
                  />
                </div>
              </FormField>
            </div>

            {/* College & USN/Student ID in 2 columns */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField label="College / University" error={errors.college_name?.message}>
                <div className="relative">
                  <Building2 className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                  <Input
                    {...register("college_name")}
                    placeholder="e.g. Global Institute of Tech"
                    className="pl-10"
                    error={!!errors.college_name}
                    disabled={isSubmitting}
                  />
                </div>
              </FormField>

              <FormField label="Student ID / USN (Optional)" error={errors.student_id_number?.message}>
                <div className="relative">
                  <GraduationCap className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                  <Input
                    {...register("student_id_number")}
                    placeholder="Auto-generated if empty"
                    className="pl-10"
                    error={!!errors.student_id_number}
                    disabled={isSubmitting}
                  />
                </div>
              </FormField>
            </div>

            {/* Password & Confirm Password */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField label="Password" error={errors.password?.message} required>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                  <Input
                    {...register("password")}
                    type="password"
                    placeholder="Min 8 chars, 1 num"
                    className="pl-10"
                    error={!!errors.password}
                    disabled={isSubmitting}
                  />
                </div>
              </FormField>

              <FormField label="Confirm Password" error={errors.confirm_password?.message} required>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                  <Input
                    {...register("confirm_password")}
                    type="password"
                    placeholder="Re-enter password"
                    className="pl-10"
                    error={!!errors.confirm_password}
                    disabled={isSubmitting}
                  />
                </div>
              </FormField>
            </div>

            {/* Password Strength Indicator */}
            {currentPassword && (
              <div className="space-y-1.5 pt-1">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-500 dark:text-slate-400">Password Strength:</span>
                  <span className="font-semibold text-slate-700 dark:text-slate-300">
                    {strength.label}
                  </span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-slate-200 dark:bg-surface-800 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-300 ${strength.color}`}
                    style={{ width: `${strength.score}%` }}
                  />
                </div>
              </div>
            )}

            {/* Terms and Conditions */}
            <div className="pt-2">
              <label className="flex items-start gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  {...register("agree_terms")}
                  className="mt-0.5 h-4 w-4 rounded border-slate-300 dark:border-surface-700 text-brand-600 focus:ring-brand-500/20"
                />
                <span className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  I agree to the{" "}
                  <span className="font-medium text-brand-600 dark:text-brand-400">
                    Academic Integrity Policy
                  </span>{" "}
                  and{" "}
                  <span className="font-medium text-brand-600 dark:text-brand-400">
                    Terms of Platform Usage
                  </span>
                  .
                </span>
              </label>
              {errors.agree_terms && (
                <p className="mt-1 text-xs text-rose-500 font-medium">
                  {errors.agree_terms.message}
                </p>
              )}
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              className="w-full mt-4 py-3 text-sm font-semibold shadow-lg shadow-brand-600/25"
              isLoading={isSubmitting}
            >
              <span>Complete Registration & Enter</span>
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </form>

          {/* Links Footer */}
          <div className="mt-8 border-t border-slate-200 dark:border-surface-800 pt-6 space-y-3 text-center">
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Already have an account?{" "}
              <Link
                to="/login"
                className="font-semibold text-brand-600 dark:text-brand-400 hover:underline"
              >
                Sign In to Student Portal
              </Link>
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Instructor or Administrator?{" "}
              <Link
                to="/admin/login"
                className="font-medium text-slate-700 dark:text-slate-300 hover:underline"
              >
                Go to Admin Portal &rarr;
              </Link>
            </p>
          </div>
        </div>

        {/* Security / System Subtitle */}
        <div className="mt-6 flex items-center justify-center gap-2 text-xs text-slate-500">
          <ShieldCheck className="h-4 w-4 text-emerald-500" />
          <span>Protected with 256-bit Encryption &bull; Supabase Database</span>
        </div>
      </div>
    </div>
  );
};
