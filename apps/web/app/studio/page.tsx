"use client";

import { FormEvent, useEffect, useState } from "react";
import { StudioChat } from "../../components/StudioChat";
import { StudioSocketClient } from "../../lib/StudioSocketClient";

type MetadataResponse = {
  asset_id: string;
  filename: string;
  source_sha256: string;
  metadata: {
    bpm_estimate: number | null;
    key_estimate: string | null;
    timbre_hint: string;
    duration_seconds: number;
    analyzed_seconds: number;
    semantic_embedding: null;
    notes: string[];
    [key: string]: unknown;
  };
};

async function readError(response: Response) {
  const body = await response.json().catch(() => ({}));
  throw new Error(typeof body.detail === "string" ? body.detail : `Sonic returned HTTP ${response.status}.`);
}

export default function StudioPage() {
  const [apiOrigin, setApiOrigin] = useState("http://127.0.0.1:8000");
  const [token, setToken] = useState("");
  const [socketClient, setSocketClient] = useState<StudioSocketClient | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [metadata, setMetadata] = useState<MetadataResponse | null>(null);
  const [notice, setNotice] = useState("");

  useEffect(() => () => socketClient?.disconnect(), [socketClient]);

  async function connect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setConnecting(true);
    setNotice("");
    let client: StudioSocketClient | null = null;
    try {
      client = new StudioSocketClient(apiOrigin);
      await client.connect(token);
      setSocketClient(client);
      setNotice("Connected to local Sonic. Brief previews do not modify saved sessions.");
    } catch (error) {
      client?.disconnect();
      setNotice(error instanceof Error ? error.message : "Connection failed.");
    } finally {
      setConnecting(false);
    }
  }

  async function analyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!socketClient || !file || uploading) return;
    setUploading(true);
    setMetadata(null);
    setNotice("Importing audio without modifying the source...");
    try {
      const body = new FormData();
      body.append("file", file);
      const headers = { Authorization: `Bearer ${token}` };
      const uploaded = await fetch(`${socketClient.origin}/workbench/api/imports`, {
        method: "POST", headers, body,
      });
      if (!uploaded.ok) await readError(uploaded);
      const asset = (await uploaded.json()) as { id: string; name: string };
      setNotice(`Imported ${asset.name}; extracting bounded musical descriptors...`);
      const response = await fetch(
        `${socketClient.origin}/workbench/api/studio/assets/${encodeURIComponent(asset.id)}/metadata`,
        { headers },
      );
      if (!response.ok) await readError(response);
      setMetadata((await response.json()) as MetadataResponse);
      setNotice("Sample imported and analyzed. Results are estimates, not confirmed musical facts.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Audio processing failed.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#0b0c10] p-4 text-zinc-100 sm:p-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-blue-400">Omega House · Sonic AI V3</p>
          <h1 className="mt-2 text-3xl font-bold">Browser Studio · Experimental</h1>
          <p className="mt-2 text-sm text-zinc-400">Local preview chat and imported sample metadata. No track editing, cloud calls or automatic mastering.</p>
        </div>
        <form onSubmit={connect} className="mb-5 grid gap-3 rounded-xl border border-zinc-800 bg-zinc-900 p-4 sm:grid-cols-[1fr_1fr_auto]">
          <label className="text-xs text-zinc-400">Local API address
            <input value={apiOrigin} onChange={(e) => setApiOrigin(e.target.value)}
              aria-label="Local Sonic API URL" placeholder="http://127.0.0.1:8000"
              className="mt-1 w-full rounded-md border border-zinc-700 bg-zinc-950 p-2 text-sm text-zinc-100" />
          </label>
          <label className="text-xs text-zinc-400">Operator token (kept in this browser tab only)
            <input type="password" value={token} onChange={(e) => setToken(e.target.value)}
              aria-label="Sonic operator token" autoComplete="off"
              className="mt-1 w-full rounded-md border border-zinc-700 bg-zinc-950 p-2 text-sm text-zinc-100" />
          </label>
          <button disabled={connecting} className="self-end rounded-md bg-blue-700 px-4 py-2 text-sm font-semibold disabled:opacity-40">
            {connecting ? "Connecting…" : socketClient ? "Reconnect" : "Connect"}
          </button>
        </form>
        {notice && <p role="status" className="mb-4 text-sm text-amber-200">{notice}</p>}
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(330px,400px)]">
          <section className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
            <h2 className="text-lg font-semibold">Sample Metadata</h2>
            <p className="mt-1 text-sm text-zinc-400">WAV, FLAC, MP3, OGG, or AIFF, under 100 MB and 20 minutes. The first 90 seconds inform tempo and key estimates.</p>
            <form onSubmit={analyze} className="my-5 flex flex-col gap-3">
              <input type="file" accept=".wav,.flac,.mp3,.ogg,.aiff,.aif,audio/*"
                aria-label="Audio sample" onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="block w-full text-sm file:mr-3 file:rounded file:border-0 file:bg-zinc-700 file:px-3 file:py-2 file:text-zinc-100" />
              <button type="submit" disabled={!socketClient || !file || uploading}
                className="rounded-md bg-blue-700 px-4 py-2 text-sm font-semibold disabled:opacity-40">
                {uploading ? "Analyzing…" : "Import + Analyze Sample"}
              </button>
            </form>
            {metadata ? (
              <div className="space-y-3 rounded-lg border border-zinc-700 bg-zinc-950 p-4">
                <p className="break-all text-xs text-zinc-400">{metadata.filename}</p>
                <div className="grid grid-cols-2 gap-4">
                  <div><p className="text-xs text-zinc-500">Tempo estimate</p><p className="text-xl">{metadata.metadata.bpm_estimate ?? "Unknown"} <span className="text-xs">BPM</span></p></div>
                  <div><p className="text-xs text-zinc-500">Key estimate</p><p className="text-xl">{metadata.metadata.key_estimate ?? "Unknown"}</p></div>
                  <div><p className="text-xs text-zinc-500">Timbre hint</p><p>{metadata.metadata.timbre_hint}</p></div>
                  <div><p className="text-xs text-zinc-500">Duration</p><p>{metadata.metadata.duration_seconds}s</p></div>
                </div>
                <p className="text-xs text-zinc-500">Analyzed {metadata.metadata.analyzed_seconds}s; no neural semantic embedding generated.</p>
                <p className="text-xs text-zinc-500">{metadata.metadata.notes.join(" ")}</p>
              </div>
            ) : <p className="text-sm text-zinc-500">No sample analyzed this session.</p>}
          </section>
          {socketClient ? (
            <StudioChat socketClient={socketClient} getCurrentProjectState={() => null} />
          ) : (
            <section className="flex h-[550px] items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900 p-6 text-center text-sm text-zinc-400">
              Connect to the local Sonic API to preview production briefs.
            </section>
          )}
        </div>
      </div>
    </main>
  );
}
