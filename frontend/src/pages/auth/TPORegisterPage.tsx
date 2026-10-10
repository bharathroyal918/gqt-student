import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Building2,
  ShieldCheck,
  ShieldAlert,
  Sun,
  Moon,
  ArrowRight,
  CheckCircle2,
  Lock,
  Mail,
  User as UserIcon,
  Phone,
  Briefcase,
} from "lucide-react";

import { authApi } from "../../api/authApi";
import { collegesApi } from "../../api/collegesApi";
import { useThemeStore } from "../../store/themeStore";
import { Button } from "../../components/ui/Button";
import { FormField, Input } from "../../components/ui/Form";
import { Modal } from "../../components/ui/Modal";
import { BrandLogo } from "../../components/common/BrandLogo";

const tpoRegisterSchema = z
  .object({
    full_name: z.string().min(2, "Full Name must be at least 2 characters"),
    email: z.string().email("Please enter a valid official institutional email address"),
    college_id: z.string().min(1, "Please select your institutional college"),
    mobile_number: z.string().min(10, "Please enter a valid 10-digit mobile number"),
    designation: z.string().min(2, "Designation is required"),
    department: z.string().min(2, "Department is required"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string().min(8, "Confirm Password is required"),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type TPORegisterFormData = z.infer<typeof tpoRegisterSchema>;

export const TPORegisterPage: React.FC = () => {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSuccessModalOpen, setIsSuccessModalOpen] = useState(false);
  const [registeredCollegeName, setRegisteredCollegeName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { theme, toggleTheme } = useThemeStore();
  const navigate = useNavigate();

  // Fetch verified active colleges
  const { data: colleges = [], isLoading: isCollegesLoading } = useQuery({
    queryKey: ["public-colleges"],
    queryFn: () => collegesApi.getColleges(),
    staleTime: 5 * 60 * 1000,
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TPORegisterFormData>({
    resolver: zodResolver(tpoRegisterSchema),
    defaultValues: {
      full_name: "",
      email: "",
      college_id: "",
      mobile_number: "",
      designation: "Training & Placement Officer",
      department: "Training & Placement Cell",
      password: "",
      confirm_password: "",
    },
  });

  const onSubmit = async (data: TPORegisterFormData) => {
    setIsLoading(true);
    setErrorMessage(null);

    const selectedCollege = colleges.find((c) => c.id === data.college_id);
    const collegeName = selectedCollege ? selectedCollege.name : "";

    try {
      await authApi.registerTPO({
        full_name: data.full_name,
        email: data.email,
        password: data.password,
        college_id: data.college_id,
        college_name: collegeName,
        mobile_number: data.mobile_number,
        designation: data.designation,
        department: data.department,
        phone_number: data.mobile_number,
      });

      setRegisteredCollegeName(collegeName || "your selected institution");
      setIsSuccessModalOpen(true);
    } catch (err: any) {
      const apiMsg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.message ||
        "Registration failed. Please check the provided details and try again.";
      setErrorMessage(apiMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center bg-slate-50 dark:bg-surface-950 p-4 sm:p-6 lg:p-8 font-sans text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* Background ambient lighting */}
      <div className="pointer-events-none fixed inset-0 flex items-center justify-center overflow-hidden">
        <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-brand-500/10 dark:bg-brand-500/15 blur-[128px]" />
        <div className="absolute -bottom-40 -left-40 h-96 w-96 rounded-full bg-indigo-500/10 dark:bg-indigo-500/15 blur-[128px]" />
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

      {/* Registration Card */}
      <div className="relative w-full max-w-2xl my-8">
        <div className="rounded-3xl border border-slate-200 dark:border-surface-800 bg-white/95 dark:bg-surface-900/85 p-8 shadow-2xl shadow-brand-500/5 dark:shadow-black/60 backdrop-blur-2xl sm:p-10 transition-colors">
          {/* Header */}
          <div className="flex flex-col items-center text-center">
            <BrandLogo
              variant="full"
              badge="TPO Portal"
              badgeVariant="admin"
              subtitle="Institutional Placement Officer Onboarding"
            />
            <h1 className="mt-6 text-xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-2xl">
              TPO Officer Registration
            </h1>
            <p className="mt-2 text-xs text-slate-500 dark:text-slate-400 max-w-md leading-relaxed">
              Create your institutional account and link your college. Once approved by the portal administrator, you will gain access to your college's live student directory and analytics.
            </p>
          </div>

          {/* Access Policy Notice */}
          <div className="mt-6 flex items-start gap-3 rounded-2xl border border-brand-200 dark:border-brand-500/20 bg-brand-50 dark:bg-brand-500/10 p-3.5 text-xs text-brand-800 dark:text-brand-300">
            <ShieldCheck className="h-4 w-4 shrink-0 text-brand-600 dark:text-brand-400 mt-0.5" />
            <span>
              <strong>Admin Verification Required:</strong> After submitting, your college selection is sent to administrators. Student telemetry remains hidden until granted access.
            </span>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div className="mt-4 flex items-start gap-3 rounded-2xl border border-rose-200 dark:border-rose-500/20 bg-rose-50 dark:bg-rose-500/10 p-3.5 text-xs text-rose-700 dark:text-rose-300">
              <ShieldAlert className="h-4 w-4 shrink-0 text-rose-500 dark:text-rose-400 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Registration Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField label="Full Name" error={errors.full_name?.message} required>
                <div className="relative">
                  <UserIcon className="absolute left-3 top-2.5 h-4 w-4 text-slate-400 dark:text-slate-500" />
                  <Input
                    {...register("full_name")}
                    placeholder="Prof. Ramesh Kumar"
                    className="pl-9"
                  />
                </div>
              </FormField>

              <FormField label="Official Institutional Email" error={errors.email?.message} required>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400 dark:text-slate-500" />
                  <Input
                    {...register("email")}
                    type="email"
                    placeholder="tpo@institution.edu"
                    className="pl-9"
                  />
                </div>
              </FormField>
            </div>

            {/* College Selection */}
            <FormField
              label="Select Institutional College"
              error={errors.college_id?.message}
              required
            >
              <div className="relative">
                <Building2 className="absolute left-3 top-3 h-4 w-4 text-slate-400 dark:text-slate-500 pointer-events-none" />
                <select
                  {...register("college_id")}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50/80 dark:bg-surface-950/80 pl-10 pr-4 py-2.5 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-surface-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 transition-colors"
                >
                  <option value="">
                    {isCollegesLoading ? "Loading colleges list..." : "Choose your college / institution..."}
                  </option>
                  {colleges.map((col) => (
                    <option key={col.id} value={col.id}>
                      {col.name} {col.code ? `(${col.code})` : ""} {col.city ? `— ${col.city}` : ""}
                    </option>
                  ))}
                </select>
              </div>
            </FormField>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <FormField label="Mobile Number" error={errors.mobile_number?.message} required>
                <div className="relative">
                  <Phone className="absolute left-3 top-2.5 h-4 w-4 text-slate-400 dark:text-slate-500" />
                  <Input
                    {...register("mobile_number")}
                    placeholder="9876543210"
                    className="pl-9"
                  />
                </div>
              </FormField>

              <FormField label="Designation" error={errors.designation?.message} required>
                <div className="relative">
                  <Briefcase className="absolute left-3 top-2.5 h-4 w-4 text-slate-400 dark:text-slate-500" />
                  <Input
                    {...register("designation")}
                    placeholder="Training & Placement Officer"
                    className="pl-9"
                  />
                </div>
              </FormField>

              <FormField label="Department" error={errors.department?.message} required>
                <Input
                  {...register("department")}
                  placeholder="Training & Placement Cell"
                />
              </FormField>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField label="Create Password" error={errors.password?.message} required>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400 dark:text-slate-500" />
                  <Input
                    {...register("password")}
                    type="password"
                    placeholder="••••••••••••"
                    className="pl-9"
                  />
                </div>
              </FormField>

              <FormField
                label="Confirm Password"
                error={errors.confirm_password?.message}
                required
              >
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400 dark:text-slate-500" />
                  <Input
                    {...register("confirm_password")}
                    type="password"
                    placeholder="••••••••••••"
                    className="pl-9"
                  />
                </div>
              </FormField>
            </div>

            <div className="pt-3">
              <Button
                type="submit"
                isLoading={isLoading}
                className="w-full h-11 text-sm font-semibold shadow-lg shadow-brand-500/25 flex items-center justify-center gap-2"
              >
                <span>Submit TPO Registration</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          </form>

          {/* Navigation to Login */}
          <div className="mt-8 border-t border-slate-200 dark:border-surface-800 pt-6 text-center text-xs text-slate-500 dark:text-slate-400">
            <span>Already have an authorized TPO account? </span>
            <Link
              to="/tpo/login"
              className="font-semibold text-brand-600 dark:text-brand-400 hover:text-brand-700 dark:hover:text-brand-300 hover:underline transition-colors"
            >
              Sign In to TPO Portal →
            </Link>
          </div>
        </div>
      </div>

      {/* Success Modal */}
      <Modal
        isOpen={isSuccessModalOpen}
        onClose={() => {
          setIsSuccessModalOpen(false);
          navigate("/tpo/login");
        }}
        title="Registration Submitted for Approval"
      >
        <div className="space-y-4 text-center py-3">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-500 dark:text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="h-8 w-8" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Application Under Review
            </h3>
            <p className="mt-2 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              Your TPO registration for <strong className="text-brand-600 dark:text-brand-400">{registeredCollegeName}</strong> has been received and forwarded to the administrator for verification.
            </p>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-100 dark:bg-surface-900 border border-slate-200 dark:border-surface-800 text-xs text-slate-600 dark:text-slate-400 text-left">
            <p className="font-semibold text-slate-800 dark:text-slate-200 mb-1">What happens next?</p>
            <ul className="list-disc list-inside space-y-1 text-[11px]">
              <li>The administrator will review your college affiliation.</li>
              <li>Once access is granted, you will be able to sign in to the TPO Portal.</li>
              <li>No student information is accessible until approval is confirmed.</li>
            </ul>
          </div>
          <div className="pt-2">
            <Button
              className="w-full"
              onClick={() => {
                setIsSuccessModalOpen(false);
                navigate("/tpo/login");
              }}
            >
              Proceed to TPO Sign In
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
