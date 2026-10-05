import React, { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Briefcase,
  Search,
  Building2,
  MapPin,
  Clock,
  DollarSign,
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
  Sparkles,
  FileText,
  Send,
  Award,
  TrendingUp,
  UploadCloud,
  FileCheck,
  X,
  AlertCircle,
  Download,
} from "lucide-react";
import { placementsApi } from "../../api/placementsApi";
import { useAuthStore } from "../../store/authStore";
import {
  PlacementDrive,
  PlacementApplication,
  ApplyPlacementPayload,
} from "../../types/placement";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Modal } from "../../components/ui/Modal";
import { EmptyState } from "../../components/ui/EmptyState";
import { LoadingState } from "../../components/ui/LoadingState";

export const StudentPlacementsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { studentProfile, user } = useAuthStore();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [activeTab, setActiveTab] = useState<"DRIVES" | "MY_APPLICATIONS">("DRIVES");
  const [searchTerm, setSearchTerm] = useState("");
  const [modeFilter, setModeFilter] = useState<string>("ALL");
  const [applyingDrive, setApplyingDrive] = useState<PlacementDrive | null>(null);
  const [applyError, setApplyError] = useState<string | null>(null);

  // Student apply form state
  const [applyForm, setApplyForm] = useState<ApplyPlacementPayload>({
    phone_number: user?.mobile_number || "+91 9876543210",
    college_name: studentProfile?.college_name || "GQT Academy of Tech",
    branch: "Computer Science & Engineering",
    graduation_year: studentProfile?.graduation_year || 2026,
    cgpa_or_percentage: "8.50 CGPA",
    resume_file: null,
    resume_url: "",
    github_url: "",
    linkedin_url: "",
    portfolio_url: "",
    skills_summary: "Java, Python, React, SQL, Problem Solving",
    cover_note: "",
  });

  // Fetch available drives
  const { data: drivesData, isLoading: isDrivesLoading } = useQuery({
    queryKey: ["student-placement-drives", modeFilter, searchTerm],
    queryFn: () =>
      placementsApi.studentGetAvailableDrives({
        mode_of_work: modeFilter === "ALL" ? undefined : modeFilter,
        search: searchTerm || undefined,
      }),
  });

  // Fetch student's submitted applications
  const { data: myApplications = [], isLoading: isMyAppsLoading } = useQuery({
    queryKey: ["student-my-placement-applications"],
    queryFn: placementsApi.studentGetMyApplications,
  });

  const applyMutation = useMutation({
    mutationFn: ({ driveId, payload }: { driveId: string; payload: ApplyPlacementPayload }) =>
      placementsApi.studentApplyToDrive(driveId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["student-placement-drives"] });
      queryClient.invalidateQueries({ queryKey: ["student-my-placement-applications"] });
      setApplyingDrive(null);
      setApplyError(null);
    },
    onError: (err: any) => {
      const msg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.message ||
        "Failed to submit application. Please verify your details and uploaded resume.";
      setApplyError(msg);
    },
  });

  const handleOpenApply = (drive: PlacementDrive) => {
    setApplyError(null);
    setApplyingDrive(drive);
    setApplyForm({
      phone_number: user?.mobile_number || "+91 9876543210",
      college_name: studentProfile?.college_name || "GQT Engineering Academy",
      branch: "Computer Science & Engineering",
      graduation_year: studentProfile?.graduation_year || 2026,
      cgpa_or_percentage: "8.50 CGPA",
      resume_file: null,
      resume_url: "",
      github_url: "https://github.com",
      linkedin_url: "https://linkedin.com",
      portfolio_url: "",
      skills_summary: drive.skills || "Java, React, SQL, Problem Solving",
      cover_note: `I am highly enthusiastic about the ${drive.role} position at ${drive.company_name} and confident that my practical technical training makes me a great fit.`,
    });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        setApplyError("Resume file size must be less than 10MB.");
        return;
      }
      setApplyError(null);
      setApplyForm((prev) => ({ ...prev, resume_file: file }));
    }
  };

  const handleRemoveFile = () => {
    setApplyForm((prev) => ({ ...prev, resume_file: null }));
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleApplySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setApplyError(null);

    if (!applyForm.resume_file && !applyForm.resume_url?.trim()) {
      setApplyError("Please upload a resume file (PDF/DOCX) or provide a cloud link.");
      return;
    }

    if (!applyingDrive) return;
    applyMutation.mutate({ driveId: applyingDrive.id, payload: applyForm });
  };

  const [downloadingResumeId, setDownloadingResumeId] = useState<string | null>(null);

  const handleDownloadResume = async (app: PlacementApplication) => {
    if (app.has_resume_file && app.resume_download_url) {
      setDownloadingResumeId(app.id);
      try {
        const response = await fetch(`${app.resume_download_url}?download=1`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("gqt_access_token") || ""}`,
          },
        });

        if (!response.ok) {
          if (app.resume_url) {
            window.open(app.resume_url, "_blank", "noopener,noreferrer");
            return;
          }
          throw new Error("Resume document was not found on server.");
        }

        const blob = await response.blob();
        if (blob.type.includes("application/json")) {
          const text = await blob.text();
          let msg = "Failed to download resume file.";
          try {
            const err = JSON.parse(text);
            msg = err?.error?.message || err?.message || msg;
          } catch {
            // ignore
          }
          if (app.resume_url) {
            window.open(app.resume_url, "_blank", "noopener,noreferrer");
            return;
          }
          throw new Error(msg);
        }

        let filename = app.resume_filename || "my_resume.pdf";
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      } catch (err: any) {
        if (app.resume_url) {
          window.open(app.resume_url, "_blank", "noopener,noreferrer");
        } else {
          alert(err?.message || "Unable to download resume file.");
        }
      } finally {
        setDownloadingResumeId(null);
      }
    } else if (app.resume_url) {
      window.open(app.resume_url, "_blank", "noopener,noreferrer");
    }
  };

  const drives = drivesData?.drives || [];
  const summary = drivesData?.summary || {
    total_available_drives: drives.length,
    my_applications_count: myApplications.length,
    my_shortlisted_count: myApplications.filter((a) => a.status === "SHORTLISTED").length,
    my_selected_count: myApplications.filter((a) => a.status === "SELECTED").length,
  };

  return (
    <div className="space-y-6">
      {/* Hero Career Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-brand-900 via-indigo-950 to-slate-950 p-6 sm:p-8 text-white shadow-xl">
        <div className="relative z-10 max-w-2xl space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full bg-brand-500/20 px-3 py-1 text-xs font-semibold text-brand-300 backdrop-blur border border-brand-500/30">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Campus Placement & Career Hub</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
            Placement & Career Drives
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            Apply to top tier tech organizations, track your application pipeline in real time, and kickstart your dream software engineering career.
          </p>
        </div>

        {/* Decorative background glow */}
        <div className="absolute -right-16 -top-16 h-64 w-64 rounded-full bg-brand-500/20 blur-3xl" />
        <div className="absolute right-32 -bottom-16 h-64 w-64 rounded-full bg-indigo-500/20 blur-3xl" />
      </div>

      {/* Metric Counters */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 p-4 shadow-sm backdrop-blur">
          <div className="flex items-center justify-between text-xs font-medium text-slate-500 dark:text-slate-400">
            <span>Available Drives</span>
            <Building2 className="h-4 w-4 text-brand-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {summary.total_available_drives}
          </div>
          <div className="mt-1 text-xs text-brand-600 dark:text-brand-400 font-medium">
            Open for applications
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 p-4 shadow-sm backdrop-blur">
          <div className="flex items-center justify-between text-xs font-medium text-slate-500 dark:text-slate-400">
            <span>My Applications</span>
            <FileText className="h-4 w-4 text-purple-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {summary.my_applications_count}
          </div>
          <div className="mt-1 text-xs text-slate-400">Submitted drives</div>
        </div>

        <div className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 p-4 shadow-sm backdrop-blur">
          <div className="flex items-center justify-between text-xs font-medium text-slate-500 dark:text-slate-400">
            <span>Shortlisted</span>
            <TrendingUp className="h-4 w-4 text-amber-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-amber-600 dark:text-amber-400">
            {summary.my_shortlisted_count}
          </div>
          <div className="mt-1 text-xs text-slate-400">Interview stage</div>
        </div>

        <div className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 p-4 shadow-sm backdrop-blur">
          <div className="flex items-center justify-between text-xs font-medium text-slate-500 dark:text-slate-400">
            <span>Selected / Offers</span>
            <Award className="h-4 w-4 text-emerald-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400">
            {summary.my_selected_count}
          </div>
          <div className="mt-1 text-xs text-slate-400">Offers secured</div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-surface-800 pb-1">
        <button
          onClick={() => setActiveTab("DRIVES")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
            activeTab === "DRIVES"
              ? "bg-brand-600 text-white shadow-md shadow-brand-500/20"
              : "bg-white dark:bg-surface-900/60 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-surface-800"
          }`}
        >
          <Briefcase className="h-4 w-4" />
          <span>Explore Drives</span>
          <span className="ml-1 rounded-full bg-white/20 px-2 py-0.5 text-xs">
            {drives.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("MY_APPLICATIONS")}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
            activeTab === "MY_APPLICATIONS"
              ? "bg-brand-600 text-white shadow-md shadow-brand-500/20"
              : "bg-white dark:bg-surface-900/60 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-surface-800"
          }`}
        >
          <FileText className="h-4 w-4" />
          <span>My Applications</span>
          <span className="ml-1 rounded-full bg-white/20 px-2 py-0.5 text-xs">
            {myApplications.length}
          </span>
        </button>
      </div>

      {/* TAB 1: EXPLORE DRIVES */}
      {activeTab === "DRIVES" && (
        <div className="space-y-5">
          {/* Search & Mode Filters */}
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

            <div className="flex items-center gap-2">
              <select
                value={modeFilter}
                onChange={(e) => setModeFilter(e.target.value)}
                className="rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 px-3 py-2 text-xs font-medium text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="ALL">All Work Modes</option>
                <option value="ON_SITE">On-site</option>
                <option value="REMOTE">Remote</option>
                <option value="HYBRID">Hybrid</option>
              </select>
            </div>
          </div>

          {/* Drives Cards Grid */}
          {isDrivesLoading ? (
            <LoadingState message="Loading available placement drives..." />
          ) : drives.length === 0 ? (
            <EmptyState
              title="No Placement Drives Found"
              description="No active drives currently match your filter criteria. Check back soon for new openings."
            />
          ) : (
            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              {drives.map((drive) => {
                const hasApplied = drive.has_applied;
                const myStatus = drive.my_application_status;

                return (
                  <div
                    key={drive.id}
                    className="group rounded-3xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 p-6 shadow-sm transition-all duration-200 hover:border-brand-500/40 hover:shadow-lg flex flex-col justify-between"
                  >
                    <div>
                      {/* Top Header */}
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-3.5">
                          <div className="flex h-13 w-13 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600/10 to-indigo-600/10 border border-brand-500/20 text-brand-600 dark:text-brand-400 font-black text-xl">
                            {drive.company_name.slice(0, 2).toUpperCase()}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <h3 className="font-bold text-slate-900 dark:text-white text-base sm:text-lg">
                                {drive.company_name}
                              </h3>
                              {drive.company_code && (
                                <span className="text-[11px] font-mono text-slate-400 bg-slate-100 dark:bg-surface-800 px-2 py-0.5 rounded-md">
                                  {drive.company_code}
                                </span>
                              )}
                            </div>
                            <p className="text-sm font-semibold text-brand-600 dark:text-brand-400">
                              {drive.role}
                            </p>
                          </div>
                        </div>

                        {hasApplied ? (
                          <Badge
                            variant={
                              myStatus === "SELECTED"
                                ? "emerald"
                                : myStatus === "SHORTLISTED"
                                  ? "indigo"
                                  : myStatus === "REJECTED"
                                    ? "rose"
                                    : "amber"
                            }
                            size="md"
                          >
                            Status: {myStatus}
                          </Badge>
                        ) : (
                          <Badge variant="brand" size="sm">
                            {drive.mode_of_work}
                          </Badge>
                        )}
                      </div>

                      {/* Package & Key Specs */}
                      <div className="mt-5 grid grid-cols-2 gap-3 text-xs text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-surface-950/60 p-3.5 rounded-2xl">
                        <div className="flex items-center gap-2">
                          <DollarSign className="h-4 w-4 text-emerald-500 shrink-0" />
                          <div>
                            <span className="text-[10px] text-slate-400 block font-medium">Package / CTC</span>
                            <span className="font-bold text-slate-900 dark:text-white">
                              {drive.stipend_or_ctc}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <MapPin className="h-4 w-4 text-rose-500 shrink-0" />
                          <div>
                            <span className="text-[10px] text-slate-400 block font-medium">Location</span>
                            <span className="font-medium text-slate-900 dark:text-white truncate">
                              {drive.location}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <ShieldCheck className="h-4 w-4 text-amber-500 shrink-0" />
                          <div>
                            <span className="text-[10px] text-slate-400 block font-medium">Bond / Agreement</span>
                            <span className="font-medium text-slate-900 dark:text-white truncate">
                              {drive.bond_period}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4 text-indigo-500 shrink-0" />
                          <div>
                            <span className="text-[10px] text-slate-400 block font-medium">Apply By</span>
                            <span className="font-medium text-slate-900 dark:text-white">
                              {new Date(drive.application_deadline).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Eligibility Criteria */}
                      <div className="mt-3.5 text-xs text-slate-600 dark:text-slate-300">
                        <span className="font-semibold text-slate-900 dark:text-white">Eligibility: </span>
                        {drive.eligibility_criteria}
                      </div>

                      {/* Required Skills */}
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {drive.skills.split(",").map((s, idx) => (
                          <span
                            key={idx}
                            className="rounded-lg bg-brand-500/10 dark:bg-brand-500/20 px-2.5 py-0.5 text-[11px] font-semibold text-brand-700 dark:text-brand-300"
                          >
                            {s.trim()}
                          </span>
                        ))}
                      </div>

                      {/* Description preview */}
                      <p className="mt-3 text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
                        {drive.job_description}
                      </p>
                    </div>

                    {/* Bottom CTA */}
                    <div className="mt-6 pt-4 border-t border-slate-200 dark:border-surface-800 flex items-center justify-between">
                      <span className="text-xs text-slate-400">
                        Batch: {drive.eligible_batches}
                      </span>

                      {hasApplied ? (
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                            <CheckCircle2 className="h-4 w-4" />
                            Applied
                          </span>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setActiveTab("MY_APPLICATIONS")}
                            className="text-xs"
                          >
                            View Status
                          </Button>
                        </div>
                      ) : (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => handleOpenApply(drive)}
                          className="flex items-center gap-1.5 font-bold shadow-md shadow-brand-500/20"
                        >
                          <Send className="h-3.5 w-3.5" />
                          <span>Apply Now</span>
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: MY APPLICATIONS */}
      {activeTab === "MY_APPLICATIONS" && (
        <div className="space-y-4">
          {isMyAppsLoading ? (
            <LoadingState message="Loading your placement applications..." />
          ) : myApplications.length === 0 ? (
            <EmptyState
              title="No Applications Submitted"
              description="You have not applied for any placement drives yet. Browse open drives to begin."
              actionLabel="Explore Placement Drives"
              onAction={() => setActiveTab("DRIVES")}
            />
          ) : (
            myApplications.map((app) => {
              const isSelected = app.status === "SELECTED";
              const isRejected = app.status === "REJECTED";
              const isShortlisted = app.status === "SHORTLISTED";
              const isUnderReview = app.status === "UNDER_REVIEW";

              return (
                <div
                  key={app.id}
                  className="rounded-3xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 p-6 shadow-sm"
                >
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <div className="flex items-center gap-3">
                        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-600 dark:text-brand-400 font-bold text-lg">
                          {(app.drive_details?.company_name || "Company").slice(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                            {app.drive_details?.company_name}
                          </h3>
                          <p className="text-xs font-semibold text-brand-600 dark:text-brand-400">
                            {app.drive_details?.role}
                          </p>
                        </div>
                      </div>

                      <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
                        {app.drive_details?.stipend_or_ctc && (
                          <span className="font-semibold text-slate-900 dark:text-white">
                            CTC: {app.drive_details.stipend_or_ctc}
                          </span>
                        )}
                        {app.drive_details?.location && (
                          <span>Location: {app.drive_details.location}</span>
                        )}
                        <span>Applied on: {new Date(app.submitted_at).toLocaleDateString()}</span>
                      </div>
                    </div>

                    <div className="flex flex-col items-start sm:items-end gap-1.5">
                      <span className="text-[11px] font-medium text-slate-400">Current Status</span>
                      <Badge
                        variant={
                          isSelected
                            ? "emerald"
                            : isShortlisted
                              ? "indigo"
                              : isRejected
                                ? "rose"
                                : isUnderReview
                                  ? "amber"
                                  : "slate"
                        }
                        size="md"
                      >
                        {app.status}
                      </Badge>
                    </div>
                  </div>

                  {/* Submission Snapshot */}
                  <div className="mt-4 rounded-2xl bg-slate-50 dark:bg-surface-950/60 p-4 text-xs space-y-2">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      <div>
                        <span className="text-slate-400 block text-[11px]">Submitted CGPA / Marks:</span>
                        <span className="font-bold text-slate-900 dark:text-white">
                          {app.cgpa_or_percentage}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[11px]">Contact Phone:</span>
                        <span className="font-medium text-slate-900 dark:text-white">{app.phone_number}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[11px]">Resume:</span>
                        <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                          {app.has_resume_file && app.resume_download_url ? (
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={() => handleDownloadResume(app)}
                              disabled={downloadingResumeId === app.id}
                              className="h-7 inline-flex items-center gap-1.5 px-2.5 rounded-lg bg-brand-600 text-white text-xs font-semibold hover:bg-brand-700 shadow-sm"
                            >
                              <Download className="h-3 w-3" />
                              <span>
                                {downloadingResumeId === app.id
                                  ? "Downloading..."
                                  : `Download ${app.resume_filename ? `(${app.resume_filename})` : "Resume"}`}
                              </span>
                            </Button>
                          ) : null}
                          {app.resume_url ? (
                            <a
                              href={app.resume_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-brand-600 dark:text-brand-400 font-semibold hover:underline inline-flex items-center gap-1 text-xs"
                            >
                              <span>Cloud Link</span>
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          ) : null}
                          {!app.has_resume_file && !app.resume_url && (
                            <span className="text-slate-400">N/A</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {app.cover_note && (
                      <div className="pt-2 border-t border-slate-200 dark:border-surface-800 text-slate-600 dark:text-slate-300">
                        <span className="font-semibold text-slate-900 dark:text-white">Cover Statement:</span>{" "}
                        "{app.cover_note}"
                      </div>
                    )}
                  </div>

                  {/* Admin Feedback Box */}
                  {(app.admin_notes || app.rejection_reason) && (
                    <div className="mt-3 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 p-4 text-xs">
                      <div className="font-bold text-brand-600 dark:text-brand-300 mb-1 flex items-center gap-1.5">
                        <Sparkles className="h-3.5 w-3.5" />
                        <span>Recruiter / Institutional Feedback:</span>
                      </div>
                      {app.admin_notes && <p className="text-slate-700 dark:text-slate-200">{app.admin_notes}</p>}
                      {app.rejection_reason && (
                        <p className="mt-1 text-rose-500 font-medium">
                          Note: {app.rejection_reason}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Modal: Student Apply Now */}
      {applyingDrive && (
        <Modal
          isOpen={true}
          onClose={() => setApplyingDrive(null)}
          title={`Apply to ${applyingDrive.company_name}`}
          size="lg"
        >
          <form onSubmit={handleApplySubmit} className="space-y-4 max-h-[75vh] overflow-y-auto px-1 pr-2">
            {applyError && (
              <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-3.5 text-xs text-rose-500 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{applyError}</span>
              </div>
            )}

            <div className="rounded-2xl bg-brand-50 dark:bg-surface-950 p-4 border border-brand-500/20 text-xs text-slate-600 dark:text-slate-300">
              <div className="font-bold text-brand-700 dark:text-brand-300 text-sm mb-1">
                {applyingDrive.role}
              </div>
              <div>CTC / Stipend: <span className="font-semibold text-slate-900 dark:text-white">{applyingDrive.stipend_or_ctc}</span></div>
              <div>Location: <span className="font-semibold text-slate-900 dark:text-white">{applyingDrive.location} ({applyingDrive.mode_of_work})</span></div>
              <div>Service Agreement: <span className="font-semibold text-slate-900 dark:text-white">{applyingDrive.bond_period}</span></div>
            </div>

            {/* Resume Upload Box */}
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                Upload Resume (PDF, DOCX) *
              </label>

              <div
                onClick={() => fileInputRef.current?.click()}
                className="cursor-pointer border-2 border-dashed border-brand-500/40 hover:border-brand-500 hover:bg-brand-50/50 dark:hover:bg-brand-950/20 rounded-2xl p-4 text-center transition-all"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileChange}
                  className="hidden"
                />

                {applyForm.resume_file ? (
                  <div className="flex items-center justify-between bg-brand-500/10 dark:bg-brand-500/20 p-2.5 rounded-xl text-left">
                    <div className="flex items-center gap-2.5 truncate">
                      <FileCheck className="h-6 w-6 text-brand-600 dark:text-brand-400 shrink-0" />
                      <div className="truncate">
                        <p className="text-xs font-bold text-slate-900 dark:text-white truncate">
                          {applyForm.resume_file.name}
                        </p>
                        <p className="text-[10px] text-slate-500 dark:text-slate-400">
                          {(applyForm.resume_file.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveFile();
                      }}
                      className="p-1 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-white/50 dark:hover:bg-surface-800"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center gap-1.5 py-2">
                    <UploadCloud className="h-8 w-8 text-brand-500" />
                    <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                      Click or drag & drop to upload your resume
                    </p>
                    <p className="text-[11px] text-slate-400">
                      Supports PDF, DOC, DOCX up to 10MB
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Cloud Resume Link as alternative */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Or Cloud Resume URL (Google Drive / OneDrive link)
              </label>
              <input
                type="url"
                placeholder="https://drive.google.com/file/d/.../view"
                value={applyForm.resume_url}
                onChange={(e) => setApplyForm({ ...applyForm, resume_url: e.target.value })}
                className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Contact Phone Number *
                </label>
                <input
                  type="text"
                  required
                  placeholder="+91 9876543210"
                  value={applyForm.phone_number}
                  onChange={(e) => setApplyForm({ ...applyForm, phone_number: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  CGPA / Aggregate Percentage *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 8.75 CGPA or 85%"
                  value={applyForm.cgpa_or_percentage}
                  onChange={(e) => setApplyForm({ ...applyForm, cgpa_or_percentage: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Degree / Branch *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Computer Science & Engineering"
                  value={applyForm.branch}
                  onChange={(e) => setApplyForm({ ...applyForm, branch: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Graduation Year *
                </label>
                <input
                  type="number"
                  required
                  placeholder="2026"
                  value={applyForm.graduation_year || 2026}
                  onChange={(e) =>
                    setApplyForm({ ...applyForm, graduation_year: parseInt(e.target.value) || 2026 })
                  }
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  GitHub Profile Link
                </label>
                <input
                  type="url"
                  placeholder="https://github.com/your-handle"
                  value={applyForm.github_url}
                  onChange={(e) => setApplyForm({ ...applyForm, github_url: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  LinkedIn Profile Link
                </label>
                <input
                  type="url"
                  placeholder="https://linkedin.com/in/your-profile"
                  value={applyForm.linkedin_url}
                  onChange={(e) => setApplyForm({ ...applyForm, linkedin_url: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Technical Skills & Strengths
              </label>
              <input
                type="text"
                placeholder="e.g. Java, Python, React, PostgreSQL, Docker, Data Structures"
                value={applyForm.skills_summary}
                onChange={(e) => setApplyForm({ ...applyForm, skills_summary: e.target.value })}
                className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Statement / Note to Recruiter
              </label>
              <textarea
                rows={3}
                placeholder="Explain why you are a strong match for this role..."
                value={applyForm.cover_note}
                onChange={(e) => setApplyForm({ ...applyForm, cover_note: e.target.value })}
                className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200 dark:border-surface-800">
              <Button type="button" variant="outline" onClick={() => setApplyingDrive(null)}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={applyMutation.isPending}
                className="flex items-center gap-1.5"
              >
                <Send className="h-4 w-4" />
                <span>{applyMutation.isPending ? "Submitting..." : "Submit Application"}</span>
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
