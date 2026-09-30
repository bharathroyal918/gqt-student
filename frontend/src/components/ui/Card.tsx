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
      className={`rounded-2xl border border-surface-800 bg-surface-900/60 p-6 shadow-xl backdrop-blur-md transition-all duration-200 ${
        onClick ? "cursor-pointer hover:border-surface-700 hover:bg-surface-900/80" : ""
      } ${className}`}
    >
      {children}
    </div>
  );
};
