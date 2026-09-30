import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, useNavigate } from "react-router-dom";
import { KeyRound, Lock, ArrowLeft } from "lucide-react";

import { authApi } from "../../api/authApi";
import { Button } from "../../components/ui/Button";
import { FormField, Input } from "../../components/ui/Form";
import { useToast } from "../../context/ToastContext";

const resetSchema = z
  .object({
    token: z.string().min(1, "Reset token is required"),
    new_password: z.string().min(10, "Password must be at least 10 characters"),
    confirm_password: z.string().min(1, "Please confirm password"),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type ResetFormData = z.infer<typeof resetSchema>;

export const ResetPasswordPage: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
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
      navigate("/auth/login");
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
    <div className="flex min-h-screen items-center justify-center bg-surface-950 p-4">
      <div className="w-full max-w-md">
        <div className="rounded-3xl border border-surface-800 bg-surface-900/80 p-8 shadow-2xl backdrop-blur-xl">
          <Link
            to="/auth/login"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-white mb-6 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to login
          </Link>

          <div className="text-left mb-6">
            <h1 className="text-2xl font-bold tracking-tight text-white">Reset Password</h1>
            <p className="mt-1 text-xs text-slate-400">
              Provide your token and choose a secure 10+ character password.
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <FormField label="Reset Token" error={errors.token?.message} required>
              <div className="relative">
                <KeyRound className="absolute left-3.5 top-3 h-4 w-4 text-slate-500 pointer-events-none" />
                <Input
                  {...register("token")}
                  placeholder="Paste reset token here"
                  className="pl-10 font-mono text-xs"
                  error={!!errors.token}
                  disabled={isLoading}
                />
              </div>
            </FormField>

            <FormField label="New Password" error={errors.new_password?.message} required>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-500 pointer-events-none" />
                <Input
                  {...register("new_password")}
                  type="password"
                  placeholder="At least 10 characters"
                  className="pl-10"
                  error={!!errors.new_password}
                  disabled={isLoading}
                />
              </div>
            </FormField>

            <FormField label="Confirm Password" error={errors.confirm_password?.message} required>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-500 pointer-events-none" />
                <Input
                  {...register("confirm_password")}
                  type="password"
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
