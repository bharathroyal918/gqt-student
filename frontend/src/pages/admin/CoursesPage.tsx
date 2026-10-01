import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  BookOpen,
  Plus,
  Eye,
  Edit2,
  Trash2,
  CheckCircle2,
  XCircle,
  Layers,
  Users,
} from "lucide-react";
import { adminApi } from "../../api/adminApi";
import { CourseItem } from "../../types/admin";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { StatusDot } from "../../components/ui/StatusDot";
import { DataTable, Column } from "../../components/ui/DataTable";
import { SearchInput } from "../../components/ui/SearchInput";
import { Modal } from "../../components/ui/Modal";
import { FormField, Input, Textarea, Checkbox } from "../../components/ui/Form";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { useToast } from "../../context/ToastContext";

export const CoursesPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [search, setSearch] = useState("");

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingCourse, setEditingCourse] = useState<CourseItem | null>(null);
  const [deletingCourse, setDeletingCourse] = useState<CourseItem | null>(null);

  const [formData, setFormData] = useState({
    title: "",
    slug: "",
    description: "",
    thumbnail_url: "",
    is_published: true,
    order: 0,
  });

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["admin-courses", { page, pageSize, search }],
    queryFn: () =>
      adminApi.getCourses({
        page,
        page_size: pageSize,
        search: search.trim() || undefined,
      }),
  });

  const createMutation = useMutation({
    mutationFn: adminApi.createCourse,
    onSuccess: (course) => {
      success("Course Created", `Track '${course.title}' has been configured.`);
      setIsCreateModalOpen(false);
      resetForm();
      queryClient.invalidateQueries({ queryKey: ["admin-courses"] });
      queryClient.invalidateQueries({ queryKey: ["admin-dashboard-stats"] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.message || err.response?.data?.error?.message || "Failed to create course";
      toastError("Creation Failed", msg);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<CourseItem> }) =>
      adminApi.updateCourse(id, payload),
    onSuccess: () => {
      success("Course Updated", "Changes saved successfully.");
      setEditingCourse(null);
      queryClient.invalidateQueries({ queryKey: ["admin-courses"] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.message || err.response?.data?.error?.message || "Failed to update course";
      toastError("Update Failed", msg);
    },
  });

  const publishMutation = useMutation({
    mutationFn: ({ id, is_published }: { id: string; is_published: boolean }) =>
      adminApi.publishCourse(id, is_published),
    onSuccess: (res) => {
      success("Publication Updated", `Course is now ${res.is_published ? "Published" : "Unpublished"}.`);
      queryClient.invalidateQueries({ queryKey: ["admin-courses"] });
    },
    onError: () => toastError("Publication Failed", "Could not toggle publication status."),
  });

  const archiveMutation = useMutation({
    mutationFn: (id: string) => adminApi.archiveCourse(id),
    onSuccess: () => {
      success("Course Archived", "The course track has been safely removed.");
      setDeletingCourse(null);
      queryClient.invalidateQueries({ queryKey: ["admin-courses"] });
      queryClient.invalidateQueries({ queryKey: ["admin-dashboard-stats"] });
    },
    onError: () => toastError("Archive Failed", "Could not archive the course track."),
  });

  const resetForm = () => {
    setFormData({
      title: "",
      slug: "",
      description: "",
      thumbnail_url: "",
      is_published: true,
      order: 0,
    });
  };

  const handleOpenEdit = (course: CourseItem) => {
    setEditingCourse(course);
    setFormData({
      title: course.title,
      slug: course.slug,
      description: course.description || "",
      thumbnail_url: course.thumbnail_url || "",
      is_published: course.is_published,
      order: course.order || 0,
    });
  };

  const columns: Column<CourseItem>[] = [
    {
      key: "title",
      header: "Course Track",
      cell: (row) => (
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-500/10 text-brand-400 border border-brand-500/20 font-bold">
            <BookOpen className="h-5 w-5" />
          </div>
          <div>
            <button
              onClick={() => navigate(`/admin/courses/${row.id}`)}
              className="text-left font-semibold text-slate-900 dark:text-white hover:text-brand-600 dark:hover:text-brand-400 transition-colors"
            >
              {row.title}
            </button>
            <div className="text-xs text-slate-500 dark:text-slate-400 font-mono mt-0.5">{row.slug}</div>
          </div>
        </div>
      ),
    },
    {
      key: "metrics",
      header: "Modules & Students",
      cell: (row) => (
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300">
            <Layers className="h-4 w-4 text-indigo-500" />
            {row.modules_count} modules
          </span>
          <span className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300">
            <Users className="h-4 w-4 text-emerald-500" />
            {row.enrolled_students_count} students
          </span>
        </div>
      ),
    },
    {
      key: "order",
      header: "Display Order",
      cell: (row) => <span className="font-mono text-xs text-slate-500 dark:text-slate-400">{row.order}</span>,
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => (
        <div className="flex items-center gap-1.5">
          <StatusDot status={row.is_published ? "online" : "offline"} pulse={row.is_published} />
          <Badge variant={row.is_published ? "emerald" : "slate"} size="sm">
            {row.is_published ? "Published" : "Draft"}
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
          <Button
            size="sm"
            variant="ghost"
            onClick={() => navigate(`/admin/courses/${row.id}`)}
            title="View Course & Modules"
          >
            <Eye className="h-4 w-4 text-slate-400 hover:text-slate-900 dark:hover:text-white" />
          </Button>

          <Button
            size="sm"
            variant="ghost"
            onClick={() => handleOpenEdit(row)}
            title="Edit Course"
          >
            <Edit2 className="h-4 w-4 text-slate-400 hover:text-brand-500" />
          </Button>

          <Button
            size="sm"
            variant="ghost"
            onClick={() => publishMutation.mutate({ id: row.id, is_published: !row.is_published })}
            title={row.is_published ? "Unpublish" : "Publish"}
          >
            {row.is_published ? (
              <XCircle className="h-4 w-4 text-amber-500 hover:text-amber-600" />
            ) : (
              <CheckCircle2 className="h-4 w-4 text-emerald-500 hover:text-emerald-600" />
            )}
          </Button>

          <Button
            size="sm"
            variant="ghost"
            onClick={() => setDeletingCourse(row)}
            title="Archive Course"
          >
            <Trash2 className="h-4 w-4 text-rose-500 hover:text-rose-600" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            Course Management
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Build learning curriculum paths, configure modules, prerequisites, and publish tracks.
          </p>
        </div>

        <Button onClick={() => { resetForm(); setIsCreateModalOpen(true); }}>
          <Plus className="h-4 w-4 mr-2" />
          New Course Track
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900/60 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="w-full sm:max-w-xs">
          <SearchInput
            value={search}
            onChange={(val) => {
              setSearch(val);
              setPage(1);
            }}
            placeholder="Search courses..."
          />
        </div>
      </div>

      {/* Course Data Table */}
      <DataTable
        data={data?.data || []}
        columns={columns}
        isLoading={isLoading}
        isError={isError}
        errorMessage="Unable to load courses. Check API server connectivity."
        onRetry={() => refetch()}
        emptyTitle="No Courses Yet"
        emptyDescription="Get started by creating your first course track with structured learning modules."
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

      {/* Create Course Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create Course Track"
        description="Configure a new subject curriculum to host sequential modules and coding assignments."
        size="md"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createMutation.mutate({
              title: formData.title,
              slug: formData.slug || undefined,
              description: formData.description,
              thumbnail_url: formData.thumbnail_url || undefined,
              is_published: formData.is_published,
              order: Number(formData.order) || 0,
            });
          }}
          className="space-y-4"
        >
          <FormField label="Course Title" required>
            <Input
              placeholder="e.g. Full-Stack Python & React Masterclass"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              required
            />
          </FormField>

          <FormField label="URL Slug (Optional)">
            <Input
              placeholder="e.g. full-stack-python"
              value={formData.slug}
              onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
            />
          </FormField>

          <FormField label="Description">
            <Textarea
              rows={3}
              placeholder="Comprehensive track description and student learning outcomes..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField label="Display Order">
              <Input
                type="number"
                value={formData.order}
                onChange={(e) => setFormData({ ...formData, order: Number(e.target.value) })}
              />
            </FormField>

            <div className="flex items-center pt-8">
              <Checkbox
                label="Publish Immediately"
                checked={formData.is_published}
                onChange={(e) => setFormData({ ...formData, is_published: e.target.checked })}
              />
            </div>
          </div>

          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-surface-800">
            <Button variant="secondary" type="button" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createMutation.isPending}>
              Create Course
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Course Modal */}
      <Modal
        isOpen={Boolean(editingCourse)}
        onClose={() => setEditingCourse(null)}
        title="Edit Course Track"
        description="Update track details, descriptions, and ordering."
        size="md"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!editingCourse) return;
            updateMutation.mutate({
              id: editingCourse.id,
              payload: {
                title: formData.title,
                slug: formData.slug,
                description: formData.description,
                order: Number(formData.order),
                is_published: formData.is_published,
              },
            });
          }}
          className="space-y-4"
        >
          <FormField label="Course Title" required>
            <Input
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              required
            />
          </FormField>

          <FormField label="URL Slug" required>
            <Input
              value={formData.slug}
              onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
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
            <FormField label="Display Order">
              <Input
                type="number"
                value={formData.order}
                onChange={(e) => setFormData({ ...formData, order: Number(e.target.value) })}
              />
            </FormField>

            <div className="flex items-center pt-8">
              <Checkbox
                label="Published"
                checked={formData.is_published}
                onChange={(e) => setFormData({ ...formData, is_published: e.target.checked })}
              />
            </div>
          </div>

          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-surface-800">
            <Button variant="secondary" type="button" onClick={() => setEditingCourse(null)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={updateMutation.isPending}>
              Save Changes
            </Button>
          </div>
        </form>
      </Modal>

      {/* Confirm Archive Dialog */}
      <ConfirmDialog
        isOpen={Boolean(deletingCourse)}
        onClose={() => setDeletingCourse(null)}
        onConfirm={() => deletingCourse && archiveMutation.mutate(deletingCourse.id)}
        isLoading={archiveMutation.isPending}
        title="Archive Course Track?"
        message={`Are you sure you want to archive '${deletingCourse?.title}'? Enrolled students will no longer be able to submit tasks for this course.`}
        confirmText="Archive Course"
        variant="danger"
      />
    </div>
  );
};
