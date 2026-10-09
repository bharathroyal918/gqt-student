import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Briefcase,
  Plus,
  Search,
  Building2,
  MapPin,
  Clock,
  DollarSign,
  Users,
  CheckCircle2,
  Layers,
  Edit2,
  Trash2,
  ShieldCheck,
  AlertCircle,
} from "lucide-react";
import { placementsApi } from "../../api/placementsApi";
import {
  PlacementDrive,
  CreatePlacementDrivePayload,
  WorkMode,
  DriveStatus,
} from "../../types/placement";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Modal } from "../../components/ui/Modal";
import { EmptyState } from "../../components/ui/EmptyState";
import { LoadingState } from "../../components/ui/LoadingState";

export const PlacementDrivesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [modeFilter, setModeFilter] = useState<string>("ALL");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingDrive, setEditingDrive] = useState<PlacementDrive | null>(null);
  const [deletingDriveId, setDeletingDriveId] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState<CreatePlacementDrivePayload>({
    company_name: "",
    company_code: "",
    company_logo_url: "",
    role: "",
    skills: "",
    location: "Bengaluru, Karnataka",
    mode_of_work: "HYBRID",
    stipend_or_ctc: "",
    bond_period: "None",
    eligibility_criteria: "BE/B.Tech (CSE/ISE/ECE/IT), Min 60% or 6.0 CGPA, No active backlogs",
    min_cgpa: 6.0,
    eligible_batches: "2025, 2026",
    job_description: "",
    application_deadline: new Date(Date.now() + 14 * 86400000).toISOString().slice(0, 16),
    drive_date: new Date(Date.now() + 20 * 86400000).toISOString().slice(0, 16),
    status: "ONGOING",
    is_active: true,
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-placement-drives", statusFilter, modeFilter, searchTerm],
    queryFn: () =>
      placementsApi.adminGetDrives({
        status: statusFilter === "ALL" ? undefined : statusFilter,
        mode_of_work: modeFilter === "ALL" ? undefined : modeFilter,
        search: searchTerm || undefined,
      }),
  });

  const [formError, setFormError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: placementsApi.adminCreateDrive,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-placement-drives"] });
      setIsCreateModalOpen(false);
      setFormError(null);
      resetForm();
    },
    onError: (err: any) => {
      const msg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.message ||
        "Failed to publish placement drive. Please verify the form inputs.";
      setFormError(msg);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<CreatePlacementDrivePayload> }) =>
      placementsApi.adminUpdateDrive(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-placement-drives"] });
      setEditingDrive(null);
      setFormError(null);
      resetForm();
    },
    onError: (err: any) => {
      const msg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.message ||
        "Failed to update placement drive.";
      setFormError(msg);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: placementsApi.adminDeleteDrive,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-placement-drives"] });
      setDeletingDriveId(null);
    },
  });

  const resetForm = () => {
    setFormError(null);
    setFormData({
      company_name: "",
      company_code: "",
      company_logo_url: "",
      role: "",
      skills: "",
      location: "",
      mode_of_work: "HYBRID",
      stipend_or_ctc: "",
      bond_period: "None",
      eligibility_criteria: "",
      min_cgpa: 0.0,
      eligible_batches: "2025, 2026",
      job_description: "",
      application_deadline: new Date(Date.now() + 14 * 86400000).toISOString().slice(0, 16),
      drive_date: new Date(Date.now() + 20 * 86400000).toISOString().slice(0, 16),
      status: "ONGOING",
      is_active: true,
    });
  };

  const handleOpenEdit = (drive: PlacementDrive) => {
    setFormError(null);
    setEditingDrive(drive);
    setFormData({
      company_name: drive.company_name,
      company_code: drive.company_code || "",
      company_logo_url: drive.company_logo_url || "",
      role: drive.role,
      skills: drive.skills,
      location: drive.location,
      mode_of_work: drive.mode_of_work,
      stipend_or_ctc: drive.stipend_or_ctc,
      bond_period: drive.bond_period,
      eligibility_criteria: drive.eligibility_criteria,
      min_cgpa: drive.min_cgpa,
      eligible_batches: drive.eligible_batches,
      job_description: drive.job_description,
      application_deadline: drive.application_deadline ? drive.application_deadline.slice(0, 16) : "",
      drive_date: drive.drive_date ? drive.drive_date.slice(0, 16) : "",
      status: drive.status,
      is_active: drive.is_active,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    const payload: CreatePlacementDrivePayload = {
      ...formData,
      company_code: formData.company_code?.trim() || undefined,
      company_logo_url: formData.company_logo_url?.trim() || undefined,
      drive_date: formData.drive_date ? new Date(formData.drive_date).toISOString() : null,
      application_deadline: formData.application_deadline
        ? new Date(formData.application_deadline).toISOString()
        : new Date(Date.now() + 14 * 86400000).toISOString(),
    };

    if (editingDrive) {
      updateMutation.mutate({ id: editingDrive.id, payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const metrics = data?.metrics || {
    total_drives: 0,
    active_drives: 0,
    total_applications: 0,
    selected_candidates: 0,
    shortlisted_candidates: 0,
    rejected_candidates: 0,
  };

  const drives = data?.drives || [];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <Briefcase className="h-7 w-7 text-brand-600 dark:text-brand-400" />
            Placement Drives Management
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Publish institutional recruitment drives, review student applications, and manage selection pipelines.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/admin/placements/applicants">
            <Button
              variant="outline"
              className="flex items-center gap-2"
            >
              <Users className="h-4 w-4" />
              <span>All Applicants ({metrics.total_applications})</span>
            </Button>
          </Link>

          <Button
            variant="primary"
            onClick={() => {
              resetForm();
              setIsCreateModalOpen(true);
            }}
            className="flex items-center gap-2 shadow-lg shadow-brand-500/20"
          >
            <Plus className="h-4 w-4" />
            <span>Create Placement Drive</span>
          </Button>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 p-4 shadow-sm backdrop-blur">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Total Drives</span>
            <div className="rounded-xl bg-blue-500/10 p-2 text-blue-500">
              <Building2 className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">{metrics.total_drives}</div>
          <div className="mt-1 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
            {metrics.active_drives} Active & Ongoing
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 p-4 shadow-sm backdrop-blur">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Total Applications</span>
            <div className="rounded-xl bg-purple-500/10 p-2 text-purple-500">
              <Users className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">{metrics.total_applications}</div>
          <div className="mt-1 text-xs text-slate-400">Submitted by students</div>
        </div>

        <div className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 p-4 shadow-sm backdrop-blur">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Selected / Offers</span>
            <div className="rounded-xl bg-emerald-500/10 p-2 text-emerald-500">
              <CheckCircle2 className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400">{metrics.selected_candidates}</div>
          <div className="mt-1 text-xs text-slate-400">Final hiring offers</div>
        </div>

        <div className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 p-4 shadow-sm backdrop-blur">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Shortlisted</span>
            <div className="rounded-xl bg-amber-500/10 p-2 text-amber-500">
              <ShieldCheck className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-2 text-2xl font-bold text-amber-600 dark:text-amber-400">{metrics.shortlisted_candidates}</div>
          <div className="mt-1 text-xs text-slate-400">In interview rounds</div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/40 p-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search company, role, skills, location..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 pl-10 pr-4 py-2 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Status Filter */}
          <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-surface-800/80 p-1 rounded-xl text-xs font-medium">
            {["ALL", "ONGOING", "UPCOMING", "CLOSED"].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-lg transition-colors ${statusFilter === st
                  ? "bg-white dark:bg-surface-950 text-brand-600 dark:text-brand-400 font-bold shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                  }`}
              >
                {st === "ALL" ? "All Status" : st}
              </button>
            ))}
          </div>

          {/* Work Mode Filter */}
          <select
            value={modeFilter}
            onChange={(e) => setModeFilter(e.target.value)}
            className="rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 px-3 py-2 text-xs font-medium text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="ALL">All Modes</option>
            <option value="ON_SITE">On-site</option>
            <option value="REMOTE">Remote</option>
            <option value="HYBRID">Hybrid</option>
          </select>
        </div>
      </div>

      {/* Content Area */}
      {isLoading ? (
        <LoadingState message="Loading placement drives..." />
      ) : error ? (
        <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-6 text-center text-rose-400">
          <AlertCircle className="mx-auto h-8 w-8 mb-2" />
          <p className="font-semibold">Failed to load placement drives</p>
        </div>
      ) : drives.length === 0 ? (
        <EmptyState
          title="No Placement Drives Found"
          description="Create your first placement drive to begin accepting student applications."
          actionLabel="Create Placement Drive"
          onAction={() => {
            resetForm();
            setIsCreateModalOpen(true);
          }}
        />
      ) : (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          {drives.map((drive) => {
            return (
              <div
                key={drive.id}
                className="group relative rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 p-5 shadow-sm transition-all duration-200 hover:border-brand-500/40 hover:shadow-md flex flex-col justify-between overflow-hidden min-w-0"
              >
                <div className="min-w-0">
                  {/* Top Bar */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500/10 to-indigo-500/10 border border-brand-500/20 text-brand-600 dark:text-brand-400 font-bold text-lg">
                        {drive.company_name.slice(0, 2).toUpperCase()}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="font-bold text-slate-900 dark:text-white text-base truncate" title={drive.company_name}>
                            {drive.company_name}
                          </h3>
                          {drive.company_code && (
                            <span className="text-[11px] font-mono font-medium text-slate-400 bg-slate-100 dark:bg-surface-800 px-2 py-0.5 rounded-md shrink-0">
                              {drive.company_code}
                            </span>
                          )}
                        </div>
                        <p className="text-sm font-semibold text-brand-600 dark:text-brand-400 mt-0.5 truncate" title={drive.role}>
                          {drive.role}
                        </p>
                      </div>
                    </div>

                    <div className="shrink-0">
                      <Badge
                        variant={
                          drive.status === "ONGOING"
                            ? "emerald"
                            : drive.status === "UPCOMING"
                              ? "amber"
                              : "slate"
                        }
                        size="sm"
                      >
                        {drive.status}
                      </Badge>
                    </div>
                  </div>

                  {/* Highlights Grid */}
                  <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-slate-600 dark:text-slate-300">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <DollarSign className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                      <span className="font-semibold text-slate-900 dark:text-white truncate block flex-1" title={drive.stipend_or_ctc}>
                        {drive.stipend_or_ctc}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 min-w-0">
                      <MapPin className="h-3.5 w-3.5 text-rose-500 shrink-0" />
                      <span className="truncate block flex-1" title={drive.location}>{drive.location}</span>
                    </div>

                    <div className="flex items-center gap-1.5 min-w-0">
                      <Layers className="h-3.5 w-3.5 text-indigo-500 shrink-0" />
                      <span className="capitalize truncate block flex-1">{drive.mode_of_work.toLowerCase()}</span>
                    </div>

                    <div className="flex items-center gap-1.5 min-w-0">
                      <ShieldCheck className="h-3.5 w-3.5 text-amber-500 shrink-0" />
                      <span className="truncate block flex-1" title={`Bond: ${drive.bond_period}`}>Bond: {drive.bond_period}</span>
                    </div>
                  </div>

                  {/* Skills tags */}
                  <div className="mt-3.5 flex flex-wrap gap-1.5">
                    {drive.skills.split(",").slice(0, 4).map((s, idx) => (
                      <span
                        key={idx}
                        className="rounded-lg bg-slate-100 dark:bg-surface-800/80 px-2 py-0.5 text-[11px] font-medium text-slate-600 dark:text-slate-300"
                      >
                        {s.trim()}
                      </span>
                    ))}
                    {drive.skills.split(",").length > 4 && (
                      <span className="text-[11px] text-slate-400 self-center">
                        +{drive.skills.split(",").length - 4} more
                      </span>
                    )}
                  </div>

                  {/* Application Metrics Badges */}
                  <div className="mt-4 flex items-center gap-2 rounded-xl bg-slate-50 dark:bg-surface-950/60 p-2.5 text-xs">
                    <div className="flex-1 text-center border-r border-slate-200 dark:border-surface-800">
                      <span className="text-slate-400 block text-[10px]">Applicants</span>
                      <span className="font-bold text-slate-900 dark:text-white">
                        {drive.total_applications || 0}
                      </span>
                    </div>
                    <div className="flex-1 text-center border-r border-slate-200 dark:border-surface-800">
                      <span className="text-slate-400 block text-[10px]">Shortlisted</span>
                      <span className="font-bold text-amber-500">
                        {drive.shortlisted_count || 0}
                      </span>
                    </div>
                    <div className="flex-1 text-center border-r border-slate-200 dark:border-surface-800">
                      <span className="text-slate-400 block text-[10px]">Selected</span>
                      <span className="font-bold text-emerald-500">
                        {drive.selected_count || 0}
                      </span>
                    </div>
                    <div className="flex-1 text-center">
                      <span className="text-slate-400 block text-[10px]">Rejected</span>
                      <span className="font-bold text-rose-500">
                        {drive.rejected_count || 0}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Footer Action Bar */}
                <div className="mt-5 flex items-center justify-between border-t border-slate-200 dark:border-surface-800/80 pt-3">
                  <div className="flex items-center gap-1.5 text-xs text-slate-400">
                    <Clock className="h-3.5 w-3.5 text-amber-500" />
                    <span>
                      Deadline: {new Date(drive.application_deadline).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleOpenEdit(drive)}
                      className="h-8 w-8 p-0 text-slate-400 hover:text-brand-500"
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setDeletingDriveId(drive.id)}
                      className="h-8 w-8 p-0 text-slate-400 hover:text-rose-500"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>

                    <Link to={`/admin/placements/${drive.id}/applicants`}>
                      <Button variant="primary" size="sm" className="flex items-center gap-1.5 h-8 text-xs font-semibold">
                        <Users className="h-3.5 w-3.5" />
                        <span>View Applicants</span>
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal: Create / Edit Placement Drive */}
      {(isCreateModalOpen || editingDrive) && (
        <Modal
          isOpen={true}
          onClose={() => {
            setIsCreateModalOpen(false);
            setEditingDrive(null);
          }}
          title={editingDrive ? `Edit Placement Drive: ${editingDrive.company_name}` : "Create New Placement Drive"}
          size="xl"
        >
          <form onSubmit={handleSubmit} className="space-y-4 max-h-[75vh] overflow-y-auto px-1 pr-2">
            {formError && (
              <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-500 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Company Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Google Cloud, TCS, Amazon"
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Company Code / Drive Ref
                </label>
                <input
                  type="text"
                  placeholder="e.g. GQT-GOOG-2026"
                  value={formData.company_code}
                  onChange={(e) => setFormData({ ...formData, company_code: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Job Role / Position *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Software Development Engineer (SDE-1)"
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Stipend / CTC Package *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. ₹8.5 - ₹12.0 LPA or ₹30,000/mo"
                  value={formData.stipend_or_ctc}
                  onChange={(e) => setFormData({ ...formData, stipend_or_ctc: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Work Mode *
                </label>
                <select
                  value={formData.mode_of_work}
                  onChange={(e) => setFormData({ ...formData, mode_of_work: e.target.value as WorkMode })}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
                >
                  <option value="HYBRID">Hybrid</option>
                  <option value="ON_SITE">On-site</option>
                  <option value="REMOTE">Remote</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Agreement / Bond Period *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. None or 1 Year Service Agreement"
                  value={formData.bond_period}
                  onChange={(e) => setFormData({ ...formData, bond_period: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Drive Status
                </label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as DriveStatus })}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
                >
                  <option value="ONGOING">Active / Ongoing</option>
                  <option value="UPCOMING">Upcoming</option>
                  <option value="CLOSED">Closed</option>
                  <option value="CANCELLED">Cancelled</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Required Skills & Tech Stack *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Java, Python, React, PostgreSQL, Docker, Data Structures"
                value={formData.skills}
                onChange={(e) => setFormData({ ...formData, skills: e.target.value })}
                className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Job Location(s) *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Bengaluru, Hyderabad, Pune"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Eligible Batches
                </label>
                <input
                  type="text"
                  placeholder="e.g. 2025, 2026"
                  value={formData.eligible_batches}
                  onChange={(e) => setFormData({ ...formData, eligible_batches: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Application Deadline *
                </label>
                <input
                  type="datetime-local"
                  required
                  value={formData.application_deadline}
                  onChange={(e) => setFormData({ ...formData, application_deadline: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Drive / Interview Date
                </label>
                <input
                  type="datetime-local"
                  value={formData.drive_date || ""}
                  onChange={(e) => setFormData({ ...formData, drive_date: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Eligibility Criteria Details
              </label>
              <textarea
                rows={2}
                placeholder="e.g. B.Tech / BE in CSE, ISE, ECE, IT. Minimum 6.5 CGPA with no pending backlogs."
                value={formData.eligibility_criteria}
                onChange={(e) => setFormData({ ...formData, eligibility_criteria: e.target.value })}
                className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Job Description & Interview Rounds
              </label>
              <textarea
                rows={4}
                placeholder="Detail the roles, responsibilities, interview rounds (Online Coding, Technical Interview, HR Round), and expectations..."
                value={formData.job_description}
                onChange={(e) => setFormData({ ...formData, job_description: e.target.value })}
                className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200 dark:border-surface-800">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setIsCreateModalOpen(false);
                  setEditingDrive(null);
                }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={createMutation.isPending || updateMutation.isPending}
              >
                {editingDrive ? "Save Changes" : "Publish Placement Drive"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Confirmation Modal: Delete Drive */}
      {deletingDriveId && (
        <Modal
          isOpen={true}
          onClose={() => setDeletingDriveId(null)}
          title="Delete Placement Drive"
        >
          <div className="space-y-4">
            <p className="text-sm text-slate-600 dark:text-slate-300">
              Are you sure you want to delete this placement drive? All associated student applications will be permanently removed.
            </p>
            <div className="flex justify-end gap-3 pt-3">
              <Button variant="outline" onClick={() => setDeletingDriveId(null)}>
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={() => deleteMutation.mutate(deletingDriveId)}
                disabled={deleteMutation.isPending}
              >
                Confirm Delete
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
