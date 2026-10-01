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
} from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import { studentApi } from "../../api/studentApi";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";

export const StudentAssignmentsPage: React.FC = () => {
  const { user } = useAuthStore();
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const {
    data: questions,
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

  const filteredQuestions = useMemo(() => {
    if (!questions) return [];
    return questions.filter((q) => {
      const matchesDiff =
        selectedDifficulty === "ALL" || q.difficulty === selectedDifficulty;
      const matchesSearch =
        !searchQuery.trim() ||
        q.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        q.module_title.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesDiff && matchesSearch;
    });
  }, [questions, selectedDifficulty, searchQuery]);

  const stats = useMemo(() => {
    if (!questions) return { total: 0, solved: 0, totalPoints: 0, earnedPoints: 0 };
    const total = questions.length;
    const solved = questions.filter((q) => q.is_solved).length;
    const totalPoints = questions.reduce((sum, q) => sum + q.points, 0);
    const earnedPoints = questions.reduce((sum, q) => sum + (q.is_solved ? q.points : q.best_score), 0);
    return { total, solved, totalPoints, earnedPoints };
  }, [questions]);

  if (isLoading) {
    return (
      <div className="flex h-96 flex-col items-center justify-center">
        <LoadingState message="Loading coding challenges catalog..." />
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
      {/* Top Banner & Stats */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <Code2 className="h-7 w-7 text-brand-400" />
            Coding Practice Platform
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Solve algorithmic problems in Python, Java, C, C++, or JavaScript with automated sandboxed evaluation.
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
        <Card className="p-4">
          <p className="text-[11px] uppercase font-semibold tracking-wider text-slate-400">Total Challenges</p>
          <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{stats.total}</p>
        </Card>
        <Card className="p-4">
          <p className="text-[11px] uppercase font-semibold tracking-wider text-slate-400">Solved</p>
          <p className="text-2xl font-bold text-emerald-500 mt-1">{stats.solved}</p>
        </Card>
        <Card className="p-4">
          <p className="text-[11px] uppercase font-semibold tracking-wider text-slate-400">Points Earned</p>
          <p className="text-2xl font-bold text-amber-500 mt-1">{stats.earnedPoints} <span className="text-xs text-slate-400 font-normal">/ {stats.totalPoints}</span></p>
        </Card>
        <Card className="p-4">
          <p className="text-[11px] uppercase font-semibold tracking-wider text-slate-400">Completion Rate</p>
          <p className="text-2xl font-bold text-brand-500 mt-1">
            {stats.total > 0 ? Math.round((stats.solved / stats.total) * 100) : 0}%
          </p>
        </Card>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          {(["ALL", "EASY", "MEDIUM", "HARD"] as const).map((diff) => (
            <button
              key={diff}
              onClick={() => setSelectedDifficulty(diff)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                selectedDifficulty === diff
                  ? "bg-brand-600 text-white shadow-sm"
                  : "bg-slate-100 dark:bg-surface-800/60 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-surface-800"
              }`}
            >
              {diff === "ALL" ? "All Levels" : diff.charAt(0) + diff.slice(1).toLowerCase()}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search problems..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-xl border border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-900/90 pl-9 pr-4 py-1.5 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:border-brand-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Questions Grid */}
      <div className="space-y-3">
        {filteredQuestions.length === 0 ? (
          <Card className="p-12 text-center">
            <Code2 className="h-10 w-10 text-slate-500 mx-auto mb-3 opacity-60" />
            <p className="text-sm font-semibold text-slate-300">No coding challenges found</p>
            <p className="text-xs text-slate-500 mt-1">Try adjusting your filters or search terms.</p>
          </Card>
        ) : (
          filteredQuestions.map((q, idx) => {
            const diffVariant =
              q.difficulty === "EASY"
                ? "emerald"
                : q.difficulty === "MEDIUM"
                ? "amber"
                : "rose";

            return (
              <motion.div
                key={q.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.03, duration: 0.2 }}
              >
                <Card className="p-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between hover:border-brand-500/40 transition-all">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <h3 className="font-bold text-slate-900 dark:text-white text-base">
                        {q.title}
                      </h3>
                      <Badge variant={diffVariant} size="sm">
                        {q.difficulty}
                      </Badge>
                      <Badge variant="indigo" size="sm">
                        {q.points} pts
                      </Badge>
                      {q.is_solved && (
                        <Badge variant="success" size="sm" className="flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3" />
                          Solved
                        </Badge>
                      )}
                    </div>

                    <div className="mt-2 flex items-center gap-3 text-xs text-slate-400 flex-wrap">
                      <span className="text-brand-400 font-mono">
                        Module {q.module_order}: {q.module_title}
                      </span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Cpu className="h-3 w-3" />
                        {q.allowed_languages.join(", ")}
                      </span>
                      {q.attempts_count > 0 && (
                        <>
                          <span>•</span>
                          <span>{q.attempts_count} attempt{q.attempts_count !== 1 ? "s" : ""}</span>
                        </>
                      )}
                    </div>
                  </div>

                  <Link to={`/assignments/${q.id}`} className="shrink-0 self-start sm:self-center">
                    <Button size="sm" className="flex items-center gap-1.5">
                      <Code2 className="h-4 w-4" />
                      <span>{q.is_solved ? "Solve Again" : "Open Problem"}</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Button>
                  </Link>
                </Card>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
};
