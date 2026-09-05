const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = "Request failed";
    try {
      const payload = await response.json();
      detail = payload?.detail ?? payload?.message ?? detail;
    } catch {
      detail = response.statusText || detail;
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export interface IntelligenceSnapshot {
  asset: {
    id: number;
    project_id: number;
    filename: string;
    filepath: string;
    file_type: string;
    duration: number | null;
    bpm: number | null;
    key: string | null;
    sample_rate: number | null;
    channels: number | null;
    created_at?: string;
  } | null;
  analysis: {
    file_type: string | null;
    duration: number | null;
    sample_rate: number | null;
    channels: number | null;
    confidence: number | null;
    provenance: string | null;
  };
  checkpoint: {
    id: number;
    asset_id: number | null;
    project_id: number | null;
    relevance_score: number;
    value_score: number;
    confidence_score: number;
    novelty_score: number;
    creative_signal_score: number;
    persistence_decision: string;
    reason: string;
    facts: string[];
    observations: string[];
    candidate_insights: string[];
    creator_dna_signals: string[];
    value_class: string;
    created_at: string;
  } | null;
  dna: {
    project_id: number | null;
    signals: Array<{
      category: string;
      signal: string;
      strength: number;
      confidence: number;
      evidence_count: number;
    }>;
    version: string;
    status: string;
  };
  memories: Array<{
    id: number;
    memory_type: string;
    category: string;
    content: string;
    project_id: number | null;
    confidence: number;
    source: string;
    created_at: string;
    updated_at: string;
  }>;
  summary: string;
}

export async function getProjectIntelligenceSnapshot(projectId: number | null, assetId?: number | null): Promise<IntelligenceSnapshot> {
  const params = new URLSearchParams();
  if (projectId !== null && projectId !== undefined) params.set("project_id", String(projectId));
  if (assetId !== null && assetId !== undefined) params.set("asset_id", String(assetId));
  const query = params.toString();
  return request<IntelligenceSnapshot>(`/intelligence/snapshot${query ? `?${query}` : ""}`);
}
