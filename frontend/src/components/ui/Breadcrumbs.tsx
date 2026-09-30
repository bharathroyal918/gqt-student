import React from "react";
import { Link, useLocation } from "react-router-dom";
import { ChevronRight, Home } from "lucide-react";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  items?: BreadcrumbItem[];
  className?: string;
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ items, className = "" }) => {
  const location = useLocation();

  // If items not explicitly provided, generate automatically from path segments
  const breadcrumbItems: BreadcrumbItem[] = React.useMemo(() => {
    if (items && items.length > 0) return items;

    const segments = location.pathname.split("/").filter(Boolean);
    const generated: BreadcrumbItem[] = [{ label: "Home", href: "/dashboard" }];

    let accumulatedPath = "";
    for (const segment of segments) {
      accumulatedPath += `/${segment}`;
      // Format segment name nicely (e.g. "help-ai" -> "Help AI", "assignments" -> "Assignments")
      const formattedLabel = segment
        .split("-")
        .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
        .join(" ");

      generated.push({
        label: formattedLabel,
        href: accumulatedPath,
      });
    }

    return generated;
  }, [items, location.pathname]);

  return (
    <nav aria-label="Breadcrumb" className={`flex items-center text-xs text-slate-400 ${className}`}>
      <ol className="flex items-center space-x-1.5 overflow-x-auto whitespace-nowrap">
        {breadcrumbItems.map((item, index) => {
          const isLast = index === breadcrumbItems.length - 1;
          const isFirst = index === 0;

          return (
            <li key={index} className="flex items-center">
              {index > 0 && <ChevronRight className="h-3.5 w-3.5 mx-1 text-slate-600 shrink-0" />}

              {isLast ? (
                <span className="font-semibold text-white truncate max-w-[200px]" aria-current="page">
                  {item.label}
                </span>
              ) : (
                <Link
                  to={item.href || "#"}
                  className="flex items-center gap-1 hover:text-brand-400 transition-colors"
                >
                  {isFirst && <Home className="h-3.5 w-3.5" />}
                  <span>{item.label}</span>
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};
