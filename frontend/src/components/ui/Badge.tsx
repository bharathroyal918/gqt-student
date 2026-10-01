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
    primary: "bg-brand-500/10 text-brand-700 dark:text-brand-400 border-brand-500/25",
    success: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/25",
    warning: "bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/25",
    danger: "bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/25",
    neutral: "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700",
    cyan: "bg-cyan-500/10 text-cyan-700 dark:text-cyan-400 border-cyan-500/25",
    easy: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/25",
    medium: "bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/25",
    hard: "bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/25",
    indigo: "bg-indigo-500/10 text-indigo-700 dark:text-indigo-400 border-indigo-500/25",
    emerald: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/25",
    amber: "bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/25",
    rose: "bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/25",
    slate: "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700",
    brand: "bg-brand-500/10 text-brand-700 dark:text-brand-400 border-brand-500/25",
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

