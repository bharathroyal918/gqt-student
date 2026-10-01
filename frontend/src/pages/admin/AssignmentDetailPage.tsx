import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Code2,
  Plus,
  Trash2,
  Edit2,
  Clock,
  Cpu,
  Eye,
  EyeOff,
} from "lucide-react";
import { adminApi } from "../../api/adminApi";
import { TestCaseItem } from "../../types/admin";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { Modal } from "../../components/ui/Modal";
import { FormField, Input, Textarea, Checkbox } from "../../components/ui/Form";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { useToast } from "../../context/ToastContext";

export const AssignmentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [isAddTestCaseOpen, setIsAddTestCaseOpen] = useState(false);
  const [editingTestCase, setEditingTestCase] = useState<TestCaseItem | null>(null);
  const [deletingTestCase, setDeletingTestCase] = useState<TestCaseItem | null>(null);

  const [testCaseForm, setTestCaseForm] = useState({
    input_data: "",
    expected_output: "",
    is_visible: true,
    weight: 10,
    order: 0,
  });

  // Query
  const {
    data: question,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["admin-question-detail", id],
    queryFn: () => adminApi.getQuestionDetail(id!),
    enabled: Boolean(id),
  });

  // Mutations
  const addTestCaseMutation = useMutation({
    mutationFn: (payload: any) => adminApi.addTestCase(id!, payload),
    onSuccess: () => {
      success("Test Case Added", "Test case registered to test suite.");
      setIsAddTestCaseOpen(false);
      resetTestCaseForm();
      queryClient.invalidateQueries({ queryKey: ["admin-question-detail", id] });
    },
    onError: () => toastError("Error", "Could not add test case."),
  });

  const updateTestCaseMutation = useMutation({
    mutationFn: ({ testCaseId, payload }: { testCaseId: string; payload: any }) =>
      adminApi.updateTestCase(testCaseId, payload),
    onSuccess: () => {
      success("Test Case Updated", "Changes saved.");
      setEditingTestCase(null);
      queryClient.invalidateQueries({ queryKey: ["admin-question-detail", id] });
    },
    onError: () => toastError("Error", "Could not update test case."),
  });

  const deleteTestCaseMutation = useMutation({
    mutationFn: (testCaseId: string) => adminApi.deleteTestCase(testCaseId),
    onSuccess: () => {
      success("Test Case Removed", "Test case removed from suite.");
      setDeletingTestCase(null);
      queryClient.invalidateQueries({ queryKey: ["admin-question-detail", id] });
    },
    onError: () => toastError("Error", "Could not delete test case."),
  });

  const resetTestCaseForm = () => {
    const nextOrder =
      question?.test_cases && question.test_cases.length > 0
        ? question.test_cases[question.test_cases.length - 1].order + 1
        : 0;
    setTestCaseForm({
      input_data: "",
      expected_output: "",
      is_visible: true,
      weight: 10,
      order: nextOrder,
    });
  };

  const handleOpenAdd = () => {
    resetTestCaseForm();
    setIsAddTestCaseOpen(true);
  };

  const handleOpenEdit = (tc: TestCaseItem) => {
    setEditingTestCase(tc);
    setTestCaseForm({
      input_data: tc.input_data,
      expected_output: tc.expected_output,
      is_visible: tc.is_visible,
      weight: parseFloat(tc.weight) || 10,
      order: tc.order,
    });
  };

  if (isLoading) {
    return <LoadingState message="Loading coding question details..." />;
  }

  if (isError || !question) {
    return (
      <ErrorState
        title="Problem Not Found"
        message="Unable to locate question details. It might have been deleted."
        onRetry={() => refetch()}
      />
    );
  }

  const visibleTestCases = question.test_cases?.filter((t) => t.is_visible) || [];
  const hiddenTestCases = question.test_cases?.filter((t) => !t.is_visible) || [];

  return (
    <div className="space-y-6">
      {/* Top back navigation */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate("/admin/assignments")}>
          <ArrowLeft className="h-4 w-4 mr-1.5" />
          Back to Assignments
        </Button>
      </div>

      {/* Question Header Card */}
      <Card className="p-6 border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 shadow-sm dark:shadow-none">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20">
              <Code2 className="h-7 w-7" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2.5">
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{question.title}</h1>
                <Badge
                  variant={
                    question.difficulty === "EASY"
                      ? "emerald"
                      : question.difficulty === "MEDIUM"
                      ? "amber"
                      : "rose"
                  }
                >
                  {question.difficulty}
                </Badge>
                <Badge variant="indigo">{question.points} Points</Badge>
              </div>

              <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
                <span>Module: {question.module_title}</span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5" />
                  {question.time_limit_seconds}s limit
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Cpu className="h-3.5 w-3.5" />
                  {question.memory_limit_mb}MB limit
                </span>
              </div>
            </div>
          </div>

          <Button onClick={handleOpenAdd}>
            <Plus className="h-4 w-4 mr-1.5" />
            Add Test Case
          </Button>
        </div>

        {/* Problem Statement Preview */}
        <div className="mt-6 border-t border-slate-200 dark:border-surface-800 pt-4">
          <h3 className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-2">
            Problem Statement
          </h3>
          <div className="rounded-xl bg-slate-50 dark:bg-surface-900/60 p-4 text-sm text-slate-800 dark:text-slate-300 whitespace-pre-wrap font-sans leading-relaxed border border-slate-200 dark:border-surface-800">
            {question.problem_statement}
          </div>
        </div>

        {/* Languages Allowed */}
        <div className="mt-4 flex items-center gap-2">
          <span className="text-xs text-slate-600 dark:text-slate-400">Allowed Languages:</span>
          {question.allowed_languages.map((l) => (
            <Badge key={l} variant="slate" size="sm">
              {l}
            </Badge>
          ))}
        </div>
      </Card>

      {/* Test Cases Suite */}
      <div className="space-y-6">
        {/* Visible Test Cases */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
              <Eye className="h-4 w-4 text-emerald-500 dark:text-emerald-400" />
              Visible Test Cases (Student Samples)
              <span className="text-xs text-slate-500 dark:text-slate-400 font-normal">({visibleTestCases.length})</span>
            </h2>
          </div>

          {visibleTestCases.length === 0 ? (
            <div className="rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900/40 p-6 text-center text-sm text-slate-600 dark:text-slate-400">
              No sample visible test cases created.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {visibleTestCases.map((tc) => (
                <Card key={tc.id} className="p-4 space-y-3 border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 shadow-sm dark:shadow-none">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="emerald" size="sm">Sample #{tc.order}</Badge>
                      <span className="text-xs text-slate-500 dark:text-slate-400">Weight: {tc.weight}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button size="sm" variant="ghost" onClick={() => handleOpenEdit(tc)}>
                        <Edit2 className="h-3.5 w-3.5 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white" />
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setDeletingTestCase(tc)}>
                        <Trash2 className="h-3.5 w-3.5 text-rose-500 hover:text-rose-600 dark:text-rose-400 dark:hover:text-rose-300" />
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2 text-xs font-mono">
                    <div>
                      <span className="text-slate-600 dark:text-slate-400 font-sans">Input:</span>
                      <pre className="mt-1 rounded-lg bg-slate-50 dark:bg-surface-950 p-2.5 text-slate-800 dark:text-slate-200 overflow-x-auto border border-slate-200 dark:border-surface-800">
                        {tc.input_data || "<empty>"}
                      </pre>
                    </div>
                    <div>
                      <span className="text-slate-600 dark:text-slate-400 font-sans">Expected Output:</span>
                      <pre className="mt-1 rounded-lg bg-slate-50 dark:bg-surface-950 p-2.5 text-emerald-700 dark:text-emerald-300 overflow-x-auto border border-slate-200 dark:border-surface-800">
                        {tc.expected_output || "<empty>"}
                      </pre>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Hidden Test Cases */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
              <EyeOff className="h-4 w-4 text-amber-500 dark:text-amber-400" />
              Hidden Test Cases (Grading Suite)
              <span className="text-xs text-slate-500 dark:text-slate-400 font-normal">({hiddenTestCases.length})</span>
            </h2>
          </div>

          {hiddenTestCases.length === 0 ? (
            <div className="rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900/40 p-6 text-center text-sm text-slate-600 dark:text-slate-400">
              No hidden test cases configured. Submissions will only be verified against visible samples.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {hiddenTestCases.map((tc) => (
                <Card key={tc.id} className="p-4 space-y-3 border-amber-500/30 dark:border-amber-500/20 bg-white dark:bg-surface-900 shadow-sm dark:shadow-none">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="amber" size="sm">Hidden #{tc.order}</Badge>
                      <span className="text-xs text-slate-500 dark:text-slate-400">Weight: {tc.weight}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button size="sm" variant="ghost" onClick={() => handleOpenEdit(tc)}>
                        <Edit2 className="h-3.5 w-3.5 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white" />
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setDeletingTestCase(tc)}>
                        <Trash2 className="h-3.5 w-3.5 text-rose-500 hover:text-rose-600 dark:text-rose-400 dark:hover:text-rose-300" />
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2 text-xs font-mono">
                    <div>
                      <span className="text-slate-600 dark:text-slate-400 font-sans">Input:</span>
                      <pre className="mt-1 rounded-lg bg-slate-50 dark:bg-surface-950 p-2.5 text-slate-800 dark:text-slate-200 overflow-x-auto border border-slate-200 dark:border-surface-800">
                        {tc.input_data || "<empty>"}
                      </pre>
                    </div>
                    <div>
                      <span className="text-slate-600 dark:text-slate-400 font-sans">Expected Output:</span>
                      <pre className="mt-1 rounded-lg bg-slate-50 dark:bg-surface-950 p-2.5 text-amber-700 dark:text-amber-300 overflow-x-auto border border-slate-200 dark:border-surface-800">
                        {tc.expected_output || "<empty>"}
                      </pre>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Add Test Case Modal */}
      <Modal
        isOpen={isAddTestCaseOpen}
        onClose={() => setIsAddTestCaseOpen(false)}
        title="Add Test Case"
        description="Provide input arguments and the exact expected standard output."
        size="md"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            addTestCaseMutation.mutate({
              input_data: testCaseForm.input_data,
              expected_output: testCaseForm.expected_output,
              is_visible: testCaseForm.is_visible,
              weight: Number(testCaseForm.weight),
              order: Number(testCaseForm.order),
            });
          }}
          className="space-y-4"
        >
          <FormField label="Standard Input Data (stdin)">
            <Textarea
              rows={3}
              className="font-mono text-xs"
              placeholder="e.g. 5&#10;1 2 3 4 5"
              value={testCaseForm.input_data}
              onChange={(e) => setTestCaseForm({ ...testCaseForm, input_data: e.target.value })}
            />
          </FormField>

          <FormField label="Expected Output Data (stdout)" required>
            <Textarea
              rows={3}
              className="font-mono text-xs"
              placeholder="e.g. 15"
              value={testCaseForm.expected_output}
              onChange={(e) => setTestCaseForm({ ...testCaseForm, expected_output: e.target.value })}
              required
            />
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField label="Weight / Marks">
              <Input
                type="number"
                value={testCaseForm.weight}
                onChange={(e) => setTestCaseForm({ ...testCaseForm, weight: Number(e.target.value) })}
              />
            </FormField>

            <FormField label="Execution Order #">
              <Input
                type="number"
                value={testCaseForm.order}
                onChange={(e) => setTestCaseForm({ ...testCaseForm, order: Number(e.target.value) })}
              />
            </FormField>
          </div>

          <Checkbox
            label="Make Visible to Students (Sample Test Case)"
            checked={testCaseForm.is_visible}
            onChange={(e) => setTestCaseForm({ ...testCaseForm, is_visible: e.target.checked })}
          />

          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-surface-800">
            <Button variant="secondary" type="button" onClick={() => setIsAddTestCaseOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={addTestCaseMutation.isPending}>
              Add Test Case
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Test Case Modal */}
      <Modal
        isOpen={Boolean(editingTestCase)}
        onClose={() => setEditingTestCase(null)}
        title="Edit Test Case"
        description="Update input parameters, target output, or visibility flag."
        size="md"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!editingTestCase) return;
            updateTestCaseMutation.mutate({
              testCaseId: editingTestCase.id,
              payload: {
                input_data: testCaseForm.input_data,
                expected_output: testCaseForm.expected_output,
                is_visible: testCaseForm.is_visible,
                weight: Number(testCaseForm.weight),
                order: Number(testCaseForm.order),
              },
            });
          }}
          className="space-y-4"
        >
          <FormField label="Standard Input Data (stdin)">
            <Textarea
              rows={3}
              className="font-mono text-xs"
              value={testCaseForm.input_data}
              onChange={(e) => setTestCaseForm({ ...testCaseForm, input_data: e.target.value })}
            />
          </FormField>

          <FormField label="Expected Output Data (stdout)" required>
            <Textarea
              rows={3}
              className="font-mono text-xs"
              value={testCaseForm.expected_output}
              onChange={(e) => setTestCaseForm({ ...testCaseForm, expected_output: e.target.value })}
              required
            />
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField label="Weight / Marks">
              <Input
                type="number"
                value={testCaseForm.weight}
                onChange={(e) => setTestCaseForm({ ...testCaseForm, weight: Number(e.target.value) })}
              />
            </FormField>

            <FormField label="Execution Order #">
              <Input
                type="number"
                value={testCaseForm.order}
                onChange={(e) => setTestCaseForm({ ...testCaseForm, order: Number(e.target.value) })}
              />
            </FormField>
          </div>

          <Checkbox
            label="Make Visible to Students"
            checked={testCaseForm.is_visible}
            onChange={(e) => setTestCaseForm({ ...testCaseForm, is_visible: e.target.checked })}
          />

          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-surface-800">
            <Button variant="secondary" type="button" onClick={() => setEditingTestCase(null)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={updateTestCaseMutation.isPending}>
              Save Test Case
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Test Case Confirmation */}
      <ConfirmDialog
        isOpen={Boolean(deletingTestCase)}
        onClose={() => setDeletingTestCase(null)}
        onConfirm={() => deletingTestCase && deleteTestCaseMutation.mutate(deletingTestCase.id)}
        isLoading={deleteTestCaseMutation.isPending}
        title="Delete Test Case?"
        message="Are you sure you want to remove this test case from the assessment suite?"
        confirmText="Delete Test Case"
        variant="danger"
      />
    </div>
  );
};
