import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link } from "react-router-dom";
import { Mail, ArrowLeft, CheckCircle2 } from "lucide-react";

import { authApi } from "../../api/authApi";
import { Button } from "../../components/ui/Button";
import { FormField, Input } from "../../components/ui/Form";
import { useToast } from "../../context/ToastContext";

const forgotSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
});

type ForgotFormData = z.infer<typeof forgotSchema>;

export const ForgotPasswordPage: React.FC = () => {
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { error: toastError } = useToast();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotFormData>({
    resolver: zodResolver(forgotSchema),
  });

  const onSubmit = async (data: ForgotFormData) => {
    setIsLoading(true);
    try {
      await authApi.requestPasswordReset(data.email);
      setSubmittedEmail(data.email);
      setIsSubmitted(true);
    } catch (err: any) {
      toastError("Request Failed", "Unable to process password reset request. Please try again.");
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

          {isSubmitted ? (
            <div className="text-center py-4">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-400 mb-4">
                <CheckCircle2 className="h-7 w-7" />
              </div>
              <h2 className="text-xl font-bold text-white">Reset Instructions Dispatched</h2>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                If an approved account is associated with <strong className="text-white">{submittedEmail}</strong>,
                password reset instructions and token have been issued.
              </p>
              <div className="mt-6">
                <Link to="/auth/reset-password">
                  <Button variant="secondary" className="w-full">
                    Proceed to Enter Reset Token
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            <>
              <div className="text-left mb-6">
                <h1 className="text-2xl font-bold tracking-tight text-white">Forgot Password</h1>
                <p className="mt-1 text-xs text-slate-400">
                  Enter your registered administrative email to receive a password reset token.
                </p>
              </div>

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <FormField label="Email Address" error={errors.email?.message} required>
                  <div className="relative">
                    <Mail className="absolute left-3.5 top-3 h-4 w-4 text-slate-500 pointer-events-none" />
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

                <Button type="submit" className="w-full mt-2" isLoading={isLoading}>
                  Send Reset Token
                </Button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
