export type NudgeLevel = "gentle" | "moderate" | "firm";
export type NudgeType = "deadline_approaching" | "overdue" | "stale" | "follow_up";

export interface Nudge {
  id: string;
  task_id: string;
  task_title: string;
  nudge_level: NudgeLevel;
  nudge_type: NudgeType;
  message: string;
  delivered_at: string;
}

export interface NudgeListResponse {
  nudges: Nudge[];
  count: number;
}

export interface NudgeHistoryItem {
  id: string;
  task_id: string;
  task_title: string;
  nudge_level: NudgeLevel;
  nudge_type: NudgeType;
  message: string;
  delivered_at: string;
  acknowledged_at: string | null;
}

export interface NudgeHistoryResponse {
  items: NudgeHistoryItem[];
  next_cursor: string | null;
  has_more: boolean;
  total_count: number;
}

export interface NudgeAcknowledgeResponse {
  id: string;
  acknowledged_at: string;
}
