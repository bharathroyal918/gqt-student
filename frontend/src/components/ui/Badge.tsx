import React from "react";

export type BadgeVariant =
  | "primary"
  | "success"
  | "warning"
  | "danger"
  | "neutral"
  | "cyan"
  | "easy"
  | "medium"
  | "hard"
  | "indigo"
  | "emerald"
  | "amber"
  | "rose"
  | "slate"
  | "brand";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: "sm" | "md";
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "neutral",
  size = "md",
  className = "",
}) => {
  const variantStyles: Record<BadgeVariant, string> = {
    primary: "bg-brand-500/15 text-brand-700 dark:text-brand-300 border-brand-500/30",
    success: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/30",
    warning: "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30",
    danger: "bg-rose-500/15 text-rose-700 dark:text-rose-300 border-rose-500/30",
    neutral: "bg-slate-100 dark:bg-surface-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-surface-700",
    cyan: "bg-cyan-500/15 text-cyan-700 dark:text-cyan-300 border-cyan-500/30",
    easy: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/30",
    medium: "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30",
    hard: "bg-rose-500/15 text-rose-700 dark:text-rose-300 border-rose-500/30",
    indigo: "bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 border-indigo-500/30",
    emerald: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/30",
    amber: "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30",
    rose: "bg-rose-500/15 text-rose-700 dark:text-rose-300 border-rose-500/30",
    slate: "bg-slate-100 dark:bg-surface-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-surface-700",
    brand: "bg-brand-500/15 text-brand-700 dark:text-brand-300 border-brand-500/30",
  };

  const sizeStyles = {
    sm: "px-2 py-0.5 text-xs font-medium",
    md: "px-2.5 py-1 text-xs font-semibold",
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border transition-colors ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {children}
    </span>
  );
};
