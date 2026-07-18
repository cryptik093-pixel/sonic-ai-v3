export interface Project {
  id: number;
  name: string;
  artist: string;
  genre: string;
  bpm: number;
  key: string;
  notes: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreatePayload {
  name: string;
  artist: string;
  genre: string;
  bpm: number;
  key: string;
  notes: string;
  status: string;
}

export interface DashboardSummary {
  projects: number;
  assets: number;
  ai_jobs: number;
  status: string;
}
