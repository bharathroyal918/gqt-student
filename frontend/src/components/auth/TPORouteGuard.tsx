import React from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Building2, LogOut } from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import { tpoApi } from "../../api/tpoApi";
import { Button } from "../ui/Button";

export const TPORouteGuard: React.FC = () => {
  const { user, clearAuth } = useAuthStore();

  if (!user || user.role !== "TPO") {
    return <Navigate to="/unauthorized" replace />;
  }

  // Fetch current TPO profile and assigned college directly from authoritative backend
  const { data: profile, isLoading } = useQuery({
    queryKey: ["tpo-profile-me", user.id],
    queryFn: tpoApi.getMe,
    staleTime: 60 * 1000,
  });

  if (isLoading) {
    return (
      <div className="flex min-h-screen w-screen items-center justify-center bg-slate-950 text-slate-100">
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="h-10 w-10 animate-spin rounded-full border-3 border-brand-500 border-t-transparent" />
          <p className="text-sm font-medium text-slate-400">Verifying college assignment...</p>
        </div>
      </div>
    );
  }

  // If no college is assigned or college is inactive, fail closed gracefully
  if (!profile?.college || !profile.college.is_active || !profile.is_active) {
    return (
      <div className="flex min-h-screen w-screen items-center justify-center bg-slate-900 p-4 font-sans text-slate-100">
        <div className="max-w-md w-full rounded-2xl border border-amber-500/20 bg-slate-950/80 p-8 text-center shadow-2xl backdrop-blur-xl">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-400 border border-amber-500/20 mb-5">
            <Building2 className="h-8 w-8" />
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            College Assignment Pending
          </h2>
          <p className="mt-3 text-sm text-slate-400 leading-relaxed">
            Your Training & Placement Officer account has been created, but an administrator has
            not assigned you to an active institution yet or your assignment is currently inactive.
          </p>
          <div className="mt-6 flex flex-col gap-3">
            <Button
              variant="outline"
              onClick={() => window.location.reload()}
              className="w-full"
            >
              Check Again
            </Button>
            <Button
              variant="ghost"
              onClick={() => {
                clearAuth();
                window.location.href = "/login";
              }}
              className="w-full text-slate-400 hover:text-white"
            >
              <LogOut className="h-4 w-4 mr-2" /> Sign Out
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return <Outlet />;
};
