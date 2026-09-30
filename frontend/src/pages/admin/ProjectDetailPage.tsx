import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Github,
  ExternalLink,
  FileCode,
  Download,
  Clock,
  MessageSquare,
  Sparkles,
} from "lucide-react";
import { adminApi } from "../../api/adminApi";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { FormField, Input, Textarea, Select } from "../../components/ui/Form";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { useToast } from "../../context/ToastContext";

export const ProjectDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [reviewForm, setReviewForm] = useState({
    status: "UNDER_REVIEW",
    score: 0,
    rating: 5,
    feedback_text: "",
    suggested_changes: "",
  });

  // Query
  const {
    data: submission,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["admin-submission-detail", id],
    queryFn: () => adminApi.getSubmissionDetail(id!),
    enabled: Boolean(id),
  });

  useEffect(() => {
    if (submission) {
      const latestFeedback = submission.feedbacks && submission.feedbacks.length > 0 ? submission.feedbacks[0] : null;
      setReviewForm({
        status: submission.status,
        score: submission.score !== null ? parseFloat(submission.score) : parseFloat(submission.max_score),
        rating: latestFeedback?.rating || 5,
        feedback_text: latestFeedback?.feedback_text || "",
        suggested_changes: latestFeedback?.suggested_changes || "",
      });
    }
  }, [submission]);

  // Mutation
  const reviewMutation = useMutation({
    mutationFn: (payload: any) => adminApi.reviewSubmission(id!, payload),
    onSuccess: () => {
      success("Review Recorded", "Grading evaluation and feedback saved successfully.");
      queryClient.invalidateQueries({ queryKey: ["admin-submission-detail", id] });
      queryClient.invalidateQueries({ queryKey: ["admin-project-submissions"] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.message || err.response?.data?.error?.message || "Failed to save review";
      toastError("Review Failed", msg);
    },
  });

  if (isLoading) {
    return <LoadingState message="Loading submission deliverables..." />;
  }

  if (isError || !submission) {
    return (
      <ErrorState
        title="Submission Not Found"
        message="Unable to locate project submission record."
        onRetry={() => refetch()}
      />
    );
  }

  const maxScoreNum = parseFloat(submission.max_score) || 100;

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate("/admin/projects")}>
          <ArrowLeft className="h-4 w-4 mr-1.5" />
          Back to Project Submissions
        </Button>
      </div>

      {/* Header Info */}
      <Card className="p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="text-2xl font-bold text-white">{submission.project_title}</h1>
              <Badge
                variant={
                  submission.status === "APPROVED"
                    ? "emerald"
                    : submission.status === "CHANGES_REQUESTED"
                    ? "amber"
                    : submission.status === "REJECTED"
                    ? "rose"
                    : "indigo"
                }
              >
                {submission.status.replace("_", " ")}
              </Badge>
            </div>

            <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-slate-400">
              <span className="font-semibold text-slate-200">Student: {submission.student_name}</span>
              <span>•</span>
              <span className="font-mono text-slate-300">ID: {submission.student_id_number}</span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" />
                Submitted: {new Date(submission.submitted_at).toLocaleString()}
              </span>
            </div>
          </div>

          {/* External links */}
          <div className="flex flex-wrap items-center gap-3">
            {submission.github_repository_url && (
              <a
                href={submission.github_repository_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="secondary" size="sm">
                  <Github className="h-4 w-4 mr-1.5" />
                  GitHub Repository
                  <ExternalLink className="h-3.5 w-3.5 ml-1.5 text-slate-400" />
                </Button>
              </a>
            )}
            {submission.live_demo_url && (
              <a
                href={submission.live_demo_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="secondary" size="sm">
                  <Sparkles className="h-4 w-4 mr-1.5 text-brand-400" />
                  Live Demo
                  <ExternalLink className="h-3.5 w-3.5 ml-1.5 text-slate-400" />
                </Button>
              </a>
            )}
          </div>
        </div>
      </Card>

      {/* Main Grid: Left Deliverables, Right Review Form */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left: Deliverables & Files (7 cols) */}
        <div className="space-y-6 lg:col-span-7">
          {/* Student Notes */}
          <Card className="p-6">
            <h2 className="text-base font-semibold text-white mb-2 flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-brand-400" />
              Student Notes & Submission Summary
            </h2>
            <div className="rounded-xl bg-surface-900/60 p-4 text-sm text-slate-300 whitespace-pre-wrap leading-relaxed border border-surface-800">
              {submission.notes || "No additional comments submitted by the student."}
            </div>
          </Card>

          {/* Attached Deliverable Files */}
          <Card className="p-6">
            <h2 className="text-base font-semibold text-white mb-3 flex items-center gap-2">
              <FileCode className="h-4 w-4 text-indigo-400" />
              Attached Deliverable Files ({submission.files?.length || 0})
            </h2>

            {!submission.files || submission.files.length === 0 ? (
              <div className="rounded-xl border border-surface-800 bg-surface-900/40 p-6 text-center text-sm text-slate-400">
                No uploaded files attached (Repository link was provided).
              </div>
            ) : (
              <div className="divide-y divide-surface-800 rounded-xl border border-surface-800 bg-surface-900/50 overflow-hidden">
                {submission.files.map((f) => (
                  <div key={f.id} className="p-4 flex items-center justify-between">
                    <div>
                      <div className="font-medium text-slate-200 text-sm">{f.file_name}</div>
                      <div className="text-xs text-slate-400 mt-0.5">
                        {(f.file_size_bytes / 1024).toFixed(1)} KB • {f.mime_type || "Document"}
                      </div>
                    </div>

                    <a href={f.download_url} download target="_blank" rel="noopener noreferrer">
                      <Button size="sm" variant="secondary">
                        <Download className="h-3.5 w-3.5 mr-1.5" />
                        Download
                      </Button>
                    </a>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right: Review & Grading Form (5 cols) */}
        <div className="space-y-6 lg:col-span-5">
          <Card className="p-6">
            <h2 className="text-base font-semibold text-white mb-1">Grading & Review Rubric</h2>
            <p className="text-xs text-slate-400 mb-6">
              Evaluate submission code quality, allocate points, and specify corrective actions.
            </p>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                reviewMutation.mutate({
                  status: reviewForm.status,
                  score: Number(reviewForm.score),
                  rating: Number(reviewForm.rating),
                  feedback_text: reviewForm.feedback_text,
                  suggested_changes: reviewForm.suggested_changes,
                });
              }}
              className="space-y-4"
            >
              <FormField label="Review Decision Status" required>
                <Select
                  value={reviewForm.status}
                  onChange={(e) => setReviewForm({ ...reviewForm, status: e.target.value })}
                  required
                >
                  <option value="UNDER_REVIEW">Under Review</option>
                  <option value="APPROVED">Approved (Pass)</option>
                  <option value="CHANGES_REQUESTED">Changes Requested (Resubmit)</option>
                  <option value="REJECTED">Rejected (Fail)</option>
                </Select>
              </FormField>

              <div className="grid grid-cols-2 gap-4">
                <FormField label={`Score (Max: ${maxScoreNum} pts)`} required>
                  <Input
                    type="number"
                    min={0}
                    max={maxScoreNum}
                    value={reviewForm.score}
                    onChange={(e) => setReviewForm({ ...reviewForm, score: Number(e.target.value) })}
                    required
                  />
                </FormField>

                <FormField label="Quality Rating (1 - 5 Stars)">
                  <Select
                    value={reviewForm.rating}
                    onChange={(e) => setReviewForm({ ...reviewForm, rating: Number(e.target.value) })}
                  >
                    <option value={5}>5 Stars (Exceptional)</option>
                    <option value={4}>4 Stars (Good)</option>
                    <option value={3}>3 Stars (Acceptable)</option>
                    <option value={2}>2 Stars (Needs Work)</option>
                    <option value={1}>1 Star (Unsatisfactory)</option>
                  </Select>
                </FormField>
              </div>

              <FormField label="Qualitative Feedback" required>
                <Textarea
                  rows={4}
                  placeholder="Commendations, architecture observations, code quality notes..."
                  value={reviewForm.feedback_text}
                  onChange={(e) => setReviewForm({ ...reviewForm, feedback_text: e.target.value })}
                  required
                />
              </FormField>

              <FormField label="Suggested Changes / Remediation (Optional)">
                <Textarea
                  rows={3}
                  placeholder="Specific items the student must revise if resubmission is needed..."
                  value={reviewForm.suggested_changes}
                  onChange={(e) =>
                    setReviewForm({ ...reviewForm, suggested_changes: e.target.value })
                  }
                />
              </FormField>

              <div className="pt-4 border-t border-surface-800">
                <Button type="submit" className="w-full" isLoading={reviewMutation.isPending}>
                  Save Evaluation & Feedback
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
};
