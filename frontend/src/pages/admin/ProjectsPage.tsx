import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  Plus,
  Github,
  ExternalLink,
  FileCheck,
} from "lucide-react";
import { adminApi } from "../../api/adminApi";
import { ProjectItem, ProjectSubmissionItem, CourseItem } from "../../types/admin";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { DataTable, Column } from "../../components/ui/DataTable";
import { Modal } from "../../components/ui/Modal";
import { FormField, Input, Textarea, Select, Checkbox } from "../../components/ui/Form";
import { useToast } from "../../context/ToastContext";

export const ProjectsPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [activeTab, setActiveTab] = useState<"submissions" | "projects">("submissions");

  // Submissions Tab State
  const [subPage, setSubPage] = useState(1);
  const [subPageSize, setSubPageSize] = useState(10);
  const [statusFilter, setStatusFilter] = useState("");

  // Projects Tab State
  const [projPage, setProjPage] = useState(1);
  const [projPageSize, setProjPageSize] = useState(10);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const [projectForm, setProjectForm] = useState({
    title: "",
    slug: "",
    description: "",
    deliverables_instructions: "",
    course_id: "",
    max_score: 100,
    due_date: "",
    is_active: true,
  });

  // Queries
  const {
    data: submissionsData,
    isLoading: isSubLoading,
    isError: isSubError,
    refetch: refetchSubmissions,
  } = useQuery({
    queryKey: ["admin-project-submissions", { subPage, subPageSize, statusFilter }],
    queryFn: () =>
      adminApi.getSubmissions({
        page: subPage,
        page_size: subPageSize,
        status: statusFilter || undefined,
      }),
    enabled: activeTab === "submissions",
  });

  const {
    data: projectsData,
    isLoading: isProjLoading,
    isError: isProjError,
    refetch: refetchProjects,
  } = useQuery({
    queryKey: ["admin-projects-list", { projPage, projPageSize }],
    queryFn: () =>
      adminApi.getProjects({
        page: projPage,
        page_size: projPageSize,
      }),
    enabled: activeTab === "projects" || isCreateModalOpen,
  });

  const { data: coursesData } = useQuery({
    queryKey: ["admin-all-courses-projects"],
    queryFn: () => adminApi.getCourses({ page_size: 100 }),
    enabled: isCreateModalOpen,
  });

  // Mutations
  const createProjectMutation = useMutation({
    mutationFn: adminApi.createProject,
    onSuccess: (p) => {
      success("Project Created", `Capstone '${p.title}' is active.`);
      setIsCreateModalOpen(false);
      resetProjectForm();
      queryClient.invalidateQueries({ queryKey: ["admin-projects-list"] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.message || err.response?.data?.error?.message || "Failed to create project";
      toastError("Creation Failed", msg);
    },
  });

  const resetProjectForm = () => {
    setProjectForm({
      title: "",
      slug: "",
      description: "",
      deliverables_instructions: "",
      course_id: "",
      max_score: 100,
      due_date: "",
      is_active: true,
    });
  };

  // Submissions Columns
  const subColumns: Column<ProjectSubmissionItem>[] = [
    {
      key: "student",
      header: "Student & ID",
      cell: (row) => (
        <div>
          <div className="font-semibold text-slate-900 dark:text-white">{row.student_name}</div>
          <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            <span className="font-mono text-slate-600 dark:text-slate-300">{row.student_id_number}</span>
          </div>
        </div>
      ),
    },
    {
      key: "project",
      header: "Project Title",
      cell: (row) => (
        <div>
          <div className="font-medium text-slate-800 dark:text-slate-200">{row.project_title}</div>
          {row.github_repository_url && (
            <a
              href={row.github_repository_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-brand-600 dark:text-brand-400 hover:text-brand-700 mt-0.5"
            >
              <Github className="h-3 w-3" />
              Repository
              <ExternalLink className="h-2.5 w-2.5" />
            </a>
          )}
        </div>
      ),
    },
    {
      key: "status",
      header: "Review Status",
      cell: (row) => {
        const variant =
          row.status === "APPROVED"
            ? "emerald"
            : row.status === "CHANGES_REQUESTED"
            ? "amber"
            : row.status === "REJECTED"
            ? "rose"
            : "indigo";
        return (
          <Badge variant={variant} size="sm">
            {row.status.replace("_", " ")}
          </Badge>
        );
      },
    },
    {
      key: "score",
      header: "Score & Feedback",
      cell: (row) => (
        <div className="text-xs">
          {row.score !== null ? (
            <div className="font-bold text-amber-500">
              {row.score} / {row.max_score} pts
            </div>
          ) : (
            <span className="text-slate-400 dark:text-slate-500">Ungraded</span>
          )}
          {row.feedbacks && row.feedbacks.length > 0 && (
            <div className="text-slate-500 dark:text-slate-400 truncate max-w-[180px] mt-0.5">
              {row.feedbacks[0].feedback_text}
            </div>
          )}
        </div>
      ),
    },
    {
      key: "actions",
      header: "Action",
      align: "right",
      cell: (row) => (
        <Button
          size="sm"
          onClick={() => navigate(`/admin/projects/submissions/${row.id}`)}
          className="shadow-sm"
        >
          <FileCheck className="h-3.5 w-3.5 mr-1" />
          Review & Grade
        </Button>
      ),
    },
  ];

  // Project List Columns
  const projColumns: Column<ProjectItem>[] = [
    {
      key: "title",
      header: "Capstone Project",
      cell: (row) => (
        <div>
          <div className="font-semibold text-slate-900 dark:text-white">{row.title}</div>
          <div className="text-xs text-slate-500 dark:text-slate-400 line-clamp-1">{row.description}</div>
        </div>
      ),
    },
    {
      key: "course",
      header: "Course Track",
      cell: (row) => (
        <div className="text-xs text-slate-600 dark:text-slate-300">{row.course_title || "General / Platform-wide"}</div>
      ),
    },
    {
      key: "score",
      header: "Max Score",
      cell: (row) => <span className="font-bold text-amber-500 text-xs">{row.max_score} pts</span>,
    },
    {
      key: "submissions",
      header: "Total Submissions",
      cell: (row) => (
        <Badge variant="indigo" size="sm">
          {row.submissions_count} submitted
        </Badge>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            Capstone Projects & Reviews
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Grade student capstone repository submissions, examine code deliverables, and post qualitative feedback.
          </p>
        </div>

        <Button onClick={() => { resetProjectForm(); setIsCreateModalOpen(true); }}>
          <Plus className="h-4 w-4 mr-2" />
          New Capstone
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 dark:border-surface-800">
        <button
          onClick={() => setActiveTab("submissions")}
          className={`px-5 py-3 text-sm font-medium border-b-2 transition-all ${
            activeTab === "submissions"
              ? "border-brand-500 text-brand-600 dark:text-brand-400 font-semibold"
              : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
          }`}
        >
          Submissions Queue
        </button>
        <button
          onClick={() => setActiveTab("projects")}
          className={`px-5 py-3 text-sm font-medium border-b-2 transition-all ${
            activeTab === "projects"
              ? "border-brand-500 text-brand-600 dark:text-brand-400 font-semibold"
              : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
          }`}
        >
          Project Catalog
        </button>
      </div>

      {/* Tab 1: Submissions */}
      {activeTab === "submissions" && (
        <div className="space-y-4">
          {/* Status Filter */}
          <div className="flex items-center gap-3">
            <div className="w-48">
              <Select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setSubPage(1);
                }}
              >
                <option value="">All Review States</option>
                <option value="SUBMITTED">SUBMITTED</option>
                <option value="UNDER_REVIEW">UNDER REVIEW</option>
                <option value="APPROVED">APPROVED</option>
                <option value="CHANGES_REQUESTED">CHANGES REQUESTED</option>
                <option value="REJECTED">REJECTED</option>
              </Select>
            </div>
            {statusFilter && (
              <Button variant="secondary" size="sm" onClick={() => setStatusFilter("")}>
                Clear Filter
              </Button>
            )}
          </div>

          <DataTable
            data={submissionsData?.data || []}
            columns={subColumns}
            isLoading={isSubLoading}
            isError={isSubError}
            errorMessage="Unable to load project submissions."
            onRetry={() => refetchSubmissions()}
            emptyTitle="No Submissions in Queue"
            emptyDescription="No student capstone project submissions currently match your filter."
            pagination={
              submissionsData?.meta?.pagination
                ? {
                    page: submissionsData.meta.pagination.page,
                    pageSize: submissionsData.meta.pagination.page_size,
                    totalRecords: submissionsData.meta.pagination.total_records,
                    totalPages: submissionsData.meta.pagination.total_pages,
                    onPageChange: (p) => setSubPage(p),
                    onPageSizeChange: (s) => {
                      setSubPageSize(s);
                      setSubPage(1);
                    },
                  }
                : undefined
            }
          />
        </div>
      )}

      {/* Tab 2: Projects Catalog */}
      {activeTab === "projects" && (
        <div className="space-y-4">
          <DataTable
            data={projectsData?.data || []}
            columns={projColumns}
            isLoading={isProjLoading}
            isError={isProjError}
            errorMessage="Unable to load project catalog."
            onRetry={() => refetchProjects()}
            emptyTitle="No Capstone Projects"
            emptyDescription="Create a capstone project definition to accept student git submissions."
            pagination={
              projectsData?.meta?.pagination
                ? {
                    page: projectsData.meta.pagination.page,
                    pageSize: projectsData.meta.pagination.page_size,
                    totalRecords: projectsData.meta.pagination.total_records,
                    totalPages: projectsData.meta.pagination.total_pages,
                    onPageChange: (p) => setProjPage(p),
                    onPageSizeChange: (s) => {
                      setProjPageSize(s);
                      setProjPage(1);
                    },
                  }
                : undefined
            }
          />
        </div>
      )}

      {/* Create Project Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Define Capstone Project"
        description="Configure deliverables requirements, grading rubric maximum, and optional course linkage."
        size="lg"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createProjectMutation.mutate({
              title: projectForm.title,
              slug: projectForm.slug || undefined,
              description: projectForm.description,
              deliverables_instructions: projectForm.deliverables_instructions,
              course_id: projectForm.course_id || null,
              max_score: Number(projectForm.max_score),
              due_date: projectForm.due_date || null,
              is_active: projectForm.is_active,
            });
          }}
          className="space-y-4"
        >
          <FormField label="Project Title" required>
            <Input
              placeholder="e.g. Distributed Task Scheduler with Redis & Celery"
              value={projectForm.title}
              onChange={(e) => setProjectForm({ ...projectForm, title: e.target.value })}
              required
            />
          </FormField>

          <FormField label="Assigned Course Track (Optional)">
            <Select
              value={projectForm.course_id}
              onChange={(e) => setProjectForm({ ...projectForm, course_id: e.target.value })}
            >
              <option value="">General (Cross-curriculum)</option>
              {coursesData?.data.map((c: CourseItem) => (
                <option key={c.id} value={c.id}>
                  {c.title}
                </option>
              ))}
            </Select>
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField label="Maximum Score (Points)" required>
              <Input
                type="number"
                value={projectForm.max_score}
                onChange={(e) => setProjectForm({ ...projectForm, max_score: Number(e.target.value) })}
                required
              />
            </FormField>

            <FormField label="Due Date (Optional)">
              <Input
                type="date"
                value={projectForm.due_date}
                onChange={(e) => setProjectForm({ ...projectForm, due_date: e.target.value })}
              />
            </FormField>
          </div>

          <FormField label="Project Overview & Problem Statement" required>
            <Textarea
              rows={4}
              placeholder="High level overview of the architectural requirements..."
              value={projectForm.description}
              onChange={(e) => setProjectForm({ ...projectForm, description: e.target.value })}
              required
            />
          </FormField>

          <FormField label="Deliverables Instructions & Rubric Guidelines" required>
            <Textarea
              rows={4}
              placeholder="Specify requirements for GitHub repo, README, Docker setup, and tests..."
              value={projectForm.deliverables_instructions}
              onChange={(e) =>
                setProjectForm({ ...projectForm, deliverables_instructions: e.target.value })
              }
              required
            />
          </FormField>

          <Checkbox
            label="Active (Students can submit files & repositories)"
            checked={projectForm.is_active}
            onChange={(e) => setProjectForm({ ...projectForm, is_active: e.target.checked })}
          />

          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-surface-800">
            <Button variant="secondary" type="button" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createProjectMutation.isPending}>
              Create Capstone Project
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
