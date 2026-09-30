import React from "react";
import { Loader2 } from "lucide-react";

export type ButtonVariant = "primary" | "secondary" | "danger" | "ghost" | "outline";
export type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  size = "md",
  isLoading = false,
  icon,
  className = "",
  disabled,
  ...props
}) => {
  const base =
    "inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none active:scale-[0.98]";

  const variants: Record<ButtonVariant, string> = {
    primary:
      "bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-500/25 focus:ring-brand-500 focus:ring-offset-surface-950",
    secondary:
      "bg-surface-800 hover:bg-surface-700 text-slate-200 border border-surface-700/60 focus:ring-surface-700 focus:ring-offset-surface-950",
    danger:
      "bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-500/20 focus:ring-rose-500 focus:ring-offset-surface-950",
    ghost:
      "bg-transparent hover:bg-surface-800 text-slate-300 hover:text-white focus:ring-slate-700",
    outline:
      "bg-transparent border border-surface-700 hover:border-surface-600 text-slate-300 hover:text-white hover:bg-surface-800/50 focus:ring-brand-500",
  };

  const sizes: Record<ButtonSize, string> = {
    sm: "h-8 px-3 text-xs gap-1.5",
    md: "h-10 px-4 text-sm gap-2",
    lg: "h-12 px-6 text-base gap-2.5",
  };

  return (
    <button
      className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="h-4 w-4 animate-spin text-current" />
      ) : (
        icon && <span className="shrink-0">{icon}</span>
      )}
      {children}
    </button>
  );
};
