export type Confidence = "low" | "medium" | "high";

export interface RepositoryIndexResponse {
  repo_id: string;
  status: string;
  chunk_count: number;
}

export interface SourceCitation {
  chunk_id: string;
  file_path: string;
  start_line: number;
  end_line: number;
  repo_owner: string;
  repo_name: string;
  commit_sha: string;
  github_url: string;
  snippet: string;
}

export interface AskResponse {
  repo_id: string;
  question: string;
  answer: string;
  citations: SourceCitation[];
  confidence: Confidence;
}
