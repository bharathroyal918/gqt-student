import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  Code2,
  Plus,
  Eye,
  Trash2,
} from "lucide-react";
import { adminApi } from "../../api/adminApi";
import { CodingQuestionListItem, ModuleItem } from "../../types/admin";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { StatusDot } from "../../components/ui/StatusDot";
import { DataTable, Column } from "../../components/ui/DataTable";
import { SearchInput } from "../../components/ui/SearchInput";
import { Modal } from "../../components/ui/Modal";
import { FormField, Input, Textarea, Select, Checkbox } from "../../components/ui/Form";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { useToast } from "../../context/ToastContext";

export const AssignmentsPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState("");
  const [difficultyFilter, setDifficultyFilter] = useState("");

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [deletingQuestion, setDeletingQuestion] = useState<CodingQuestionListItem | null>(null);

  const [formData, setFormData] = useState({
    module_id: "",
    title: "",
    slug: "",
    difficulty: "EASY" as "EASY" | "MEDIUM" | "HARD",
    problem_statement: "",
    points: 15,
    time_limit_seconds: 2,
    memory_limit_mb: 256,
    allowed_languages: ["PYTHON", "JAVASCRIPT", "JAVA", "CPP"],
  });

  // Queries
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["admin-questions", { page, pageSize, search, difficultyFilter }],
    queryFn: () =>
      adminApi.getQuestions({
        page,
        page_size: pageSize,
        search: search.trim() || undefined,
        difficulty: difficultyFilter || undefined,
      }),
  });

  const { data: modulesData } = useQuery({
    queryKey: ["admin-all-modules-select"],
    queryFn: () => adminApi.getModules({ page_size: 100 }),
    enabled: isCreateModalOpen,
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: adminApi.createQuestion,
    onSuccess: (q) => {
      success("Question Created", `Challenge '${q.title}' has been registered.`);
      setIsCreateModalOpen(false);
      resetForm();
      queryClient.invalidateQueries({ queryKey: ["admin-questions"] });
      queryClient.invalidateQueries({ queryKey: ["admin-dashboard-stats"] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.message || err.response?.data?.error?.message || "Failed to create question";
      toastError("Creation Failed", msg);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminApi.archiveQuestion(id),
    onSuccess: () => {
      success("Question Deleted", "Coding question removed.");
      setDeletingQuestion(null);
      queryClient.invalidateQueries({ queryKey: ["admin-questions"] });
    },
    onError: () => toastError("Delete Failed", "Could not remove question."),
  });

  const resetForm = () => {
    setFormData({
      module_id: modulesData?.data[0]?.id || "",
      title: "",
      slug: "",
      difficulty: "EASY",
      problem_statement: "",
      points: 15,
      time_limit_seconds: 2,
      memory_limit_mb: 256,
      allowed_languages: ["PYTHON", "JAVASCRIPT", "JAVA", "CPP"],
    });
  };

  const handleLanguageToggle = (lang: string) => {
    setFormData((prev) => ({
      ...prev,
      allowed_languages: prev.allowed_languages.includes(lang)
        ? prev.allowed_languages.filter((l) => l !== lang)
        : [...prev.allowed_languages, lang],
    }));
  };

  const columns: Column<CodingQuestionListItem>[] = [
    {
      key: "title",
      header: "Question & Module",
      cell: (row) => (
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-500/10 text-brand-400 border border-brand-500/20">
            <Code2 className="h-5 w-5" />
          </div>
          <div>
            <button
              onClick={() => navigate(`/admin/assignments/${row.id}`)}
              className="text-left font-semibold text-slate-900 dark:text-white hover:text-brand-600 dark:hover:text-brand-400 transition-colors"
            >
              {row.title}
            </button>
            <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              <span>{row.module_title}</span>
              <span>•</span>
              <span className="font-mono text-slate-500 dark:text-slate-400">{row.slug}</span>
            </div>
          </div>
        </div>
      ),
    },
    {
      key: "difficulty",
      header: "Difficulty & Marks",
      cell: (row) => {
        const variant =
          row.difficulty === "EASY" ? "emerald" : row.difficulty === "MEDIUM" ? "amber" : "rose";
        return (
          <div className="space-y-1">
            <Badge variant={variant} size="sm">
              {row.difficulty}
            </Badge>
            <div className="text-xs font-semibold text-amber-500">{row.points} pts</div>
          </div>
        );
      },
    },
    {
      key: "testcases",
      header: "Test Cases",
      cell: (row) => (
        <div className="text-xs text-slate-700 dark:text-slate-300">
          <span className="font-semibold text-slate-900 dark:text-white">{row.test_cases_count}</span> test cases
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => (
        <div className="flex items-center gap-1.5">
          <StatusDot status={row.is_active ? "online" : "offline"} pulse={row.is_active} />
          <span className="text-xs text-slate-700 dark:text-slate-300">{row.is_active ? "Active" : "Archived"}</span>
        </div>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      cell: (row) => (
        <div className="flex items-center justify-end gap-1.5">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => navigate(`/admin/assignments/${row.id}`)}
            title="View Details & Test Cases"
          >
            <Eye className="h-4 w-4 text-slate-400 hover:text-slate-900 dark:hover:text-white" />
          </Button>

          <Button
            size="sm"
            variant="ghost"
            onClick={() => setDeletingQuestion(row)}
            title="Delete Question"
          >
            <Trash2 className="h-4 w-4 text-rose-500 hover:text-rose-600" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            Coding Assignments & Problems
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Configure algorithmic questions, test suites, constraints, and sandbox execution parameters.
          </p>
        </div>

        <Button
          onClick={() => {
            resetForm();
            setIsCreateModalOpen(true);
          }}
        >
          <Plus className="h-4 w-4 mr-2" />
          New Problem
        </Button>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900/60 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="w-full sm:max-w-xs">
          <SearchInput
            value={search}
            onChange={(val) => {
              setSearch(val);
              setPage(1);
            }}
            placeholder="Search problems..."
          />
        </div>

        <div className="flex items-center gap-3">
          <div className="w-36">
            <Select
              value={difficultyFilter}
              onChange={(e) => {
                setDifficultyFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All Difficulties</option>
              <option value="EASY">Easy</option>
              <option value="MEDIUM">Medium</option>
              <option value="HARD">Hard</option>
            </Select>
          </div>

          {(search || difficultyFilter) && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setSearch("");
                setDifficultyFilter("");
                setPage(1);
              }}
            >
              Clear
            </Button>
          )}
        </div>
      </div>

      {/* Table */}
      <DataTable
        data={data?.data || []}
        columns={columns}
        isLoading={isLoading}
        isError={isError}
        errorMessage="Unable to load questions. Check backend connectivity."
        onRetry={() => refetch()}
        emptyTitle="No Coding Questions Found"
        emptyDescription="Create your first coding assessment problem to start evaluating student code."
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

      {/* Create Problem Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create Coding Question"
        description="Configure problem statement, execution constraints, and attach to a module."
        size="lg"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createMutation.mutate({
              module_id: formData.module_id,
              title: formData.title,
              slug: formData.slug || undefined,
              difficulty: formData.difficulty,
              problem_statement: formData.problem_statement,
              points: Number(formData.points),
              time_limit_seconds: Number(formData.time_limit_seconds),
              memory_limit_mb: Number(formData.memory_limit_mb),
              allowed_languages: formData.allowed_languages,
            });
          }}
          className="space-y-4"
        >
          <FormField label="Assigned Module" required>
            <Select
              value={formData.module_id}
              onChange={(e) => setFormData({ ...formData, module_id: e.target.value })}
              required
            >
              <option value="">Select a module...</option>
              {modulesData?.data.map((m: ModuleItem) => (
                <option key={m.id} value={m.id}>
                  {m.title}
                </option>
              ))}
            </Select>
          </FormField>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FormField label="Problem Title" required>
              <Input
                placeholder="e.g. Two Sum Optimal Solution"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                required
              />
            </FormField>

            <FormField label="Slug (Optional)">
              <Input
                placeholder="e.g. two-sum"
                value={formData.slug}
                onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
              />
            </FormField>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <FormField label="Difficulty" required>
              <Select
                value={formData.difficulty}
                onChange={(e) => {
                  const diff = e.target.value as "EASY" | "MEDIUM" | "HARD";
                  const pts = diff === "EASY" ? 15 : diff === "MEDIUM" ? 25 : 30;
                  setFormData({ ...formData, difficulty: diff, points: pts });
                }}
              >
                <option value="EASY">Easy (15 pts)</option>
                <option value="MEDIUM">Medium (25 pts)</option>
                <option value="HARD">Hard (30 pts)</option>
              </Select>
            </FormField>

            <FormField label="Marks / Points" required>
              <Input
                type="number"
                value={formData.points}
                onChange={(e) => setFormData({ ...formData, points: Number(e.target.value) })}
                required
              />
            </FormField>

            <FormField label="Time Limit (sec)">
              <Input
                type="number"
                value={formData.time_limit_seconds}
                onChange={(e) => setFormData({ ...formData, time_limit_seconds: Number(e.target.value) })}
              />
            </FormField>
          </div>

          <FormField label="Problem Statement & Constraints" required>
            <Textarea
              rows={6}
              placeholder="Describe the problem, input format, output format, and constraints..."
              value={formData.problem_statement}
              onChange={(e) => setFormData({ ...formData, problem_statement: e.target.value })}
              required
            />
          </FormField>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-2">
              Allowed Programming Languages
            </label>
            <div className="flex flex-wrap gap-4">
              {["PYTHON", "JAVASCRIPT", "JAVA", "CPP"].map((lang) => (
                <Checkbox
                  key={lang}
                  label={lang}
                  checked={formData.allowed_languages.includes(lang)}
                  onChange={() => handleLanguageToggle(lang)}
                />
              ))}
            </div>
          </div>

          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-surface-800">
            <Button variant="secondary" type="button" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createMutation.isPending}>
              Create Problem
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Question Confirmation */}
      <ConfirmDialog
        isOpen={Boolean(deletingQuestion)}
        onClose={() => setDeletingQuestion(null)}
        onConfirm={() => deletingQuestion && deleteMutation.mutate(deletingQuestion.id)}
        isLoading={deleteMutation.isPending}
        title="Archive Question?"
        message={`Are you sure you want to remove '${deletingQuestion?.title}'? Existing student submissions will be retained.`}
        confirmText="Archive Question"
        variant="danger"
      />
    </div>
  );
};
