import { Project, ProjectCreatePayload } from "../types/project";

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

export async function getProjects(): Promise<Project[]> {
  return request<Project[]>("/projects");
}

export async function createProject(payload: ProjectCreatePayload): Promise<Project> {
  return request<Project>("/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
