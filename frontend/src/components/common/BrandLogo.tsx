import React from "react";

export interface BrandLogoProps {
  variant?: "full" | "icon" | "image-card" | "sidebar" | "banner";
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
  subtitle?: string;
  badge?: string;
  badgeVariant?: "admin" | "student" | "default";
}

export const BrandLogo: React.FC<BrandLogoProps> = ({
  variant = "full",
  size = "md",
  className = "",
  subtitle,
  badge,
  badgeVariant = "default",
}) => {
  // Size mapping for icon
  const iconSizes = {
    sm: "h-8 w-8",
    md: "h-9 w-9",
    lg: "h-12 w-12",
    xl: "h-16 w-16",
  };

  // Badge styles
  const badgeStyles = {
    admin: "bg-brand-500/15 text-brand-600 dark:text-brand-400 border border-brand-500/25",
    student: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/25",
    default: "bg-slate-100 dark:bg-surface-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-surface-700",
  };

  // Full Image Card for Login Screens and Prominent Branding
  if (variant === "image-card" || variant === "banner") {
    return (
      <div className={`inline-flex items-center justify-center rounded-2xl bg-white p-3.5 shadow-xl shadow-brand-500/5 dark:shadow-black/40 ring-1 ring-slate-200/80 transition-all duration-300 hover:shadow-brand-500/20 hover:ring-brand-500/30 ${className}`}>
        <img
          src="/gqt-logo.jpg"
          alt="Global Quest Technologies - Training | Innovation | Placement"
          className="h-16 w-auto max-w-[260px] object-contain select-none"
        />
      </div>
    );
  }

  // Sidebar Header Layout
  if (variant === "sidebar") {
    return (
      <div className={`flex items-center gap-3 ${className}`}>
        {/* Crisp White Logo Badge */}
        <div className="relative flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white p-1 shadow-md shadow-brand-950/20 dark:shadow-brand-950/50 ring-1 ring-slate-200 dark:ring-white/30 transition-transform duration-200 hover:scale-105">
          <img
            src="/gqt-logo.jpg"
            alt="GQT"
            className="h-full w-full object-contain"
          />
        </div>

        {/* Brand Text Lockup */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <span className="text-sm font-bold tracking-tight text-slate-900 dark:text-white">
              GQT Portal
            </span>
            {badge && (
              <span className={`rounded-md px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider ${badgeStyles[badgeVariant]}`}>
                {badge}
              </span>
            )}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium truncate">
            {subtitle || "Global Quest Technologies"}
          </p>
        </div>
      </div>
    );
  }

  // Icon Only
  if (variant === "icon") {
    return (
      <div className={`relative flex shrink-0 items-center justify-center rounded-xl bg-white p-1 shadow-md shadow-brand-950/20 ring-1 ring-slate-200 ${iconSizes[size]} ${className}`}>
        <img
          src="/gqt-logo.jpg"
          alt="GQT"
          className="h-full w-full object-contain"
        />
      </div>
    );
  }

  // Default 'full' variant
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="relative flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white p-1 shadow-md shadow-brand-950/20 ring-1 ring-slate-200">
        <img
          src="/gqt-logo.jpg"
          alt="GQT"
          className="h-full w-full object-contain"
        />
      </div>
      <div>
        <div className="flex items-center gap-2">
          <span className="text-base font-extrabold tracking-tight text-slate-900 dark:text-white">
            GQT Portal
          </span>
          {badge && (
            <span className={`rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${badgeStyles[badgeVariant]}`}>
              {badge}
            </span>
          )}
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
          {subtitle || "Global Quest Technologies"}
        </p>
      </div>
    </div>
  );
};
