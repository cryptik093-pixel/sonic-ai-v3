export type ChatRole = "user" | "assistant" | "system";
export type StudioFocus =
  | "general"
  | "production"
  | "mixing"
  | "mastering"
  | "sound_design"
  | "arrangement"
  | "theory"
  | "workflow";

export const FOCUS_OPTIONS: Array<{ value: StudioFocus; label: string }> = [
  { value: "general", label: "General" },
  { value: "production", label: "Production" },
  { value: "mixing", label: "Mixing" },
  { value: "mastering", label: "Mastering" },
  { value: "sound_design", label: "Sound Design" },
  { value: "arrangement", label: "Arrangement" },
  { value: "theory", label: "Theory" },
  { value: "workflow", label: "Workflow" },
];

export interface ChatMessage {
  id: number;
  session_id: number;
  role: ChatRole;
  content: string;
  created_at: string;
}

export interface ChatSession {
  id: number;
  title: string;
  project_id: number | null;
  focus: StudioFocus;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionDetail extends ChatSession {
  messages: ChatMessage[];
}

export interface ChatSendRequest {
  message: string;
  project_id?: number | null;
  focus?: StudioFocus;
}

export interface ChatSendResponse {
  session_id: number;
  message: ChatMessage;
  reply: ChatMessage;
  context_used: string[];
}

export type MemoryType = "project" | "studio" | "producer";
export type MemoryCategory =
  | "general"
  | "creative"
  | "engineering"
  | "mix"
  | "master"
  | "workflow"
  | "preference"
  | "lesson";

export interface Memory {
  id: number;
  memory_type: MemoryType;
  category: MemoryCategory;
  content: string;
  project_id: number | null;
  confidence: number;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface MemoryCreate {
  memory_type?: MemoryType;
  category?: MemoryCategory;
  content: string;
  project_id?: number | null;
  confidence?: number;
  source?: string;
}
