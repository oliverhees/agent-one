export type NudgeIntensity = "low" | "medium" | "high";

export interface ADHSSettings {
  adhs_mode: boolean;
  nudge_intensity: NudgeIntensity;
  auto_breakdown: boolean;
  gamification_enabled: boolean;
  focus_timer_minutes: number;
  quiet_hours_start: string;
  quiet_hours_end: string;
  preferred_reminder_times: string[];
}

export type ADHSSettingsUpdate = Partial<ADHSSettings>;
