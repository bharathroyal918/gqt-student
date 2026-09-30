import React from "react";

interface StatusDotProps {
  status: boolean | "ACTIVE" | "IN_PROGRESS" | "COMPLETED" | "PENDING_ACTIVATION" | "SUSPENDED" | string;
  label?: string;
  pulse?: boolean;
  className?: string;
}

export const StatusDot: React.FC<StatusDotProps> = ({ status, label, pulse: pulseProp, className = "" }) => {
  let color = "bg-slate-400";
  let pulse = pulseProp !== undefined ? pulseProp : false;

  if (typeof status === "boolean") {
    color = status ? "bg-emerald-400" : "bg-rose-400";
  } else {
    switch (status?.toUpperCase()) {
      case "ACTIVE":
      case "COMPLETED":
      case "APPROVED":
        color = "bg-emerald-400";
        break;
      case "IN_PROGRESS":
      case "UNDER_REVIEW":
        color = "bg-amber-400";
        pulse = true;
        break;
      case "PENDING_ACTIVATION":
      case "CHANGES_REQUESTED":
        color = "bg-cyan-400";
        break;
      case "SUSPENDED":
      case "REJECTED":
      case "LOCKED":
        color = "bg-rose-400";
        break;
      default:
        color = "bg-slate-400";
    }
  }

  return (
    <div className={`inline-flex items-center gap-2 text-xs font-medium text-slate-300 ${className}`}>
      <span className="relative flex h-2 w-2">
        {pulse && (
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${color}`} />
        )}
        <span className={`relative inline-flex rounded-full h-2 w-2 ${color}`} />
      </span>
      {label && <span>{label}</span>}
    </div>
  );
};
