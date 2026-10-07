import React from "react";
import { LoadingState } from "./LoadingState";
import { ErrorState } from "./ErrorState";
import { EmptyState } from "./EmptyState";
import { Pagination } from "./Pagination";

export interface Column<T> {
  key?: string;
  header: React.ReactNode;
  accessor?: keyof T | ((row: T) => React.ReactNode);
  cell?: (row: T) => React.ReactNode;
  align?: "left" | "center" | "right";
  className?: string;
  headerClassName?: string;
}

interface DataTablePagination {
  currentPage?: number;
  page?: number;
  totalPages: number;
  totalRecords?: number;
  pageSize?: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data?: T[];
  isLoading?: boolean;
  isError?: boolean;
  errorMessage?: string;
  onRetry?: () => void;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyMessage?: string;
  onRowClick?: (row: T) => void;
  keyExtractor?: (row: T, index: number) => string | number;
  pagination?: DataTablePagination;
  className?: string;
}

export function DataTable<T>({
  columns,
  data = [],
  isLoading = false,
  isError = false,
  errorMessage,
  onRetry,
  emptyTitle = "No records found",
  emptyDescription,
  emptyMessage = "There are currently no items to display in this table.",
  onRowClick,
  keyExtractor,
  pagination,
  className = "",
}: DataTableProps<T>) {
  if (isLoading && data.length === 0) {
    return (
      <div className={`overflow-hidden rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/80 shadow-sm dark:shadow-xl ${className}`}>
        <LoadingState type="skeleton" rows={5} />
      </div>
    );
  }

  if (isError && data.length === 0) {
    return (
      <div className={`overflow-hidden rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/80 shadow-sm dark:shadow-xl ${className}`}>
        <ErrorState message={errorMessage} onRetry={onRetry} />
      </div>
    );
  }

  return (
    <div className={`overflow-hidden rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/80 shadow-sm dark:shadow-xl backdrop-blur-md flex flex-col ${className}`}>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-200 dark:border-surface-800 bg-slate-50/80 dark:bg-surface-950/70 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              {columns.map((col, idx) => (
                <th
                  key={col.key || idx}
                  className={`px-5 py-3.5 whitespace-nowrap ${
                    col.align === "right"
                      ? "text-right"
                      : col.align === "center"
                      ? "text-center"
                      : "text-left"
                  } ${col.headerClassName || col.className || ""}`}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-surface-800/60 text-sm">
            {data.length === 0 ? (
              <tr>
                <td colSpan={columns.length}>
                  <EmptyState title={emptyTitle} description={emptyDescription || emptyMessage} />
                </td>
              </tr>
            ) : (
              data.map((row, rowIdx) => {
                const rowKey = keyExtractor
                  ? keyExtractor(row, rowIdx)
                  : ((row as any).id || rowIdx);

                return (
                  <tr
                    key={rowKey}
                    onClick={() => onRowClick && onRowClick(row)}
                    className={`transition-colors duration-150 hover:bg-slate-50 dark:hover:bg-surface-800/60 ${
                      onRowClick ? "cursor-pointer" : ""
                    }`}
                  >
                    {columns.map((col, colIdx) => {
                      let cellContent: React.ReactNode = null;
                      if (col.cell) {
                        cellContent = col.cell(row);
                      } else if (typeof col.accessor === "function") {
                        cellContent = col.accessor(row);
                      } else if (col.accessor) {
                        cellContent = row[col.accessor] as unknown as React.ReactNode;
                      }

                      return (
                        <td
                          key={col.key || colIdx}
                          className={`px-5 py-4 whitespace-nowrap text-slate-800 dark:text-slate-100 ${
                            col.align === "right"
                              ? "text-right"
                              : col.align === "center"
                              ? "text-center"
                              : "text-left"
                          } ${col.className || ""}`}
                        >
                          {cellContent}
                        </td>
                      );
                    })}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {pagination && (
        <Pagination
          currentPage={pagination.currentPage ?? pagination.page ?? 1}
          totalPages={pagination.totalPages}
          totalRecords={pagination.totalRecords}
          pageSize={pagination.pageSize}
          onPageChange={pagination.onPageChange}
          onPageSizeChange={pagination.onPageSizeChange}
        />
      )}
    </div>
  );
}
