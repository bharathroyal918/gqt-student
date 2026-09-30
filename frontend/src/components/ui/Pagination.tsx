import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalRecords?: number;
  pageSize?: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  className?: string;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  totalRecords,
  pageSize = 20,
  onPageChange,
  onPageSizeChange,
  className = "",
}) => {
  if (totalPages <= 1 && (!totalRecords || totalRecords <= pageSize)) {
    return null;
  }

  const startRecord = (currentPage - 1) * pageSize + 1;
  const endRecord = totalRecords ? Math.min(currentPage * pageSize, totalRecords) : currentPage * pageSize;

  return (
    <div className={`flex flex-wrap items-center justify-between gap-4 border-t border-surface-800 px-4 py-3 text-xs text-slate-400 ${className}`}>
      <div className="flex items-center gap-2">
        {totalRecords !== undefined ? (
          <span>
            Showing <strong className="text-white">{startRecord}</strong> to{" "}
            <strong className="text-white">{endRecord}</strong> of{" "}
            <strong className="text-white">{totalRecords}</strong> results
          </span>
        ) : (
          <span>Page {currentPage} of {totalPages}</span>
        )}

        {onPageSizeChange && (
          <div className="flex items-center gap-1.5 ml-4">
            <span>Per page:</span>
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              className="rounded-lg border border-surface-700 bg-surface-900 px-2 py-1 text-xs text-white focus:border-brand-500 focus:outline-none"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        )}
      </div>

      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-surface-800 bg-surface-900 text-slate-300 hover:bg-surface-800 hover:text-white disabled:opacity-30 disabled:pointer-events-none transition-colors"
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>

        <span className="px-3 text-white font-medium">
          {currentPage} / {Math.max(totalPages, 1)}
        </span>

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-surface-800 bg-surface-900 text-slate-300 hover:bg-surface-800 hover:text-white disabled:opacity-30 disabled:pointer-events-none transition-colors"
          aria-label="Next page"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};
