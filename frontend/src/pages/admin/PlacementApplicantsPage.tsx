import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Users,
  Search,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Clock,
  ExternalLink,
  Mail,
  Phone,
  GraduationCap,
  FileText,
  Github,
  Linkedin,
  Globe,
  Download,
  AlertCircle,
  ShieldCheck,
  Eye,
  FileCheck,
} from "lucide-react";
import { placementsApi } from "../../api/placementsApi";
import {
  PlacementApplication,
  ApplicationStatus,
  UpdateApplicationStatusPayload,
} from "../../types/placement";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Modal } from "../../components/ui/Modal";
import { EmptyState } from "../../components/ui/EmptyState";
import { LoadingState } from "../../components/ui/LoadingState";

export const PlacementApplicantsPage: React.FC = () => {
  const { id: rawDriveId } = useParams<{ id: string }>();
  const isSpecificDrive = !!rawDriveId && rawDriveId !== "all" && rawDriveId !== "applicants";
  const driveId = isSpecificDrive ? rawDriveId : undefined;
  const queryClient = useQueryClient();

  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [actionModal, setActionModal] = useState<{
    application: PlacementApplication;
    newStatus: ApplicationStatus;
  } | null>(null);
  const [previewResumeApp, setPreviewResumeApp] = useState<PlacementApplication | null>(null);
  const [adminNotes, setAdminNotes] = useState("");
  const [rejectionReason, setRejectionReason] = useState("");

  // Fetch drive details if driveId is present
  const { data: driveData } = useQuery({
    queryKey: ["admin-placement-drive-detail", driveId],
    queryFn: () => (driveId ? placementsApi.adminGetDrive(driveId) : null),
    enabled: !!driveId,
  });

  // Fetch applications
  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-placement-applications", driveId, selectedStatus, searchTerm],
    queryFn: () =>
      placementsApi.adminGetApplications({
        drive_id: driveId,
        status: selectedStatus === "ALL" ? undefined : selectedStatus,
        search: searchTerm || undefined,
      }),
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({
      applicationId,
      payload,
    }: {
      applicationId: string;
      payload: UpdateApplicationStatusPayload;
    }) => placementsApi.adminUpdateApplicationStatus(applicationId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-placement-applications"] });
      queryClient.invalidateQueries({ queryKey: ["admin-placement-drives"] });
      queryClient.invalidateQueries({ queryKey: ["admin-placement-drive-detail"] });
      setActionModal(null);
      setAdminNotes("");
      setRejectionReason("");
    },
  });

  const handleStatusActionClick = (
    application: PlacementApplication,
    newStatus: ApplicationStatus
  ) => {
    setAdminNotes(application.admin_notes || "");
    setRejectionReason(application.rejection_reason || "");
    setActionModal({ application, newStatus });
  };

  const handleConfirmStatusUpdate = () => {
    if (!actionModal) return;
    updateStatusMutation.mutate({
      applicationId: actionModal.application.id,
      payload: {
        status: actionModal.newStatus,
        admin_notes: adminNotes,
        rejection_reason:
          actionModal.newStatus === "REJECTED" ? rejectionReason : undefined,
      },
    });
  };

  const applications = data?.applications || [];
  const stats = data?.stats || {
    total: 0,
    applied: 0,
    under_review: 0,
    shortlisted: 0,
    selected: 0,
    rejected: 0,
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

        // Determine filename with proper extension
        let filename = app.resume_filename;
        if (!filename) {
          const cleanName = app.student_name.toLowerCase().replace(/[^a-z0-9]+/g, "_");
          filename = `${cleanName}_resume.pdf`;
        }

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

  const handleExportCSV = () => {
    if (!applications.length) return;

    const escapeCsv = (val: any): string => {
      if (val === null || val === undefined) return '""';
      const str = String(val).replace(/"/g, '""').replace(/[\r\n]+/g, " ");
      return `"${str}"`;
    };

    const headers = [
      "Candidate Name",
      "Student Roll Number",
      "Email Address",
      "Phone Number",
      "College / Institution",
      "Branch / Discipline",
      "Graduation Year",
      "CGPA / Percentage",
      "Application Status",
      "Technical Skills",
      "Cover Statement",
      "Resume Filename",
      "Resume Link / File",
      "GitHub Profile",
      "LinkedIn Profile",
      "Portfolio",
      "Submitted At",
      "Admin Evaluation Notes",
      "Rejection Reason",
    ];

    const rows = applications.map((app) => [
      escapeCsv(app.student_name),
      escapeCsv(app.student_id_number),
      escapeCsv(app.email),
      escapeCsv(app.phone_number),
      escapeCsv(app.college_name),
      escapeCsv(app.branch),
      escapeCsv(app.graduation_year || ""),
      escapeCsv(app.cgpa_or_percentage),
      escapeCsv(app.status),
      escapeCsv(app.skills_summary || ""),
      escapeCsv(app.cover_note || ""),
      escapeCsv(app.resume_filename || ""),
      escapeCsv(app.resume_download_url || app.resume_url || ""),
      escapeCsv(app.github_url || ""),
      escapeCsv(app.linkedin_url || ""),
      escapeCsv(app.portfolio_url || ""),
      escapeCsv(new Date(app.submitted_at).toLocaleString()),
      escapeCsv(app.admin_notes || ""),
      escapeCsv(app.rejection_reason || ""),
    ]);

    const csvContent = [headers.join(","), ...rows.map((e) => e.join(","))].join("\r\n");

    // Add UTF-8 BOM (\uFEFF) so Excel and standard tools parse Unicode and columns cleanly
    const blob = new Blob(["\uFEFF" + csvContent], {
      type: "text/csv;charset=utf-8;",
    });

    const companySlug = driveData?.drive?.company_name
      ? driveData.drive.company_name.toLowerCase().replace(/[^a-z0-9]+/g, "_")
      : "all_drives";
    const dateStamp = new Date().toISOString().slice(0, 10);
    const fileName = `placement_applicants_${companySlug}_${dateStamp}.csv`;

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", fileName);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleExportJSON = () => {
    if (!applications.length) return;

    const dataToExport = applications.map((app) => ({
      id: app.id,
      student_name: app.student_name,
      student_id_number: app.student_id_number,
      email: app.email,
      phone_number: app.phone_number,
      college_name: app.college_name,
      branch: app.branch,
      graduation_year: app.graduation_year,
      cgpa_or_percentage: app.cgpa_or_percentage,
      status: app.status,
      skills_summary: app.skills_summary,
      cover_note: app.cover_note,
      resume_filename: app.resume_filename,
      resume_download_url: app.resume_download_url,
      resume_url: app.resume_url,
      github_url: app.github_url,
      linkedin_url: app.linkedin_url,
      portfolio_url: app.portfolio_url,
      submitted_at: app.submitted_at,
      admin_notes: app.admin_notes,
      rejection_reason: app.rejection_reason,
    }));

    const jsonString = JSON.stringify(dataToExport, null, 2);
    const blob = new Blob([jsonString], { type: "application/json;charset=utf-8;" });

    const companySlug = driveData?.drive?.company_name
      ? driveData.drive.company_name.toLowerCase().replace(/[^a-z0-9]+/g, "_")
      : "all_drives";
    const dateStamp = new Date().toISOString().slice(0, 10);
    const fileName = `placement_applicants_${companySlug}_${dateStamp}.json`;

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", fileName);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const filterTabs = [
    { key: "ALL", label: "All Applicants", count: stats.total, variant: "slate" },
    { key: "SELECTED", label: "Selected / Offers", count: stats.selected, variant: "emerald" },
    { key: "SHORTLISTED", label: "Shortlisted", count: stats.shortlisted, variant: "indigo" },
    { key: "UNDER_REVIEW", label: "Under Review", count: stats.under_review, variant: "amber" },
    { key: "REJECTED", label: "Rejected", count: stats.rejected, variant: "rose" },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Link to="/admin/placements">
            <Button variant="ghost" size="sm" className="h-9 w-9 p-0 rounded-xl">
              <ArrowLeft className="h-5 w-5 text-slate-400" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              <Users className="h-6 w-6 text-brand-600 dark:text-brand-400" />
              {driveData?.drive
                ? `${driveData.drive.company_name} Applicants`
                : "All Placement Applicants"}
            </h1>
            {driveData?.drive && (
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                Role: <span className="font-semibold text-slate-700 dark:text-slate-200">{driveData.drive.role}</span> | CTC:{" "}
                <span className="font-semibold text-emerald-600 dark:text-emerald-400">{driveData.drive.stipend_or_ctc}</span> | Location:{" "}
                {driveData.drive.location}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportJSON}
            className="flex items-center gap-1.5 text-xs font-semibold"
          >
            <Download className="h-3.5 w-3.5 text-slate-400" />
            <span>Export JSON</span>
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 text-xs font-semibold shadow-sm"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Export CSV</span>
          </Button>
        </div>
      </div>

      {/* Filter Tabs Bar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 border-b border-slate-200 dark:border-surface-800">
        {filterTabs.map((tab) => {
          const isActive = selectedStatus === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setSelectedStatus(tab.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${isActive
                ? "bg-brand-600 text-white shadow-md shadow-brand-500/20"
                : "bg-white dark:bg-surface-900/60 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-surface-800"
                }`}
            >
              <span>{tab.label}</span>
              <span
                className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${isActive
                  ? "bg-white/20 text-white"
                  : "bg-slate-100 dark:bg-surface-800 text-slate-600 dark:text-slate-300"
                  }`}
              >
                {tab.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Search Bar */}
      <div className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/40 p-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by student name, roll number, email, branch..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 pl-10 pr-4 py-2 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>
      </div>

      {/* Applications List */}
      {isLoading ? (
        <LoadingState message="Fetching student applications..." />
      ) : error ? (
        <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-6 text-center text-rose-400">
          <AlertCircle className="mx-auto h-8 w-8 mb-2" />
          <p className="font-semibold">Failed to load applicants</p>
        </div>
      ) : applications.length === 0 ? (
        <EmptyState
          title="No Applicants Found"
          description={
            selectedStatus !== "ALL"
              ? `No student applications matching status "${selectedStatus}".`
              : "No students have applied for this drive yet."
          }
        />
      ) : (
        <div className="space-y-4">
          {applications.map((app) => {
            const isSelected = app.status === "SELECTED";
            const isRejected = app.status === "REJECTED";
            const isShortlisted = app.status === "SHORTLISTED";
            const isUnderReview = app.status === "UNDER_REVIEW";
            const hasResumeFile = Boolean(app.has_resume_file && app.resume_download_url);
            const hasResumeUrl = Boolean(app.resume_url);

            return (
              <div
                key={app.id}
                className="rounded-2xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/60 p-5 shadow-sm transition-all hover:border-brand-500/30"
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  {/* Student Information */}
                  <div className="flex items-start gap-4">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500/10 to-brand-500/10 border border-indigo-500/20 text-brand-600 dark:text-brand-300 font-bold text-base">
                      {app.student_name.slice(0, 2).toUpperCase()}
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-bold text-slate-900 dark:text-white text-base">
                          {app.student_name}
                        </h3>
                        <span className="text-xs font-mono font-semibold bg-slate-100 dark:bg-surface-800 px-2 py-0.5 rounded-md text-slate-600 dark:text-slate-300">
                          {app.student_id_number}
                        </span>
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
                          size="sm"
                        >
                          {app.status}
                        </Badge>
                      </div>

                      {/* College & Academic Details */}
                      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
                        <span className="flex items-center gap-1">
                          <GraduationCap className="h-3.5 w-3.5 text-indigo-400" />
                          {app.college_name || "GQT Academy"} ({app.branch})
                        </span>
                        {app.graduation_year && <span>Class of {app.graduation_year}</span>}
                        {app.cgpa_or_percentage && (
                          <span className="font-bold text-brand-600 dark:text-brand-400 bg-brand-500/10 px-2 py-0.5 rounded-md">
                            CGPA / Marks: {app.cgpa_or_percentage}
                          </span>
                        )}
                      </div>

                      {/* Contact Channels */}
                      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600 dark:text-slate-400 pt-1">
                        <a
                          href={`mailto:${app.email}`}
                          className="flex items-center gap-1 hover:text-brand-500 transition-colors"
                        >
                          <Mail className="h-3.5 w-3.5 text-slate-400" />
                          <span>{app.email}</span>
                        </a>
                        {app.phone_number && (
                          <a
                            href={`tel:${app.phone_number}`}
                            className="flex items-center gap-1 hover:text-brand-500 transition-colors"
                          >
                            <Phone className="h-3.5 w-3.5 text-slate-400" />
                            <span>{app.phone_number}</span>
                          </a>
                        )}
                        <span className="text-[11px] text-slate-400">
                          Applied on {new Date(app.submitted_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Quick Action Selection Buttons */}
                  <div className="flex flex-wrap items-center gap-2 self-end lg:self-start">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleStatusActionClick(app, "SHORTLISTED")}
                      disabled={isShortlisted || updateStatusMutation.isPending}
                      className={`h-8 text-xs font-semibold ${isShortlisted
                        ? "bg-indigo-500/10 text-indigo-400 border-indigo-500/20"
                        : "hover:bg-indigo-500/10 hover:text-indigo-600 hover:border-indigo-500/30"
                        }`}
                    >
                      <ShieldCheck className="h-3.5 w-3.5 mr-1" />
                      <span>Shortlist</span>
                    </Button>

                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => handleStatusActionClick(app, "SELECTED")}
                      disabled={isSelected || updateStatusMutation.isPending}
                      className={`h-8 text-xs font-semibold ${isSelected
                        ? "bg-emerald-600 text-white cursor-default"
                        : "bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm"
                        }`}
                    >
                      <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                      <span>Select / Offer</span>
                    </Button>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleStatusActionClick(app, "REJECTED")}
                      disabled={isRejected || updateStatusMutation.isPending}
                      className={`h-8 text-xs font-semibold ${isRejected
                        ? "bg-rose-500/10 text-rose-500 border-rose-500/20"
                        : "hover:bg-rose-500/10 hover:text-rose-600 hover:border-rose-500/30 text-rose-500"
                        }`}
                    >
                      <XCircle className="h-3.5 w-3.5 mr-1" />
                      <span>Reject</span>
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleStatusActionClick(app, "UNDER_REVIEW")}
                      disabled={isUnderReview || updateStatusMutation.isPending}
                      className="h-8 text-xs text-slate-400 hover:text-amber-500"
                    >
                      <Clock className="h-3.5 w-3.5 mr-1" />
                      <span>Review</span>
                    </Button>
                  </div>
                </div>

                {/* Candidate Attachments & Statement */}
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-surface-800/80 flex flex-col md:flex-row md:items-center md:justify-between gap-3 text-xs">
                  <div className="flex flex-wrap items-center gap-2.5">
                    {/* View Resume Button (Opens In-App Viewer Modal) */}
                    {(hasResumeFile || hasResumeUrl) && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPreviewResumeApp(app)}
                        className="h-8 inline-flex items-center gap-1.5 px-3 rounded-xl bg-brand-50 dark:bg-brand-950/40 text-brand-600 dark:text-brand-300 font-bold border-brand-500/30 hover:bg-brand-500 hover:text-white transition-all text-xs"
                      >
                        <Eye className="h-3.5 w-3.5" />
                        <span>View Resume</span>
                      </Button>
                    )}

                    {/* Direct Download Button */}
                    {hasResumeFile && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleDownloadResume(app)}
                        disabled={downloadingResumeId === app.id}
                        className="inline-flex items-center gap-1.5 h-8 px-3 rounded-xl bg-brand-600 text-white font-semibold hover:bg-brand-700 shadow-sm transition-colors text-xs"
                      >
                        <Download className="h-3.5 w-3.5" />
                        <span>
                          {downloadingResumeId === app.id
                            ? "Downloading..."
                            : `Download ${app.resume_filename ? `(${app.resume_filename})` : "Resume"}`}
                        </span>
                      </Button>
                    )}

                    {/* Cloud Link Button */}
                    {hasResumeUrl && (
                      <a
                        href={app.resume_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 h-8 px-3 rounded-xl bg-slate-100 dark:bg-surface-800 text-slate-700 dark:text-slate-300 font-medium hover:bg-slate-200 dark:hover:bg-surface-700 transition-colors text-xs"
                      >
                        <FileText className="h-3.5 w-3.5" />
                        <span>Cloud Link</span>
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    )}

                    {/* Portfolio / Profiles */}
                    {app.github_url && (
                      <a
                        href={app.github_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-surface-800 text-slate-700 dark:text-slate-300 hover:text-white transition-colors"
                      >
                        <Github className="h-3.5 w-3.5" />
                        <span>GitHub</span>
                      </a>
                    )}

                    {app.linkedin_url && (
                      <a
                        href={app.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 hover:bg-blue-500/20 transition-colors"
                      >
                        <Linkedin className="h-3.5 w-3.5" />
                        <span>LinkedIn</span>
                      </a>
                    )}

                    {app.portfolio_url && (
                      <a
                        href={app.portfolio_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400 hover:bg-purple-500/20 transition-colors"
                      >
                        <Globe className="h-3.5 w-3.5" />
                        <span>Portfolio</span>
                      </a>
                    )}
                  </div>

                  {app.skills_summary && (
                    <div className="text-slate-500 dark:text-slate-400 truncate max-w-md">
                      <span className="font-semibold text-slate-700 dark:text-slate-300">Skills:</span> {app.skills_summary}
                    </div>
                  )}
                </div>

                {/* Cover Note & Admin Remarks (If present) */}
                {(app.cover_note || app.admin_notes || app.rejection_reason) && (
                  <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                    {app.cover_note && (
                      <div className="rounded-xl bg-slate-50 dark:bg-surface-950 p-3 text-xs text-slate-600 dark:text-slate-300">
                        <span className="font-semibold text-slate-900 dark:text-white block mb-1">
                          Applicant Cover Note:
                        </span>
                        <p className="italic">"{app.cover_note}"</p>
                      </div>
                    )}

                    {(app.admin_notes || app.rejection_reason) && (
                      <div className="rounded-xl bg-indigo-50/50 dark:bg-surface-950/80 border border-indigo-500/10 p-3 text-xs text-slate-600 dark:text-slate-300">
                        <span className="font-semibold text-indigo-600 dark:text-indigo-400 block mb-1">
                          Admin Feedback / Internal Remarks:
                        </span>
                        {app.admin_notes && <p className="mb-1">{app.admin_notes}</p>}
                        {app.rejection_reason && (
                          <p className="text-rose-500 font-medium">
                            Rejection Reason: {app.rejection_reason}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Modal 1: Resume Preview & Document Viewer */}
      {previewResumeApp && (
        <Modal
          isOpen={true}
          onClose={() => setPreviewResumeApp(null)}
          title={`Resume: ${previewResumeApp.student_name}`}
          size="xl"
        >
          <div className="space-y-4">
            {/* Top Bar with Student Info & Action Buttons */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-3.5 rounded-2xl bg-slate-50 dark:bg-surface-950 border border-slate-200 dark:border-surface-800">
              <div className="text-xs space-y-0.5">
                <div className="font-bold text-slate-900 dark:text-white text-sm">
                  {previewResumeApp.student_name} ({previewResumeApp.student_id_number})
                </div>
                <div className="text-slate-500 dark:text-slate-400">
                  {previewResumeApp.branch} | CGPA:{" "}
                  <span className="font-semibold text-brand-600 dark:text-brand-400">
                    {previewResumeApp.cgpa_or_percentage}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                {previewResumeApp.has_resume_file && previewResumeApp.resume_download_url && (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleDownloadResume(previewResumeApp)}
                    disabled={downloadingResumeId === previewResumeApp.id}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold shadow-sm transition-colors"
                  >
                    <Download className="h-3.5 w-3.5" />
                    <span>{downloadingResumeId === previewResumeApp.id ? "Downloading..." : "Download File"}</span>
                  </Button>
                )}

                {previewResumeApp.has_resume_file && previewResumeApp.resume_download_url && (
                  <a
                    href={previewResumeApp.resume_download_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-surface-700 bg-white dark:bg-surface-900 text-slate-700 dark:text-slate-200 hover:bg-slate-50 text-xs font-semibold transition-colors"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                    <span>Open in New Tab</span>
                  </a>
                )}

                {previewResumeApp.resume_url && (
                  <a
                    href={previewResumeApp.resume_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-500/20 text-xs font-semibold transition-colors"
                  >
                    <Globe className="h-3.5 w-3.5" />
                    <span>Cloud Resume Link</span>
                  </a>
                )}
              </div>
            </div>

            {/* Embedded Resume View */}
            {previewResumeApp.has_resume_file && previewResumeApp.resume_download_url ? (
              <div className="rounded-2xl border border-slate-200 dark:border-surface-800 overflow-hidden bg-slate-100 dark:bg-surface-950 h-[65vh]">
                <iframe
                  src={previewResumeApp.resume_download_url}
                  title={`Resume of ${previewResumeApp.student_name}`}
                  className="w-full h-full border-0"
                />
              </div>
            ) : previewResumeApp.resume_url ? (
              <div className="rounded-2xl border border-slate-200 dark:border-surface-800 p-8 text-center bg-slate-50 dark:bg-surface-950 space-y-3">
                <FileCheck className="mx-auto h-12 w-12 text-brand-500" />
                <h4 className="font-bold text-slate-900 dark:text-white">
                  External Cloud Document
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
                  The applicant provided an external cloud resume link (Google Drive, OneDrive, or Dropbox).
                </p>
                <a
                  href={previewResumeApp.resume_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-sm shadow-md transition-colors"
                >
                  <ExternalLink className="h-4 w-4" />
                  <span>Open External Resume</span>
                </a>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-400 text-xs">
                No resume file or link attached to this application.
              </div>
            )}

            {/* Quick Status Bar inside preview */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-200 dark:border-surface-800">
              <span className="text-xs text-slate-500">
                Current Status: <Badge variant="brand" size="sm">{previewResumeApp.status}</Badge>
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const app = previewResumeApp;
                    setPreviewResumeApp(null);
                    handleStatusActionClick(app, "SHORTLISTED");
                  }}
                  className="text-xs"
                >
                  Shortlist
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    const app = previewResumeApp;
                    setPreviewResumeApp(null);
                    handleStatusActionClick(app, "SELECTED");
                  }}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs"
                >
                  Select / Offer
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const app = previewResumeApp;
                    setPreviewResumeApp(null);
                    handleStatusActionClick(app, "REJECTED");
                  }}
                  className="text-rose-500 hover:bg-rose-500/10 text-xs"
                >
                  Reject
                </Button>
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal 2: Status Action Feedback / Notes */}
      {actionModal && (
        <Modal
          isOpen={true}
          onClose={() => setActionModal(null)}
          title={`Update Application: ${actionModal.application.student_name}`}
        >
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Changing status to:</span>
              <Badge
                variant={
                  actionModal.newStatus === "SELECTED"
                    ? "emerald"
                    : actionModal.newStatus === "SHORTLISTED"
                      ? "indigo"
                      : actionModal.newStatus === "REJECTED"
                        ? "rose"
                        : "amber"
                }
              >
                {actionModal.newStatus}
              </Badge>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Admin Evaluation Notes / Interview Remarks
              </label>
              <textarea
                rows={3}
                placeholder="e.g. Candidate performed exceptionally in technical round. Offer CTC: ₹8.5 LPA."
                value={adminNotes}
                onChange={(e) => setAdminNotes(e.target.value)}
                className="w-full rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-950 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500"
              />
            </div>

            {actionModal.newStatus === "REJECTED" && (
              <div>
                <label className="block text-xs font-semibold text-rose-500 mb-1">
                  Rejection Reason (Feedback for candidate / audit)
                </label>
                <textarea
                  rows={2}
                  placeholder="e.g. Cut-off criteria not met or failed technical coding assessment."
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  className="w-full rounded-xl border border-rose-200 dark:border-rose-900/40 bg-rose-50/20 dark:bg-rose-950/20 p-2.5 text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-rose-500"
                />
              </div>
            )}

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-surface-800">
              <Button variant="outline" onClick={() => setActionModal(null)}>
                Cancel
              </Button>
              <Button
                variant={actionModal.newStatus === "REJECTED" ? "danger" : "primary"}
                onClick={handleConfirmStatusUpdate}
                disabled={updateStatusMutation.isPending}
              >
                Confirm {actionModal.newStatus}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
