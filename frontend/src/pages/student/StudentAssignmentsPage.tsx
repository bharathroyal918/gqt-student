import React, { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Code2,
  Search,
  CheckCircle2,
  ArrowRight,
  RefreshCw,
  Cpu,
  Lock,
  Unlock,
  AlertTriangle,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import { studentApi, StudentQuestionItem, ModuleProgressItem } from "../../api/studentApi";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";

export const StudentAssignmentsPage: React.FC = () => {
  const { user } = useAuthStore();
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>("ALL");
  const [selectedModule, setSelectedModule] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ["student", "assignments", user?.id],
    queryFn: () => studentApi.getQuestions(),
    enabled: !!user?.id,
    staleTime: 1000 * 30,
  });

  const questions: StudentQuestionItem[] = useMemo(() => {
    return data?.questions || [];
  }, [data]);

  const modulesProgress: ModuleProgressItem[] = useMemo(() => {
    return data?.modules_progress || [];
  }, [data]);

  // Active module is the first unlocked module that is not yet completed
  const activeModule = useMemo(() => {
    return modulesProgress.find((m) => !m.is_locked && !m.is_completed) || modulesProgress[0];
  }, [modulesProgress]);

  const modulesList = useMemo(() => {
    if (modulesProgress.length > 0) {
      return modulesProgress.map((m) => ({
        order: m.order_index,
        title: m.title,
        count: m.total_questions,
        solved: m.solved_questions,
        is_locked: m.is_locked,
        is_completed: m.is_completed,
        unlock_requirement: m.unlock_requirement,
      }));
    }

    const map = new Map<number, { order: number; title: string; count: number; solved: number; is_locked: boolean; is_completed: boolean; unlock_requirement: string | null }>();
    questions.forEach((q) => {
      if (!map.has(q.module_order)) {
        map.set(q.module_order, {
          order: q.module_order,
          title: q.module_title,
          count: 0,
          solved: 0,
          is_locked: q.is_module_locked || false,
          is_completed: false,
          unlock_requirement: q.module_unlock_requirement || null,
        });
      }
      const entry = map.get(q.module_order)!;
      entry.count += 1;
      if (q.is_solved) entry.solved += 1;
    });
    return Array.from(map.values()).sort((a, b) => a.order - b.order);
  }, [modulesProgress, questions]);

  const selectedModuleInfo = useMemo(() => {
    if (selectedModule === "ALL") return null;
    return modulesList.find((m) => String(m.order) === selectedModule);
  }, [selectedModule, modulesList]);

  const filteredQuestions = useMemo(() => {
    return questions.filter((q) => {
      const matchesDiff =
        selectedDifficulty === "ALL" || q.difficulty === selectedDifficulty;
      const matchesModule =
        selectedModule === "ALL" || String(q.module_order) === selectedModule;
      const matchesStatus =
        selectedStatus === "ALL" ||
        (selectedStatus === "SOLVED" && q.is_solved) ||
        (selectedStatus === "UNSOLVED" && !q.is_solved);
      const matchesSearch =
        !searchQuery.trim() ||
        q.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        q.module_title.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesDiff && matchesModule && matchesStatus && matchesSearch;
    });
  }, [questions, selectedDifficulty, selectedModule, selectedStatus, searchQuery]);

  const stats = useMemo(() => {
    const total = questions.length;
    const solved = questions.filter((q) => q.is_solved).length;
    const totalPoints = questions.reduce((sum, q) => sum + q.points, 0);
    const earnedPoints = questions.reduce((sum, q) => sum + (q.is_solved ? q.points : q.best_score), 0);
    const unlockedCount = questions.filter((q) => !q.is_module_locked).length;
    return { total, solved, totalPoints, earnedPoints, unlockedCount };
  }, [questions]);

  if (isLoading) {
    return (
      <div className="flex h-96 flex-col items-center justify-center">
        <LoadingState message="Loading curriculum coding progression & challenges..." />
      </div>
    );
  }

  if (isError) {
    return (
      <ErrorState
        title="Unable to load coding challenges"
        message={error instanceof Error ? error.message : "Failed to fetch challenges from server."}
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner & Refresh */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <Code2 className="h-7 w-7 text-brand-400" />
            Coding Practice Platform
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Solve algorithmic challenges module-by-module. Complete all problems in each module to unlock the next level.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-1.5 self-start"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin text-brand-500" : ""}`} />
          <span>Refresh</span>
        </Button>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card className="p-4 border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/70 shadow-sm backdrop-blur-sm">
          <p className="text-[11px] uppercase font-semibold tracking-wider text-slate-500 dark:text-slate-400">Total Challenges</p>
          <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
            {stats.total}{" "}
            <span className="text-xs font-normal text-slate-500 dark:text-slate-400">({stats.unlockedCount} unlocked)</span>
          </p>
        </Card>
        <Card className="p-4 border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/70 shadow-sm backdrop-blur-sm">
          <p className="text-[11px] uppercase font-semibold tracking-wider text-slate-500 dark:text-slate-400">Problems Solved</p>
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">{stats.solved}</p>
        </Card>
        <Card className="p-4 border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/70 shadow-sm backdrop-blur-sm">
          <p className="text-[11px] uppercase font-semibold tracking-wider text-slate-500 dark:text-slate-400">Points Earned</p>
          <p className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1">
            {stats.earnedPoints}{" "}
            <span className="text-xs text-slate-500 dark:text-slate-400 font-normal">/ {stats.totalPoints}</span>
          </p>
        </Card>
        <Card className="p-4 border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/70 shadow-sm backdrop-blur-sm">
          <p className="text-[11px] uppercase font-semibold tracking-wider text-slate-500 dark:text-slate-400">Completion Rate</p>
          <p className="text-2xl font-bold text-brand-600 dark:text-brand-400 mt-1">
            {stats.total > 0 ? Math.round((stats.solved / stats.total) * 100) : 0}%
          </p>
        </Card>
      </div>

      {/* Sequential Module Progression Track */}
      {modulesList.length > 0 && (
        <Card className="p-5 border-slate-200 dark:border-surface-800 bg-slate-50/90 dark:bg-surface-900/90 shadow-sm backdrop-blur-sm">
          <div className="flex items-center justify-between gap-2 mb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-brand-600 dark:text-brand-400" />
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 dark:text-slate-100">
                Curriculum Progression Track (17 Modules)
              </h2>
            </div>
            {activeModule && (
              <span className="text-xs text-brand-600 dark:text-brand-400 font-semibold">
                Active: Module {activeModule.order_index} ({activeModule.title})
              </span>
            )}
          </div>

          {/* Module Pills Carousel */}
          <div className="flex gap-2.5 overflow-x-auto pb-2 pt-1 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-700">
            {modulesList.map((m) => {
              const isSelected = selectedModule === String(m.order);
              const isCurrentActive = activeModule?.order_index === m.order;

              return (
                <button
                  key={m.order}
                  onClick={() => setSelectedModule(String(m.order))}
                  className={`shrink-0 text-left rounded-xl p-3 border transition-all duration-200 w-44 flex flex-col justify-between ${
                    isSelected
                      ? "ring-2 ring-brand-500 border-brand-500 bg-brand-50/90 dark:bg-brand-950/50 shadow-sm"
                      : m.is_completed
                      ? "border-emerald-200 dark:border-emerald-800/60 bg-emerald-50/80 dark:bg-emerald-950/30 hover:border-emerald-400"
                      : isCurrentActive
                      ? "border-brand-300 dark:border-brand-700/60 bg-brand-50/80 dark:bg-brand-950/30 shadow-sm hover:border-brand-400"
                      : m.is_locked
                      ? "border-slate-200 dark:border-slate-800/80 bg-slate-100/80 dark:bg-slate-900/60 opacity-75 hover:opacity-95"
                      : "border-slate-200 dark:border-slate-800 bg-white dark:bg-surface-800/60 hover:border-slate-300 dark:hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between gap-1 mb-1.5">
                    <span className="text-[11px] font-mono font-bold text-slate-500 dark:text-slate-400">
                      MOD {m.order}
                    </span>
                    {m.is_completed ? (
                      <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-700 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-900/50 px-1.5 py-0.5 rounded-md">
                        <CheckCircle2 className="h-3 w-3" /> Solved
                      </span>
                    ) : m.is_locked ? (
                      <span className="flex items-center gap-1 text-[10px] font-bold text-slate-600 dark:text-slate-400 bg-slate-200 dark:bg-slate-800 px-1.5 py-0.5 rounded-md">
                        <Lock className="h-3 w-3" /> Locked
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-[10px] font-bold text-brand-700 dark:text-brand-300 bg-brand-100 dark:bg-brand-900/50 px-1.5 py-0.5 rounded-md">
                        <Unlock className="h-3 w-3" /> Active
                      </span>
                    )}
                  </div>

                  <p className="text-xs font-semibold text-slate-900 dark:text-slate-100 line-clamp-1">
                    {m.title}
                  </p>

                  <div className="mt-2.5">
                    <div className="flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400 mb-1 font-medium">
                      <span>{m.solved}/{m.count} solved</span>
                      <span>{m.count > 0 ? Math.round((m.solved / m.count) * 100) : 0}%</span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
                      <div
                        className={`h-full transition-all duration-300 ${
                          m.is_completed
                            ? "bg-emerald-500"
                            : isCurrentActive
                            ? "bg-brand-500"
                            : "bg-slate-400 dark:bg-slate-500"
                        }`}
                        style={{ width: `${m.count > 0 ? (m.solved / m.count) * 100 : 0}%` }}
                      />
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </Card>
      )}

      {/* Module Locked Notification Banner if selected module is locked */}
      {selectedModuleInfo && selectedModuleInfo.is_locked && (
        <motion.div
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-amber-200 dark:border-amber-500/30 bg-amber-50 dark:bg-amber-950/30 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm"
        >
          <div className="flex items-start gap-3.5">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-100 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-500/30">
              <Lock className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-amber-900 dark:text-amber-100 text-base flex items-center gap-2">
                Module {selectedModuleInfo.order}: {selectedModuleInfo.title} is Locked
              </h3>
              <p className="text-xs text-amber-800 dark:text-amber-200/90 mt-1 max-w-2xl leading-relaxed font-medium">
                {selectedModuleInfo.unlock_requirement || "You must solve all problems in the previous module to unlock this module."}
              </p>
            </div>
          </div>

          {activeModule && (
            <Button
              size="sm"
              onClick={() => setSelectedModule(String(activeModule.order_index))}
              className="shrink-0 flex items-center gap-1.5 self-start sm:self-center"
            >
              <span>Go to Active Module ({activeModule.order_index})</span>
              <ChevronRight className="h-3.5 w-3.5" />
            </Button>
          )}
        </motion.div>
      )}

      {/* Filters Bar: Module Dropdown, Difficulty Tabs, Status, Search */}
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Difficulty Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
            {[
              { id: "ALL", label: "All Levels" },
              { id: "EASY", label: "Easy (15 pts)" },
              { id: "MEDIUM", label: "Medium (25 pts)" },
              { id: "HARD", label: "Hard (30 pts)" },
            ].map((diff) => (
              <button
                key={diff.id}
                onClick={() => setSelectedDifficulty(diff.id)}
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all whitespace-nowrap ${
                  selectedDifficulty === diff.id
                    ? "bg-brand-600 text-white shadow-sm"
                    : "bg-slate-100 dark:bg-surface-800/60 text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-surface-800"
                }`}
              >
                {diff.label}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search challenges..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 pl-9 pr-4 py-1.5 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:border-brand-500 focus:outline-none"
            />
          </div>
        </div>

        {/* Secondary Filters: Module Filter & Status Filter */}
        <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-100 dark:border-surface-800/60">
          <span className="text-xs text-slate-600 dark:text-slate-400 font-medium">Filter by:</span>

          <select
            value={selectedModule}
            onChange={(e) => setSelectedModule(e.target.value)}
            className="rounded-lg border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 px-2.5 py-1 text-xs text-slate-800 dark:text-slate-200 font-medium focus:border-brand-500 focus:outline-none"
          >
            <option value="ALL">All Modules ({modulesList.length})</option>
            {modulesList.map((m) => (
              <option key={m.order} value={String(m.order)}>
                {m.is_locked ? "🔒" : m.is_completed ? "✓" : "⚡"} Module {m.order}: {m.title} ({m.solved}/{m.count} solved{m.is_locked ? " - Locked" : ""})
              </option>
            ))}
          </select>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="rounded-lg border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900 px-2.5 py-1 text-xs text-slate-800 dark:text-slate-200 font-medium focus:border-brand-500 focus:outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="SOLVED">Solved Only</option>
            <option value="UNSOLVED">Unsolved Only</option>
          </select>

          {(selectedDifficulty !== "ALL" || selectedModule !== "ALL" || selectedStatus !== "ALL" || searchQuery) && (
            <button
              onClick={() => {
                setSelectedDifficulty("ALL");
                setSelectedModule("ALL");
                setSelectedStatus("ALL");
                setSearchQuery("");
              }}
              className="text-[11px] text-brand-600 dark:text-brand-400 hover:text-brand-700 dark:hover:text-brand-300 font-medium underline underline-offset-2 ml-2"
            >
              Reset Filters
            </button>
          )}

          <span className="ml-auto text-xs text-slate-500 dark:text-slate-400 font-mono font-medium">
            Showing {filteredQuestions.length} of {stats.total}
          </span>
        </div>
      </div>

      {/* Questions List */}
      <div className="space-y-3">
        {filteredQuestions.length === 0 ? (
          <Card className="p-12 text-center border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900">
            <Code2 className="h-10 w-10 text-slate-400 dark:text-slate-500 mx-auto mb-3 opacity-60" />
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">No coding challenges found</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Try adjusting your filters or search terms.</p>
          </Card>
        ) : (
          filteredQuestions.map((q, idx) => {
            const diffVariant =
              q.difficulty === "EASY"
                ? "emerald"
                : q.difficulty === "MEDIUM"
                ? "amber"
                : "rose";

            const isLocked = q.is_module_locked;

            return (
              <motion.div
                key={q.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.02, duration: 0.2 }}
              >
                <Card
                  className={`p-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between transition-all ${
                    isLocked
                      ? "border-slate-200 dark:border-slate-800/80 bg-slate-50/60 dark:bg-slate-900/30 opacity-75"
                      : "border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/90 hover:border-brand-400/60 shadow-sm"
                  }`}
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <div className="flex items-center gap-2">
                        {isLocked && <Lock className="h-4 w-4 text-amber-500 shrink-0" />}
                        <h3 className={`font-bold text-base ${isLocked ? "text-slate-500 dark:text-slate-400" : "text-slate-900 dark:text-white"}`}>
                          {q.title}
                        </h3>
                      </div>

                      <Badge variant={diffVariant} size="sm">
                        {q.difficulty}
                      </Badge>
                      <Badge variant="indigo" size="sm">
                        {q.points} pts
                      </Badge>

                      {isLocked ? (
                        <Badge variant="amber" size="sm" className="flex items-center gap-1">
                          <Lock className="h-3 w-3" />
                          Module Locked
                        </Badge>
                      ) : q.is_solved ? (
                        <Badge variant="success" size="sm" className="flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3" />
                          Solved
                        </Badge>
                      ) : null}
                    </div>

                    <div className="mt-2 flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 flex-wrap font-medium">
                      <span className="text-brand-600 dark:text-brand-400 font-mono font-semibold">
                        Module {q.module_order}: {q.module_title}
                      </span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Cpu className="h-3.5 w-3.5 text-slate-400" />
                        {q.allowed_languages.join(", ")}
                      </span>
                      {q.attempts_count > 0 && (
                        <>
                          <span>•</span>
                          <span>{q.attempts_count} attempt{q.attempts_count !== 1 ? "s" : ""}</span>
                        </>
                      )}
                    </div>

                    {isLocked && q.module_unlock_requirement && (
                      <p className="mt-2 text-xs text-amber-700 dark:text-amber-300 flex items-center gap-1.5 font-medium">
                        <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-amber-600 dark:text-amber-400" />
                        <span>{q.module_unlock_requirement}</span>
                      </p>
                    )}
                  </div>

                  <div className="shrink-0 self-start sm:self-center">
                    {isLocked ? (
                      <Button
                        size="sm"
                        disabled
                        variant="outline"
                        className="flex items-center gap-1.5 opacity-60 cursor-not-allowed text-slate-400 border-slate-200 dark:border-slate-700"
                        title={q.module_unlock_requirement || "Module is locked"}
                      >
                        <Lock className="h-3.5 w-3.5" />
                        <span>Locked</span>
                      </Button>
                    ) : (
                      <Link to={`/assignments/${q.id}`}>
                        <Button size="sm" className="flex items-center gap-1.5">
                          <Code2 className="h-4 w-4" />
                          <span>{q.is_solved ? "Solve Again" : "Open Problem"}</span>
                          <ArrowRight className="h-3.5 w-3.5" />
                        </Button>
                      </Link>
                    )}
                  </div>
                </Card>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
};
