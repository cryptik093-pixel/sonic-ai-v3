export type StudioFocus =
  | "general"
  | "production"
  | "mixing"
  | "mastering"
  | "sound_design"
  | "arrangement"
  | "theory"
  | "workflow";

export interface ChatMessage {
  id: number;
  session_id: number;
  role: "user" | "assistant" | "system";
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

export interface Memory {
  id: number;
  memory_type: string;
  category: string;
  content: string;
  project_id: number | null;
  confidence: number;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface MemoryCreatePayload {
  content: string;
  memory_type?: string;
  category?: string;
  project_id?: number | null;
  confidence?: number;
  source?: string;
}

export const FOCUS_OPTIONS: { value: StudioFocus; label: string; description: string }[] = [
  { value: "general", label: "General", description: "Full-spectrum studio guidance" },
  { value: "production", label: "Production", description: "Sound selection, layering, groove" },
  { value: "mixing", label: "Mixing", description: "EQ, compression, bussing, imaging" },
  { value: "mastering", label: "Mastering", description: "LUFS, limiting, delivery specs" },
  { value: "sound_design", label: "Sound Design", description: "Synthesis, sampling, timbre" },
  { value: "arrangement", label: "Arrangement", description: "Structure, energy, transitions" },
  { value: "theory", label: "Theory", description: "Keys, harmony, progression" },
  { value: "workflow", label: "Workflow", description: "Templates, organization, exports" },
];
