"use client";

import { FormEvent, useState } from "react";
import { createProject } from "../../services/projects";
import { ProjectCreatePayload } from "../../types/project";

type Props = {
  onSuccess: () => void;
  onError: (message: string) => void;
  onCancel: () => void;
};

const emptyForm: ProjectCreatePayload = {
  name: "",
  artist: "",
  genre: "",
  bpm: 120,
  key: "",
  notes: "",
  status: "draft",
};

export default function ProjectForm({ onSuccess, onError, onCancel }: Props) {
  const [form, setForm] = useState<ProjectCreatePayload>(emptyForm);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();

    const trimmed = {
      ...form,
      name: form.name.trim(),
      artist: form.artist.trim(),
      genre: form.genre.trim(),
      key: form.key.trim(),
      notes: form.notes.trim(),
    };

    if (!trimmed.name || !trimmed.artist || !trimmed.genre || !trimmed.key || !trimmed.notes) {
      onError("Please complete every required field before saving the project.");
      return;
    }

    setIsSubmitting(true);

    try {
      await createProject(trimmed);
      setForm(emptyForm);
      onSuccess();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to create project.";
      onError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="text-sm text-zinc-300">
          <span className="mb-2 block">Project Name</span>
          <input
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-white outline-none focus:border-cyan-500"
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            placeholder="My New Project"
          />
        </label>

        <label className="text-sm text-zinc-300">
          <span className="mb-2 block">Artist</span>
          <input
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-white outline-none focus:border-cyan-500"
            value={form.artist}
            onChange={(event) => setForm({ ...form, artist: event.target.value })}
            placeholder="Artist Name"
          />
        </label>

        <label className="text-sm text-zinc-300">
          <span className="mb-2 block">Genre</span>
          <input
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-white outline-none focus:border-cyan-500"
            value={form.genre}
            onChange={(event) => setForm({ ...form, genre: event.target.value })}
            placeholder="Genre"
          />
        </label>

        <label className="text-sm text-zinc-300">
          <span className="mb-2 block">BPM</span>
          <input
            type="number"
            min="40"
            max="240"
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-white outline-none focus:border-cyan-500"
            value={form.bpm}
            onChange={(event) => setForm({ ...form, bpm: Number(event.target.value) })}
          />
        </label>

        <label className="text-sm text-zinc-300">
          <span className="mb-2 block">Key</span>
          <input
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-white outline-none focus:border-cyan-500"
            value={form.key}
            onChange={(event) => setForm({ ...form, key: event.target.value })}
            placeholder="C minor"
          />
        </label>

        <label className="text-sm text-zinc-300">
          <span className="mb-2 block">Status</span>
          <select
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-white outline-none focus:border-cyan-500"
            value={form.status}
            onChange={(event) => setForm({ ...form, status: event.target.value as ProjectCreatePayload["status"] })}
          >
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="archived">Archived</option>
          </select>
        </label>
      </div>

      <label className="block text-sm text-zinc-300">
        <span className="mb-2 block">Notes</span>
        <textarea
          className="min-h-24 w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-white outline-none focus:border-cyan-500"
          value={form.notes}
          onChange={(event) => setForm({ ...form, notes: event.target.value })}
          placeholder="Capture ideas, references, or production notes..."
        />
      </label>

      <div className="flex justify-end gap-3">
        <button
          type="button"
          className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300"
          onClick={onCancel}
        >
          Cancel
        </button>

        <button
          type="submit"
          className="rounded-lg bg-cyan-600 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Saving..." : "Create Project"}
        </button>
      </div>
    </form>
  );
}
