export interface GamificationStats {
  total_xp: number;
  level: number;
  current_streak: number;
  longest_streak: number;
  xp_for_next_level: number;
  progress_percent: number;
  tasks_completed: number;
}

export interface XPHistoryEntry {
  date: string;
  xp_earned: number;
  tasks_completed: number;
}

export interface XPHistoryResponse {
  history: XPHistoryEntry[];
  total_days: number;
}

export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: "beginner" | "streak" | "tasks" | "brain" | "special";
  xp_reward: number;
  unlocked: boolean;
  unlocked_at: string | null;
}

export interface AchievementListResponse {
  achievements: Achievement[];
  total_count: number;
  unlocked_count: number;
}
