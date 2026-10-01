import React from "react";
import { Loader2 } from "lucide-react";

interface LoadingStateProps {
  message?: string;
  rows?: number;
  type?: "spinner" | "skeleton";
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = "Loading records...",
  rows = 5,
  type = "spinner",
  className = "",
}) => {
  if (type === "skeleton") {
    return (
      <div className={`space-y-3 p-4 animate-pulse ${className}`}>
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="h-10 rounded-xl bg-slate-200/80 dark:bg-surface-800/60 w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className={`flex flex-col items-center justify-center p-12 text-center ${className}`}>
      <Loader2 className="h-8 w-8 animate-spin text-brand-500 mb-3" />
      <p className="text-sm font-medium text-slate-600 dark:text-slate-400">{message}</p>
    </div>
  );
};

