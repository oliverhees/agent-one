export type BrainEntryType =
  | "manual"
  | "chat_extract"
  | "url_import"
  | "file_import"
  | "voice_note";

export type EmbeddingStatus = "pending" | "processing" | "completed" | "failed";

export interface BrainEntry {
  id: string;
  user_id: string;
  title: string;
  content: string;
  entry_type: BrainEntryType;
  tags: string[];
  source_url: string | null;
  metadata: Record<string, unknown>;
  embedding_status: EmbeddingStatus;
  created_at: string;
  updated_at: string;
}

export interface BrainEntryCreate {
  title: string;
  content: string;
  entry_type?: BrainEntryType;
  tags?: string[];
  source_url?: string;
}

export interface BrainEntryUpdate {
  title?: string;
  content?: string;
  tags?: string[];
  source_url?: string | null;
}

export interface BrainEntryListResponse {
  items: BrainEntry[];
  next_cursor: string | null;
  has_more: boolean;
  total_count: number;
}

export interface BrainSearchResult {
  entry: BrainEntry;
  score: number;
  matched_chunks: string[];
}

export interface BrainSearchResponse {
  results: BrainSearchResult[];
  query: string;
  total_results: number;
}

export interface BrainEntryListParams {
  cursor?: string;
  limit?: number;
  entry_type?: BrainEntryType;
  tags?: string;
}

export interface BrainSearchParams {
  q: string;
  limit?: number;
  min_score?: number;
}
