import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Editor from "@monaco-editor/react";
import {
  ArrowLeft,
  Clock,
  Cpu,
  Play,
  CheckCircle2,
  XCircle,
  RotateCcw,
  Sparkles,
  History,
  FileCode,
  Terminal,
  Layers,
  ChevronRight,
  Send,
} from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import {
  studentApi,
  CodeRunResponse,
  CodeSubmitResponse,
} from "../../api/studentApi";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { useToast } from "../../context/ToastContext";

const LANGUAGE_OPTIONS = [
  { value: "python", label: "Python 3.11", monacoLang: "python" },
  { value: "javascript", label: "JavaScript (Node 20)", monacoLang: "javascript" },
  { value: "java", label: "Java 17 (OpenJDK)", monacoLang: "java" },
  { value: "cpp", label: "C++ 20 (GCC)", monacoLang: "cpp" },
  { value: "c", label: "C 11 (GCC)", monacoLang: "c" },
];

export const StudentAssignmentDetailPage: React.FC = () => {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const { user, hydrateAuth } = useAuthStore();
  const queryClient = useQueryClient();
  const { success: toastSuccess, error: toastError } = useToast();

  const [selectedLanguage, setSelectedLanguage] = useState<string>("python");
  const [sourceCode, setSourceCode] = useState<string>("");
  const [activeLeftTab, setActiveLeftTab] = useState<"description" | "submissions">("description");
  const [activeBottomTab, setActiveBottomTab] = useState<"testcases" | "results" | "custom">("testcases");
  const [customInput, setCustomInput] = useState<string>("");
  const [activeSampleIndex, setActiveSampleIndex] = useState<number>(0);

  // Execution Results state
  const [runResult, setRunResult] = useState<CodeRunResponse | null>(null);
  const [submitResult, setSubmitResult] = useState<CodeSubmitResponse | null>(null);

  // Fetch Question Details
  const {
    data: question,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["student", "assignment-detail", assignmentId, user?.id],
    queryFn: () => studentApi.getQuestionDetail(assignmentId!),
    enabled: !!assignmentId && !!user?.id,
    staleTime: 1000 * 60,
  });

  // Fetch Submissions History
  const {
    data: submissions,
    refetch: refetchSubmissions,
  } = useQuery({
    queryKey: ["student", "assignment-submissions", assignmentId, user?.id],
    queryFn: () => studentApi.getQuestionSubmissions(assignmentId!),
    enabled: !!assignmentId && !!user?.id && activeLeftTab === "submissions",
  });

  // Initialize starter code when question or language changes
  useEffect(() => {
    if (question?.starter_code) {
      const code = question.starter_code[selectedLanguage] || "";
      setSourceCode(code);
    }
  }, [question, selectedLanguage]);

  // Run Code Mutation
  const runMutation = useMutation({
    mutationFn: () =>
      studentApi.runCode(assignmentId!, {
        language: selectedLanguage,
        source_code: sourceCode,
        custom_input: activeBottomTab === "custom" ? customInput : undefined,
      }),
    onSuccess: (data) => {
      setRunResult(data);
      setSubmitResult(null);
      setActiveBottomTab("results");
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.error?.message || "Execution error occurred.";
      toastError("Run Failed", msg);
    },
  });

  // Submit Code Mutation
  const submitMutation = useMutation({
    mutationFn: () =>
      studentApi.submitCode(assignmentId!, {
        language: selectedLanguage,
        source_code: sourceCode,
      }),
    onSuccess: (data) => {
      setSubmitResult(data);
      setRunResult(null);
      setActiveBottomTab("results");

      if (data.status === "ACCEPTED") {
        toastSuccess(
          "Accepted! 🎉",
          `All ${data.total_test_cases} test cases passed. +${data.score_awarded} points added to your profile!`
        );
      } else {
        toastError(
          `Evaluation: ${data.status.replace(/_/g, " ")}`,
          `Passed ${data.passed_test_cases} of ${data.total_test_cases} test cases.`
        );
      }

      // Immediately synchronize queries & live student profile points across header/sidebar
      queryClient.invalidateQueries({ queryKey: ["student"] });
      hydrateAuth(true);
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.error?.message || "Submission failed.";
      toastError("Submission Error", msg);
    },
  });

  // Hotkey handlers (Ctrl+Enter = Run, Ctrl+Shift+Enter = Submit)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        if (e.shiftKey) {
          e.preventDefault();
          if (!submitMutation.isPending) submitMutation.mutate();
        } else {
          e.preventDefault();
          if (!runMutation.isPending) runMutation.mutate();
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [runMutation, submitMutation]);

  if (isLoading) {
    return (
      <div className="flex h-96 flex-col items-center justify-center">
        <LoadingState message="Loading coding sandbox environment..." />
      </div>
    );
  }

  if (isError || !question) {
    return (
      <ErrorState
        title="Unable to load problem"
        message={error instanceof Error ? error.message : "Failed to load question details."}
        onRetry={() => refetch()}
      />
    );
  }

  const currentMonacoLang =
    LANGUAGE_OPTIONS.find((l) => l.value === selectedLanguage)?.monacoLang || "python";

  return (
    <div className="space-y-4">
      {/* Top Breadcrumb & Controls */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Link to="/assignments" className="hover:text-white transition-colors flex items-center gap-1">
            <ArrowLeft className="h-3.5 w-3.5" />
            Problems
          </Link>
          <ChevronRight className="h-3 w-3 text-slate-600" />
          <span className="text-brand-400 font-mono">Module {question.module_order}</span>
          <ChevronRight className="h-3 w-3 text-slate-600" />
          <span className="text-slate-200 font-medium truncate max-w-xs">{question.title}</span>
        </div>

        {question.is_solved && (
          <Badge variant="success" size="sm" className="flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3" />
            Solved ({question.best_score} pts)
          </Badge>
        )}
      </div>

      {/* Main 2-Column Split Workspace */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12 min-h-[720px]">
        {/* Left Column: Problem Statement & Submissions (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          <Card className="p-0 overflow-hidden flex flex-col flex-1">
            {/* Header Tabs */}
            <div className="flex items-center border-b border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900/60 px-4 pt-2">
              <button
                onClick={() => setActiveLeftTab("description")}
                className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                  activeLeftTab === "description"
                    ? "border-brand-500 text-brand-600 dark:text-brand-400"
                    : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              >
                <FileCode className="h-3.5 w-3.5" />
                Problem Description
              </button>
              <button
                onClick={() => {
                  setActiveLeftTab("submissions");
                  refetchSubmissions();
                }}
                className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                  activeLeftTab === "submissions"
                    ? "border-brand-500 text-brand-600 dark:text-brand-400"
                    : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              >
                <History className="h-3.5 w-3.5" />
                Submissions
                {question.attempts_count > 0 && (
                  <span className="rounded-full bg-slate-200 dark:bg-surface-800 px-1.5 py-0.2 text-[10px] text-slate-700 dark:text-slate-300 font-semibold">
                    {question.attempts_count}
                  </span>
                )}
              </button>
            </div>

            {/* Left Body Content */}
            <div className="p-5 overflow-y-auto max-h-[660px] flex-1 space-y-4">
              {activeLeftTab === "description" ? (
                <>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h1 className="text-lg font-bold text-slate-900 dark:text-white">{question.title}</h1>
                      <Badge
                        variant={
                          question.difficulty === "EASY"
                            ? "emerald"
                            : question.difficulty === "MEDIUM"
                            ? "amber"
                            : "rose"
                        }
                        size="sm"
                      >
                        {question.difficulty}
                      </Badge>
                      <Badge variant="indigo" size="sm">
                        {question.points} Points
                      </Badge>
                    </div>

                    <div className="mt-2 flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5" />
                        {question.time_limit_seconds}s limit
                      </span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Cpu className="h-3.5 w-3.5" />
                        {question.memory_limit_mb} MB
                      </span>
                    </div>
                  </div>

                  {/* Problem Statement Markdown */}
                  <div className="border-t border-slate-200 dark:border-surface-800 pt-4 text-xs text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap space-y-2">
                    {question.problem_statement}
                  </div>

                  {/* Sample Testcases Preview */}
                  {question.visible_test_cases.length > 0 && (
                    <div className="border-t border-slate-200 dark:border-surface-800 pt-4 space-y-3">
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                        Sample Test Cases
                      </h3>
                      {question.visible_test_cases.map((tc, idx) => (
                        <div
                          key={tc.id}
                          className="rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-950 p-3 space-y-2 font-mono text-xs"
                        >
                          <div className="text-slate-600 dark:text-slate-400 font-sans text-[11px] font-semibold">
                            Sample Case #{idx + 1}:
                          </div>
                          <div>
                            <span className="text-slate-500 font-sans text-[11px]">Input:</span>
                            <pre className="mt-0.5 rounded-lg border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-2 text-slate-800 dark:text-slate-200">
                              {tc.input_data}
                            </pre>
                          </div>
                          <div>
                            <span className="text-slate-500 font-sans text-[11px]">Expected Output:</span>
                            <pre className="mt-0.5 rounded-lg border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-2 text-emerald-600 dark:text-emerald-400 font-semibold">
                              {tc.expected_output}
                            </pre>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                /* Submissions History Tab */
                <div className="space-y-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Your Submission History
                  </h3>
                  {!submissions || submissions.length === 0 ? (
                    <p className="text-xs text-slate-500 italic py-6 text-center">
                      No submissions recorded yet for this question.
                    </p>
                  ) : (
                    submissions.map((sub) => (
                      <div
                        key={sub.id}
                        className="rounded-xl border border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-950 p-3 flex items-center justify-between gap-3 text-xs"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span
                              className={`font-bold ${
                                sub.status === "ACCEPTED"
                                  ? "text-emerald-600 dark:text-emerald-400"
                                  : "text-rose-600 dark:text-rose-400"
                              }`}
                            >
                              {sub.status.replace(/_/g, " ")}
                            </span>
                            <Badge variant="indigo" size="sm">
                              {sub.language}
                            </Badge>
                          </div>
                          <p className="text-[11px] text-slate-500 mt-1">
                            {new Date(sub.submitted_at).toLocaleString()} • {sub.passed_test_cases}/{sub.total_test_cases} tests
                          </p>
                        </div>

                        <div className="text-right">
                          <span className="text-xs font-bold text-amber-600 dark:text-amber-400">
                            +{sub.score_awarded} pts
                          </span>
                          {sub.execution_time_ms && (
                            <p className="text-[10px] text-slate-500">{sub.execution_time_ms} ms</p>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Right Column: Code Editor & Execution Sandbox (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-4">
          <Card className="p-0 overflow-hidden flex flex-col flex-1">
            {/* Editor Toolbar */}
            <div className="flex items-center justify-between gap-3 border-b border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900/80 px-4 py-2 flex-wrap">
              {/* Language Selector */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">Language:</span>
                <select
                  value={selectedLanguage}
                  onChange={(e) => setSelectedLanguage(e.target.value)}
                  className="rounded-lg border border-slate-200 dark:border-surface-700 bg-white dark:bg-surface-800 px-2.5 py-1 text-xs text-slate-900 dark:text-slate-200 font-semibold focus:border-brand-500 focus:outline-none"
                >
                  {LANGUAGE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Reset to Starter Code */}
              <button
                onClick={() => {
                  if (question.starter_code && question.starter_code[selectedLanguage]) {
                    setSourceCode(question.starter_code[selectedLanguage]);
                  }
                }}
                className="text-xs text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 flex items-center gap-1 transition-colors"
                title="Reset code to original starter template"
              >
                <RotateCcw className="h-3 w-3" />
                Reset Code
              </button>
            </div>

            {/* Monaco Code Editor */}
            <div className="h-[360px] w-full bg-[#1e1e1e]">
              <Editor
                height="100%"
                language={currentMonacoLang}
                theme="vs-dark"
                value={sourceCode}
                onChange={(val) => setSourceCode(val || "")}
                options={{
                  fontSize: 13,
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  tabSize: 4,
                  wordWrap: "on",
                  lineNumbersMinChars: 3,
                }}
              />
            </div>

            {/* Bottom Console Tabs & Execution Bar */}
            <div className="border-t border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-950 flex flex-col">
              <div className="flex items-center justify-between border-b border-slate-200 dark:border-surface-800/80 px-4 pt-2 bg-slate-100/60 dark:bg-surface-900/40">
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setActiveBottomTab("testcases")}
                    className={`pb-2 px-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                      activeBottomTab === "testcases"
                        ? "border-brand-500 text-brand-600 dark:text-brand-400"
                        : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                    }`}
                  >
                    <Layers className="h-3.5 w-3.5" />
                    Test Cases
                  </button>
                  <button
                    onClick={() => setActiveBottomTab("custom")}
                    className={`pb-2 px-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                      activeBottomTab === "custom"
                        ? "border-brand-500 text-brand-600 dark:text-brand-400"
                        : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                    }`}
                  >
                    <Terminal className="h-3.5 w-3.5" />
                    Custom Input
                  </button>
                  <button
                    onClick={() => setActiveBottomTab("results")}
                    className={`pb-2 px-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                      activeBottomTab === "results"
                        ? "border-brand-500 text-brand-600 dark:text-brand-400"
                        : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                    }`}
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                    Test Results
                    {(runResult || submitResult) && (
                      <span className="h-2 w-2 rounded-full bg-brand-500 dark:bg-brand-400 animate-pulse" />
                    )}
                  </button>
                </div>

                {/* Hotkey Guide */}
                <span className="hidden sm:inline text-[11px] text-slate-500">
                  <kbd className="rounded bg-slate-200 dark:bg-surface-800 px-1 py-0.5 font-mono text-slate-700 dark:text-slate-300">Ctrl</kbd> + <kbd className="rounded bg-slate-200 dark:bg-surface-800 px-1 py-0.5 font-mono text-slate-700 dark:text-slate-300">Enter</kbd> to Run
                </span>
              </div>

              {/* Bottom Tab Content Body */}
              <div className="p-4 min-h-[160px] max-h-[220px] overflow-y-auto text-xs font-mono">
                {activeBottomTab === "testcases" && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      {question.visible_test_cases.map((tc, idx) => (
                        <button
                          key={tc.id}
                          onClick={() => setActiveSampleIndex(idx)}
                          className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition-all ${
                            activeSampleIndex === idx
                              ? "bg-brand-50 dark:bg-brand-600/30 text-brand-600 dark:text-brand-300 border border-brand-500/40"
                              : "bg-white dark:bg-surface-900 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 border border-slate-200 dark:border-surface-800"
                          }`}
                        >
                          Case #{idx + 1}
                        </button>
                      ))}
                    </div>

                    {question.visible_test_cases[activeSampleIndex] && (
                      <div className="space-y-2">
                        <div>
                          <span className="text-[11px] text-slate-500 font-sans">Input:</span>
                          <pre className="mt-0.5 rounded-lg border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-2 text-slate-800 dark:text-slate-200">
                            {question.visible_test_cases[activeSampleIndex].input_data}
                          </pre>
                        </div>
                        <div>
                          <span className="text-[11px] text-slate-500 font-sans">Expected Output:</span>
                          <pre className="mt-0.5 rounded-lg border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-2 text-emerald-600 dark:text-emerald-400 font-semibold">
                            {question.visible_test_cases[activeSampleIndex].expected_output}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {activeBottomTab === "custom" && (
                  <div className="space-y-2 font-sans">
                    <label className="text-[11px] text-slate-600 dark:text-slate-400 font-semibold">
                      Standard Input (stdin):
                    </label>
                    <textarea
                      rows={4}
                      value={customInput}
                      onChange={(e) => setCustomInput(e.target.value)}
                      placeholder="Paste or type test input values here..."
                      className="w-full rounded-lg border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-2 font-mono text-xs text-slate-900 dark:text-slate-200 focus:border-brand-500 focus:outline-none"
                    />
                  </div>
                )}

                {activeBottomTab === "results" && (
                  <div>
                    {!runResult && !submitResult ? (
                      <p className="text-slate-500 italic py-4 text-center font-sans text-xs">
                        Click "Run Code" or "Submit Solution" to inspect compiler & test outputs.
                      </p>
                    ) : runResult ? (
                      /* Run Code Output */
                      <div className="space-y-3 font-sans">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-800 dark:text-slate-300">Run Status:</span>
                          <Badge
                            variant={
                              runResult.overall_status === "ACCEPTED" || runResult.status === "ACCEPTED"
                                ? "success"
                                : "rose"
                            }
                            size="sm"
                          >
                            {(runResult.overall_status || runResult.status || "RUN_COMPLETE").replace(/_/g, " ")}
                          </Badge>
                          {runResult.execution_time_ms !== undefined && (
                            <span className="text-[11px] text-slate-500 dark:text-slate-400">
                              {runResult.execution_time_ms} ms
                            </span>
                          )}
                        </div>

                        {runResult.test_results?.map((res, i) => (
                          <div
                            key={i}
                            className="rounded-xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-3 font-mono text-xs space-y-1.5"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-slate-800 dark:text-slate-300">
                                Sample Case #{res.order}
                              </span>
                              <Badge
                                variant={res.status === "ACCEPTED" ? "success" : "rose"}
                                size="sm"
                              >
                                {res.status}
                              </Badge>
                            </div>
                            {res.stderr ? (
                              <pre className="text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/20 p-2 rounded-lg whitespace-pre-wrap border border-rose-200 dark:border-rose-900/40">
                                {res.stderr}
                              </pre>
                            ) : (
                              <div className="grid grid-cols-2 gap-2 text-[11px]">
                                <div>
                                  <span className="text-slate-500">Your Output:</span>
                                  <pre className="mt-0.5 text-slate-800 dark:text-slate-200 bg-slate-50 dark:bg-surface-950 p-1.5 rounded border border-slate-200 dark:border-surface-800">
                                    {res.actual_output}
                                  </pre>
                                </div>
                                <div>
                                  <span className="text-slate-500">Expected:</span>
                                  <pre className="mt-0.5 text-emerald-600 dark:text-emerald-400 bg-slate-50 dark:bg-surface-950 p-1.5 rounded border border-slate-200 dark:border-surface-800 font-semibold">
                                    {res.expected_output}
                                  </pre>
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : submitResult ? (
                      /* Official Submit Code Output */
                      <div className="space-y-3 font-sans">
                        <div className="flex items-center justify-between bg-white dark:bg-surface-900 p-3 rounded-xl border border-slate-200 dark:border-surface-800 shadow-sm">
                          <div className="flex items-center gap-2.5">
                            {submitResult.status === "ACCEPTED" ? (
                              <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                            ) : (
                              <XCircle className="h-5 w-5 text-rose-500" />
                            )}
                            <div>
                              <h4 className="font-bold text-sm text-slate-900 dark:text-white">
                                {submitResult.status.replace(/_/g, " ")}
                              </h4>
                              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                                Passed {submitResult.passed_test_cases} of {submitResult.total_test_cases} test cases
                              </p>
                            </div>
                          </div>

                          <div className="text-right">
                            <span className="text-base font-bold text-amber-600 dark:text-amber-400">
                              +{submitResult.score_awarded} pts
                            </span>
                            <p className="text-[10px] text-slate-500">
                              {submitResult.execution_time_ms} ms avg
                            </p>
                          </div>
                        </div>

                        {/* Breakdown */}
                        <div className="space-y-1.5">
                          {submitResult.results.map((r, i) => (
                            <div
                              key={i}
                              className="flex items-center justify-between rounded-lg bg-slate-50 dark:bg-surface-900/60 px-3 py-1.5 border border-slate-200 dark:border-surface-800 text-xs"
                            >
                              <span className="font-mono text-slate-700 dark:text-slate-300">
                                {r.is_visible ? `Sample Case #${r.order}` : `Hidden Test #${r.order}`}
                              </span>
                              <Badge
                                variant={r.status === "PASSED" ? "success" : "rose"}
                                size="sm"
                              >
                                {r.status}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : null}
                  </div>
                )}
              </div>

              {/* Action Buttons Bar */}
              <div className="flex items-center justify-between gap-3 border-t border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-3">
                <span className="text-[11px] text-slate-500 dark:text-slate-400">
                  Sandboxed external evaluation
                </span>

                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => runMutation.mutate()}
                    disabled={runMutation.isPending || submitMutation.isPending}
                    className="flex items-center gap-1.5"
                  >
                    {runMutation.isPending ? (
                      <>
                        <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-400 border-t-transparent" />
                        <span>Running...</span>
                      </>
                    ) : (
                      <>
                        <Play className="h-3.5 w-3.5 text-brand-500" />
                        <span>Run Code</span>
                      </>
                    )}
                  </Button>

                  <Button
                    size="sm"
                    onClick={() => submitMutation.mutate()}
                    disabled={runMutation.isPending || submitMutation.isPending}
                    className="flex items-center gap-1.5"
                  >
                    {submitMutation.isPending ? (
                      <>
                        <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                        <span>Submitting...</span>
                      </>
                    ) : (
                      <>
                        <Send className="h-3.5 w-3.5" />
                        <span>Submit Solution</span>
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
