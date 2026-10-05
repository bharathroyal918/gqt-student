import React, { useState, useEffect, useCallback, useRef } from "react";
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
  Send,
  Columns,
  PanelLeftClose,
  ChevronUp,
  ChevronDown,
  Copy,
  Check,
  ZoomIn,
  ZoomOut,
  Expand,
  Shrink,
  BookOpen,
  Code2,
  LayoutGrid,
  Lock,
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
import { MarkdownView } from "../../components/common/MarkdownView";
import { useToast } from "../../context/ToastContext";

const LANGUAGE_OPTIONS = [
  { value: "python", label: "Python 3.11", monacoLang: "python" },
  { value: "javascript", label: "JavaScript (Node 20)", monacoLang: "javascript" },
  { value: "java", label: "Java 17 (OpenJDK)", monacoLang: "java" },
  { value: "cpp", label: "C++ 20 (GCC)", monacoLang: "cpp" },
  { value: "c", label: "C 11 (GCC)", monacoLang: "c" },
];

type LayoutMode = "split" | "editor" | "description" | "stacked";
type SplitRatio = 35 | 40 | 50 | 60 | 65;
type ConsoleHeight = "collapsed" | "normal" | "expanded";

export const StudentAssignmentDetailPage: React.FC = () => {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const { user, hydrateAuth } = useAuthStore();
  const queryClient = useQueryClient();
  const { success: toastSuccess, error: toastError, info: toastInfo } = useToast();

  const [selectedLanguage, setSelectedLanguage] = useState<string>("python");
  const [sourceCode, setSourceCode] = useState<string>("");
  const [activeLeftTab, setActiveLeftTab] = useState<"description" | "submissions">("description");
  const [activeBottomTab, setActiveBottomTab] = useState<"testcases" | "results" | "custom">("testcases");
  const [customInput, setCustomInput] = useState<string>("");
  const [activeSampleIndex, setActiveSampleIndex] = useState<number>(0);
  const [isCopiedCode, setIsCopiedCode] = useState(false);

  // Layout & Workspace Customization States
  const [layoutMode, setLayoutMode] = useState<LayoutMode>(() => {
    return (localStorage.getItem("gqt_editor_layout") as LayoutMode) || "split";
  });
  const [splitRatio, setSplitRatio] = useState<SplitRatio>(() => {
    const saved = localStorage.getItem("gqt_editor_split");
    return saved ? (parseInt(saved) as SplitRatio) : 50;
  });
  const [consoleHeight, setConsoleHeight] = useState<ConsoleHeight>("normal");
  const [fontSize, setFontSize] = useState<number>(() => {
    const saved = localStorage.getItem("gqt_editor_font_size");
    return saved ? parseInt(saved) : 13;
  });
  const [editorTheme, setEditorTheme] = useState<"vs-dark" | "vs-light" | "hc-black">(() => {
    return (localStorage.getItem("gqt_editor_theme") as any) || "vs-dark";
  });
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showProblemPeek, setShowProblemPeek] = useState(false);

  // Execution Results state
  const [runResult, setRunResult] = useState<CodeRunResponse | null>(null);
  const [submitResult, setSubmitResult] = useState<CodeSubmitResponse | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);

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

  // Draft Code Storage Key
  const draftKey = `gqt_draft_${assignmentId}_${selectedLanguage}`;

  // Initialize or restore code when question or language changes
  useEffect(() => {
    if (!question) return;

    const savedDraft = localStorage.getItem(draftKey);
    if (savedDraft) {
      setSourceCode(savedDraft);
    } else if (question.starter_code && question.starter_code[selectedLanguage]) {
      setSourceCode(question.starter_code[selectedLanguage]);
    } else {
      setSourceCode("");
    }
  }, [question, selectedLanguage, draftKey]);

  // Save code changes to local draft
  const handleCodeChange = (val: string | undefined) => {
    const newCode = val || "";
    setSourceCode(newCode);
    if (assignmentId) {
      localStorage.setItem(draftKey, newCode);
    }
  };

  // Persist Layout Preferences
  const handleLayoutModeChange = (mode: LayoutMode) => {
    setLayoutMode(mode);
    localStorage.setItem("gqt_editor_layout", mode);
  };

  const handleSplitRatioChange = (ratio: SplitRatio) => {
    setSplitRatio(ratio);
    localStorage.setItem("gqt_editor_split", ratio.toString());
  };

  const handleFontSizeChange = (delta: number) => {
    setFontSize((prev) => {
      const next = Math.min(22, Math.max(10, prev + delta));
      localStorage.setItem("gqt_editor_font_size", next.toString());
      return next;
    });
  };

  const handleThemeChange = (theme: "vs-dark" | "vs-light" | "hc-black") => {
    setEditorTheme(theme);
    localStorage.setItem("gqt_editor_theme", theme);
  };

  // Fullscreen toggle
  const toggleFullscreen = useCallback(() => {
    if (!containerRef.current) return;

    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen?.().then(() => setIsFullscreen(true)).catch(() => {
        setIsFullscreen(!isFullscreen);
      });
    } else {
      document.exitFullscreen?.().then(() => setIsFullscreen(false)).catch(() => {
        setIsFullscreen(false);
      });
    }
  }, [isFullscreen]);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, []);

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
      if (consoleHeight === "collapsed") {
        setConsoleHeight("normal");
      }
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
      if (consoleHeight === "collapsed") {
        setConsoleHeight("normal");
      }

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

  // Hotkey handlers (Ctrl+Enter = Run, Ctrl+Shift+Enter = Submit, F11 / Esc = Fullscreen)
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

  const copyCodeToClipboard = () => {
    navigator.clipboard.writeText(sourceCode);
    setIsCopiedCode(true);
    toastInfo("Copied", "Source code copied to clipboard.");
    setTimeout(() => setIsCopiedCode(false), 2000);
  };

  const resetToStarterCode = () => {
    if (question?.starter_code && question.starter_code[selectedLanguage]) {
      setSourceCode(question.starter_code[selectedLanguage]);
      localStorage.removeItem(draftKey);
      toastInfo("Reset Complete", "Code reset to original starter template.");
    }
  };

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

  if (question.is_module_locked) {
    return (
      <div className="mx-auto max-w-2xl py-12 px-4 text-center">
        <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-amber-500/10 text-amber-500 border border-amber-500/20 shadow-lg shadow-amber-500/5 mb-6">
          <Lock className="h-10 w-10" />
        </div>
        <Badge variant="amber" size="md" className="mb-3">
          Module {question.module_order}: {question.module_title} is Locked
        </Badge>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          {question.title}
        </h1>
        <p className="mt-3 text-sm text-slate-600 dark:text-slate-400 max-w-lg mx-auto leading-relaxed">
          {question.module_unlock_requirement || "You must solve all problems in the previous module to unlock this challenge."}
        </p>
        <div className="mt-8 flex items-center justify-center gap-3">
          <Link to="/assignments">
            <Button className="flex items-center gap-2">
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Practice Portal</span>
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  const currentMonacoLang =
    LANGUAGE_OPTIONS.find((l) => l.value === selectedLanguage)?.monacoLang || "python";

  // Calculate dynamic grid spans according to split ratio and layout mode
  const getLeftSpanClass = () => {
    if (layoutMode === "editor") return "hidden";
    if (layoutMode === "description") return "w-full";
    if (layoutMode === "stacked") return "w-full";

    switch (splitRatio) {
      case 35:
        return "lg:w-[35%]";
      case 40:
        return "lg:w-[40%]";
      case 60:
        return "lg:w-[60%]";
      case 65:
        return "lg:w-[65%]";
      default:
        return "lg:w-[50%]";
    }
  };

  const getRightSpanClass = () => {
    if (layoutMode === "description") return "hidden";
    if (layoutMode === "editor") return "w-full";
    if (layoutMode === "stacked") return "w-full";

    switch (splitRatio) {
      case 35:
        return "lg:w-[65%]";
      case 40:
        return "lg:w-[60%]";
      case 60:
        return "lg:w-[40%]";
      case 65:
        return "lg:w-[35%]";
      default:
        return "lg:w-[50%]";
    }
  };

  // Dynamic console height
  const getConsoleHeightClass = () => {
    switch (consoleHeight) {
      case "collapsed":
        return "h-0 overflow-hidden p-0 border-none";
      case "expanded":
        return "h-[360px] max-h-[420px]";
      default:
        return "h-[190px] max-h-[240px]";
    }
  };

  const getEditorHeight = () => {
    if (layoutMode === "editor") {
      return consoleHeight === "collapsed" ? "calc(100vh - 160px)" : consoleHeight === "expanded" ? "380px" : "480px";
    }
    if (consoleHeight === "collapsed") return "560px";
    if (consoleHeight === "expanded") return "320px";
    return "400px";
  };

  return (
    <div
      ref={containerRef}
      className={`space-y-3 transition-all ${isFullscreen ? "fixed inset-0 z-50 bg-surface-950 p-4 overflow-y-auto" : ""
        }`}
    >
      {/* =========================================================================
          TOP ACTION BAR & LAYOUT CONTROLS
         ========================================================================= */}
      <div className="flex flex-col gap-2.5 sm:flex-row sm:items-center sm:justify-between bg-white dark:bg-surface-900 p-3 rounded-2xl border border-slate-200 dark:border-surface-800 shadow-sm">
        {/* Left: Breadcrumbs & Solved Badge */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <Link
            to="/assignments"
            className="flex items-center gap-1.5 rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-50 dark:bg-surface-800/80 px-2.5 py-1 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-surface-700 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Problems</span>
          </Link>

          <span className="text-slate-300 dark:text-slate-700">|</span>

          <span className="text-xs font-mono font-semibold text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-950/40 border border-brand-500/20 px-2 py-0.5 rounded-md">
            Module {question.module_order}
          </span>

          <h1 className="text-xs sm:text-sm font-bold text-slate-900 dark:text-white truncate max-w-[200px] sm:max-w-xs">
            {question.title}
          </h1>

          {question.is_solved && (
            <Badge variant="success" size="sm" className="flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3" />
              Solved (+{question.best_score} pts)
            </Badge>
          )}
        </div>

        {/* Right: Workspace & Layout Customization Controls */}
        <div className="flex items-center gap-1.5 flex-wrap self-end sm:self-auto">
          {/* Layout Mode Switcher */}
          <div className="flex items-center rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-100 dark:bg-surface-950 p-0.5">
            <button
              onClick={() => handleLayoutModeChange("split")}
              className={`flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] font-semibold transition-all ${layoutMode === "split"
                  ? "bg-white dark:bg-surface-800 text-slate-900 dark:text-white shadow-sm"
                  : "text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              title="Split View (Side-by-side)"
            >
              <Columns className="h-3.5 w-3.5" />
              <span className="hidden md:inline">Split</span>
            </button>

            <button
              onClick={() => handleLayoutModeChange("editor")}
              className={`flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] font-semibold transition-all ${layoutMode === "editor"
                  ? "bg-white dark:bg-surface-800 text-slate-900 dark:text-white shadow-sm"
                  : "text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              title="Maximize Code Editor (Focus Mode)"
            >
              <Code2 className="h-3.5 w-3.5 text-brand-500" />
              <span className="hidden md:inline">Max Editor</span>
            </button>

            <button
              onClick={() => handleLayoutModeChange("description")}
              className={`flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] font-semibold transition-all ${layoutMode === "description"
                  ? "bg-white dark:bg-surface-800 text-slate-900 dark:text-white shadow-sm"
                  : "text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              title="Maximize Problem Description"
            >
              <BookOpen className="h-3.5 w-3.5 text-indigo-500" />
              <span className="hidden md:inline">Max Problem</span>
            </button>

            <button
              onClick={() => handleLayoutModeChange("stacked")}
              className={`flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] font-semibold transition-all ${layoutMode === "stacked"
                  ? "bg-white dark:bg-surface-800 text-slate-900 dark:text-white shadow-sm"
                  : "text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              title="Stacked View (Top/Bottom)"
            >
              <LayoutGrid className="h-3.5 w-3.5" />
              <span className="hidden md:inline">Stacked</span>
            </button>
          </div>

          {/* Split Ratio Dropdown (Visible in split mode) */}
          {layoutMode === "split" && (
            <div className="hidden lg:flex items-center rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-100 dark:bg-surface-950 p-0.5">
              {[
                { ratio: 35, label: "35:65" },
                { ratio: 50, label: "50:50" },
                { ratio: 65, label: "65:35" },
              ].map((item) => (
                <button
                  key={item.ratio}
                  onClick={() => handleSplitRatioChange(item.ratio as SplitRatio)}
                  className={`rounded-lg px-2 py-1 text-[10px] font-bold transition-all ${splitRatio === item.ratio
                      ? "bg-white dark:bg-surface-800 text-brand-600 dark:text-brand-400 shadow-sm"
                      : "text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
                    }`}
                  title={`Adjust Split to ${item.label}`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          )}

          {/* Editor Font Size Adjustment */}
          <div className="flex items-center rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-100 dark:bg-surface-950 p-0.5">
            <button
              onClick={() => handleFontSizeChange(-1)}
              className="rounded-lg p-1 text-slate-500 hover:text-slate-900 dark:hover:text-white"
              title="Decrease Editor Font Size"
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </button>
            <span className="px-1.5 text-[10px] font-mono font-bold text-slate-700 dark:text-slate-300">
              {fontSize}px
            </span>
            <button
              onClick={() => handleFontSizeChange(1)}
              className="rounded-lg p-1 text-slate-500 hover:text-slate-900 dark:hover:text-white"
              title="Increase Editor Font Size"
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Fullscreen Workspace Button */}
          <button
            onClick={toggleFullscreen}
            className="flex items-center gap-1 rounded-xl border border-slate-200 dark:border-surface-700 bg-slate-100 dark:bg-surface-950 px-2.5 py-1.5 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-surface-800 transition-colors"
            title={isFullscreen ? "Exit Fullscreen" : "Fullscreen Focus Mode"}
          >
            {isFullscreen ? <Shrink className="h-3.5 w-3.5 text-amber-500" /> : <Expand className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      {/* Floating Peek Problem Description Drawer (when editor is maximized) */}
      {layoutMode === "editor" && (
        <div className="flex items-center justify-between bg-brand-50 dark:bg-brand-950/40 border border-brand-500/20 px-4 py-2 rounded-xl text-xs">
          <div className="flex items-center gap-2 text-brand-700 dark:text-brand-300">
            <Code2 className="h-4 w-4" />
            <span className="font-semibold">Focus Mode Active:</span>
            <span className="text-slate-600 dark:text-slate-400">Editor is maximized. Need problem details?</span>
          </div>
          <button
            onClick={() => setShowProblemPeek(!showProblemPeek)}
            className="flex items-center gap-1 font-bold text-brand-600 dark:text-brand-400 hover:underline"
          >
            {showProblemPeek ? "Hide Problem Statement" : "Peek Problem Statement"}
            {showProblemPeek ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>
        </div>
      )}

      {/* Peek Drawer Content */}
      {layoutMode === "editor" && showProblemPeek && (
        <Card className="p-5 max-h-96 overflow-y-auto border-brand-500/30 bg-white dark:bg-surface-900 shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-surface-800 pb-3 mb-3">
            <h3 className="font-bold text-sm text-slate-900 dark:text-white">{question.title}</h3>
            <Badge variant="indigo" size="sm">{question.points} Pts</Badge>
          </div>
          <MarkdownView content={question.problem_statement} />
        </Card>
      )}

      {/* =========================================================================
          MAIN WORKSPACE LAYOUT CONTAINER
         ========================================================================= */}
      <div
        className={`flex ${layoutMode === "stacked" ? "flex-col" : "flex-col lg:flex-row"
          } gap-3 min-h-[640px] items-stretch`}
      >
        {/* =======================================================================
            LEFT / TOP PANEL: Problem Description & Submissions History
           ======================================================================= */}
        <div className={`${getLeftSpanClass()} flex flex-col transition-all duration-200`}>
          <Card className="p-0 overflow-hidden flex flex-col flex-1 border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 shadow-sm">
            {/* Header Tabs */}
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900/60 px-4 pt-2">
              <div className="flex items-center">
                <button
                  onClick={() => setActiveLeftTab("description")}
                  className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${activeLeftTab === "description"
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
                  className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${activeLeftTab === "submissions"
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

              {/* Collapse button for side-by-side mode */}
              {layoutMode === "split" && (
                <button
                  onClick={() => handleLayoutModeChange("editor")}
                  className="pb-2 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                  title="Collapse problem statement panel"
                >
                  <PanelLeftClose className="h-4 w-4" />
                </button>
              )}
            </div>

            {/* Left Body Content */}
            <div className="p-5 overflow-y-auto max-h-[660px] flex-1 space-y-4">
              {activeLeftTab === "description" ? (
                <>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h2 className="text-lg font-bold text-slate-900 dark:text-white">{question.title}</h2>
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

                    <div className="mt-2.5 flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5 text-brand-500" />
                        {question.time_limit_seconds}s execution limit
                      </span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Cpu className="h-3.5 w-3.5 text-indigo-500" />
                        {question.memory_limit_mb} MB RAM
                      </span>
                    </div>
                  </div>

                  {/* Problem Statement Markdown with Rich Renderer */}
                  <div className="border-t border-slate-200 dark:border-surface-800 pt-4 text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                    <MarkdownView content={question.problem_statement} />
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
                            <pre className="mt-0.5 rounded-lg border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-2 text-slate-800 dark:text-slate-200 overflow-x-auto">
                              {tc.input_data}
                            </pre>
                          </div>
                          <div>
                            <span className="text-slate-500 font-sans text-[11px]">Expected Output:</span>
                            <pre className="mt-0.5 rounded-lg border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-2 text-emerald-600 dark:text-emerald-400 font-semibold overflow-x-auto">
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
                              className={`font-bold ${sub.status === "ACCEPTED"
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

        {/* =======================================================================
            RIGHT / BOTTOM PANEL: Code Editor & Execution Sandbox
           ======================================================================= */}
        <div className={`${getRightSpanClass()} flex flex-col transition-all duration-200`}>
          <Card className="p-0 overflow-hidden flex flex-col flex-1 border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 shadow-sm">
            {/* Editor Toolbar */}
            <div className="flex items-center justify-between gap-2.5 border-b border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-900/80 px-4 py-2 flex-wrap">
              {/* Language & Theme Selectors */}
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

                <select
                  value={editorTheme}
                  onChange={(e) => handleThemeChange(e.target.value as any)}
                  className="hidden sm:block rounded-lg border border-slate-200 dark:border-surface-700 bg-white dark:bg-surface-800 px-2 py-1 text-[11px] text-slate-700 dark:text-slate-300 font-medium focus:outline-none"
                  title="Editor Theme"
                >
                  <option value="vs-dark">Dark Theme</option>
                  <option value="vs-light">Light Theme</option>
                  <option value="hc-black">High Contrast</option>
                </select>
              </div>

              {/* Editor Actions: Copy, Reset, Console Toggle */}
              <div className="flex items-center gap-2">
                {/* Copy Code */}
                <button
                  onClick={copyCodeToClipboard}
                  className="text-xs text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 flex items-center gap-1 transition-colors"
                  title="Copy code to clipboard"
                >
                  {isCopiedCode ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                  <span className="hidden sm:inline">{isCopiedCode ? "Copied" : "Copy"}</span>
                </button>

                {/* Reset to Starter Code */}
                <button
                  onClick={resetToStarterCode}
                  className="text-xs text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 flex items-center gap-1 transition-colors"
                  title="Reset code to original starter template"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Reset</span>
                </button>

                {/* Toggle Console Tray Height */}
                <button
                  onClick={() =>
                    setConsoleHeight((prev) =>
                      prev === "normal" ? "expanded" : prev === "expanded" ? "collapsed" : "normal"
                    )
                  }
                  className="text-xs text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 flex items-center gap-1 border-l border-slate-200 dark:border-surface-700 pl-2 transition-colors"
                  title={`Console: ${consoleHeight} (Click to toggle)`}
                >
                  {consoleHeight === "collapsed" ? (
                    <ChevronUp className="h-3.5 w-3.5 text-brand-500" />
                  ) : consoleHeight === "expanded" ? (
                    <ChevronDown className="h-3.5 w-3.5 text-amber-500" />
                  ) : (
                    <Layers className="h-3.5 w-3.5" />
                  )}
                  <span className="text-[11px] font-semibold uppercase">{consoleHeight}</span>
                </button>
              </div>
            </div>

            {/* Monaco Code Editor */}
            <div
              style={{ height: getEditorHeight() }}
              className="w-full bg-[#1e1e1e] transition-all duration-200 relative"
            >
              <Editor
                height="100%"
                language={currentMonacoLang}
                theme={editorTheme}
                value={sourceCode}
                onChange={handleCodeChange}
                options={{
                  fontSize: fontSize,
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  tabSize: 4,
                  wordWrap: "on",
                  lineNumbersMinChars: 3,
                  cursorBlinking: "smooth",
                  cursorSmoothCaretAnimation: "on",
                  fontFamily: "'JetBrains Mono', 'Fira Code', Menlo, Monaco, 'Courier New', monospace",
                  fontLigatures: true,
                }}
              />
            </div>

            {/* Bottom Console Tabs & Execution Bar */}
            <div className="border-t border-slate-200 dark:border-surface-800 bg-slate-50 dark:bg-surface-950 flex flex-col">
              {/* Console Tabs Header */}
              <div className="flex items-center justify-between border-b border-slate-200 dark:border-surface-800/80 px-4 pt-2 bg-slate-100/60 dark:bg-surface-900/40">
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => {
                      setActiveBottomTab("testcases");
                      if (consoleHeight === "collapsed") setConsoleHeight("normal");
                    }}
                    className={`pb-2 px-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${activeBottomTab === "testcases"
                        ? "border-brand-500 text-brand-600 dark:text-brand-400"
                        : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                      }`}
                  >
                    <Layers className="h-3.5 w-3.5" />
                    Test Cases
                  </button>
                  <button
                    onClick={() => {
                      setActiveBottomTab("custom");
                      if (consoleHeight === "collapsed") setConsoleHeight("normal");
                    }}
                    className={`pb-2 px-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${activeBottomTab === "custom"
                        ? "border-brand-500 text-brand-600 dark:text-brand-400"
                        : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                      }`}
                  >
                    <Terminal className="h-3.5 w-3.5" />
                    Custom Input
                  </button>
                  <button
                    onClick={() => {
                      setActiveBottomTab("results");
                      if (consoleHeight === "collapsed") setConsoleHeight("normal");
                    }}
                    className={`pb-2 px-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${activeBottomTab === "results"
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

                {/* Hotkey Guide & Collapse Toggle */}
                <div className="flex items-center gap-3">
                  <span className="hidden sm:inline text-[11px] text-slate-500">
                    <kbd className="rounded bg-slate-200 dark:bg-surface-800 px-1 py-0.5 font-mono text-slate-700 dark:text-slate-300">
                      Ctrl
                    </kbd>{" "}
                    +{" "}
                    <kbd className="rounded bg-slate-200 dark:bg-surface-800 px-1 py-0.5 font-mono text-slate-700 dark:text-slate-300">
                      Enter
                    </kbd>{" "}
                    to Run
                  </span>
                  <button
                    onClick={() => setConsoleHeight((prev) => (prev === "collapsed" ? "normal" : "collapsed"))}
                    className="pb-1 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                    title={consoleHeight === "collapsed" ? "Expand Console" : "Minimize Console"}
                  >
                    {consoleHeight === "collapsed" ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* Bottom Tab Content Body */}
              <div className={`${getConsoleHeightClass()} p-4 overflow-y-auto text-xs font-mono transition-all duration-200`}>
                {activeBottomTab === "testcases" && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      {question.visible_test_cases.map((tc, idx) => (
                        <button
                          key={tc.id}
                          onClick={() => setActiveSampleIndex(idx)}
                          className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition-all ${activeSampleIndex === idx
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
                          <pre className="mt-0.5 rounded-lg border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-2 text-slate-800 dark:text-slate-200 overflow-x-auto">
                            {question.visible_test_cases[activeSampleIndex].input_data}
                          </pre>
                        </div>
                        <div>
                          <span className="text-[11px] text-slate-500 font-sans">Expected Output:</span>
                          <pre className="mt-0.5 rounded-lg border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-2 text-emerald-600 dark:text-emerald-400 font-semibold overflow-x-auto">
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
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                                <div>
                                  <span className="text-slate-500">Your Output:</span>
                                  <pre className="mt-0.5 text-slate-800 dark:text-slate-200 bg-slate-50 dark:bg-surface-950 p-1.5 rounded border border-slate-200 dark:border-surface-800 overflow-x-auto">
                                    {res.actual_output}
                                  </pre>
                                </div>
                                <div>
                                  <span className="text-slate-500">Expected:</span>
                                  <pre className="mt-0.5 text-emerald-600 dark:text-emerald-400 bg-slate-50 dark:bg-surface-950 p-1.5 rounded border border-slate-200 dark:border-surface-800 font-semibold overflow-x-auto">
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
                <span className="text-[11px] text-slate-500 dark:text-slate-400 hidden sm:inline">
                  Draft auto-saved locally • Press <kbd className="px-1 py-0.5 bg-slate-100 dark:bg-surface-800 rounded font-mono">Ctrl+Enter</kbd>
                </span>

                <div className="flex items-center gap-2 ml-auto">
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

