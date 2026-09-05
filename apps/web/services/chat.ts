import type {
  ChatSendRequest,
  ChatSendResponse,
  ChatSession,
  ChatSessionDetail,
  Memory,
  MemoryCreate,
} from "../types/chat";

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

export async function getChatSessions(): Promise<ChatSession[]> {
  return request<ChatSession[]>("/chat/sessions");
}

export async function getChatSession(sessionId: number): Promise<ChatSessionDetail> {
  return request<ChatSessionDetail>(`/chat/sessions/${sessionId}`);
}

export async function startChat(payload: ChatSendRequest): Promise<ChatSendResponse> {
  return request<ChatSendResponse>("/chat/messages", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function sendChatMessage(
  sessionId: number,
  payload: ChatSendRequest,
): Promise<ChatSendResponse> {
  return request<ChatSendResponse>(`/chat/sessions/${sessionId}/messages`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getMemories(): Promise<Memory[]> {
  return request<Memory[]>("/memory");
}

export async function createMemory(payload: MemoryCreate): Promise<Memory> {
  return request<Memory>("/memory", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
