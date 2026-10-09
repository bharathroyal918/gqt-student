import React, { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Building2,
  Plus,
  Search,
  Edit2,
  Trash2,
  CheckCircle2,
  GraduationCap,
  MapPin,
  Sparkles,
  AlertCircle,
  Users,
} from "lucide-react";
import { collegesApi } from "../../api/collegesApi";
import { College, CreateCollegePayload, UpdateCollegePayload } from "../../types/college";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Modal } from "../../components/ui/Modal";
import { FormField, Input } from "../../components/ui/Form";
import { LoadingState } from "../../components/ui/LoadingState";
import { EmptyState } from "../../components/ui/EmptyState";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";

export const CollegesPage: React.FC = () => {
  const queryClient = useQueryClient();

  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "ACTIVE" | "INACTIVE">("ALL");

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingCollege, setEditingCollege] = useState<College | null>(null);
  const [deletingCollege, setDeletingCollege] = useState<College | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  // Form State for Create / Edit
  const [formData, setFormData] = useState<CreateCollegePayload>({
    name: "",
    code: "",
    city: "",
    state: "",
    is_active: true,
  });

  // Fetch Colleges
  const { data: colleges = [], isLoading } = useQuery({
    queryKey: ["admin-colleges"],
    queryFn: () => collegesApi.adminGetColleges(),
  });

  // Create Mutation
  const createMutation = useMutation({
    mutationFn: (payload: CreateCollegePayload) => collegesApi.adminCreateCollege(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-colleges"] });
      queryClient.invalidateQueries({ queryKey: ["student-colleges"] });
      setIsCreateModalOpen(false);
      resetForm();
    },
    onError: (err: any) => {
      const msg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.message ||
        "Failed to create institutional college option.";
      setFormError(msg);
    },
  });

  // Update Mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateCollegePayload }) =>
      collegesApi.adminUpdateCollege(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-colleges"] });
      queryClient.invalidateQueries({ queryKey: ["student-colleges"] });
      setEditingCollege(null);
      resetForm();
    },
    onError: (err: any) => {
      const msg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.message ||
        "Failed to update college.";
      setFormError(msg);
    },
  });

  // Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => collegesApi.adminDeleteCollege(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-colleges"] });
      queryClient.invalidateQueries({ queryKey: ["student-colleges"] });
      setDeletingCollege(null);
    },
    onError: (err: any) => {
      alert(err?.response?.data?.message || "Failed to remove college.");
    },
  });

  const resetForm = () => {
    setFormData({
      name: "",
      code: "",
      city: "",
      state: "",
      is_active: true,
    });
    setFormError(null);
  };

  const handleOpenCreate = () => {
    resetForm();
    setIsCreateModalOpen(true);
  };

  const handleOpenEdit = (college: College) => {
    setFormError(null);
    setEditingCollege(college);
    setFormData({
      name: college.name,
      code: college.code || "",
      city: college.city || "",
      state: college.state || "",
      is_active: college.is_active,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!formData.name.trim()) {
      setFormError("College name is required.");
      return;
    }

    if (editingCollege) {
      updateMutation.mutate({ id: editingCollege.id, payload: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  // Filtered colleges
  const filteredColleges = useMemo(() => {
    return colleges.filter((c) => {
      const matchesSearch =
        c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (c.code && c.code.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (c.city && c.city.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (c.state && c.state.toLowerCase().includes(searchTerm.toLowerCase()));

      const matchesStatus =
        statusFilter === "ALL" ||
        (statusFilter === "ACTIVE" && c.is_active) ||
        (statusFilter === "INACTIVE" && !c.is_active);

      return matchesSearch && matchesStatus;
    });
  }, [colleges, searchTerm, statusFilter]);

  const totalColleges = colleges.length;
  const activeColleges = colleges.filter((c) => c.is_active).length;
  const totalStudents = colleges.reduce((acc, c) => acc + (c.student_count || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-brand-900 via-indigo-950 to-slate-950 p-6 sm:p-8 text-white shadow-xl">
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-brand-500/20 px-3 py-1 text-xs font-semibold text-brand-300 backdrop-blur border border-brand-500/30">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Institutional Directory Management</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
              Approved Colleges & Campuses
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              Configure and manage partner colleges and institutions. Students select from this verified institutional list in their profiles and registration.
            </p>
          </div>

          <Button
            variant="primary"
            onClick={handleOpenCreate}
            className="flex items-center gap-2 font-bold shadow-lg shadow-brand-500/30 shrink-0 self-start sm:self-auto"
          >
            <Plus className="h-4 w-4" />
            <span>Add New College</span>
          </Button>
        </div>

        {/* Decorative background glow */}
        <div className="absolute -right-16 -top-16 h-64 w-64 rounded-full bg-brand-500/20 blur-3xl" />
        <div className="absolute right-32 -bottom-16 h-64 w-64 rounded-full bg-indigo-500/20 blur-3xl" />
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 p-4 shadow-sm">
          <div className="flex items-center justify-between text-xs font-medium text-slate-500 dark:text-slate-400">
            <span>Total Institutions</span>
            <Building2 className="h-4 w-4 text-brand-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {totalColleges}
          </div>
          <div className="mt-1 text-xs text-brand-600 dark:text-brand-400 font-medium">
            Configured institutional options
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 p-4 shadow-sm">
          <div className="flex items-center justify-between text-xs font-medium text-slate-500 dark:text-slate-400">
            <span>Active for Selection</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400">
            {activeColleges}
          </div>
          <div className="mt-1 text-xs text-slate-400">Visible to student portals</div>
        </div>

        <div className="col-span-2 sm:col-span-1 rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 p-4 shadow-sm">
          <div className="flex items-center justify-between text-xs font-medium text-slate-500 dark:text-slate-400">
            <span>Enrolled Students</span>
            <Users className="h-4 w-4 text-purple-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {totalStudents}
          </div>
          <div className="mt-1 text-xs text-slate-400">Linked to approved campuses</div>
        </div>
      </div>

      {/* Filter & Search Toolbar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/40 p-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search college name, code, city, state..."
            value={searchTerm}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
            className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 pl-10 pr-4 py-2 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setStatusFilter(e.target.value as any)}
            className="rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 px-3 py-2 text-xs font-medium text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="ALL">All Statuses ({colleges.length})</option>
            <option value="ACTIVE">Active ({activeColleges})</option>
            <option value="INACTIVE">Inactive ({totalColleges - activeColleges})</option>
          </select>
        </div>
      </div>

      {/* College List / Cards */}
      {isLoading ? (
        <LoadingState message="Loading institutional colleges..." />
      ) : filteredColleges.length === 0 ? (
        <EmptyState
          title="No Colleges Found"
          description={
            searchTerm
              ? `No colleges match "${searchTerm}".`
              : "No institutional colleges added yet. Click 'Add New College' to create the first one."
          }
          actionLabel="Add New College"
          onAction={handleOpenCreate}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredColleges.map((college) => (
            <div
              key={college.id}
              className="group rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 p-5 shadow-sm transition-all duration-200 hover:border-brand-500/40 hover:shadow-md flex flex-col justify-between overflow-hidden min-w-0"
            >
              <div className="min-w-0">
                <div className="flex items-start justify-between gap-2.5">
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-600 dark:text-brand-400 font-black text-sm">
                      <GraduationCap className="h-5 w-5" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3
                        className="font-bold text-slate-900 dark:text-white text-sm truncate"
                        title={college.name}
                      >
                        {college.name}
                      </h3>
                      {college.code && (
                        <span className="text-[11px] font-mono text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-950/40 px-2 py-0.5 rounded-md font-semibold inline-block mt-0.5">
                          {college.code}
                        </span>
                      )}
                    </div>
                  </div>

                  <Badge
                    variant={college.is_active ? "emerald" : "slate"}
                    size="sm"
                    className="shrink-0"
                  >
                    {college.is_active ? "Active" : "Inactive"}
                  </Badge>
                </div>

                <div className="mt-4 space-y-1.5 text-xs text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-surface-950/60 p-3 rounded-xl">
                  {(college.city || college.state) && (
                    <div className="flex items-center gap-1.5 min-w-0">
                      <MapPin className="h-3.5 w-3.5 text-rose-500 shrink-0" />
                      <span className="truncate">
                        {[college.city, college.state].filter(Boolean).join(", ")}
                      </span>
                    </div>
                  )}

                  <div className="flex items-center gap-1.5 min-w-0">
                    <Users className="h-3.5 w-3.5 text-indigo-500 shrink-0" />
                    <span className="font-semibold text-slate-900 dark:text-white">
                      {college.student_count || 0}
                    </span>
                    <span className="text-slate-400">students enrolled</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-4 pt-3 border-t border-slate-100 dark:border-surface-800 flex items-center justify-between">
                <span className="text-[11px] text-slate-400">
                  {college.is_active ? "Available in dropdown" : "Hidden from students"}
                </span>

                <div className="flex items-center gap-1.5">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleOpenEdit(college)}
                    className="h-8 w-8 p-0 text-slate-400 hover:text-brand-600 dark:hover:text-brand-400"
                    title="Edit College"
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDeletingCollege(college)}
                    className="h-8 w-8 p-0 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400"
                    title="Delete / Deactivate College"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal: Create / Edit College */}
      {(isCreateModalOpen || editingCollege) && (
        <Modal
          isOpen={true}
          onClose={() => {
            setIsCreateModalOpen(false);
            setEditingCollege(null);
          }}
          title={editingCollege ? `Edit College: ${editingCollege.name}` : "Add Institutional College Option"}
          maxWidth="md"
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            {formError && (
              <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-500 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <FormField label="College / University Name *" required>
              <Input
                type="text"
                required
                placeholder="e.g. RV College of Engineering"
                value={formData.name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setFormData({ ...formData, name: e.target.value })
                }
              />
            </FormField>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormField label="Institution Code / Acronym">
                <Input
                  type="text"
                  placeholder="e.g. RVCE or GQT-ENG"
                  value={formData.code}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setFormData({ ...formData, code: e.target.value.toUpperCase() })
                  }
                />
              </FormField>

              <FormField label="City / Campus">
                <Input
                  type="text"
                  placeholder="e.g. Bengaluru"
                  value={formData.city}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setFormData({ ...formData, city: e.target.value })
                  }
                />
              </FormField>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormField label="State / Region">
                <Input
                  type="text"
                  placeholder="e.g. Karnataka"
                  value={formData.state}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setFormData({ ...formData, state: e.target.value })
                  }
                />
              </FormField>

              <FormField label="Portal Status">
                <select
                  value={formData.is_active ? "true" : "false"}
                  onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                    setFormData({ ...formData, is_active: e.target.value === "true" })
                  }
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
                >
                  <option value="true">Active (Students can choose this)</option>
                  <option value="false">Inactive (Hidden from dropdown)</option>
                </select>
              </FormField>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-200 dark:border-surface-800">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setIsCreateModalOpen(false);
                  setEditingCollege(null);
                }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={createMutation.isPending || updateMutation.isPending}
              >
                {createMutation.isPending || updateMutation.isPending
                  ? "Saving..."
                  : editingCollege
                    ? "Update College"
                    : "Create College"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Delete / Deactivate Confirmation Dialog */}
      {deletingCollege && (
        <ConfirmDialog
          isOpen={true}
          title={`Remove "${deletingCollege.name}"?`}
          message={
            deletingCollege.student_count && deletingCollege.student_count > 0
              ? `This college currently has ${deletingCollege.student_count} registered students. Deleting it will safely deactivate it so existing student records stay intact while hiding it from future dropdown selections.`
              : "Are you sure you want to delete this college option from the portal?"
          }
          confirmText="Delete / Deactivate"
          onConfirm={() => deleteMutation.mutate(deletingCollege.id)}
          onClose={() => setDeletingCollege(null)}
          variant="danger"
        />
      )}
    </div>
  );
};
