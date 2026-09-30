import React, { useEffect } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";

export const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, isLoading, user, hydrateAuth } = useAuthStore();
  const location = useLocation();

  useEffect(() => {
    // If we have a token stored but user object is not yet hydrated, hydrate from backend
    if (isAuthenticated && !user) {
      hydrateAuth();
    }
  }, [isAuthenticated, user, hydrateAuth]);

  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-surface-950 text-slate-400">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
          <span className="text-sm font-medium">Validating student session...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
};
