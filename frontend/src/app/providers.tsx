import React from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { ToastProvider } from "../context/ToastContext";
import { queryClient } from "./queryClient";

interface AppProvidersProps {
  children: React.ReactNode;
}

export const AppProviders: React.FC<AppProvidersProps> = ({ children }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        {children}
      </ToastProvider>
    </QueryClientProvider>
  );
};
