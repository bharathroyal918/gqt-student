import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate, Link } from "react-router-dom";
import {
  UserPlus,
  Eye,
  Edit2,
  CheckCircle2,
  XCircle,
  ShieldCheck,
  ShieldAlert,
  BookOpen,
  MailCheck,
} from "lucide-react";
import { adminApi } from "../../api/adminApi";
import { collegesApi } from "../../api/collegesApi";
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
import { UserAvatar } from "../../components/ui/UserAvatar";

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
  const [isAuthorizeEmailModalOpen, setIsAuthorizeEmailModalOpen] = useState(false);
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
    avatar_url: "",
  });

  // Authorize by Email Form State
  const [authEmailData, setAuthEmailData] = useState({
    email: "",
    course_opted: "Full Stack Software & Assessment Track",
    batch_code: "Batch-2026-3",
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

  // Authorize By Email Mutation
  const grantByEmailMutation = useMutation({
    mutationFn: (payload: { email: string; course_opted?: string; batch_code?: string }) =>
      adminApi.grantAccessByEmail(payload),
    onSuccess: (student) => {
      success("Access Granted", `Portal and curriculum access successfully authorized for ${student.full_name} (${student.email}).`);
      setIsAuthorizeEmailModalOpen(false);
      setAuthEmailData({
        email: "",
        course_opted: "Full Stack Software & Assessment Track",
        batch_code: "Batch-2026-3",
      });
      queryClient.invalidateQueries({ queryKey: ["admin-students"] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.error?.message || "Failed to grant access by email.";
      toastError("Authorization Failed", msg);
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

  // Grant Access Direct Mutation
  const { data: colleges = [] } = useQuery({
    queryKey: ["admin-colleges"],
    queryFn: () => collegesApi.adminGetColleges(),
  });

  const grantAccessMutation = useMutation({
    mutationFn: (id: string) => adminApi.grantStudentAccess(id),
    onSuccess: (res) => {
      success("Access Granted", `Portal access approved for ${res.full_name}.`);
      queryClient.invalidateQueries({ queryKey: ["admin-students"] });
    },
    onError: () => toastError("Error", "Could not grant student access."),
  });

  // Revoke Access Direct Mutation
  const revokeAccessMutation = useMutation({
    mutationFn: (id: string) => adminApi.revokeStudentAccess(id),
    onSuccess: (res) => {
      success("Access Revoked", `Portal access suspended for ${res.full_name}.`);
      queryClient.invalidateQueries({ queryKey: ["admin-students"] });
    },
    onError: () => toastError("Error", "Could not revoke student access."),
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
      avatar_url: "",
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
      avatar_url: student.avatar_url || "",
    });
  };

  const handleStatusActionConfirm = () => {
    if (!statusDialogStudent) return;
    const { student, action } = statusDialogStudent;

    if (action === "grant") {
      grantAccessMutation.mutate(student.id);
    } else if (action === "revoke") {
      revokeAccessMutation.mutate(student.id);
    } else {
      let payload: any = {};
      if (action === "activate") payload = { is_active: true };
      if (action === "deactivate") payload = { is_active: false };
      updateMutation.mutate({ id: student.id, payload });
    }
    setStatusDialogStudent(null);
  };

  // Table Columns
  const columns: Column<StudentListItem>[] = [
    {
      key: "student",
      header: "Student",
      cell: (row) => (
        <div className="flex items-center gap-3">
          <UserAvatar
            src={row.avatar_url}
            name={row.full_name}
            size="md"
            className="!h-10 !w-10 rounded-xl ring-2 ring-brand-500/20 shadow-sm shrink-0"
          />
          <div className="min-w-0">
            <button
              onClick={() => navigate(`/admin/students/${row.id}`)}
              className="text-left font-semibold text-slate-900 dark:text-white hover:text-brand-600 dark:hover:text-brand-400 transition-colors truncate block"
            >
              {row.full_name}
            </button>
            <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
              <span className="font-mono text-slate-600 dark:text-slate-300">{row.student_id_number}</span>
              <span>•</span>
              <span className="text-slate-500 dark:text-slate-400">{row.email || row.mobile_number || "No Contact"}</span>
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
          <div className="text-slate-500 dark:text-slate-400 mt-1 truncate max-w-[150px]">{row.college_name || "—"}</div>
        </div>
      ),
    },
    {
      key: "performance",
      header: "Points / Courses",
      cell: (row) => (
        <div className="text-xs">
          <div className="font-semibold text-amber-500 flex items-center gap-1">
            <span>{parseFloat(row.total_points || "0").toLocaleString()} pts</span>
          </div>
          <div className="text-slate-500 dark:text-slate-400 mt-0.5 flex items-center gap-1">
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
            <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
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
              {row.onboarding_status === "PENDING_ACTIVATION" ? "Pending Approval" : row.onboarding_status}
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
          {/* Quick Grant Access Button if pending */}
          {row.onboarding_status !== "ACTIVE" && (
            <Button
              size="sm"
              variant="outline"
              className="text-xs text-emerald-600 dark:text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/10"
              onClick={() => setStatusDialogStudent({ student: row, action: "grant" })}
              title="Grant Full Portal Access"
            >
              <ShieldCheck className="h-3.5 w-3.5 mr-1 text-emerald-500" />
              Authorize
            </Button>
          )}

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

          {/* Revoke Portal Access */}
          {row.onboarding_status === "ACTIVE" && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setStatusDialogStudent({ student: row, action: "revoke" })}
              title="Revoke Portal Access"
            >
              <ShieldAlert className="h-4 w-4 text-amber-400 hover:text-amber-300" />
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
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            Student Management & Access Control
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Authorize registered student accounts, manage institutional courses, attendance, and credentials.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={() => setIsAuthorizeEmailModalOpen(true)}
            className="border-emerald-500/30 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10"
          >
            <MailCheck className="h-4 w-4 mr-2 text-emerald-500" />
            Authorize by Email
          </Button>

          <Button onClick={handleOpenAdd} className="shadow-lg shadow-brand-600/25">
            <UserPlus className="h-4 w-4 mr-2" />
            Add Student
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900/60 p-4 sm:flex-row sm:items-center sm:justify-between">
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
              <option value="Batch-2025-3">Batch-2025-3</option>
              <option value="Batch-2025-6">Batch-2025-6</option>
              <option value="Batch-2026-3">Batch-2026-3</option>
            </Select>
          </div>

          {/* Access Status Filter */}
          <div className="w-48">
            <Select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All Access States</option>
              <option value="PENDING_ACTIVATION">⏳ Pending Approval</option>
              <option value="ACTIVE">✓ Active (Approved)</option>
              <option value="SUSPENDED">✗ Suspended</option>
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
        emptyDescription="No registered students match your filter criteria. Click 'Add Student' or 'Authorize by Email'."
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

      {/* Quick Authorize by Email Modal */}
      <Modal
        isOpen={isAuthorizeEmailModalOpen}
        onClose={() => setIsAuthorizeEmailModalOpen(false)}
        title="Authorize Student by Institutional Email"
        description="Enter the registered email of the student to grant them full access to the portal, course curriculum, and daily attendance."
        size="md"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!authEmailData.email.trim()) return;
            grantByEmailMutation.mutate(authEmailData);
          }}
          className="space-y-4"
        >
          <FormField label="Student Registered Email" required>
            <Input
              type="email"
              placeholder="student@gqt.edu / student@example.com"
              value={authEmailData.email}
              onChange={(e) => setAuthEmailData({ ...authEmailData, email: e.target.value })}
              required
            />
          </FormField>

          <FormField label="Assigned Fixed Course Track">
            <Select
              value={authEmailData.course_opted}
              onChange={(e) => setAuthEmailData({ ...authEmailData, course_opted: e.target.value })}
            >
              <option value="Full Stack Software & Assessment Track">Full Stack Software & Assessment Track</option>
              <option value="Java Enterprise & Cloud Microservices">Java Enterprise & Cloud Microservices</option>
              <option value="Data Science, Python & AI Track">Data Science, Python & AI Track</option>
              <option value="Frontend Modern Web Architecture">Frontend Modern Web Architecture</option>
            </Select>
          </FormField>

          <FormField label="Batch Assignment">
            <Select
              value={authEmailData.batch_code}
              onChange={(e) => setAuthEmailData({ ...authEmailData, batch_code: e.target.value })}
            >
              <option value="Batch-2026-3">Batch-2026-3 (Active Cohort)</option>
              <option value="Batch-2025-3">Batch-2025-3</option>
              <option value="Batch-2025-6">Batch-2025-6</option>
            </Select>
          </FormField>

          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-surface-800">
            <Button variant="secondary" type="button" onClick={() => setIsAuthorizeEmailModalOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              isLoading={grantByEmailMutation.isPending}
              className="bg-emerald-600 hover:bg-emerald-500 text-white"
            >
              <ShieldCheck className="h-4 w-4 mr-2" />
              Authorize Access
            </Button>
          </div>
        </form>
      </Modal>

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
                placeholder="e.g. Batch-2026-3"
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

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                College / Institution Name
              </label>
              <Link
                to="/admin/colleges"
                className="text-[11px] text-brand-600 dark:text-brand-400 hover:underline font-medium"
              >
                Manage Colleges &rarr;
              </Link>
            </div>
            <select
              value={formData.college_name || ""}
              onChange={(e) => setFormData({ ...formData, college_name: e.target.value })}
              className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="">-- Select Approved College / University --</option>
              {colleges.map((c) => (
                <option key={c.id} value={c.name}>
                  {c.name} {c.code ? `(${c.code})` : ""} {c.city ? `— ${c.city}` : ""}
                </option>
              ))}
              {formData.college_name &&
                !colleges.some(
                  (c) => c.name.toLowerCase() === formData.college_name?.toLowerCase()
                ) && (
                  <option value={formData.college_name}>
                    {formData.college_name} (Current)
                  </option>
                )}
            </select>
          </div>

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
                avatar_url: formData.avatar_url || "",
              } as any,
            });
          }}
          className="space-y-4"
        >
          {/* Avatar Preview & URL */}
          <div className="flex items-center gap-4 p-3 rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900/40">
            <UserAvatar
              src={formData.avatar_url}
              name={formData.full_name}
              size="lg"
              className="ring-2 ring-brand-500/20 shadow-sm shrink-0"
            />
            <div className="flex-1 min-w-0">
              <FormField label="Profile Photo Image URL (Optional)">
                <Input
                  type="url"
                  placeholder="https://..."
                  value={formData.avatar_url}
                  onChange={(e) => setFormData({ ...formData, avatar_url: e.target.value })}
                />
              </FormField>
            </div>
          </div>

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

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                College / Institution Name
              </label>
              <Link
                to="/admin/colleges"
                className="text-[11px] text-brand-600 dark:text-brand-400 hover:underline font-medium"
              >
                Manage Colleges &rarr;
              </Link>
            </div>
            <select
              value={formData.college_name || ""}
              onChange={(e) => setFormData({ ...formData, college_name: e.target.value })}
              className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="">-- Select Approved College / University --</option>
              {colleges.map((c) => (
                <option key={c.id} value={c.name}>
                  {c.name} {c.code ? `(${c.code})` : ""} {c.city ? `— ${c.city}` : ""}
                </option>
              ))}
              {formData.college_name &&
                !colleges.some(
                  (c) => c.name.toLowerCase() === formData.college_name?.toLowerCase()
                ) && (
                  <option value={formData.college_name}>
                    {formData.college_name} (Current)
                  </option>
                )}
            </select>
          </div>

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
        isLoading={updateMutation.isPending || grantAccessMutation.isPending || revokeAccessMutation.isPending}
        title={
          statusDialogStudent?.action === "activate"
            ? "Activate Student Account?"
            : statusDialogStudent?.action === "deactivate"
            ? "Deactivate Student Account?"
            : statusDialogStudent?.action === "grant"
            ? "Grant Full Portal Access?"
            : "Revoke Portal Access?"
        }
        message={
          statusDialogStudent?.action === "activate"
            ? `Enable authentication for ${statusDialogStudent?.student.full_name}. They will be able to log in.`
            : statusDialogStudent?.action === "deactivate"
            ? `Deactivating ${statusDialogStudent?.student.full_name} will immediately prevent portal login.`
            : statusDialogStudent?.action === "grant"
            ? `Approve ${statusDialogStudent?.student.full_name}'s access to all course curriculum, assessments, and attendance.`
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

