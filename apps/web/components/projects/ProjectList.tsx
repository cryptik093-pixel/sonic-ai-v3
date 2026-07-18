import { Project } from "../../types/project";

type Props = {
  projects: Project[];
  isLoading: boolean;
  error: string | null;
};

export default function ProjectList({ projects, isLoading, error }: Props) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 text-zinc-400">
        Loading projects...
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-500/40 bg-rose-950/40 p-6 text-rose-200">
        {error}
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-zinc-700 bg-zinc-900/70 p-6 text-zinc-400">
        No projects yet. Create your first one to get started.
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {projects.map((project) => (
        <div key={project.id} className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-lg font-semibold text-white">{project.name}</h3>
              <p className="mt-1 text-sm text-cyan-400">{project.artist}</p>
            </div>
            <span className="rounded-full bg-zinc-800 px-3 py-1 text-xs uppercase tracking-wide text-zinc-300">
              {project.status}
            </span>
          </div>

          <div className="mt-4 space-y-2 text-sm text-zinc-400">
            <p>Genre: {project.genre}</p>
            <p>BPM: {project.bpm}</p>
            <p>Key: {project.key}</p>
          </div>

          <p className="mt-4 text-sm text-zinc-400">{project.notes}</p>
        </div>
      ))}
    </div>
  );
}
