"use client";

import { FormEvent, useEffect, useState } from "react";
import { Brain, Plus } from "lucide-react";

import AppShell from "../../components/layout/AppShell";
import { createMemory, getMemories } from "../../services/chat";
import { Memory } from "../../types/chat";

export default function MemoryPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [content, setContent] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadMemories = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getMemories();
      setMemories(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to load memories.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadMemories();
  }, []);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const trimmed = content.trim();
    if (!trimmed || isSaving) return;

    setIsSaving(true);
    setError(null);

    try {
      await createMemory({ content: trimmed, category: "preference" });
      setContent("");
      await loadMemories();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to save memory.";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl space-y-6">
        <div>
          <h1 className="flex items-center gap-2 text-3xl font-bold text-white">
            <Brain size={28} className="text-violet-400" />
            Memory
          </h1>
          <p className="mt-2 text-zinc-400">
            Studio memory persists across sessions. Sonic uses this context in the Studio AI.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4">
          <label className="text-sm font-medium text-zinc-300">Save a studio memory</label>
          <textarea
            value={content}
            onChange={(event) => setContent(event.target.value)}
            placeholder="e.g. I always high-pass vocals at 80Hz and use parallel compression on drums"
            rows={3}
            className="mt-2 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-white placeholder:text-zinc-500 focus:border-violet-600 focus:outline-none"
          />
          <button
            type="submit"
            disabled={isSaving || !content.trim()}
            className="mt-3 flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-violet-500 disabled:opacity-40"
          >
            <Plus size={16} />
            {isSaving ? "Saving..." : "Save Memory"}
          </button>
        </form>

        {error ? (
          <div className="rounded-lg border border-red-800/50 bg-red-950/30 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        ) : null}

        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-white">Studio Memories</h2>

          {isLoading ? (
            <p className="text-sm text-zinc-500">Loading...</p>
          ) : memories.length === 0 ? (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 text-sm text-zinc-400">
              No memories yet. Save preferences, workflows, and lessons so Sonic remembers them.
            </div>
          ) : (
            memories.map((memory) => (
              <div
                key={memory.id}
                className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3"
              >
                <div className="mb-1 flex items-center gap-2 text-xs text-zinc-500">
                  <span className="capitalize">{memory.category}</span>
                  <span>·</span>
                  <span>{Math.round(memory.confidence * 100)}% confidence</span>
                </div>
                <p className="text-sm text-zinc-200">{memory.content}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </AppShell>
  );
}
