import React from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";

export const StudentRouteGuard: React.FC = () => {
  const { user } = useAuthStore();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Prevent admin from accessing student portal
  if (user.role === "ADMIN") {
    return <Navigate to="/admin/dashboard" replace />;
  }

  // Prevent TPO from accessing student portal
  if (user.role === "TPO") {
    return <Navigate to="/tpo/dashboard" replace />;
  }

  if (user.role !== "STUDENT") {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
};
