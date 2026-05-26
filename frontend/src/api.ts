import type { AskResponse, RepositoryIndexResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

interface ApiErrorBody {
  detail?: string;
}

async function request<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as ApiErrorBody;
      if (body.detail) {
        message = body.detail;
      }
    } catch {
      // Keep the status-based fallback.
    }
    throw new Error(message);
  }

  return (await response.json()) as T;
}

export function buildRepoId(repoUrl: string): string {
  try {
    const url = new URL(repoUrl);
    const [owner, repo] = url.pathname.replace(/^\/|\/$/g, "").split("/");
    const cleanRepo = repo?.replace(/\.git$/, "");
    if (owner && cleanRepo) {
      return `${owner}-${cleanRepo}`.toLowerCase().replace(/[^a-z0-9._-]+/g, "-");
    }
  } catch {
    // Fall through to a deterministic local fallback.
  }

  return repoUrl.toLowerCase().replace(/[^a-z0-9._-]+/g, "-").replace(/^-+|-+$/g, "");
}

export function indexRepository(repoId: string, repoUrl: string): Promise<RepositoryIndexResponse> {
  return request<RepositoryIndexResponse>(`/repos/${encodeURIComponent(repoId)}/index`, {
    method: "POST",
    body: JSON.stringify({ url: repoUrl }),
  });
}

export function askRepository(
  repoId: string,
  question: string,
  topK = 5,
): Promise<AskResponse> {
  return request<AskResponse>(`/repos/${encodeURIComponent(repoId)}/ask`, {
    method: "POST",
    body: JSON.stringify({ question, top_k: topK }),
  });
}
