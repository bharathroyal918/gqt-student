import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  CalendarCheck,
  Plus,
  Edit2,
  Trash2,
  Calendar,
  Code2,
} from "lucide-react";
import { adminApi } from "../../api/adminApi";
import { TaskItem, CodingQuestionListItem } from "../../types/admin";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { StatusDot } from "../../components/ui/StatusDot";
import { DataTable, Column } from "../../components/ui/DataTable";
import { SearchInput } from "../../components/ui/SearchInput";
import { Modal } from "../../components/ui/Modal";
import { FormField, Input, Textarea, Select, Checkbox } from "../../components/ui/Form";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { useToast } from "../../context/ToastContext";

export const TasksPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState("");

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<TaskItem | null>(null);
  const [deletingTask, setDeletingTask] = useState<TaskItem | null>(null);

  const [formData, setFormData] = useState({
    title: "",
    description: "",
    scheduled_date: new Date().toISOString().split("T")[0],
    question_id: "" as string,
    points: 20,
    is_active: true,
  });

  // Queries
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["admin-tasks", { page, pageSize, search }],
    queryFn: () =>
      adminApi.getTasks({
        page,
        page_size: pageSize,
        search: search.trim() || undefined,
      }),
  });

  const { data: questionsData } = useQuery({
    queryKey: ["admin-all-questions-select"],
    queryFn: () => adminApi.getQuestions({ page_size: 100 }),
    enabled: isCreateModalOpen || Boolean(editingTask),
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: adminApi.createTask,
    onSuccess: (task) => {
      success("Daily Task Created", `Task '${task.title}' scheduled for ${task.scheduled_date}.`);
      setIsCreateModalOpen(false);
      resetForm();
      queryClient.invalidateQueries({ queryKey: ["admin-tasks"] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.message || err.response?.data?.error?.message || "Failed to create task";
      toastError("Creation Failed", msg);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<TaskItem> }) =>
      adminApi.updateTask(id, payload),
    onSuccess: () => {
      success("Task Updated", "Changes saved.");
      setEditingTask(null);
      queryClient.invalidateQueries({ queryKey: ["admin-tasks"] });
    },
    onError: () => toastError("Update Failed", "Could not update task."),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminApi.deleteTask(id),
    onSuccess: () => {
      success("Task Deleted", "Daily task removed.");
      setDeletingTask(null);
      queryClient.invalidateQueries({ queryKey: ["admin-tasks"] });
    },
    onError: () => toastError("Delete Failed", "Could not remove task."),
  });

  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      scheduled_date: new Date().toISOString().split("T")[0],
      question_id: "",
      points: 20,
      is_active: true,
    });
  };

  const handleOpenEdit = (task: TaskItem) => {
    setEditingTask(task);
    setFormData({
      title: task.title,
      description: task.description,
      scheduled_date: task.scheduled_date,
      question_id: task.question_id || "",
      points: parseFloat(task.points) || 20,
      is_active: task.is_active,
    });
  };

  const columns: Column<TaskItem>[] = [
    {
      key: "title",
      header: "Daily Task",
      cell: (row) => (
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-500/10 text-brand-400 border border-brand-500/20">
            <CalendarCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="font-semibold text-slate-900 dark:text-white">{row.title}</div>
            <div className="text-xs text-slate-500 dark:text-slate-400 line-clamp-1 mt-0.5">{row.description}</div>
          </div>
        </div>
      ),
    },
    {
      key: "date",
      header: "Scheduled Date",
      cell: (row) => (
        <div className="flex items-center gap-1.5 text-xs text-slate-700 dark:text-slate-300">
          <Calendar className="h-3.5 w-3.5 text-indigo-500" />
          <span>{row.scheduled_date}</span>
        </div>
      ),
    },
    {
      key: "linkage",
      header: "Linked Coding Problem",
      cell: (row) => (
        <div className="text-xs">
          {row.question_title ? (
            <span className="flex items-center gap-1 text-brand-600 dark:text-brand-300 font-medium">
              <Code2 className="h-3.5 w-3.5 text-brand-500" />
              {row.question_title}
            </span>
          ) : (
            <span className="text-slate-400 dark:text-slate-500">Standalone Practice</span>
          )}
        </div>
      ),
    },
    {
      key: "points",
      header: "Points",
      cell: (row) => <span className="font-semibold text-amber-500 text-xs">{row.points} pts</span>,
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => (
        <div className="flex items-center gap-1.5">
          <StatusDot status={row.is_active ? "online" : "offline"} pulse={row.is_active} />
          <Badge variant={row.is_active ? "emerald" : "slate"} size="sm">
            {row.is_active ? "Active" : "Archived"}
          </Badge>
        </div>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      cell: (row) => (
        <div className="flex items-center justify-end gap-1.5">
          <Button size="sm" variant="ghost" onClick={() => handleOpenEdit(row)} title="Edit Task">
            <Edit2 className="h-4 w-4 text-slate-400 hover:text-brand-500" />
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setDeletingTask(row)} title="Delete Task">
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
            Daily Practice Tasks
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Schedule calendar-driven daily practice problems to drive student learning consistency and streaks.
          </p>
        </div>

        <Button
          onClick={() => {
            resetForm();
            setIsCreateModalOpen(true);
          }}
        >
          <Plus className="h-4 w-4 mr-2" />
          New Daily Task
        </Button>
      </div>

      {/* Search Bar */}
      <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900/60 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="w-full sm:max-w-xs">
          <SearchInput
            value={search}
            onChange={(val) => {
              setSearch(val);
              setPage(1);
            }}
            placeholder="Search daily tasks..."
          />
        </div>
      </div>

      {/* Table */}
      <DataTable
        data={data?.data || []}
        columns={columns}
        isLoading={isLoading}
        isError={isError}
        errorMessage="Unable to load tasks."
        onRetry={() => refetch()}
        emptyTitle="No Daily Tasks Scheduled"
        emptyDescription="Schedule daily practice challenges to help students earn daily streak bonuses."
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

      {/* Create Task Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Schedule Daily Task"
        description="Configure target challenge date, point rewards, and link to a coding assessment."
        size="md"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createMutation.mutate({
              title: formData.title,
              description: formData.description,
              scheduled_date: formData.scheduled_date,
              question_id: formData.question_id || null,
              points: Number(formData.points),
              is_active: formData.is_active,
            });
          }}
          className="space-y-4"
        >
          <FormField label="Task Title" required>
            <Input
              placeholder="e.g. Day 14: Dynamic Programming Primer"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              required
            />
          </FormField>

          <FormField label="Description">
            <Textarea
              rows={3}
              placeholder="Brief context and daily objective for students..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField label="Scheduled Date" required>
              <Input
                type="date"
                value={formData.scheduled_date}
                onChange={(e) => setFormData({ ...formData, scheduled_date: e.target.value })}
                required
              />
            </FormField>

            <FormField label="Award Points" required>
              <Input
                type="number"
                value={formData.points}
                onChange={(e) => setFormData({ ...formData, points: Number(e.target.value) })}
                required
              />
            </FormField>
          </div>

          <FormField label="Link to Coding Problem (Optional)">
            <Select
              value={formData.question_id}
              onChange={(e) => setFormData({ ...formData, question_id: e.target.value })}
            >
              <option value="">None (Self-study)</option>
              {questionsData?.data.map((q: CodingQuestionListItem) => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.difficulty} - {q.points}pts)
                </option>
              ))}
            </Select>
          </FormField>

          <Checkbox
            label="Active and Visible to Students"
            checked={formData.is_active}
            onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
          />

          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-surface-800">
            <Button variant="secondary" type="button" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createMutation.isPending}>
              Schedule Task
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Task Modal */}
      <Modal
        isOpen={Boolean(editingTask)}
        onClose={() => setEditingTask(null)}
        title="Edit Daily Task"
        description="Update practice schedule, points, or linked problem."
        size="md"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!editingTask) return;
            updateMutation.mutate({
              id: editingTask.id,
              payload: {
                title: formData.title,
                description: formData.description,
                scheduled_date: formData.scheduled_date,
                question_id: formData.question_id || null,
                points: String(formData.points),
                is_active: formData.is_active,
              },
            });
          }}
          className="space-y-4"
        >
          <FormField label="Task Title" required>
            <Input
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              required
            />
          </FormField>

          <FormField label="Description">
            <Textarea
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField label="Scheduled Date" required>
              <Input
                type="date"
                value={formData.scheduled_date}
                onChange={(e) => setFormData({ ...formData, scheduled_date: e.target.value })}
                required
              />
            </FormField>

            <FormField label="Award Points" required>
              <Input
                type="number"
                value={formData.points}
                onChange={(e) => setFormData({ ...formData, points: Number(e.target.value) })}
                required
              />
            </FormField>
          </div>

          <FormField label="Link to Coding Problem (Optional)">
            <Select
              value={formData.question_id}
              onChange={(e) => setFormData({ ...formData, question_id: e.target.value })}
            >
              <option value="">None (Self-study)</option>
              {questionsData?.data.map((q: CodingQuestionListItem) => (
                <option key={q.id} value={q.id}>
                  {q.title} ({q.difficulty} - {q.points}pts)
                </option>
              ))}
            </Select>
          </FormField>

          <Checkbox
            label="Active"
            checked={formData.is_active}
            onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
          />

          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-surface-800">
            <Button variant="secondary" type="button" onClick={() => setEditingTask(null)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={updateMutation.isPending}>
              Save Changes
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={Boolean(deletingTask)}
        onClose={() => setDeletingTask(null)}
        onConfirm={() => deletingTask && deleteMutation.mutate(deletingTask.id)}
        isLoading={deleteMutation.isPending}
        title="Delete Daily Task?"
        message={`Are you sure you want to remove '${deletingTask?.title}'?`}
        confirmText="Delete Task"
        variant="danger"
      />
    </div>
  );
};
