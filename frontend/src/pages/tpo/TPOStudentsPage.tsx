import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Users,
  Search,
  Eye,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { tpoApi } from "../../api/tpoApi";
import { useAuthStore } from "../../store/authStore";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { LoadingState } from "../../components/ui/LoadingState";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorState } from "../../components/ui/ErrorState";
import { UserAvatar } from "../../components/ui/UserAvatar";

export const TPOStudentsPage: React.FC = () => {
  const { user } = useAuthStore();

  // Filters and Pagination state
  const [searchTerm, setSearchTerm] = useState("");
  const [batchFilter, setBatchFilter] = useState("ALL");
  const [courseFilter, setCourseFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "ACTIVE" | "INACTIVE">("ALL");
  const [ordering, setOrdering] = useState("-total_points");
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // 1. Fetch Summary for dynamic batch & course filter options
  const { data: summary } = useQuery({
    queryKey: ["tpo-college-summary", user?.id],
    queryFn: tpoApi.getCollegeSummary,
    staleTime: 60 * 1000,
  });

  // 2. Fetch Paginated Student Roster
  const {
    data: rosterResponse,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: [
      "tpo-college-students",
      user?.id,
      searchTerm,
      batchFilter,
      courseFilter,
      statusFilter,
      ordering,
      page,
    ],
    queryFn: () =>
      tpoApi.getCollegeStudents({
        search: searchTerm || undefined,
        batch_code: batchFilter === "ALL" ? undefined : batchFilter,
        course_opted: courseFilter === "ALL" ? undefined : courseFilter,
        is_active: statusFilter === "ALL" ? undefined : statusFilter === "ACTIVE",
        ordering: ordering || undefined,
        page,
        page_size: pageSize,
      }),
  });

  const students = Array.isArray(rosterResponse?.data) ? rosterResponse.data : [];
  const pagination = rosterResponse?.meta?.pagination;

  const handleResetFilters = () => {
    setSearchTerm("");
    setBatchFilter("ALL");
    setCourseFilter("ALL");
    setStatusFilter("ALL");
    setOrdering("-total_points");
    setPage(1);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
              Institutional Records
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Student Directory
          </h1>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            Authoritative performance, attendance, and assessment tracking for your assigned college.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            Refresh Roster
          </Button>
        </div>
      </div>

      {/* Filters Bar */}
      <Card className="p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Search */}
          <div className="relative lg:col-span-2">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by student name, ID, or email..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900 pl-9 pr-4 py-2 text-xs text-slate-900 dark:text-white placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>

          {/* Batch Filter */}
          <div>
            <select
              value={batchFilter}
              onChange={(e) => {
                setBatchFilter(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900 px-3 py-2 text-xs text-slate-900 dark:text-white focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="ALL">All Batches</option>
              {summary?.batch_distribution?.map((b) => (
                <option key={b.batch_code} value={b.batch_code}>
                  {b.batch_code} ({b.count})
                </option>
              ))}
            </select>
          </div>

          {/* Course / Track Filter */}
          <div>
            <select
              value={courseFilter}
              onChange={(e) => {
                setCourseFilter(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900 px-3 py-2 text-xs text-slate-900 dark:text-white focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="ALL">All Tracks / Courses</option>
              {summary?.technology_distribution?.map((t) => (
                <option key={t.name} value={t.name}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>

          {/* Sort & Status */}
          <div className="flex gap-2">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as any);
                setPage(1);
              }}
              className="w-1/2 rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900 px-2 py-2 text-xs text-slate-900 dark:text-white focus:border-brand-500 focus:outline-none"
            >
              <option value="ALL">All Status</option>
              <option value="ACTIVE">Active</option>
              <option value="INACTIVE">Inactive</option>
            </select>

            <select
              value={ordering}
              onChange={(e) => {
                setOrdering(e.target.value);
                setPage(1);
              }}
              className="w-1/2 rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900 px-2 py-2 text-xs text-slate-900 dark:text-white focus:border-brand-500 focus:outline-none"
            >
              <option value="-total_points">Points ↓</option>
              <option value="total_points">Points ↑</option>
              <option value="full_name">Name A-Z</option>
              <option value="-attendance_percentage">Attendance ↓</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Roster Table */}
      {isLoading ? (
        <LoadingState message="Loading student records..." />
      ) : isError ? (
        <ErrorState
          title="Error Loading Roster"
          message={
            (error as any)?.response?.data?.error?.message ||
            (error as any)?.response?.data?.message ||
            "Unable to fetch student roster for your assigned college."
          }
          onRetry={() => refetch()}
        />
      ) : students.length === 0 ? (
        <EmptyState
          icon={<Users className="h-8 w-8 text-brand-500" />}
          title="No Students Found"
          description={
            searchTerm || batchFilter !== "ALL" || courseFilter !== "ALL" || statusFilter !== "ALL"
              ? "No students match your filter criteria."
              : "No students are currently registered under your assigned college."
          }
          actionLabel="Reset Filters"
          onAction={handleResetFilters}
        />
      ) : (
        <div className="space-y-4">
          <div className="overflow-hidden rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
                <thead className="border-b border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-950 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  <tr>
                    <th className="px-5 py-3.5">Student</th>
                    <th className="px-5 py-3.5">Track / Branch</th>
                    <th className="px-5 py-3.5">Batch</th>
                    <th className="px-5 py-3.5">Attendance</th>
                    <th className="px-5 py-3.5">Points</th>
                    <th className="px-5 py-3.5">Account</th>
                    <th className="px-5 py-3.5 text-center">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-surface-800">
                  {students.map((student) => {
                    const fullName = student.full_name || "Student";
                    const initials = fullName.slice(0, 2).toUpperCase();
                    const attendancePct = Number(student.attendance_percentage || 0);
                    const totalPoints = Number(student.total_points || 0);

                    return (
                      <tr
                        key={student.id}
                        className="hover:bg-slate-50/80 dark:hover:bg-surface-800/40 transition-colors"
                      >
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-3">
                            <UserAvatar
                              src={student.avatar_url}
                              name={fullName}
                              initials={initials}
                              size="md"
                            />
                            <div>
                              <div className="font-semibold text-slate-900 dark:text-white">
                                {fullName}
                              </div>
                              <div className="text-xs text-slate-400 font-mono">
                                {student.student_id_number || "—"}
                              </div>
                              <div className="text-xs text-slate-500 dark:text-slate-400">
                                {student.email}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <div className="text-xs font-medium text-slate-900 dark:text-white">
                            {student.course_opted || "General"}
                          </div>
                          <div className="text-[11px] text-slate-400 mt-0.5">
                            {student.branch || "General"}
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-surface-800 text-slate-700 dark:text-slate-300">
                            {student.batch_code || "Unassigned"}
                          </span>
                        </td>
                        <td className="px-5 py-4">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                              attendancePct >= 75
                                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                                : "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                            }`}
                          >
                            {attendancePct}%
                          </span>
                        </td>
                        <td className="px-5 py-4 font-bold text-slate-900 dark:text-white">
                          {totalPoints.toFixed(0)}
                        </td>
                        <td className="px-5 py-4">
                          <Badge variant={student.is_active ? "success" : "neutral"} size="sm">
                            {student.is_active ? "Active" : "Inactive"}
                          </Badge>
                        </td>
                        <td className="px-5 py-4 text-center">
                          <Link
                            to={`/tpo/students/${student.id}`}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-brand-500/10 text-brand-600 dark:text-brand-400 hover:bg-brand-500/20 transition-colors"
                          >
                            <Eye className="h-3.5 w-3.5" /> View Profile
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {pagination && pagination.total_pages > 1 && (
            <div className="flex items-center justify-between px-2 text-xs text-slate-500 dark:text-slate-400">
              <div>
                Showing {(page - 1) * pageSize + 1} to{" "}
                {Math.min(page * pageSize, pagination.total_records)} of{" "}
                {pagination.total_records} students
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!pagination.has_prev}
                  onClick={() => setPage((p) => Math.max(p - 1, 1))}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" /> Previous
                </Button>
                <span className="font-semibold text-slate-700 dark:text-slate-300">
                  Page {pagination.page} of {pagination.total_pages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!pagination.has_next}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
