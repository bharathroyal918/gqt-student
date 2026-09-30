import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  BookOpen,
  Plus,
  ArrowUp,
  ArrowDown,
  Edit2,
  CheckCircle2,
  XCircle,
  Layers,
  Code2,
} from "lucide-react";
import { adminApi } from "../../api/adminApi";
import { ModuleItem, ModulePrerequisiteItem } from "../../types/admin";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { StatusDot } from "../../components/ui/StatusDot";
import { Card } from "../../components/ui/Card";
import { Modal } from "../../components/ui/Modal";
import { FormField, Input, Textarea, Checkbox } from "../../components/ui/Form";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { useToast } from "../../context/ToastContext";

export const CourseDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [isAddModuleOpen, setIsAddModuleOpen] = useState(false);
  const [editingModule, setEditingModule] = useState<ModuleItem | null>(null);

  const [moduleForm, setModuleForm] = useState({
    title: "",
    slug: "",
    order_index: 0,
    summary: "",
    lecture_content: "",
    passing_percentage: 70,
    is_published: true,
  });

  // Queries
  const {
    data: course,
    isLoading: isCourseLoading,
    isError: isCourseError,
    refetch: refetchCourse,
  } = useQuery({
    queryKey: ["admin-course-detail", id],
    queryFn: () => adminApi.getCourseDetail(id!),
    enabled: Boolean(id),
  });

  const {
    data: modulesData,
    isLoading: isModulesLoading,
  } = useQuery({
    queryKey: ["admin-modules", { course_id: id }],
    queryFn: () => adminApi.getModules({ course_id: id, page_size: 100 }),
    enabled: Boolean(id),
  });

  const sortedModules = React.useMemo(() => {
    if (!modulesData?.data) return [];
    return [...modulesData.data].sort((a, b) => a.order_index - b.order_index);
  }, [modulesData]);

  // Mutations
  const createModuleMutation = useMutation({
    mutationFn: (payload: any) => adminApi.createModule({ ...payload, course_id: id! }),
    onSuccess: (mod) => {
      success("Module Created", `Module '${mod.title}' added to curriculum.`);
      setIsAddModuleOpen(false);
      resetModuleForm();
      queryClient.invalidateQueries({ queryKey: ["admin-modules"] });
      queryClient.invalidateQueries({ queryKey: ["admin-course-detail", id] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.message || err.response?.data?.error?.message || "Failed to create module";
      toastError("Creation Failed", msg);
    },
  });

  const updateModuleMutation = useMutation({
    mutationFn: ({ modId, payload }: { modId: string; payload: any }) =>
      adminApi.updateModule(modId, payload),
    onSuccess: () => {
      success("Module Updated", "Changes saved.");
      setEditingModule(null);
      queryClient.invalidateQueries({ queryKey: ["admin-modules"] });
    },
    onError: () => toastError("Update Failed", "Could not update module details."),
  });

  const publishModuleMutation = useMutation({
    mutationFn: ({ modId, is_published }: { modId: string; is_published: boolean }) =>
      adminApi.publishModule(modId, is_published),
    onSuccess: (res) => {
      success("Module Publication", `Module is now ${res.is_published ? "Published" : "Unpublished"}.`);
      queryClient.invalidateQueries({ queryKey: ["admin-modules"] });
    },
    onError: () => toastError("Error", "Could not update module publication status."),
  });

  const reorderMutation = useMutation({
    mutationFn: (orders: Array<{ id: string; order_index: number }>) =>
      adminApi.reorderModules(id!, orders),
    onSuccess: () => {
      success("Sequence Updated", "Module learning progression order saved.");
      queryClient.invalidateQueries({ queryKey: ["admin-modules"] });
    },
    onError: () => toastError("Reorder Failed", "Could not reorder modules."),
  });

  const resetModuleForm = () => {
    const nextOrder = sortedModules.length > 0 ? sortedModules[sortedModules.length - 1].order_index + 1 : 0;
    setModuleForm({
      title: "",
      slug: "",
      order_index: nextOrder,
      summary: "",
      lecture_content: "",
      passing_percentage: 70,
      is_published: true,
    });
  };

  const handleOpenAddModule = () => {
    resetModuleForm();
    setIsAddModuleOpen(true);
  };

  const handleOpenEditModule = (mod: ModuleItem) => {
    setEditingModule(mod);
    setModuleForm({
      title: mod.title,
      slug: mod.slug,
      order_index: mod.order_index,
      summary: mod.summary || "",
      lecture_content: mod.lecture_content || "",
      passing_percentage: parseFloat(mod.passing_percentage as any) || 70,
      is_published: mod.is_published,
    });
  };

  const handleMoveModule = (index: number, direction: "up" | "down") => {
    if (direction === "up" && index === 0) return;
    if (direction === "down" && index === sortedModules.length - 1) return;

    const targetIndex = direction === "up" ? index - 1 : index + 1;
    const currentItem = sortedModules[index];
    const targetItem = sortedModules[targetIndex];

    const updatedOrders = [
      { id: currentItem.id, order_index: targetItem.order_index },
      { id: targetItem.id, order_index: currentItem.order_index },
    ];

    reorderMutation.mutate(updatedOrders);
  };

  if (isCourseLoading) {
    return <LoadingState message="Loading course curriculum..." />;
  }

  if (isCourseError || !course) {
    return (
      <ErrorState
        title="Course Not Found"
        message="Unable to locate course details. It may have been archived."
        onRetry={() => refetchCourse()}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate("/admin/courses")}>
          <ArrowLeft className="h-4 w-4 mr-1.5" />
          Back to Courses
        </Button>
      </div>

      {/* Course Overview Card */}
      <Card className="p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-400 border border-brand-500/20">
              <BookOpen className="h-7 w-7" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-white">{course.title}</h1>
                <Badge variant={course.is_published ? "emerald" : "slate"}>
                  {course.is_published ? "Published" : "Draft"}
                </Badge>
              </div>
              <div className="text-xs text-slate-400 font-mono mt-1">Slug: {course.slug}</div>
              <p className="text-sm text-slate-300 mt-2 max-w-2xl leading-relaxed">
                {course.description || "No description provided for this track."}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button onClick={handleOpenAddModule}>
              <Plus className="h-4 w-4 mr-1.5" />
              Add Module
            </Button>
          </div>
        </div>

        {/* Quick Highlights */}
        <div className="mt-6 grid grid-cols-2 gap-4 border-t border-surface-800 pt-4 sm:grid-cols-3">
          <div className="rounded-xl bg-surface-900/60 p-3">
            <div className="text-xs text-slate-400">Total Modules</div>
            <div className="text-lg font-bold text-white">{sortedModules.length}</div>
          </div>
          <div className="rounded-xl bg-surface-900/60 p-3">
            <div className="text-xs text-slate-400">Enrolled Students</div>
            <div className="text-lg font-bold text-emerald-400">{course.enrolled_students_count}</div>
          </div>
          <div className="rounded-xl bg-surface-900/60 p-3">
            <div className="text-xs text-slate-400">Sequential Lock</div>
            <div className="text-sm font-semibold text-brand-400 mt-0.5">Enforced by Order</div>
          </div>
        </div>
      </Card>

      {/* Modules List Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Layers className="h-5 w-5 text-indigo-400" />
            Curriculum Modules & Sequence
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Modules must be completed sequentially by students according to this order index.
          </p>
        </div>
      </div>

      {/* Modules List */}
      {isModulesLoading ? (
        <LoadingState message="Loading modules..." />
      ) : sortedModules.length === 0 ? (
        <EmptyState
          title="No Modules Created"
          description="Curriculum is empty. Add the first sequential learning module to get started."
          actionLabel="Create Module"
          onAction={handleOpenAddModule}
        />
      ) : (
        <div className="space-y-3">
          {sortedModules.map((mod, index) => (
            <Card key={mod.id} className="p-4 transition-all hover:border-surface-700">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-start gap-4">
                  {/* Sequence Order Badge */}
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-surface-800 text-slate-200 font-bold font-mono text-sm border border-surface-700">
                    #{mod.order_index}
                  </div>

                  <div>
                    <div className="flex items-center gap-2.5">
                      <h3 className="font-semibold text-white text-base">{mod.title}</h3>
                      <StatusDot status={mod.is_published ? "online" : "offline"} pulse={mod.is_published} />
                      <Badge variant={mod.is_published ? "emerald" : "slate"} size="sm">
                        {mod.is_published ? "Published" : "Draft"}
                      </Badge>
                      <Badge variant="indigo" size="sm">Pass: {mod.passing_percentage}%</Badge>
                    </div>

                    <p className="text-xs text-slate-400 mt-1 line-clamp-1">{mod.summary || "No summary provided."}</p>

                    <div className="mt-2 flex items-center gap-4 text-xs text-slate-400">
                      <span className="flex items-center gap-1">
                        <Code2 className="h-3.5 w-3.5 text-brand-400" />
                        {mod.questions_count} coding questions
                      </span>
                      {mod.prerequisites?.length > 0 && (
                        <span>
                          Prereqs: {mod.prerequisites.map((p: ModulePrerequisiteItem) => p.title).join(", ")}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Module Actions & Reorder controls */}
                <div className="flex items-center gap-1.5 self-end sm:self-center">
                  {/* Up / Down Reorder */}
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleMoveModule(index, "up")}
                    disabled={index === 0 || reorderMutation.isPending}
                    title="Move Module Up"
                  >
                    <ArrowUp className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleMoveModule(index, "down")}
                    disabled={index === sortedModules.length - 1 || reorderMutation.isPending}
                    title="Move Module Down"
                  >
                    <ArrowDown className="h-4 w-4" />
                  </Button>

                  {/* Publish toggle */}
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() =>
                      publishModuleMutation.mutate({ modId: mod.id, is_published: !mod.is_published })
                    }
                    title={mod.is_published ? "Unpublish Module" : "Publish Module"}
                  >
                    {mod.is_published ? (
                      <XCircle className="h-4 w-4 text-amber-400 hover:text-amber-300" />
                    ) : (
                      <CheckCircle2 className="h-4 w-4 text-emerald-400 hover:text-emerald-300" />
                    )}
                  </Button>

                  {/* Edit */}
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleOpenEditModule(mod)}
                    title="Edit Module"
                  >
                    <Edit2 className="h-4 w-4 text-slate-400 hover:text-brand-400" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Add Module Modal */}
      <Modal
        isOpen={isAddModuleOpen}
        onClose={() => setIsAddModuleOpen(false)}
        title="Add Learning Module"
        description="Add a sequential lecture and assessment stage to this course."
        size="lg"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createModuleMutation.mutate({
              title: moduleForm.title,
              slug: moduleForm.slug || undefined,
              order_index: Number(moduleForm.order_index),
              summary: moduleForm.summary,
              lecture_content: moduleForm.lecture_content,
              passing_percentage: Number(moduleForm.passing_percentage),
              is_published: moduleForm.is_published,
            });
          }}
          className="space-y-4"
        >
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FormField label="Module Title" required>
              <Input
                placeholder="e.g. Object-Oriented Programming & Classes"
                value={moduleForm.title}
                onChange={(e) => setModuleForm({ ...moduleForm, title: e.target.value })}
                required
              />
            </FormField>

            <FormField label="Slug (Optional)">
              <Input
                placeholder="e.g. oop-and-classes"
                value={moduleForm.slug}
                onChange={(e) => setModuleForm({ ...moduleForm, slug: e.target.value })}
              />
            </FormField>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <FormField label="Order Sequence #" required>
              <Input
                type="number"
                value={moduleForm.order_index}
                onChange={(e) => setModuleForm({ ...moduleForm, order_index: Number(e.target.value) })}
                required
              />
            </FormField>

            <FormField label="Passing Percentage (%)" required>
              <Input
                type="number"
                min={0}
                max={100}
                value={moduleForm.passing_percentage}
                onChange={(e) =>
                  setModuleForm({ ...moduleForm, passing_percentage: Number(e.target.value) })
                }
                required
              />
            </FormField>
          </div>

          <FormField label="Short Summary">
            <Input
              placeholder="Brief description of skills covered in this module..."
              value={moduleForm.summary}
              onChange={(e) => setModuleForm({ ...moduleForm, summary: e.target.value })}
            />
          </FormField>

          <FormField label="Lecture Content (Markdown / Text)">
            <Textarea
              rows={6}
              placeholder="Write the learning guide, code concepts, and instructions here..."
              value={moduleForm.lecture_content}
              onChange={(e) => setModuleForm({ ...moduleForm, lecture_content: e.target.value })}
            />
          </FormField>

          <Checkbox
            label="Publish Module immediately"
            checked={moduleForm.is_published}
            onChange={(e) => setModuleForm({ ...moduleForm, is_published: e.target.checked })}
          />

          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-surface-800">
            <Button variant="secondary" type="button" onClick={() => setIsAddModuleOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createModuleMutation.isPending}>
              Create Module
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Module Modal */}
      <Modal
        isOpen={Boolean(editingModule)}
        onClose={() => setEditingModule(null)}
        title="Edit Learning Module"
        description="Modify lecture syllabus, threshold requirements, and visibility."
        size="lg"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!editingModule) return;
            updateModuleMutation.mutate({
              modId: editingModule.id,
              payload: {
                title: moduleForm.title,
                slug: moduleForm.slug,
                order_index: Number(moduleForm.order_index),
                summary: moduleForm.summary,
                lecture_content: moduleForm.lecture_content,
                passing_percentage: Number(moduleForm.passing_percentage),
                is_published: moduleForm.is_published,
              },
            });
          }}
          className="space-y-4"
        >
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FormField label="Module Title" required>
              <Input
                value={moduleForm.title}
                onChange={(e) => setModuleForm({ ...moduleForm, title: e.target.value })}
                required
              />
            </FormField>

            <FormField label="Slug" required>
              <Input
                value={moduleForm.slug}
                onChange={(e) => setModuleForm({ ...moduleForm, slug: e.target.value })}
                required
              />
            </FormField>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <FormField label="Order Sequence #" required>
              <Input
                type="number"
                value={moduleForm.order_index}
                onChange={(e) => setModuleForm({ ...moduleForm, order_index: Number(e.target.value) })}
                required
              />
            </FormField>

            <FormField label="Passing Percentage (%)" required>
              <Input
                type="number"
                min={0}
                max={100}
                value={moduleForm.passing_percentage}
                onChange={(e) =>
                  setModuleForm({ ...moduleForm, passing_percentage: Number(e.target.value) })
                }
                required
              />
            </FormField>
          </div>

          <FormField label="Short Summary">
            <Input
              value={moduleForm.summary}
              onChange={(e) => setModuleForm({ ...moduleForm, summary: e.target.value })}
            />
          </FormField>

          <FormField label="Lecture Content (Markdown / Text)">
            <Textarea
              rows={6}
              value={moduleForm.lecture_content}
              onChange={(e) => setModuleForm({ ...moduleForm, lecture_content: e.target.value })}
            />
          </FormField>

          <Checkbox
            label="Published"
            checked={moduleForm.is_published}
            onChange={(e) => setModuleForm({ ...moduleForm, is_published: e.target.checked })}
          />

          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-surface-800">
            <Button variant="secondary" type="button" onClick={() => setEditingModule(null)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={updateModuleMutation.isPending}>
              Save Changes
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
