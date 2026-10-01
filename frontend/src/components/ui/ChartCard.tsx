import React from "react";
import { Card } from "./Card";

interface ChartCardProps {
  title: string;
  subtitle?: string;
  description?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const ChartCard: React.FC<ChartCardProps> = ({
  title,
  subtitle,
  description,
  action,
  children,
  className = "",
}) => {
  const sub = subtitle || description;
  return (
    <Card className={`flex flex-col gap-4 ${className}`}>
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 dark:border-surface-800 pb-3">
        <div>
          <h3 className="font-semibold text-slate-900 dark:text-white tracking-tight text-base">{title}</h3>
          {sub && <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{sub}</p>}
        </div>
        {action && <div>{action}</div>}
      </div>
      <div className="w-full flex-1 min-h-[260px] flex items-center justify-center">
        {children}
      </div>
    </Card>
  );
};
