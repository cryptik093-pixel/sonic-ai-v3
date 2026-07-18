import AppShell from "../../components/layout/AppShell";
import { getDashboard } from "../../services/api";
import { getProjects } from "../../services/projects";
import StatusCard from "../../components/dashboard/StatusCard";
import ProjectCard from "../../components/dashboard/ProjectCard";
import type { DashboardSummary, Project } from "../../types/project";

const fallbackDashboard: DashboardSummary = {
  projects: 0,
  assets: 0,
  ai_jobs: 0,
  status: "Backend Offline",
};

export default async function DashboardPage() {
  let dashboard: DashboardSummary = fallbackDashboard;
  let projects: Project[] = [];

  try {
    [dashboard, projects] = await Promise.all([getDashboard(), getProjects()]);
  } catch {
    dashboard = fallbackDashboard;
    projects = [];
  }

  return (
    <AppShell>
      <section className="grid grid-cols-3 gap-6">
        <StatusCard title="Projects" value={dashboard.projects.toString()} />
        <StatusCard title="Assets" value={dashboard.assets.toLocaleString()} />
        <StatusCard title="AI Jobs" value={dashboard.ai_jobs.toString()} />
      </section>

      <section className="mt-8">
        <h2 className="mb-4 text-xl font-bold text-white">Recent Projects</h2>

        <div className="grid gap-4">
          {projects.length === 0 ? (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 text-zinc-400">
              No projects yet. Create your first project from the workspace view.
            </div>
          ) : (
            projects.slice(0, 3).map((project) => (
              <ProjectCard key={project.id} name={project.name} status={project.status} />
            ))
          )}
        </div>
      </section>
    </AppShell>
  );
}