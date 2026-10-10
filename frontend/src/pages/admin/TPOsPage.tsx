import React, { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  UserCheck,
  Plus,
  Search,
  Building2,
  Phone,
  Mail,
  History,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  PowerOff,
  Eye,
  Edit3,
} from "lucide-react";
import { adminTpoApi } from "../../api/adminTpoApi";
import { collegesApi } from "../../api/collegesApi";
import {
  CreateTPOPayload,
  ReassignCollegePayload,
  TPOProfile,
  UpdateTPOPayload,
} from "../../types/tpo";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Modal } from "../../components/ui/Modal";
import { FormField, Input } from "../../components/ui/Form";
import { LoadingState } from "../../components/ui/LoadingState";
import { EmptyState } from "../../components/ui/EmptyState";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";

export const TPOsPage: React.FC = () => {
  const queryClient = useQueryClient();

  // Search & Filter State
  const [searchTerm, setSearchTerm] = useState("");
  const [collegeFilter, setCollegeFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "ACTIVE" | "INACTIVE">("ALL");

  // Modal States
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [selectedTpoDetail, setSelectedTpoDetail] = useState<TPOProfile | null>(null);
  const [reassigningTpo, setReassigningTpo] = useState<TPOProfile | null>(null);
  const [targetCollegeId, setTargetCollegeId] = useState<string>("");
  const [statusActionTpo, setStatusActionTpo] = useState<{ tpo: TPOProfile; action: "deactivate" | "reactivate" } | null>(null);
  const [editingTpo, setEditingTpo] = useState<TPOProfile | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  // Invite Form State
  const [inviteData, setInviteData] = useState<CreateTPOPayload>({
    email: "",
    full_name: "",
    college_id: "",
    designation: "Training & Placement Officer",
    department: "Training & Placement Cell",
    phone_number: "",
    bio: "",
  });

  // Edit Form State
  const [editData, setEditData] = useState<UpdateTPOPayload>({
    full_name: "",
    designation: "",
    department: "",
    phone_number: "",
    bio: "",
  });

  // 1. Fetch Colleges List for dropdowns
  const { data: colleges = [] } = useQuery({
    queryKey: ["admin-colleges"],
    queryFn: () => collegesApi.adminGetColleges({ is_active: true }),
  });

  // 2. Fetch TPOs List
  const {
    data: tposResponse,
    isLoading: isTposLoading,
  } = useQuery({
    queryKey: [
      "admin-tpos",
      searchTerm,
      collegeFilter === "ALL" ? undefined : collegeFilter,
      statusFilter === "ALL" ? undefined : statusFilter === "ACTIVE",
    ],
    queryFn: () =>
      adminTpoApi.getTPOs({
        search: searchTerm || undefined,
        college_id: collegeFilter === "ALL" ? undefined : collegeFilter,
        is_active: statusFilter === "ALL" ? undefined : statusFilter === "ACTIVE",
      }),
  });

  const tpos: TPOProfile[] = useMemo(() => {
    return tposResponse?.data || [];
  }, [tposResponse]);

  // 3. Fetch Audit History for Selected TPO
  const { data: auditLogs = [], isLoading: isAuditLoading } = useQuery({
    queryKey: ["admin-tpo-audit", selectedTpoDetail?.id],
    queryFn: () => (selectedTpoDetail ? adminTpoApi.getTPOAuditHistory(selectedTpoDetail.id) : Promise.resolve([])),
    enabled: !!selectedTpoDetail,
  });

  // Mutations
  const inviteMutation = useMutation({
    mutationFn: (payload: CreateTPOPayload) => adminTpoApi.provisionTPO(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-tpos"] });
      setIsInviteModalOpen(false);
      resetInviteForm();
    },
    onError: (err: any) => {
      setFormError(err?.response?.data?.error?.message || err?.response?.data?.message || "Failed to invite TPO.");
    },
  });

  const editMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateTPOPayload }) => adminTpoApi.updateTPO(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-tpos"] });
      setEditingTpo(null);
    },
    onError: (err: any) => {
      setFormError(err?.response?.data?.error?.message || err?.response?.data?.message || "Failed to update TPO.");
    },
  });

  const reassignMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ReassignCollegePayload }) =>
      adminTpoApi.reassignCollege(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-tpos"] });
      setReassigningTpo(null);
      setTargetCollegeId("");
    },
    onError: (err: any) => {
      alert(err?.response?.data?.error?.message || "Failed to reassign college.");
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => adminTpoApi.deactivateTPO(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-tpos"] });
      setStatusActionTpo(null);
    },
    onError: (err: any) => {
      alert(err?.response?.data?.error?.message || "Failed to deactivate TPO.");
    },
  });

  const reactivateMutation = useMutation({
    mutationFn: (id: string) => adminTpoApi.reactivateTPO(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-tpos"] });
      setStatusActionTpo(null);
    },
    onError: (err: any) => {
      alert(err?.response?.data?.error?.message || "Failed to reactivate TPO.");
    },
  });

  const resetInviteForm = () => {
    setInviteData({
      email: "",
      full_name: "",
      college_id: "",
      designation: "Training & Placement Officer",
      department: "Training & Placement Cell",
      phone_number: "",
      bio: "",
    });
    setFormError(null);
  };

  const handleOpenEdit = (tpo: TPOProfile) => {
    setEditingTpo(tpo);
    setEditData({
      full_name: tpo.full_name,
      designation: tpo.designation,
      department: tpo.department,
      phone_number: tpo.phone_number || "",
      bio: tpo.bio || "",
    });
    setFormError(null);
  };

  // KPI Metrics
  const totalCount = tpos.length;
  const activeCount = tpos.filter((t) => t.is_active && t.user_is_active).length;
  const assignedCollegesCount = new Set(tpos.map((t) => t.college?.id).filter(Boolean)).size;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              TPO Management
            </h1>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-400 border border-brand-200 dark:border-brand-800/60">
              Institutional Access
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Invite, assign, and manage Training & Placement Officers (TPOs) across institutional colleges.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            onClick={() => {
              resetInviteForm();
              setIsInviteModalOpen(true);
            }}
            className="flex items-center gap-2 shadow-sm shadow-brand-500/10"
          >
            <Plus className="h-4 w-4" />
            <span>Invite TPO</span>
          </Button>
        </div>
      </div>

      {/* KPI Stats Banner */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Total TPOs
            </span>
            <div className="rounded-xl bg-brand-50 dark:bg-brand-950/80 p-2 text-brand-600 dark:text-brand-400">
              <UserCheck className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-black text-slate-900 dark:text-white">{totalCount}</div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Provisioned institutional officers</p>
        </div>

        <div className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Active Access
            </span>
            <div className="rounded-xl bg-emerald-50 dark:bg-emerald-950/80 p-2 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-black text-emerald-600 dark:text-emerald-400">{activeCount}</div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Officers with active portal permissions</p>
        </div>

        <div className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Partner Colleges
            </span>
            <div className="rounded-xl bg-blue-50 dark:bg-blue-950/80 p-2 text-blue-600 dark:text-blue-400">
              <Building2 className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 text-3xl font-black text-blue-600 dark:text-blue-400">{assignedCollegesCount}</div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Institutions with assigned officers</p>
        </div>
      </div>

      {/* Filter and Search Controls */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-4 shadow-sm">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search by TPO name, email, designation, or college..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50/50 dark:bg-surface-950 pl-10 pr-4 py-2 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* College Filter */}
          <select
            value={collegeFilter}
            onChange={(e) => setCollegeFilter(e.target.value)}
            className="rounded-xl border border-slate-200 dark:border-surface-700 bg-white dark:bg-surface-950 px-3 py-2 text-xs font-medium text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="ALL">All Colleges</option>
            {colleges.map((col) => (
              <option key={col.id} value={col.id}>
                {col.name} ({col.code || "No Code"})
              </option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="rounded-xl border border-slate-200 dark:border-surface-700 bg-white dark:bg-surface-950 px-3 py-2 text-xs font-medium text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="ALL">All Status</option>
            <option value="ACTIVE">Active Only</option>
            <option value="INACTIVE">Inactive Only</option>
          </select>
        </div>
      </div>

      {/* TPO Table */}
      {isTposLoading ? (
        <LoadingState message="Loading TPO roster..." />
      ) : tpos.length === 0 ? (
        <EmptyState
          icon={<UserCheck className="h-8 w-8 text-brand-500" />}
          title="No TPOs Found"
          description={
            searchTerm || collegeFilter !== "ALL" || statusFilter !== "ALL"
              ? "No training & placement officers match the active filter criteria."
              : "No TPO accounts have been provisioned yet. Click 'Invite TPO' to assign one."
          }
          actionLabel="Invite First TPO"
          onAction={() => {
            resetInviteForm();
            setIsInviteModalOpen(true);
          }}
        />
      ) : (
        <div className="overflow-hidden rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="border-b border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-950 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                <tr>
                  <th className="px-5 py-3.5">TPO Officer</th>
                  <th className="px-5 py-3.5">Assigned College</th>
                  <th className="px-5 py-3.5">Department</th>
                  <th className="px-5 py-3.5">Status</th>
                  <th className="px-5 py-3.5">Assigned Date</th>
                  <th className="px-5 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-surface-800">
                {tpos.map((tpo) => (
                  <tr
                    key={tpo.id}
                    className="hover:bg-slate-50/70 dark:hover:bg-surface-800/50 transition-colors"
                  >
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div className="h-9 w-9 shrink-0 rounded-full bg-brand-500/10 dark:bg-brand-500/20 text-brand-600 dark:text-brand-400 flex items-center justify-center font-bold text-xs uppercase">
                          {tpo.full_name?.slice(0, 2) || "TP"}
                        </div>
                        <div>
                          <div className="font-semibold text-slate-900 dark:text-white">
                            {tpo.full_name || "Unnamed Officer"}
                          </div>
                          <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-2">
                            <span className="flex items-center gap-1">
                              <Mail className="h-3 w-3" />
                              {tpo.email}
                            </span>
                            {tpo.phone_number && (
                              <span className="flex items-center gap-1">
                                <Phone className="h-3 w-3" />
                                {tpo.phone_number}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </td>

                    <td className="px-5 py-4">
                      {tpo.college ? (
                        <div className="flex items-center gap-2">
                          <Building2 className="h-4 w-4 text-slate-400 shrink-0" />
                          <div>
                            <span className="font-medium text-slate-900 dark:text-white text-xs block">
                              {tpo.college.name}
                            </span>
                            <span className="text-[11px] text-slate-400">
                              {tpo.college.city}, {tpo.college.state}
                            </span>
                          </div>
                        </div>
                      ) : (
                        <Badge variant="warning">Unassigned</Badge>
                      )}
                    </td>

                    <td className="px-5 py-4">
                      <div className="text-xs font-medium text-slate-800 dark:text-slate-200">
                        {tpo.designation || "TPO"}
                      </div>
                      <div className="text-[11px] text-slate-400">{tpo.department}</div>
                    </td>

                    <td className="px-5 py-4">
                      {tpo.is_active && tpo.user_is_active ? (
                        <Badge variant="success">Active</Badge>
                      ) : (
                        <Badge variant="danger">Deactivated</Badge>
                      )}
                    </td>

                    <td className="px-5 py-4 text-xs text-slate-500 dark:text-slate-400">
                      {tpo.assigned_at
                        ? new Date(tpo.assigned_at).toLocaleDateString()
                        : new Date(tpo.created_at).toLocaleDateString()}
                    </td>

                    <td className="px-5 py-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {/* View Details / Audit Drawer */}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setSelectedTpoDetail(tpo)}
                          className="h-8 w-8 p-0 text-slate-500 hover:text-slate-900 dark:hover:text-white"
                          title="View Details & Audit History"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>

                        {/* Edit Metadata */}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleOpenEdit(tpo)}
                          className="h-8 w-8 p-0 text-slate-500 hover:text-brand-600 dark:hover:text-brand-400"
                          title="Edit Profile"
                        >
                          <Edit3 className="h-4 w-4" />
                        </Button>

                        {/* Reassign College */}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            setReassigningTpo(tpo);
                            setTargetCollegeId(tpo.college?.id || "");
                          }}
                          className="h-8 w-8 p-0 text-slate-500 hover:text-blue-600 dark:hover:text-blue-400"
                          title="Reassign College"
                        >
                          <RefreshCw className="h-4 w-4" />
                        </Button>

                        {/* Deactivate / Reactivate Toggle */}
                        {tpo.is_active && tpo.user_is_active ? (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setStatusActionTpo({ tpo, action: "deactivate" })}
                            className="h-8 w-8 p-0 text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40"
                            title="Deactivate Access"
                          >
                            <PowerOff className="h-4 w-4" />
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setStatusActionTpo({ tpo, action: "reactivate" })}
                            className="h-8 w-8 p-0 text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950/40"
                            title="Reactivate Access"
                          >
                            <CheckCircle2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* -------------------------------------------------------------------------- */}
      {/* 1. INVITE TPO MODAL */}
      {/* -------------------------------------------------------------------------- */}
      <Modal
        isOpen={isInviteModalOpen}
        onClose={() => setIsInviteModalOpen(false)}
        title="Invite Training & Placement Officer"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!inviteData.college_id) {
              setFormError("Please select a partner college for assignment.");
              return;
            }
            inviteMutation.mutate(inviteData);
          }}
          className="space-y-4"
        >
          {formError && (
            <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900 text-xs text-rose-600 dark:text-rose-400 flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          <FormField label="Full Name" required>
            <Input
              type="text"
              placeholder="e.g. Dr. K. S. Sharma"
              value={inviteData.full_name}
              onChange={(e) => setInviteData({ ...inviteData, full_name: e.target.value })}
              required
            />
          </FormField>

          <FormField label="Official Institutional Email" required>
            <Input
              type="email"
              placeholder="e.g. tpo@bit-bangalore.edu"
              value={inviteData.email}
              onChange={(e) => setInviteData({ ...inviteData, email: e.target.value })}
              required
            />
          </FormField>

          <FormField label="Assigned College" required>
            <select
              value={inviteData.college_id}
              onChange={(e) => setInviteData({ ...inviteData, college_id: e.target.value })}
              className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-white dark:bg-surface-950 px-3 py-2 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-brand-500"
              required
            >
              <option value="">Select an Institutional College...</option>
              {colleges.map((col) => (
                <option key={col.id} value={col.id}>
                  {col.name} ({col.code || "No Code"})
                </option>
              ))}
            </select>
          </FormField>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <FormField label="Designation">
              <Input
                type="text"
                value={inviteData.designation}
                onChange={(e) => setInviteData({ ...inviteData, designation: e.target.value })}
              />
            </FormField>
            <FormField label="Department">
              <Input
                type="text"
                value={inviteData.department}
                onChange={(e) => setInviteData({ ...inviteData, department: e.target.value })}
              />
            </FormField>
          </div>

          <FormField label="Contact Number (Optional)">
            <Input
              type="text"
              placeholder="+91 9876543210"
              value={inviteData.phone_number}
              onChange={(e) => setInviteData({ ...inviteData, phone_number: e.target.value })}
            />
          </FormField>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-surface-800">
            <Button variant="outline" type="button" onClick={() => setIsInviteModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={inviteMutation.isPending}>
              {inviteMutation.isPending ? "Sending Invitation..." : "Send Invitation"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* -------------------------------------------------------------------------- */}
      {/* 2. EDIT TPO METADATA MODAL */}
      {/* -------------------------------------------------------------------------- */}
      <Modal
        isOpen={!!editingTpo}
        onClose={() => setEditingTpo(null)}
        title="Edit TPO Profile Metadata"
      >
        {editingTpo && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              editMutation.mutate({ id: editingTpo.id, payload: editData });
            }}
            className="space-y-4"
          >
            {formError && (
              <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900 text-xs text-rose-600 dark:text-rose-400">
                {formError}
              </div>
            )}

            <FormField label="Full Name" required>
              <Input
                type="text"
                value={editData.full_name}
                onChange={(e) => setEditData({ ...editData, full_name: e.target.value })}
                required
              />
            </FormField>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <FormField label="Designation">
                <Input
                  type="text"
                  value={editData.designation}
                  onChange={(e) => setEditData({ ...editData, designation: e.target.value })}
                />
              </FormField>
              <FormField label="Department">
                <Input
                  type="text"
                  value={editData.department}
                  onChange={(e) => setEditData({ ...editData, department: e.target.value })}
                />
              </FormField>
            </div>

            <FormField label="Contact Number">
              <Input
                type="text"
                value={editData.phone_number}
                onChange={(e) => setEditData({ ...editData, phone_number: e.target.value })}
              />
            </FormField>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-surface-800">
              <Button variant="outline" type="button" onClick={() => setEditingTpo(null)}>
                Cancel
              </Button>
              <Button type="submit" disabled={editMutation.isPending}>
                {editMutation.isPending ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </form>
        )}
      </Modal>

      {/* -------------------------------------------------------------------------- */}
      {/* 3. REASSIGN COLLEGE MODAL */}
      {/* -------------------------------------------------------------------------- */}
      <Modal
        isOpen={!!reassigningTpo}
        onClose={() => setReassigningTpo(null)}
        title="Reassign TPO Institutional College"
      >
        {reassigningTpo && (
          <div className="space-y-4">
            <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-xs text-amber-800 dark:text-amber-300">
              <strong>Warning:</strong> Reassigning{" "}
              <span className="font-semibold">{reassigningTpo.full_name}</span> will immediately revoke their access
              to students and data from{" "}
              <span className="font-semibold">{reassigningTpo.college?.name || "current college"}</span>.
            </div>

            <FormField label="Target College" required>
              <select
                value={targetCollegeId}
                onChange={(e) => setTargetCollegeId(e.target.value)}
                className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-white dark:bg-surface-950 px-3 py-2 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-brand-500"
              >
                <option value="">Select New College...</option>
                {colleges.map((col) => (
                  <option key={col.id} value={col.id}>
                    {col.name} ({col.code || "No Code"})
                  </option>
                ))}
              </select>
            </FormField>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-surface-800">
              <Button variant="outline" onClick={() => setReassigningTpo(null)}>
                Cancel
              </Button>
              <Button
                disabled={!targetCollegeId || reassignMutation.isPending}
                onClick={() =>
                  reassignMutation.mutate({
                    id: reassigningTpo.id,
                    payload: { college_id: targetCollegeId },
                  })
                }
              >
                {reassignMutation.isPending ? "Reassigning..." : "Confirm Reassignment"}
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* -------------------------------------------------------------------------- */}
      {/* 4. DETAILS & AUDIT HISTORY MODAL */}
      {/* -------------------------------------------------------------------------- */}
      <Modal
        isOpen={!!selectedTpoDetail}
        onClose={() => setSelectedTpoDetail(null)}
        title="TPO Details & Audit History"
      >
        {selectedTpoDetail && (
          <div className="space-y-5">
            {/* Header info */}
            <div className="flex items-start justify-between p-4 rounded-xl bg-slate-50 dark:bg-surface-950 border border-slate-200 dark:border-surface-800">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  {selectedTpoDetail.full_name}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{selectedTpoDetail.email}</p>
                <div className="mt-2 flex items-center gap-2">
                  <Badge variant={selectedTpoDetail.is_active ? "success" : "danger"}>
                    {selectedTpoDetail.is_active ? "Active Officer" : "Deactivated"}
                  </Badge>
                  <span className="text-xs text-slate-400">
                    College: {selectedTpoDetail.college?.name || "Unassigned"}
                  </span>
                </div>
              </div>
            </div>

            {/* Audit History Timeline */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <History className="h-4 w-4 text-brand-500" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Audit Trail
                </h4>
              </div>

              {isAuditLoading ? (
                <div className="py-6 text-center text-xs text-slate-400">Loading audit history...</div>
              ) : auditLogs.length === 0 ? (
                <div className="py-6 text-center text-xs text-slate-400 border border-dashed border-slate-200 dark:border-surface-800 rounded-xl">
                  No administrative events recorded yet for this officer.
                </div>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                  {auditLogs.map((log) => (
                    <div
                      key={log.id}
                      className="p-3 rounded-xl bg-slate-50/70 dark:bg-surface-950 border border-slate-200/70 dark:border-surface-800 text-xs"
                    >
                      <div className="flex items-center justify-between font-semibold text-slate-900 dark:text-white">
                        <span>{log.action}</span>
                        <span className="text-[11px] font-normal text-slate-400">
                          {new Date(log.created_at).toLocaleString()}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                        By: {log.actor_email} {log.ip_address ? `(${log.ip_address})` : ""}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-100 dark:border-surface-800">
              <Button variant="outline" onClick={() => setSelectedTpoDetail(null)}>
                Close
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* -------------------------------------------------------------------------- */}
      {/* 5. CONFIRM DEACTIVATE / REACTIVATE DIALOG */}
      {/* -------------------------------------------------------------------------- */}
      {statusActionTpo && (
        <ConfirmDialog
          isOpen={true}
          title={
            statusActionTpo.action === "deactivate"
              ? "Deactivate TPO Access"
              : "Reactivate TPO Access"
          }
          message={
            statusActionTpo.action === "deactivate"
              ? `Are you sure you want to deactivate ${statusActionTpo.tpo.full_name}? They will immediately lose access to the portal.`
              : `Are you sure you want to restore portal access for ${statusActionTpo.tpo.full_name}?`
          }
          confirmText={statusActionTpo.action === "deactivate" ? "Deactivate" : "Reactivate"}
          variant={statusActionTpo.action === "deactivate" ? "danger" : "primary"}
          isLoading={deactivateMutation.isPending || reactivateMutation.isPending}
          onConfirm={() => {
            if (statusActionTpo.action === "deactivate") {
              deactivateMutation.mutate(statusActionTpo.tpo.id);
            } else {
              reactivateMutation.mutate(statusActionTpo.tpo.id);
            }
          }}
          onClose={() => setStatusActionTpo(null)}
        />
      )}
    </div>
  );
};
