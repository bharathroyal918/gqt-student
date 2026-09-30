import React from "react";
import { AlertCircle, RotateCcw } from "lucide-react";
import { Button } from "./Button";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Failed to load data",
  message = "An error occurred while fetching information from the server.",
  onRetry,
  className = "",
}) => {
  return (
    <div className={`flex flex-col items-center justify-center p-12 text-center ${className}`}>
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-500/10 text-rose-400 mb-4 border border-rose-500/20">
        <AlertCircle className="h-7 w-7" />
      </div>
      <h3 className="text-base font-semibold text-white tracking-tight">{title}</h3>
      <p className="mt-1 text-sm text-slate-400 max-w-sm leading-relaxed">{message}</p>
      {onRetry && (
        <div className="mt-5">
          <Button variant="secondary" icon={<RotateCcw className="h-4 w-4" />} onClick={onRetry}>
            Retry Request
          </Button>
        </div>
      )}
    </div>
  );
};
