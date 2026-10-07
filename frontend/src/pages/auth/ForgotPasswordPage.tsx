import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Link } from "react-router-dom";
import {
  Mail,
  KeyRound,
  Lock,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ShieldCheck,
  RotateCcw,
  Sun,
  Moon,
} from "lucide-react";

import { authApi } from "../../api/authApi";
import { useThemeStore } from "../../store/themeStore";
import { useToast } from "../../context/ToastContext";
import { Button } from "../../components/ui/Button";
import { FormField, Input } from "../../components/ui/Form";
import { BrandLogo } from "../../components/common/BrandLogo";

// Schema for Step 1: Identifier
const step1Schema = z.object({
  identifier: z
    .string()
    .min(3, "Please enter your registered email address or mobile number"),
});

// Schema for Step 2: OTP
const step2Schema = z.object({
  otp: z
    .string()
    .length(6, "OTP must be exactly 6 digits")
    .regex(/^[0-9]+$/, "OTP must contain digits only"),
});

// Schema for Step 3: New Password
const step3Schema = z
  .object({
    new_password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Za-z]/, "Password must contain at least one letter")
      .regex(/[0-9]/, "Password must contain at least one number"),
    confirm_password: z.string().min(1, "Please confirm your password"),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type Step1FormValues = z.infer<typeof step1Schema>;
type Step2FormValues = z.infer<typeof step2Schema>;
type Step3FormValues = z.infer<typeof step3Schema>;

