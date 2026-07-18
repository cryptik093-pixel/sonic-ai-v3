"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import ProjectForm from "./ProjectForm";
import ProjectList from "./ProjectList";
import { getProjects } from "../../services/projects";
import { Project } from "../../types/project";

export default function ProjectWorkspace() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const loadProjects = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getProjects();
      setProjects(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to load projects.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadProjects();
  }, []);

  const handleSuccess = async () => {
    setFeedback("Project created successfully.");
    setIsModalOpen(false);
    await loadProjects();
  };

  const handleError = (message: string) => {
    setFeedback(message);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 rounded-2xl border border-zinc-800 bg-zinc-900/70 p-6 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Project Workspace</h1>
          <p className="mt-2 text-zinc-400">Create and track projects from a single workspace.</p>
        </div>

        <button
          className="rounded-lg bg-cyan-600 px-4 py-2 font-semibold text-white transition hover:bg-cyan-500"
          onClick={() => setIsModalOpen(true)}
        >
          New Project
        </button>
      </div>

      {feedback ? (
        <div className="rounded-lg border border-cyan-700/40 bg-cyan-950/40 px-4 py-3 text-sm text-cyan-200">
          {feedback}
        </div>
      ) : null}

      <ProjectList projects={projects} isLoading={isLoading} error={error} />

      {isModalOpen && createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/80 p-4">
          <div className="w-full max-w-3xl rounded-2xl border border-zinc-800 bg-zinc-900 p-6 shadow-2xl">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-white">Create Project</h2>
                <p className="mt-1 text-sm text-zinc-400">Add a new project and make it visible immediately.</p>
              </div>
              <button className="text-zinc-400" onClick={() => setIsModalOpen(false)}>
                Close
              </button>
            </div>

            <ProjectForm
              onSuccess={handleSuccess}
              onError={handleError}
              onCancel={() => setIsModalOpen(false)}
            />
          </div>
        </div>,
        document.body,
      )}
    </div>
  );
}
