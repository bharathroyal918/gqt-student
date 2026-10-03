import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  FolderGit2,
  Plus,
  ArrowRight,
  CheckCircle2,
  Clock,
  Award,
  Loader2,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { studentApi } from "../../api/studentApi";

export const StudentProjectsPage: React.FC = () => {
  const { data, isLoading } = useQuery({
    queryKey: ["student", "projects"],
    queryFn: () => studentApi.getProjects(),
  });

  const projects = data?.projects || [];
  const submittedCount = projects.filter((p) => p.has_submitted).length;
  const approvedCount = projects.filter((p) => p.status === "APPROVED").length;
  const totalScoreEarned = projects.reduce((acc, p) => acc + (p.score || 0), 0);

  const getStatusBadge = (status: string, score: number | null, maxScore: number) => {
    switch (status) {
      case "APPROVED":
        return <Badge variant="emerald" size="sm">✓ Approved ({score ?? maxScore}/{maxScore} pts)</Badge>;
      case "PENDING_REVIEW":
        return <Badge variant="amber" size="sm">⏳ In Review</Badge>;
      case "CHANGES_REQUESTED":
        return <Badge variant="rose" size="sm">⚠️ Changes Requested</Badge>;
      case "REJECTED":
        return <Badge variant="rose" size="sm">✕ Rejected</Badge>;
      default:
        return <Badge variant="slate" size="sm">Not Submitted ({maxScore} pts)</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            Capstone & Industry Projects
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Build production-grade systems, submit repository deliverables, and receive rigorous faculty evaluation.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-2xl border border-brand-500/20 bg-brand-500/10 px-4 py-2 text-brand-600 dark:text-brand-400 font-bold text-xs">
            <Award className="h-4 w-4 text-brand-500" />
            <span>{totalScoreEarned} Project Points</span>
          </div>

          <Link to="/projects/submit">
            <Button>
              <Plus className="h-4 w-4 mr-1.5" />
              Submit Deliverable
            </Button>
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="p-4 flex items-center gap-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20">
            <FolderGit2 className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Assigned Projects</p>
            <p className="text-xl font-bold text-slate-900 dark:text-white">{projects.length}</p>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
            <Clock className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Submitted for Review</p>
            <p className="text-xl font-bold text-slate-900 dark:text-white">{submittedCount}</p>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Approved & Graded</p>
            <p className="text-xl font-bold text-slate-900 dark:text-white">{approvedCount}</p>
          </div>
        </Card>
      </div>

      {/* Project Cards List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-24">
          <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
        </div>
      ) : projects.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20">
            <FolderGit2 className="h-7 w-7" />
          </div>
          <h3 className="mt-4 text-base font-bold text-slate-900 dark:text-white">
            No Capstone Projects Assigned Yet
          </h3>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
            Capstone projects will appear here as you advance through your enrolled curriculum modules.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {projects.map((project) => (
            <Card
              key={project.id}
              className="p-6 flex flex-col justify-between hover:border-brand-500/40 transition-all shadow-sm"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20">
                    <FolderGit2 className="h-5 w-5" />
                  </div>
                  {getStatusBadge(project.status, project.score, project.max_score)}
                </div>

                <h3 className="text-base font-bold text-slate-900 dark:text-white leading-snug">
                  {project.title}
                </h3>

                <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 leading-relaxed line-clamp-3">
                  {project.description || "Comprehensive capstone project assessing system design and engineering best practices."}
                </p>

                {project.due_date && (
                  <div className="mt-3 flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                    <Clock className="h-3.5 w-3.5 text-slate-400" />
                    <span>Due: {new Date(project.due_date).toLocaleDateString()}</span>
                  </div>
                )}
              </div>

              <div className="mt-6 pt-4 border-t border-slate-200 dark:border-surface-800 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                  {project.course_title ? `Course: ${project.course_title}` : "Curriculum Track"}
                </span>

                <Link to={`/projects/submit?projectId=${project.id}`}>
                  <Button size="sm" variant={project.has_submitted ? "secondary" : "primary"}>
                    <span>{project.has_submitted ? "Update / Resubmit" : "Submit Deliverable"}</span>
                    <ArrowRight className="h-3.5 w-3.5 ml-1" />
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
