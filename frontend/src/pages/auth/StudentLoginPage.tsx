import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Phone,
  Mail,
  Lock,
  ArrowRight,
  ShieldCheck,
  KeyRound,
} from "lucide-react";
import { authApi } from "../../api/authApi";
import { useAuthStore } from "../../store/authStore";
import { useToast } from "../../context/ToastContext";
import { Button } from "../../components/ui/Button";
import { FormField, Input } from "../../components/ui/Form";

// Validation schemas
const phoneSchema = z.object({
  mobile_number: z
    .string()
    .min(10, "Mobile number must be at least 10 digits")
    .regex(/^\+?[0-9\s\-]+$/, "Please enter a valid mobile number with country code"),
});

const otpSchema = z.object({
  otp: z
    .string()
    .length(6, "OTP must be exactly 6 digits")
    .regex(/^[0-9]+$/, "OTP must contain digits only"),
});

const emailSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

type PhoneFormValues = z.infer<typeof phoneSchema>;
type OtpFormValues = z.infer<typeof otpSchema>;
type EmailFormValues = z.infer<typeof emailSchema>;

export const StudentLoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { setAuth } = useAuthStore();
  const { success, error: toastError } = useToast();

  const [authMethod, setAuthMethod] = useState<"otp" | "email">("otp");
  const [otpStep, setOtpStep] = useState<"request" | "verify">("request");
  const [targetPhone, setTargetPhone] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const from = (location.state as any)?.from?.pathname || "/dashboard";

  // Forms
  const {
    register: registerPhone,
    handleSubmit: handleSubmitPhone,
    formState: { errors: phoneErrors },
  } = useForm<PhoneFormValues>({
    resolver: zodResolver(phoneSchema),
  });

  const {
    register: registerOtp,
    handleSubmit: handleSubmitOtp,
    formState: { errors: otpErrors },
  } = useForm<OtpFormValues>({
    resolver: zodResolver(otpSchema),
  });

  const {
    register: registerEmail,
    handleSubmit: handleSubmitEmail,
    formState: { errors: emailErrors },
  } = useForm<EmailFormValues>({
    resolver: zodResolver(emailSchema),
  });

  // Step 1: Request OTP
  const onSendOtp = async (data: PhoneFormValues) => {
    setIsSubmitting(true);
    try {
      await authApi.requestOtp(data.mobile_number);
      setTargetPhone(data.mobile_number);
      setOtpStep("verify");
      success("OTP Dispatched", "If this number is approved, an access code was sent.");
    } catch (err: any) {
      const msg = err.response?.data?.message || err.response?.data?.error?.message || "Failed to send OTP.";
      toastError("Request Failed", msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Step 2: Verify OTP
  const onVerifyOtp = async (data: OtpFormValues) => {
    setIsSubmitting(true);
    try {
      const res = await authApi.verifyOtp(targetPhone, data.otp);

      if (res.user.role === "ADMIN") {
        toastError("Access Denied", "Admin accounts must log in via the Admin Portal.");
        return;
      }

      const studentName = res.user.student_profile?.full_name || res.user.email || "Student";
      setAuth(res.user, { access: res.access, refresh: res.refresh }, res.user.student_profile);
      success("Welcome Back", `Logged in as ${studentName}`);
      navigate(from, { replace: true });
    } catch (err: any) {
      const msg = err.response?.data?.message || err.response?.data?.error?.message || "Invalid or expired OTP.";
      toastError("Verification Failed", msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Email + Password Login
  const onEmailLogin = async (data: EmailFormValues) => {
    setIsSubmitting(true);
    try {
      const res = await authApi.loginEmail(data.email, data.password);

      if (res.user.role === "ADMIN") {
        toastError("Access Denied", "Admin accounts must log in via the Admin Portal.");
        return;
      }

      const studentName = res.user.student_profile?.full_name || res.user.email || "Student";
      setAuth(res.user, { access: res.access, refresh: res.refresh }, res.user.student_profile);
      success("Welcome Back", `Logged in as ${studentName}`);
      navigate(from, { replace: true });
    } catch (err: any) {
      const msg = err.response?.data?.message || err.response?.data?.error?.message || "Invalid email or password.";
      toastError("Authentication Failed", msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-950 p-4 font-sans text-slate-100">
      {/* Background radial gradient */}
      <div className="pointer-events-none fixed inset-0 flex items-center justify-center">
        <div className="h-[500px] w-[500px] rounded-full bg-brand-500/10 blur-[120px]" />
      </div>

      <div className="relative w-full max-w-md rounded-3xl border border-surface-800 bg-surface-900/80 p-8 shadow-2xl backdrop-blur-2xl">
        {/* Brand Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center p-2.5 rounded-2xl bg-white shadow-xl shadow-brand-900/40 ring-1 ring-white/20 mb-4 transition-transform duration-200 hover:scale-[1.02]">
            <img
              src="/gqt-logo.jpg"
              alt="Global Quest Technologies"
              className="h-11 w-auto max-w-[210px] object-contain"
            />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Student Portal</h1>
          <p className="text-xs text-slate-400 mt-1">
            Access your curriculum, coding labs, tasks, and project submissions.
          </p>
        </div>

        {/* Method Toggle: OTP vs Password */}
        <div className="flex rounded-xl bg-surface-950 p-1 border border-surface-800 mb-6">
          <button
            type="button"
            onClick={() => {
              setAuthMethod("otp");
              setOtpStep("request");
            }}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold transition-all ${
              authMethod === "otp"
                ? "bg-brand-600 text-white shadow-md shadow-brand-600/20"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Phone className="h-3.5 w-3.5" />
            Mobile OTP
          </button>
          <button
            type="button"
            onClick={() => setAuthMethod("email")}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold transition-all ${
              authMethod === "email"
                ? "bg-brand-600 text-white shadow-md shadow-brand-600/20"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Mail className="h-3.5 w-3.5" />
            Email & Password
          </button>
        </div>

        {/* Option 1: Mobile OTP */}
        {authMethod === "otp" && (
          <>
            {otpStep === "request" ? (
              <form onSubmit={handleSubmitPhone(onSendOtp)} className="space-y-4">
                <FormField
                  label="Registered Mobile Number"
                  error={phoneErrors.mobile_number?.message}
                  required
                >
                  <div className="relative">
                    <Phone className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                      {...registerPhone("mobile_number")}
                      type="tel"
                      placeholder="+91 98765 43210"
                      className="pl-10"
                    />
                  </div>
                </FormField>

                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Only student accounts provisioned by administrators can receive access codes.
                </p>

                <Button type="submit" className="w-full mt-2" isLoading={isSubmitting}>
                  <span>Send One-Time Password</span>
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </form>
            ) : (
              <form onSubmit={handleSubmitOtp(onVerifyOtp)} className="space-y-4">
                <div className="rounded-xl border border-surface-800 bg-surface-950/60 p-3 text-xs text-slate-300 flex items-center justify-between">
                  <span>Code sent to: <span className="font-mono text-brand-400">{targetPhone}</span></span>
                  <button
                    type="button"
                    onClick={() => setOtpStep("request")}
                    className="text-xs text-brand-400 hover:underline"
                  >
                    Change
                  </button>
                </div>

                <FormField
                  label="Enter 6-Digit OTP"
                  error={otpErrors.otp?.message}
                  required
                >
                  <div className="relative">
                    <KeyRound className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                      {...registerOtp("otp")}
                      type="text"
                      maxLength={6}
                      placeholder="••••••"
                      className="pl-10 text-center tracking-[0.4em] font-mono font-bold text-lg"
                      autoFocus
                    />
                  </div>
                </FormField>

                <Button type="submit" className="w-full mt-2" isLoading={isSubmitting}>
                  <ShieldCheck className="h-4 w-4 mr-2" />
                  <span>Verify Code & Enter</span>
                </Button>
              </form>
            )}
          </>
        )}

        {/* Option 2: Email & Password */}
        {authMethod === "email" && (
          <form onSubmit={handleSubmitEmail(onEmailLogin)} className="space-y-4">
            <FormField
              label="Student Email"
              error={emailErrors.email?.message}
              required
            >
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  {...registerEmail("email")}
                  type="email"
                  placeholder="student@institution.edu"
                  className="pl-10"
                />
              </div>
            </FormField>

            <FormField
              label="Password"
              error={emailErrors.password?.message}
              required
            >
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  {...registerEmail("password")}
                  type="password"
                  placeholder="••••••••••••"
                  className="pl-10"
                />
              </div>
            </FormField>

            <div className="flex justify-end">
              <Link
                to="/auth/forgot-password"
                className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
              >
                Forgot your password?
              </Link>
            </div>

            <Button type="submit" className="w-full mt-2" isLoading={isSubmitting}>
              <span>Sign In with Password</span>
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </form>
        )}

        {/* Footer Notice */}
        <div className="mt-8 border-t border-surface-800 pt-4 text-center">
          <p className="text-xs text-slate-500">
            Staff or Faculty Member?{" "}
            <Link to="/auth/login" className="text-brand-400 hover:underline font-medium">
              Admin Login Portal
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
