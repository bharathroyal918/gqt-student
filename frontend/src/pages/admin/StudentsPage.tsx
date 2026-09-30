import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  UserPlus,
  Eye,
  Edit2,
  CheckCircle2,
  XCircle,
  ShieldCheck,
  ShieldAlert,
  BookOpen,
} from "lucide-react";
import { adminApi } from "../../api/adminApi";
import { StudentListItem } from "../../types/admin";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { StatusDot } from "../../components/ui/StatusDot";
import { DataTable, Column } from "../../components/ui/DataTable";
import { SearchInput } from "../../components/ui/SearchInput";
import { Modal } from "../../components/ui/Modal";
import { FormField, Input, Select } from "../../components/ui/Form";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { useToast } from "../../context/ToastContext";

export const StudentsPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  // Filter & Pagination state
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState("");
  const [batchFilter, setBatchFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  // Modals state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState<StudentListItem | null>(null);
  const [statusDialogStudent, setStatusDialogStudent] = useState<{
    student: StudentListItem;
    action: "activate" | "deactivate" | "grant" | "revoke";
  } | null>(null);

  // Form states for Provisioning / Editing
  const [formData, setFormData] = useState({
    full_name: "",
    student_id_number: "",
    batch_code: "",
    email: "",
    mobile_number: "",
    college_name: "",
    graduation_year: new Date().getFullYear(),
    password: "",
  });

  // Fetch Students Query
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["admin-students", { page, pageSize, search, batchFilter, statusFilter }],
    queryFn: () =>
      adminApi.getStudents({
        page,
        page_size: pageSize,
        search: search.trim() || undefined,
        batch_code: batchFilter || undefined,
        onboarding_status: statusFilter || undefined,
      }),
  });

  // Provision Student Mutation
  const provisionMutation = useMutation({
    mutationFn: adminApi.provisionStudent,
    onSuccess: (newStudent) => {
      success("Student Provisioned", `${newStudent.full_name} (${newStudent.student_id_number}) created.`);
      setIsAddModalOpen(false);
      resetForm();
      queryClient.invalidateQueries({ queryKey: ["admin-students"] });
      queryClient.invalidateQueries({ queryKey: ["admin-dashboard-stats"] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.message || err.response?.data?.error?.message || "Failed to provision student";
      toastError("Provisioning Failed", msg);
    },
  });

  // Update Student Mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<StudentListItem> }) =>
      adminApi.updateStudent(id, payload as any),
    onSuccess: () => {
      success("Student Updated", "Account records have been saved.");
      setEditingStudent(null);
      queryClient.invalidateQueries({ queryKey: ["admin-students"] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.message || err.response?.data?.error?.message || "Failed to update student";
      toastError("Update Failed", msg);
    },
  });

  const resetForm = () => {
    setFormData({
      full_name: "",
      student_id_number: "",
      batch_code: "",
      email: "",
      mobile_number: "",
      college_name: "",
      graduation_year: new Date().getFullYear(),
      password: "",
    });
  };

  const handleOpenAdd = () => {
    resetForm();
    setIsAddModalOpen(true);
  };

  const handleOpenEdit = (student: StudentListItem) => {
    setEditingStudent(student);
    setFormData({
      full_name: student.full_name,
      student_id_number: student.student_id_number,
      batch_code: student.batch_code,
      email: student.email || "",
      mobile_number: student.mobile_number || "",
      college_name: student.college_name || "",
      graduation_year: student.graduation_year || new Date().getFullYear(),
      password: "",
    });
  };

  const handleStatusActionConfirm = () => {
    if (!statusDialogStudent) return;
    const { student, action } = statusDialogStudent;

    let payload: any = {};
    if (action === "activate") payload = { is_active: true };
    if (action === "deactivate") payload = { is_active: false };
    if (action === "grant") payload = { onboarding_status: "ACTIVE" };
    if (action === "revoke") payload = { onboarding_status: "SUSPENDED" };

    updateMutation.mutate({ id: student.id, payload });
    setStatusDialogStudent(null);
  };

  // Table Columns
  const columns: Column<StudentListItem>[] = [
    {
      key: "student",
      header: "Student",
      cell: (row) => (
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-600/30 to-indigo-600/30 text-brand-300 font-bold border border-brand-500/20 text-sm">
            {row.full_name.slice(0, 2).toUpperCase()}
          </div>
          <div className="min-w-0">
            <button
              onClick={() => navigate(`/admin/students/${row.id}`)}
              className="text-left font-semibold text-white hover:text-brand-400 transition-colors truncate block"
            >
              {row.full_name}
            </button>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="font-mono text-slate-300">{row.student_id_number}</span>
              <span>•</span>
              <span className="text-slate-400">{row.email || row.mobile_number || "No Contact"}</span>
            </div>
          </div>
        </div>
      ),
    },
    {
      key: "batch",
      header: "Batch & College",
      cell: (row) => (
        <div className="text-xs">
          <Badge variant="indigo" size="sm">{row.batch_code}</Badge>
          <div className="text-slate-400 mt-1 truncate max-w-[150px]">{row.college_name || "—"}</div>
        </div>
      ),
    },
    {
      key: "performance",
      header: "Points / Courses",
      cell: (row) => (
        <div className="text-xs">
          <div className="font-semibold text-amber-400 flex items-center gap-1">
            <span>{parseFloat(row.total_points || "0").toLocaleString()} pts</span>
          </div>
          <div className="text-slate-400 mt-0.5 flex items-center gap-1">
            <BookOpen className="h-3 w-3" />
            <span>{row.enrolled_courses_count} enrolled</span>
          </div>
        </div>
      ),
    },
    {
      key: "status",
      header: "Status & Access",
      cell: (row) => (
        <div className="space-y-1">
          <div className="flex items-center gap-1.5">
            <StatusDot status={row.is_active ? "online" : "offline"} pulse={row.is_active} />
            <span className="text-xs font-medium text-slate-300">
              {row.is_active ? "Active" : "Inactive"}
            </span>
          </div>
          <div>
            <Badge
              variant={
                row.onboarding_status === "ACTIVE"
                  ? "emerald"
                  : row.onboarding_status === "PENDING_ACTIVATION"
                  ? "amber"
                  : "rose"
              }
              size="sm"
            >
              {row.onboarding_status}
            </Badge>
          </div>
        </div>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      cell: (row) => (
        <div className="flex items-center justify-end gap-1.5">
          {/* View Details */}
          <Button
            size="sm"
            variant="ghost"
            onClick={() => navigate(`/admin/students/${row.id}`)}
            title="View Details"
          >
            <Eye className="h-4 w-4 text-slate-400 hover:text-white" />
          </Button>

          {/* Edit */}
          <Button
            size="sm"
            variant="ghost"
            onClick={() => handleOpenEdit(row)}
            title="Edit Student"
          >
            <Edit2 className="h-4 w-4 text-slate-400 hover:text-brand-400" />
          </Button>

          {/* Toggle Activation */}
          {row.is_active ? (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setStatusDialogStudent({ student: row, action: "deactivate" })}
              title="Deactivate Account"
            >
              <XCircle className="h-4 w-4 text-rose-400 hover:text-rose-300" />
            </Button>
          ) : (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setStatusDialogStudent({ student: row, action: "activate" })}
              title="Activate Account"
            >
              <CheckCircle2 className="h-4 w-4 text-emerald-400 hover:text-emerald-300" />
            </Button>
          )}

          {/* Toggle Portal Access */}
          {row.onboarding_status === "ACTIVE" ? (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setStatusDialogStudent({ student: row, action: "revoke" })}
              title="Revoke Portal Access"
            >
              <ShieldAlert className="h-4 w-4 text-amber-400 hover:text-amber-300" />
            </Button>
          ) : (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setStatusDialogStudent({ student: row, action: "grant" })}
              title="Grant Portal Access"
            >
              <ShieldCheck className="h-4 w-4 text-emerald-400 hover:text-emerald-300" />
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Student Management
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Provision student profiles, manage portal credentials, monitor progress and course enrollments.
          </p>
        </div>

        <Button onClick={handleOpenAdd} className="shadow-lg shadow-brand-600/25">
          <UserPlus className="h-4 w-4 mr-2" />
          Add Student
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col gap-3 rounded-2xl border border-surface-800 bg-surface-900/60 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="w-full sm:max-w-xs">
          <SearchInput
            value={search}
            onChange={(val) => {
              setSearch(val);
              setPage(1);
            }}
            placeholder="Search by name, ID, email..."
          />
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Batch Filter */}
          <div className="w-36">
            <Select
              value={batchFilter}
              onChange={(e) => {
                setBatchFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All Batches</option>
              <option value="BATCH-2025-A">BATCH-2025-A</option>
              <option value="BATCH-2025-B">BATCH-2025-B</option>
              <option value="BATCH-2026-A">BATCH-2026-A</option>
            </Select>
          </div>

          {/* Access Status Filter */}
          <div className="w-40">
            <Select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All Access States</option>
              <option value="ACTIVE">ACTIVE</option>
              <option value="PENDING_ACTIVATION">PENDING</option>
              <option value="SUSPENDED">SUSPENDED</option>
            </Select>
          </div>

          {(search || batchFilter || statusFilter) && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setSearch("");
                setBatchFilter("");
                setStatusFilter("");
                setPage(1);
              }}
            >
              Clear
            </Button>
          )}
        </div>
      </div>

      {/* Students Data Table */}
      <DataTable
        data={data?.data || []}
        columns={columns}
        isLoading={isLoading}
        isError={isError}
        errorMessage="Failed to load student profiles. Ensure the backend services are running."
        onRetry={() => refetch()}
        emptyTitle="No Students Found"
        emptyDescription="No registered students match your filter criteria. Click 'Add Student' to provision a new account."
        pagination={
          data?.meta?.pagination
            ? {
                page: data.meta.pagination.page,
                pageSize: data.meta.pagination.page_size,
                totalRecords: data.meta.pagination.total_records,
                totalPages: data.meta.pagination.total_pages,
                onPageChange: (newPage) => setPage(newPage),
                onPageSizeChange: (newSize) => {
                  setPageSize(newSize);
                  setPage(1);
                },
              }
            : undefined
        }
      />

      {/* Provision Student Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Provision New Student"
        description="Create an authorized student record. An invitation or initial credentials will be assigned."
        size="lg"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            provisionMutation.mutate({
              full_name: formData.full_name,
              student_id_number: formData.student_id_number,
              batch_code: formData.batch_code,
              email: formData.email || undefined,
              mobile_number: formData.mobile_number || undefined,
              college_name: formData.college_name || undefined,
              graduation_year: Number(formData.graduation_year) || undefined,
              password: formData.password || undefined,
            });
          }}
          className="space-y-4"
        >
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FormField label="Full Name" required>
              <Input
                placeholder="e.g. Jane Doe"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                required
              />
            </FormField>

            <FormField label="Student ID / Roll No." required>
              <Input
                placeholder="e.g. GQT-2025-001"
                value={formData.student_id_number}
                onChange={(e) => setFormData({ ...formData, student_id_number: e.target.value })}
                required
              />
            </FormField>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FormField label="Batch Code" required>
              <Input
                placeholder="e.g. BATCH-2025-A"
                value={formData.batch_code}
                onChange={(e) => setFormData({ ...formData, batch_code: e.target.value })}
                required
              />
            </FormField>

            <FormField label="Graduation Year">
              <Input
                type="number"
                value={formData.graduation_year}
                onChange={(e) => setFormData({ ...formData, graduation_year: Number(e.target.value) })}
              />
            </FormField>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FormField label="Email Address">
              <Input
                type="email"
                placeholder="jane@example.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </FormField>

            <FormField label="Mobile Number">
              <Input
                placeholder="+919876543210"
                value={formData.mobile_number}
                onChange={(e) => setFormData({ ...formData, mobile_number: e.target.value })}
              />
            </FormField>
          </div>

          <FormField label="College / Institute Name">
            <Input
              placeholder="e.g. National Institute of Engineering"
              value={formData.college_name}
              onChange={(e) => setFormData({ ...formData, college_name: e.target.value })}
            />
          </FormField>

          <FormField label="Initial Password (Optional)">
            <Input
              type="password"
              placeholder="Leave blank for system-generated setup"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
          </FormField>

          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-surface-800">
            <Button variant="secondary" type="button" onClick={() => setIsAddModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={provisionMutation.isPending}>
              Provision Student
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Student Modal */}
      <Modal
        isOpen={Boolean(editingStudent)}
        onClose={() => setEditingStudent(null)}
        title="Edit Student Profile"
        description="Update contact information, institutional records, and batch associations."
        size="lg"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!editingStudent) return;
            updateMutation.mutate({
              id: editingStudent.id,
              payload: {
                full_name: formData.full_name,
                batch_code: formData.batch_code,
                email: formData.email || null,
                mobile_number: formData.mobile_number || null,
                college_name: formData.college_name,
                graduation_year: Number(formData.graduation_year) || null,
              } as any,
            });
          }}
          className="space-y-4"
        >
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FormField label="Full Name" required>
              <Input
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                required
              />
            </FormField>

            <FormField label="Student ID / Roll No.">
              <Input value={formData.student_id_number} disabled className="opacity-60 cursor-not-allowed" />
            </FormField>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FormField label="Batch Code" required>
              <Input
                value={formData.batch_code}
                onChange={(e) => setFormData({ ...formData, batch_code: e.target.value })}
                required
              />
            </FormField>

            <FormField label="Graduation Year">
              <Input
                type="number"
                value={formData.graduation_year}
                onChange={(e) => setFormData({ ...formData, graduation_year: Number(e.target.value) })}
              />
            </FormField>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FormField label="Email Address">
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </FormField>

            <FormField label="Mobile Number">
              <Input
                value={formData.mobile_number}
                onChange={(e) => setFormData({ ...formData, mobile_number: e.target.value })}
              />
            </FormField>
          </div>

          <FormField label="College / Institute Name">
            <Input
              value={formData.college_name}
              onChange={(e) => setFormData({ ...formData, college_name: e.target.value })}
            />
          </FormField>

          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-surface-800">
            <Button variant="secondary" type="button" onClick={() => setEditingStudent(null)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={updateMutation.isPending}>
              Save Changes
            </Button>
          </div>
        </form>
      </Modal>

      {/* Confirm Status Change Dialog */}
      <ConfirmDialog
        isOpen={Boolean(statusDialogStudent)}
        onClose={() => setStatusDialogStudent(null)}
        onConfirm={handleStatusActionConfirm}
        isLoading={updateMutation.isPending}
        title={
          statusDialogStudent?.action === "activate"
            ? "Activate Student Account?"
            : statusDialogStudent?.action === "deactivate"
            ? "Deactivate Student Account?"
            : statusDialogStudent?.action === "grant"
            ? "Grant Portal Access?"
            : "Revoke Portal Access?"
        }
        message={
          statusDialogStudent?.action === "activate"
            ? `Enable authentication for ${statusDialogStudent?.student.full_name}. They will be able to log in.`
            : statusDialogStudent?.action === "deactivate"
            ? `Deactivating ${statusDialogStudent?.student.full_name} will immediately prevent portal login.`
            : statusDialogStudent?.action === "grant"
            ? `Approve ${statusDialogStudent?.student.full_name}'s onboarding status to ACTIVE.`
            : `Suspended status will prevent ${statusDialogStudent?.student.full_name} from taking assessments and accessing modules.`
        }
        confirmText={
          statusDialogStudent?.action === "deactivate" || statusDialogStudent?.action === "revoke"
            ? "Confirm Revoke / Deactivate"
            : "Confirm Action"
        }
        variant={
          statusDialogStudent?.action === "deactivate" || statusDialogStudent?.action === "revoke"
            ? "danger"
            : "primary"
        }
      />
    </div>
  );
};
