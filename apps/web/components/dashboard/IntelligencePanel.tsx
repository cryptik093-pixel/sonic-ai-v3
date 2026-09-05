"use client";

import { useEffect, useState } from "react";
import { getProjectIntelligenceSnapshot, type IntelligenceSnapshot } from "../../services/intelligence";

interface IntelligencePanelProps {
  projectId: number | null;
  assetId?: number | null;
}

export default function IntelligencePanel({ projectId, assetId }: IntelligencePanelProps) {
  const [snapshot, setSnapshot] = useState<IntelligenceSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (projectId === null) {
      setSnapshot(null);
      return;
    }

    let mounted = true;

    async function load() {
      try {
        const data = await getProjectIntelligenceSnapshot(projectId, assetId ?? null);
        if (mounted) setSnapshot(data);
      } catch (err) {
        if (mounted) setError(err instanceof Error ? err.message : "Unable to load intelligence snapshot.");
      }
    }

    void load();
    return () => {
      mounted = false;
    };
  }, [projectId, assetId]);

  if (projectId === null) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 text-zinc-400">
        Create a project to unlock the Sonic intelligence layer.
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-700 bg-zinc-900 p-6 text-red-300">{error}</div>
    );
  }

  if (!snapshot) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
        <div className="animate-pulse space-y-3">
          <div className="h-5 w-32 rounded bg-zinc-800" />
          <div className="h-4 w-full rounded bg-zinc-800" />
          <div className="h-4 w-4/5 rounded bg-zinc-800" />
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-cyan-700/40 bg-zinc-900 p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Asset Intelligence</h3>
        <span className="rounded-full border border-cyan-700/50 bg-cyan-950/70 px-2 py-1 text-xs text-cyan-200">
          {snapshot.checkpoint?.persistence_decision ?? "pending"}
        </span>
      </div>

      <p className="mb-4 text-sm text-zinc-300">{snapshot.summary}</p>

      <div className="grid gap-3 text-sm md:grid-cols-2">
        <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
          <div className="text-zinc-400">Asset</div>
          <div className="mt-1 text-white">{snapshot.asset?.filename ?? "No asset"}</div>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
          <div className="text-zinc-400">Sample Rate</div>
          <div className="mt-1 text-white">{snapshot.analysis.sample_rate ?? "unknown"} Hz</div>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
          <div className="text-zinc-400">Relevance</div>
          <div className="mt-1 text-white">{snapshot.checkpoint?.relevance_score ?? 0}</div>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
          <div className="text-zinc-400">DNA Signals</div>
          <div className="mt-1 text-white">{snapshot.dna.signals.length}</div>
        </div>
      </div>

      <div className="mt-4">
        <h4 className="mb-2 text-sm font-semibold uppercase tracking-wide text-zinc-400">Recent memory</h4>
        <div className="space-y-2 text-sm text-zinc-300">
          {snapshot.memories.length === 0 ? (
            <div className="rounded border border-zinc-800 bg-zinc-950 p-3 text-zinc-500">No retained memory yet.</div>
          ) : (
            snapshot.memories.slice(0, 3).map((memory) => (
              <div key={memory.id} className="rounded border border-zinc-800 bg-zinc-950 p-3">
                {memory.content}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
