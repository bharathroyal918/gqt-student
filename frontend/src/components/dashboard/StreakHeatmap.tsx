import React, { useState, useMemo } from "react";
import { Flame, Trophy, Calendar, Zap, Info, CheckCircle2 } from "lucide-react";
import { ActivityHeatmapData, ActivityHeatmapRecord } from "../../api/studentApi";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";

interface StreakHeatmapProps {
  data?: ActivityHeatmapData | null;
  isLoading?: boolean;
}

export const StreakHeatmap: React.FC<StreakHeatmapProps> = ({ data, isLoading = false }) => {
  const [hoveredDay, setHoveredDay] = useState<ActivityHeatmapRecord | null>(null);

  // Organize 365 records into 52/53 columns (weeks), each containing up to 7 days
  const { weeks, monthHeaders } = useMemo(() => {
    if (!data?.records || data.records.length === 0) {
      // Fallback empty grid of 52 weeks x 7 days
      const emptyWeeks: ActivityHeatmapRecord[][] = [];
      const now = new Date();
      for (let w = 51; w >= 0; w--) {
        const week: ActivityHeatmapRecord[] = [];
        for (let d = 0; d < 7; d++) {
          const dateObj = new Date(now.getTime() - (w * 7 + (6 - d)) * 86400000);
          week.push({
            date: dateObj.toISOString().split("T")[0],
            day_name: dateObj.toLocaleDateString("en-US", { weekday: "short" }),
            month_name: dateObj.toLocaleDateString("en-US", { month: "short" }),
            month_index: dateObj.getMonth() + 1,
            day_of_week: (dateObj.getDay() + 6) % 7, // 0 = Mon, 6 = Sun
            count: 0,
            points: 0,
            level: 0,
            is_today: w === 0 && d === 6,
          });
        }
        emptyWeeks.push(week);
      }
      return { weeks: emptyWeeks, monthHeaders: [] };
    }

    const records = data.records;
    const weeksList: ActivityHeatmapRecord[][] = [];
    let currentWeek: ActivityHeatmapRecord[] = [];

    // Map month start columns
    const months: Array<{ name: string; colIndex: number }> = [];
    let lastMonth = "";

    records.forEach((record) => {
      currentWeek.push(record);
      if (currentWeek.length === 7) {
        weeksList.push(currentWeek);
        if (record.month_name !== lastMonth) {
          months.push({ name: record.month_name, colIndex: weeksList.length - 1 });
          lastMonth = record.month_name;
        }
        currentWeek = [];
      }
    });

    if (currentWeek.length > 0) {
      weeksList.push(currentWeek);
    }

    return { weeks: weeksList, monthHeaders: months };
  }, [data]);

  const currentStreak = data?.current_streak ?? 0;
  const longestStreak = data?.longest_streak ?? 0;
  const totalActiveDays = data?.total_active_days ?? 0;
  const totalSubmissionsYear = data?.total_submissions_year ?? 0;
  const solvedToday = data?.solved_today ?? false;

  const getCellColor = (level: number, isToday: boolean) => {
    switch (level) {
      case 1:
        return "bg-emerald-300 dark:bg-emerald-600/70 border-emerald-400 dark:border-emerald-500/80 hover:ring-2 hover:ring-emerald-400";
      case 2:
        return "bg-emerald-500 dark:bg-emerald-500 border-emerald-600 dark:border-emerald-400 hover:ring-2 hover:ring-emerald-300 shadow-sm shadow-emerald-500/20";
      case 3:
        return "bg-emerald-600 dark:bg-emerald-400 border-emerald-700 dark:border-emerald-300 hover:ring-2 hover:ring-emerald-200 shadow-md shadow-emerald-500/30";
      default:
        return isToday
          ? "bg-slate-100 dark:bg-surface-800/90 border-2 border-brand-500/60 dark:border-brand-400/60 hover:bg-slate-200 dark:hover:bg-surface-700"
          : "bg-slate-100/90 dark:bg-surface-900/90 border border-slate-200/60 dark:border-surface-800/80 hover:border-brand-500/40 hover:bg-slate-200/70 dark:hover:bg-surface-800";
    }
  };

  return (
    <Card className={`overflow-hidden border-slate-200 dark:border-surface-800 bg-white dark:bg-gradient-to-br dark:from-surface-900 dark:via-surface-900 dark:to-surface-950 p-5 sm:p-6 shadow-sm transition-all ${isLoading ? "opacity-60 animate-pulse pointer-events-none" : ""}`}>
      {/* Header & Streak Telemetry Banner */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b border-slate-100 dark:border-surface-800/80 pb-5">
        <div className="flex items-center gap-3.5">
          <div className="relative flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-500/20 via-rose-500/20 to-brand-500/20 text-rose-500 dark:text-rose-400 border border-rose-500/20 shadow-sm">
            <Flame className="h-6 w-6 animate-pulse" />
            {solvedToday && (
              <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-emerald-500 text-[9px] font-bold text-white shadow ring-2 ring-white dark:ring-surface-900">
                ✓
              </span>
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Problem Solving Streak & Activity
              </h3>
              <Badge variant={solvedToday ? "emerald" : currentStreak > 0 ? "amber" : "neutral"} size="sm">
                {solvedToday ? "Active Today" : currentStreak > 0 ? "Due Today" : "Inactive"}
              </Badge>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {solvedToday
                ? "Awesome work! You solved a problem today and maintained your continuous streak."
                : "Solve at least 1 coding problem or assignment question daily to advance your streak."}
            </p>
          </div>
        </div>

        {/* 4 Quick Stat Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          <div className="flex items-center gap-2 rounded-xl bg-slate-50 dark:bg-surface-800/60 px-3 py-2 border border-slate-200/70 dark:border-surface-700/60">
            <Flame className="h-4 w-4 text-rose-500" />
            <div>
              <div className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Current</div>
              <div className="text-xs font-bold text-slate-900 dark:text-white">{currentStreak} {currentStreak === 1 ? "day" : "days"}</div>
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-xl bg-slate-50 dark:bg-surface-800/60 px-3 py-2 border border-slate-200/70 dark:border-surface-700/60">
            <Trophy className="h-4 w-4 text-amber-500" />
            <div>
              <div className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Longest</div>
              <div className="text-xs font-bold text-slate-900 dark:text-white">{longestStreak} {longestStreak === 1 ? "day" : "days"}</div>
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-xl bg-slate-50 dark:bg-surface-800/60 px-3 py-2 border border-slate-200/70 dark:border-surface-700/60">
            <Calendar className="h-4 w-4 text-indigo-500" />
            <div>
              <div className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Active Days</div>
              <div className="text-xs font-bold text-slate-900 dark:text-white">{totalActiveDays}</div>
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-xl bg-slate-50 dark:bg-surface-800/60 px-3 py-2 border border-slate-200/70 dark:border-surface-700/60">
            <Zap className="h-4 w-4 text-emerald-500" />
            <div>
              <div className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Total Solved</div>
              <div className="text-xs font-bold text-slate-900 dark:text-white">{totalSubmissionsYear}</div>
            </div>
          </div>
        </div>
      </div>

      {/* LeetCode Activity Grid Container */}
      <div className="mt-5 space-y-2">
        <div className="overflow-x-auto pb-2 scrollbar-thin">
          <div className="inline-block min-w-full">
            {/* Month Labels */}
            <div className="flex text-[11px] font-medium text-slate-400 dark:text-slate-500 pl-8 mb-1.5 gap-1 select-none">
              {monthHeaders.map((m, idx) => (
                <div
                  key={`${m.name}-${idx}`}
                  style={{ minWidth: "48px" }}
                  className="truncate"
                >
                  {m.name}
                </div>
              ))}
            </div>

            {/* Grid Container: Weekday labels on left + 52 Week Columns */}
            <div className="flex gap-2 items-start">
              {/* Day Labels (Mon, Wed, Fri) */}
              <div className="flex flex-col justify-between text-[10px] font-semibold text-slate-400 dark:text-slate-500 pt-0.5 h-[108px] w-6 select-none shrink-0">
                <span>Mon</span>
                <span>Wed</span>
                <span>Fri</span>
                <span>Sun</span>
              </div>

              {/* Heatmap Matrix: Columns of Weeks */}
              <div className="flex gap-[3.5px] items-center">
                {weeks.map((week, colIdx) => (
                  <div key={`col-${colIdx}`} className="flex flex-col gap-[3.5px]">
                    {week.map((day) => {
                      const colorClass = getCellColor(day.level, day.is_today);
                      return (
                        <div
                          key={day.date}
                          onMouseEnter={() => setHoveredDay(day)}
                          onMouseLeave={() => setHoveredDay(null)}
                          className={`h-[12px] w-[12px] rounded-[3px] cursor-pointer transition-all duration-100 ${colorClass}`}
                          title={`${day.count} solved on ${day.date}`}
                        />
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Dynamic Tooltip Bar & Legend Footer */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-3 border-t border-slate-100 dark:border-surface-800/80 text-xs text-slate-500 dark:text-slate-400">
          {/* Hovered Day Status */}
          <div className="flex items-center gap-2 min-h-[22px]">
            {hoveredDay ? (
              <div className="flex items-center gap-2 animate-fadeIn">
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {new Date(hoveredDay.date).toLocaleDateString("en-US", {
                    weekday: "short",
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}:
                </span>
                {hoveredDay.count > 0 ? (
                  <span className="inline-flex items-center gap-1 font-bold text-emerald-600 dark:text-emerald-400">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    {hoveredDay.count} {hoveredDay.count === 1 ? "problem" : "problems"} solved ({hoveredDay.points} pts)
                  </span>
                ) : (
                  <span className="text-slate-400 dark:text-slate-500">
                    No problem submissions recorded on this day.
                  </span>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-1.5 text-slate-400 dark:text-slate-500 text-[11px]">
                <Info className="h-3.5 w-3.5" />
                <span>Hover over any box to inspect daily problem-solving submissions.</span>
              </div>
            )}
          </div>

          {/* Color Scale Legend */}
          <div className="flex items-center gap-2 text-[11px] self-end sm:self-center">
            <span className="text-slate-400 dark:text-slate-500">Less</span>
            <div className="flex items-center gap-1">
              <div className="h-2.5 w-2.5 rounded-[2px] bg-slate-100 dark:bg-surface-900 border border-slate-200/60 dark:border-surface-800" title="0 submissions" />
              <div className="h-2.5 w-2.5 rounded-[2px] bg-emerald-300 dark:bg-emerald-600/70 border border-emerald-400" title="1-2 submissions" />
              <div className="h-2.5 w-2.5 rounded-[2px] bg-emerald-500 border border-emerald-600" title="3-4 submissions" />
              <div className="h-2.5 w-2.5 rounded-[2px] bg-emerald-600 dark:bg-emerald-400 border border-emerald-700" title="5+ submissions" />
            </div>
            <span className="text-slate-400 dark:text-slate-500">More</span>
          </div>
        </div>
      </div>
    </Card>
  );
};