export const ForgotPasswordPage: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4>(1);
  const [identifier, setIdentifier] = useState("");
  const [maskedTarget, setMaskedTarget] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [verifiedOtp, setVerifiedOtp] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [cooldownSeconds, setCooldownSeconds] = useState(0);

  const { theme, toggleTheme } = useThemeStore();
  const { success, error: toastError } = useToast();

  // Cooldown countdown timer
  useEffect(() => {
    if (cooldownSeconds <= 0) return;
    const interval = setInterval(() => {
      setCooldownSeconds((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, [cooldownSeconds]);

  // Step 1 Form
  const {
    register: registerStep1,
    handleSubmit: handleSubmitStep1,
    formState: { errors: errorsStep1 },
  } = useForm<Step1FormValues>({
    resolver: zodResolver(step1Schema),
  });

  // Step 2 Form
  const {
    register: registerStep2,
    handleSubmit: handleSubmitStep2,
    formState: { errors: errorsStep2 },
  } = useForm<Step2FormValues>({
    resolver: zodResolver(step2Schema),
  });

  // Step 3 Form
  const {
    register: registerStep3,
    handleSubmit: handleSubmitStep3,
    formState: { errors: errorsStep3 },
  } = useForm<Step3FormValues>({
    resolver: zodResolver(step3Schema),
  });

  // Handlers
  const handleRequestOtp = async (data: Step1FormValues) => {
    setIsLoading(true);
    try {
      const res = await authApi.requestPasswordResetOtp(data.identifier);
      setIdentifier(data.identifier);
      setMaskedTarget(res.target);
      setCooldownSeconds(60);
      setCurrentStep(2);
      success("OTP Dispatched", res.message);
    } catch (err: any) {
      const msg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.message ||
        "Unable to dispatch OTP. Please check your details and try again.";
      toastError("Request Failed", msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOtp = async () => {
    if (cooldownSeconds > 0 || !identifier) return;
    setIsLoading(true);
    try {
      const res = await authApi.requestPasswordResetOtp(identifier);
      setCooldownSeconds(60);
      success("OTP Resent", res.message);
    } catch (err: any) {
      const msg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.message ||
        "Failed to resend OTP code.";
      toastError("Resend Failed", msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOtp = async (data: Step2FormValues) => {
    setIsLoading(true);
    try {
      const res = await authApi.verifyPasswordResetOtp(identifier, data.otp);
      setResetToken(res.reset_token);
      setVerifiedOtp(data.otp);
      setCurrentStep(3);
      success("OTP Verified", "Please choose your new secure password.");
    } catch (err: any) {
      const msg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.message ||
        "Invalid or expired OTP code.";
      toastError("Verification Failed", msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async (data: Step3FormValues) => {
    setIsLoading(true);
    try {
      await authApi.resetPassword(
        resetToken,
        data.new_password,
        identifier,
        verifiedOtp
      );
      setCurrentStep(4);
      success("Password Reset Complete", "Your password has been successfully updated.");
    } catch (err: any) {
      const msg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.message ||
        "Unable to reset password. Please request a new OTP.";
      toastError("Reset Failed", msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-slate-50 dark:bg-surface-950 p-4 py-12 font-sans text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* Background glow */}
      <div className="pointer-events-none fixed inset-0 flex items-center justify-center">
        <div className="h-[500px] w-[500px] rounded-full bg-brand-500/10 blur-[130px]" />
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

      <div className="w-full max-w-md">
        <div className="rounded-3xl border border-slate-200 dark:border-surface-800 bg-white/95 dark:bg-surface-900/90 p-8 shadow-2xl shadow-brand-500/5 dark:shadow-black/70 backdrop-blur-xl">
          {/* Back to Login Link */}
          {currentStep !== 4 && (
            <div className="mb-6 flex items-center justify-between">
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to Sign In
              </Link>

              {/* Step indicator */}
              <div className="flex items-center gap-1.5">
                {[1, 2, 3].map((s) => (
                  <div
                    key={s}
                    className={`h-1.5 rounded-full transition-all duration-300 ${
                      currentStep === s
                        ? "w-6 bg-brand-600 dark:bg-brand-400"
                        : currentStep > s
                        ? "w-3 bg-emerald-500"
                        : "w-3 bg-slate-200 dark:bg-surface-800"
                    }`}
                  />
                ))}
              </div>
            </div>
          )}

          {/* STEP 1: Request OTP */}
          {currentStep === 1 && (
            <div>
              <div className="text-center mb-6">
                <BrandLogo variant="image-card" className="mb-4 mx-auto" />
                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  Reset Password
                </h1>
                <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
                  Enter your registered student or admin email/phone to receive a One-Time Password (OTP).
                </p>
              </div>

              <form onSubmit={handleSubmitStep1(handleRequestOtp)} className="space-y-4" method="POST">
                <FormField
                  label="Registered Email or Mobile"
                  error={errorsStep1.identifier?.message}
                  required
                >
                  <div className="relative">
                    <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                    <Input
                      {...registerStep1("identifier")}
                      autoComplete="username"
                      placeholder="e.g. your-email@domain.com or +91 98765..."
                      className="pl-10"
                      error={!!errorsStep1.identifier}
                      disabled={isLoading}
                    />
                  </div>
                </FormField>

                <Button type="submit" className="w-full mt-2" isLoading={isLoading}>
                  <span>Send One-Time Password</span>
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </form>
            </div>
          )}

          {/* STEP 2: Verify OTP */}
          {currentStep === 2 && (
            <div>
              <div className="text-center mb-6">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-600 dark:text-brand-400 mb-3">
                  <KeyRound className="h-6 w-6" />
                </div>
                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  Enter 6-Digit OTP
                </h1>
                <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
                  We sent a verification code to{" "}
                  <strong className="text-slate-800 dark:text-slate-200">{maskedTarget || identifier}</strong>
                </p>
              </div>

              <form onSubmit={handleSubmitStep2(handleVerifyOtp)} className="space-y-4" method="POST">
                <FormField
                  label="One-Time Password (OTP)"
                  error={errorsStep2.otp?.message}
                  required
                >
                  <div className="relative">
                    <Input
                      {...registerStep2("otp")}
                      type="text"
                      autoComplete="one-time-code"
                      maxLength={6}
                      placeholder="••••••"
                      className="text-center tracking-[0.4em] font-mono font-bold text-xl h-12"
                      error={!!errorsStep2.otp}
                      disabled={isLoading}
                      autoFocus
                    />
                  </div>
                </FormField>

                <div className="flex items-center justify-between text-xs pt-1">
                  <button
                    type="button"
                    onClick={() => setCurrentStep(1)}
                    className="text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
                  >
                    Change recipient
                  </button>

                  <button
                    type="button"
                    onClick={handleResendOtp}
                    disabled={cooldownSeconds > 0 || isLoading}
                    className={`font-medium flex items-center gap-1 transition-colors ${
                      cooldownSeconds > 0
                        ? "text-slate-400 cursor-not-allowed"
                        : "text-brand-600 dark:text-brand-400 hover:underline"
                    }`}
                  >
                    <RotateCcw className="h-3 w-3" />
                    {cooldownSeconds > 0 ? `Resend in ${cooldownSeconds}s` : "Resend OTP"}
                  </button>
                </div>

                <Button type="submit" className="w-full mt-2" isLoading={isLoading}>
                  <ShieldCheck className="h-4 w-4 mr-2" />
                  <span>Verify OTP & Continue</span>
                </Button>
              </form>
            </div>
          )}

          {/* STEP 3: Set New Password */}
          {currentStep === 3 && (
            <div>
              <div className="text-center mb-6">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 mb-3">
                  <Lock className="h-6 w-6" />
                </div>
                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  Set New Password
                </h1>
                <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
                  Choose a new password with at least 8 characters and 1 number.
                </p>
              </div>

              <form onSubmit={handleSubmitStep3(handleResetPassword)} className="space-y-4" method="POST">
                <FormField
                  label="New Password"
                  error={errorsStep3.new_password?.message}
                  required
                >
                  <div className="relative">
                    <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                    <Input
                      {...registerStep3("new_password")}
                      type="password"
                      autoComplete="new-password"
                      placeholder="••••••••••••"
                      className="pl-10"
                      error={!!errorsStep3.new_password}
                      disabled={isLoading}
                    />
                  </div>
                </FormField>

                <FormField
                  label="Confirm New Password"
                  error={errorsStep3.confirm_password?.message}
                  required
                >
                  <div className="relative">
                    <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                    <Input
                      {...registerStep3("confirm_password")}
                      type="password"
                      autoComplete="new-password"
                      placeholder="••••••••••••"
                      className="pl-10"
                      error={!!errorsStep3.confirm_password}
                      disabled={isLoading}
                    />
                  </div>
                </FormField>

                <Button type="submit" className="w-full mt-2" isLoading={isLoading}>
                  <span>Save New Password</span>
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </form>
            </div>
          )}

          {/* STEP 4: Success Screen */}
          {currentStep === 4 && (
            <div className="text-center py-4">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 mb-4 animate-bounce">
                <CheckCircle2 className="h-9 w-9" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                Password Reset Successfully!
              </h2>
              <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed max-w-sm mx-auto">
                Your credentials have been securely updated in the database. You can now log in to the portal with your new password.
              </p>

              <div className="mt-8">
                <Link to="/login" className="block">
                  <Button className="w-full py-2.5">
                    Sign In to Student Portal
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* Security Subtitle */}
        <p className="mt-6 text-center text-xs text-slate-500">
          GQT Student Learning & Assessment System &bull; Secure Authentication
        </p>
      </div>
    </div>
  );
};
