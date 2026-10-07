import React from "react";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({ children, className = "", onClick }) => {
  return (
    <div
      onClick={onClick}
      className={`rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/80 p-6 shadow-sm dark:shadow-xl backdrop-blur-md ${
        onClick
          ? "cursor-pointer hover:border-slate-300 dark:hover:border-surface-700 hover:bg-slate-50/80 dark:hover:bg-surface-850"
          : ""
      } ${className}`}
    >
      {children}
    </div>
  );
};
