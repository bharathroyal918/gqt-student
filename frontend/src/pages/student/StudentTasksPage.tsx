import React from "react";
import { Link } from "react-router-dom";
import { CalendarCheck, Flame, Calendar, ArrowRight } from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";

export const StudentTasksPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Daily Practice Challenges
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Complete daily coding challenges to maintain consistency streaks and earn leaderboard bonus points.
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-2xl border border-rose-500/20 bg-rose-500/10 px-4 py-2 text-rose-400 font-bold text-sm">
          <Flame className="h-5 w-5" />
          <span>Active Streak Challenge</span>
        </div>
      </div>

      <div className="space-y-4">
        <Card className="p-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between hover:border-brand-500/40 transition-colors">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-400 border border-brand-500/20">
              <CalendarCheck className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h3 className="font-bold text-white text-base">Day 14: Dynamic Programming Primer</h3>
                <Badge variant="emerald" size="sm">Available Today</Badge>
                <span className="text-xs font-semibold text-amber-400">20 pts</span>
              </div>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                Solve the Fibonacci Memoization challenge to extend your daily streak.
              </p>
              <div className="mt-2 flex items-center gap-4 text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" />
                  Scheduled Today
                </span>
              </div>
            </div>
          </div>

          <Link to="/assignments">
            <Button size="sm">
              <span>Start Challenge</span>
              <ArrowRight className="h-3.5 w-3.5 ml-1" />
            </Button>
          </Link>
        </Card>
      </div>
    </div>
  );
};
