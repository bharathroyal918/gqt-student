import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Github, Sparkles, CheckCircle2 } from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { FormField, Input, Textarea, Select } from "../../components/ui/Form";
import { useToast } from "../../context/ToastContext";

export const StudentProjectSubmitPage: React.FC = () => {
  const navigate = useNavigate();
  const { success } = useToast();
  const [formData, setFormData] = useState({
    project_id: "default-project",
    github_repository_url: "",
    live_demo_url: "",
    notes: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    success("Submission Recorded", "Your project has been submitted for faculty review.");
    navigate("/projects");
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center gap-4">
        <Link to="/projects">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-1.5" />
            Back to Projects
          </Button>
        </Link>
      </div>

      <Card className="p-6 sm:p-8">
        <h1 className="text-2xl font-bold text-white">Submit Capstone Project</h1>
        <p className="text-xs text-slate-400 mt-1">
          Provide your public or authorized GitHub repository URL along with architecture notes.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <FormField label="Select Project" required>
            <Select
              value={formData.project_id}
              onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
              required
            >
              <option value="default-project">Distributed Task Scheduler with Redis & Celery</option>
            </Select>
          </FormField>

          <FormField label="GitHub Repository URL" required>
            <div className="relative">
              <Github className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="https://github.com/username/project-repo"
                className="pl-10 font-mono text-xs"
                value={formData.github_repository_url}
                onChange={(e) => setFormData({ ...formData, github_repository_url: e.target.value })}
                required
              />
            </div>
          </FormField>

          <FormField label="Live Demo URL (Optional)">
            <div className="relative">
              <Sparkles className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="https://project-demo.vercel.app"
                className="pl-10 font-mono text-xs"
                value={formData.live_demo_url}
                onChange={(e) => setFormData({ ...formData, live_demo_url: e.target.value })}
              />
            </div>
          </FormField>

          <FormField label="Submission Notes & Architecture Overview">
            <Textarea
              rows={4}
              placeholder="Outline setup instructions, environment variables, test coverage, and design choices..."
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            />
          </FormField>

          <div className="pt-4 border-t border-surface-800 flex justify-end gap-3">
            <Link to="/projects">
              <Button variant="secondary" type="button">
                Cancel
              </Button>
            </Link>
            <Button type="submit">
              <CheckCircle2 className="h-4 w-4 mr-1.5" />
              Submit Capstone
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
