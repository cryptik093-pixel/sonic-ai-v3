import {
  ChatSendRequest,
  ChatSendResponse,
  ChatSession,
  ChatSessionDetail,
  Memory,
  MemoryCreatePayload,
} from "../types/chat";

const API_URL = "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || "Request failed");
  }

  return response.json() as Promise<T>;
}

export async function getChatSessions(): Promise<ChatSession[]> {
  return request<ChatSession[]>("/chat/sessions");
}

export async function getChatSession(sessionId: number): Promise<ChatSessionDetail> {
  return request<ChatSessionDetail>(`/chat/sessions/${sessionId}`);
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

export async function startChat(payload: ChatSendRequest): Promise<ChatSendResponse> {
  return request<ChatSendResponse>("/chat/messages", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getMemories(projectId?: number): Promise<Memory[]> {
  const query = projectId ? `?project_id=${projectId}` : "";
  return request<Memory[]>(`/memory${query}`);
}

export async function createMemory(payload: MemoryCreatePayload): Promise<Memory> {
  return request<Memory>("/memory", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
