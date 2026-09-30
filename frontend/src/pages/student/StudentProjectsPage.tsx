import React from "react";
import { Link } from "react-router-dom";
import { FolderGit2, Plus, ArrowRight } from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";

export const StudentProjectsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Capstone Projects
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Build full-stack software systems, submit GitHub repositories, and receive qualitative faculty grading.
          </p>
        </div>

        <Link to="/projects/submit">
          <Button>
            <Plus className="h-4 w-4 mr-1.5" />
            Submit Capstone
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card className="p-6 flex flex-col justify-between hover:border-brand-500/40 transition-colors">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-500/10 text-brand-400 border border-brand-500/20">
                <FolderGit2 className="h-6 w-6" />
              </div>
              <Badge variant="indigo">100 Points</Badge>
            </div>
            <h3 className="text-lg font-bold text-white">Distributed Task Scheduler with Redis & Celery</h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Design a production background task queue consuming asynchronous execution jobs with priority routing and retry backoff.
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-surface-800 flex items-center justify-between">
            <span className="text-xs text-slate-400">Course Track: Full-Stack</span>
            <Link to="/projects/submit">
              <Button size="sm">
                <span>Submit Deliverable</span>
                <ArrowRight className="h-3.5 w-3.5 ml-1" />
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};
