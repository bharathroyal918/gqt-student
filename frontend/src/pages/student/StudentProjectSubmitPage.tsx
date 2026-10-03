import React, { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Github,
  Sparkles,
  CheckCircle2,
  FolderGit2,
  FileText,
  MessageSquare,
  Loader2,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { FormField, Input, Textarea, Select } from "../../components/ui/Form";
import { useToast } from "../../context/ToastContext";
import { studentApi } from "../../api/studentApi";
import { useAuthStore } from "../../store/authStore";

export const StudentProjectSubmitPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();
  const { hydrateAuth } = useAuthStore();

  const preselectedProjectId = searchParams.get("projectId") || "";
  const [selectedProjectId, setSelectedProjectId] = useState<string>(preselectedProjectId);

  const [formData, setFormData] = useState({
    github_repository_url: "",
    live_demo_url: "",
    notes: "",
  });

  // Fetch available projects
  const { data: projectsData, isLoading: isLoadingProjects } = useQuery({
    queryKey: ["student", "projects"],
    queryFn: () => studentApi.getProjects(),
  });

  const projects = projectsData?.projects || [];

  // If no project selected yet and projects loaded, default to first or preselected
  useEffect(() => {
    if (!selectedProjectId && projects.length > 0) {
      const match = preselectedProjectId
        ? projects.find((p) => p.id === preselectedProjectId)
        : null;
      setSelectedProjectId(match ? match.id : projects[0].id);
    } else if (preselectedProjectId && projects.length > 0) {
      setSelectedProjectId(preselectedProjectId);
    }
  }, [projects, preselectedProjectId, selectedProjectId]);

  // Fetch project detail for the selected project
  const { data: projectDetail, isLoading: isLoadingDetail } = useQuery({
    queryKey: ["student", "project", selectedProjectId],
    queryFn: () => studentApi.getProjectDetail(selectedProjectId),
    enabled: !!selectedProjectId,
  });

  // Pre-populate fields if student previously submitted
  useEffect(() => {
    if (projectDetail?.submission_detail) {
      setFormData({
        github_repository_url: projectDetail.submission_detail.github_repository_url || "",
        live_demo_url: projectDetail.submission_detail.live_demo_url || "",
        notes: projectDetail.submission_detail.notes || "",
      });
    } else {
      setFormData({
        github_repository_url: "",
        live_demo_url: "",
        notes: "",
      });
    }
  }, [projectDetail]);

  const submitMutation = useMutation({
    mutationFn: (payload: { github_repository_url: string; live_demo_url: string; notes: string }) =>
      studentApi.submitProject(selectedProjectId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["student", "projects"] });
      queryClient.invalidateQueries({ queryKey: ["student", "project", selectedProjectId] });
      queryClient.invalidateQueries({ queryKey: ["student", "dashboard"] });
      hydrateAuth(true);
      success("Deliverables Submitted!", "Your project deliverables have been submitted for faculty review.");
      navigate("/projects");
    },
    onError: (err: any) => {
      toastError("Submission Error", err?.response?.data?.message || "Failed to submit project deliverables.");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProjectId) {
      toastError("Select Project", "Please select a valid project to submit.");
      return;
    }
    submitMutation.mutate(formData);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Back button */}
      <div className="flex items-center gap-4">
        <Link to="/projects">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-1.5" />
            Back to Projects
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Form */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="p-6 sm:p-8">
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <FolderGit2 className="h-6 w-6 text-brand-600 dark:text-brand-400" />
              Submit Capstone Deliverables
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Provide your GitHub repository URL, live application deployment link, and architecture summary.
            </p>

            {isLoadingProjects ? (
              <div className="flex justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                <FormField label="Select Project" required>
                  <Select
                    value={selectedProjectId}
                    onChange={(e) => setSelectedProjectId(e.target.value)}
                    required
                  >
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.title} ({p.max_score} pts)
                      </option>
                    ))}
                  </Select>
                </FormField>

                <FormField label="GitHub Repository URL" required>
                  <div className="relative">
                    <Github className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                    <Input
                      placeholder="https://github.com/username/project-repo"
                      className="pl-10 font-mono text-xs"
                      value={formData.github_repository_url}
                      onChange={(e) => setFormData({ ...formData, github_repository_url: e.target.value })}
                      required
                    />
                  </div>
                </FormField>

                <FormField label="Live Demo URL (Optional)">
                  <div className="relative">
                    <Sparkles className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                    <Input
                      placeholder="https://project-demo.vercel.app"
                      className="pl-10 font-mono text-xs"
                      value={formData.live_demo_url}
                      onChange={(e) => setFormData({ ...formData, live_demo_url: e.target.value })}
                    />
                  </div>
                </FormField>

                <FormField label="Architecture & Implementation Notes">
                  <Textarea
                    rows={4}
                    placeholder="Outline design decisions, framework choices, database schema, and test suite instructions..."
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  />
                </FormField>

                <div className="pt-4 border-t border-slate-200 dark:border-surface-800 flex justify-end gap-3">
                  <Link to="/projects">
                    <Button variant="secondary" type="button">
                      Cancel
                    </Button>
                  </Link>
                  <Button type="submit" isLoading={submitMutation.isPending}>
                    <CheckCircle2 className="h-4 w-4 mr-1.5" />
                    {projectDetail?.has_submitted ? "Update Submission" : "Submit Deliverables"}
                  </Button>
                </div>
              </form>
            )}
          </Card>

          {/* Submission History / Feedback Section if exists */}
          {projectDetail?.submission_detail && (
            <Card className="p-6">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-brand-500" />
                Faculty Review & Evaluation
              </h3>

              <div className="mt-3 space-y-3 text-xs">
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-100 dark:bg-surface-800">
                  <span className="text-slate-500 dark:text-slate-400">Current Status:</span>
                  <Badge
                    variant={
                      projectDetail.status === "APPROVED"
                        ? "emerald"
                        : projectDetail.status === "CHANGES_REQUESTED"
                        ? "rose"
                        : "amber"
                    }
                  >
                    {projectDetail.status}
                  </Badge>
                </div>

                {projectDetail.score !== null && (
                  <div className="flex items-center justify-between p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-300 font-bold">
                    <span>Awarded Score:</span>
                    <span>{projectDetail.score} / {projectDetail.max_score} Points</span>
                  </div>
                )}

                {projectDetail.submission_detail.feedbacks?.length > 0 ? (
                  <div className="space-y-2 mt-3">
                    <p className="font-semibold text-slate-700 dark:text-slate-300">Reviewer Comments:</p>
                    {projectDetail.submission_detail.feedbacks.map((fb, idx) => (
                      <div key={idx} className="p-3 rounded-xl bg-slate-50 dark:bg-surface-900 border border-slate-200 dark:border-surface-700">
                        <div className="flex items-center justify-between font-medium text-slate-900 dark:text-white">
                          <span>{fb.reviewer_name}</span>
                          <span className="text-[10px] text-slate-400">{fb.created_at}</span>
                        </div>
                        <p className="mt-1 text-slate-600 dark:text-slate-300">{fb.feedback_text}</p>
                        {fb.suggested_changes && (
                          <p className="mt-1 text-rose-600 dark:text-rose-400">
                            <strong>Action Required:</strong> {fb.suggested_changes}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-400 text-center py-2">
                    No faculty feedback recorded yet. A reviewer will evaluate your code soon.
                  </p>
                )}
              </div>
            </Card>
          )}
        </div>

        {/* Right Column: Project Instructions & Deliverables Guide */}
        <div className="space-y-6">
          <Card className="p-6">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2 mb-3">
              <FileText className="h-4 w-4 text-brand-500" />
              Deliverables Guidelines
            </h3>

            {isLoadingDetail ? (
              <div className="py-6 flex justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-brand-500" />
              </div>
            ) : projectDetail ? (
              <div className="space-y-3 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                <div>
                  <h4 className="font-bold text-slate-900 dark:text-white">{projectDetail.title}</h4>
                  <p className="mt-1">{projectDetail.description}</p>
                </div>

                {projectDetail.deliverables_instructions && (
                  <div className="pt-2 border-t border-slate-200 dark:border-surface-800">
                    <p className="font-semibold text-slate-900 dark:text-white mb-1">Instructions:</p>
                    <p className="whitespace-pre-line text-slate-500 dark:text-slate-400">
                      {projectDetail.deliverables_instructions}
                    </p>
                  </div>
                )}

                <div className="pt-2 border-t border-slate-200 dark:border-surface-800 space-y-1.5 text-slate-500 dark:text-slate-400">
                  <p>✓ Ensure repository is public or access is shared.</p>
                  <p>✓ Include a comprehensive README.md with run steps.</p>
                  <p>✓ Max Points: <strong>{projectDetail.max_score}</strong></p>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400">Select a project to view instructions.</p>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
