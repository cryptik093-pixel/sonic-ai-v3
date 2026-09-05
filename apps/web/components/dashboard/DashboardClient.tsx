"use client";

import { useEffect, useState } from "react";
import { getDashboard } from "../../services/api";
import { getProjects } from "../../services/projects";
import StatusCard from "./StatusCard";
import ProjectCard from "./ProjectCard";
import QuickActions from "./QuickActions";
import ActivityFeed from "./ActivityFeed";
import IntelligencePanel from "./IntelligencePanel";
import type { DashboardSummary, Project } from "../../types/project";

export default function DashboardClient() {
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const activeProjectId = projects && projects.length > 0 ? projects[0].id : null;

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const [d, p] = await Promise.all([getDashboard(), getProjects()]);
        if (!mounted) return;
        setDashboard(d);
        setProjects(p);
      } catch (err: any) {
        setError(err?.message ?? "Failed to load dashboard");
      }
    }

    load();

    return () => {
      mounted = false;
    };
  }, []);

  if (error) {
    return (
      <div className="rounded-xl border border-red-700 bg-zinc-900 p-6 text-red-300">
        <strong>Unable to load dashboard:</strong> {error}
      </div>
    );
  }

  if (!dashboard || !projects) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
        <div className="animate-pulse">
          <div className="h-6 w-40 rounded bg-zinc-800 mb-4" />
          <div className="h-40 rounded bg-zinc-800" />
        </div>
      </div>
    );
  }

  return (
    <div>
      <section className="grid grid-cols-3 gap-6">
        <StatusCard title="Projects" value={dashboard.projects.toString()} />
        <StatusCard title="Assets" value={dashboard.assets.toLocaleString()} />
        <StatusCard title="AI Jobs" value={dashboard.ai_jobs.toString()} />
      </section>

      <section className="mt-8 grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          <div>
            <h2 className="mb-4 text-xl font-bold text-white">Recent Projects</h2>

            <div className="grid gap-4">
              {projects.length === 0 ? (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 text-zinc-400">
                  No projects yet. Create your first project from the workspace view.
                </div>
              ) : (
                projects.slice(0, 6).map((project) => (
                  <ProjectCard key={project.id} name={project.name} status={project.status} />
                ))
              )}
            </div>
          </div>

          <div>
            <IntelligencePanel projectId={activeProjectId} />
          </div>
        </div>

        <aside className="col-span-1 flex flex-col gap-4">
          <QuickActions />
          <ActivityFeed />
        </aside>
      </section>
    </div>
  );
}
