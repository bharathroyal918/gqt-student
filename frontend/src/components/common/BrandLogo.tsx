import React from "react";

export interface BrandLogoProps {
  variant?: "full" | "icon" | "image-card" | "sidebar";
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
    admin: "bg-brand-500/15 text-brand-400 border border-brand-500/25",
    student: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/25",
    default: "bg-surface-800 text-slate-300 border border-surface-700",
  };

  if (variant === "icon") {
    return (
      <div className={`relative flex shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#001845] to-[#002868] p-1.5 shadow-md shadow-brand-500/20 border border-brand-500/30 ${iconSizes[size]} ${className}`}>
        <img
          src="/gqt-icon.svg"
          alt="GQT"
          className="h-full w-full object-contain"
          onError={(e) => {
            // Fallback to stylized text if svg fails
            e.currentTarget.style.display = "none";
          }}
        />
      </div>
    );
  }

  if (variant === "image-card") {
    return (
      <div className={`inline-flex items-center justify-center rounded-2xl bg-white p-2.5 shadow-xl shadow-brand-900/30 ring-1 ring-slate-200/80 ${className}`}>
        <img
          src="/gqt-logo.jpg"
          alt="Global Quest Technologies"
          className="h-12 w-auto max-w-[200px] object-contain"
        />
      </div>
    );
  }

  if (variant === "sidebar") {
    return (
      <div className={`flex items-center gap-3 ${className}`}>
        {/* Crisp high-resolution GQT Brand Icon */}
        <div className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#00173d] via-[#002868] to-[#0047ba] p-1.5 shadow-lg shadow-brand-600/20 border border-brand-500/30 transition-transform duration-200 group-hover:scale-105">
          <img
            src="/gqt-icon.svg"
            alt="GQT"
            className="h-full w-full object-contain filter drop-shadow"
          />
        </div>

        {/* Brand Text Lockup */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <span className="text-sm font-bold tracking-tight text-white">
              GQT Portal
            </span>
            {badge && (
              <span className={`rounded-md px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider ${badgeStyles[badgeVariant]}`}>
                {badge}
              </span>
            )}
          </div>
          <p className="text-[11px] text-slate-400 font-medium truncate">
            {subtitle || "Global Quest Technologies"}
          </p>
        </div>
      </div>
    );
  }

  // Default 'full' variant
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#001845] to-[#002868] p-1.5 shadow-md shadow-brand-500/20 border border-brand-500/30">
        <img
          src="/gqt-icon.svg"
          alt="GQT"
          className="h-full w-full object-contain"
        />
      </div>
      <div>
        <div className="flex items-center gap-2">
          <span className="text-base font-extrabold tracking-tight text-white">
            GQT Portal
          </span>
          {badge && (
            <span className={`rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${badgeStyles[badgeVariant]}`}>
              {badge}
            </span>
          )}
        </div>
        <p className="text-xs text-slate-400 font-medium">
          {subtitle || "Global Quest Technologies"}
        </p>
      </div>
    </div>
  );
};
