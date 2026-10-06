import React, { useState, useEffect } from "react";

export interface UserAvatarProps {
  src?: string | null;
  name?: string;
  initials?: string;
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  className?: string;
  imgClassName?: string;
}

const sizeClasses = {
  xs: "h-6 w-6 text-[10px]",
  sm: "h-7 w-7 text-xs",
  md: "h-10 w-10 text-sm",
  lg: "h-12 w-12 text-base font-semibold",
  xl: "h-20 w-20 text-2xl font-bold",
};

export const UserAvatar: React.FC<UserAvatarProps> = ({
  src,
  name = "User",
  initials,
  size = "sm",
  className = "",
  imgClassName = "",
}) => {
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    setHasError(false);
  }, [src]);

  const computedInitials =
    initials ||
    (name
      ? name
          .trim()
          .split(/\s+/)
          .map((n) => n[0])
          .slice(0, 2)
          .join("")
          .toUpperCase()
      : "U");

  const sizeClass = sizeClasses[size] || sizeClasses.sm;
  const cleanSrc = (src || "").trim();

  if (cleanSrc && !hasError) {
    return (
      <img
        src={cleanSrc}
        alt={name}
        className={`shrink-0 rounded-xl object-cover shadow-sm ring-1 ring-brand-500/20 ${sizeClass} ${imgClassName} ${className}`}
        onError={() => setHasError(true)}
      />
    );
  }

  return (
    <div
      className={`shrink-0 flex items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-indigo-600 font-bold text-white shadow-sm ring-1 ring-white/20 dark:ring-surface-800 ${sizeClass} ${className}`}
      title={name}
    >
      {computedInitials}
    </div>
  );
};
