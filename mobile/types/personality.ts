export interface Traits {
  formality: number;
  humor: number;
  strictness: number;
  empathy: number;
  verbosity: number;
}

export interface PersonalityRule {
  id?: string;
  text: string;
  enabled: boolean;
}

export interface PersonalityProfile {
  id: string;
  user_id: string;
  name: string;
  is_active: boolean;
  template_id: string | null;
  template_name: string | null;
  traits: Traits;
  rules: PersonalityRule[];
  voice_style: Record<string, unknown>;
  custom_instructions: string | null;
  created_at: string;
  updated_at: string;
}

export interface PersonalityProfileCreate {
  name: string;
  template_id?: string;
  traits?: Traits;
  rules?: Omit<PersonalityRule, "id">[];
  custom_instructions?: string;
}

export interface PersonalityProfileUpdate {
  name?: string;
  traits?: Traits;
  rules?: PersonalityRule[];
  custom_instructions?: string | null;
}

export interface PersonalityTemplate {
  id: string;
  name: string;
  description: string;
  traits: Traits;
  rules: PersonalityRule[];
  preview_message: string;
}

export interface PersonalityProfileListResponse {
  items: PersonalityProfile[];
  total_count: number;
}

export interface PersonalityTemplateListResponse {
  items: PersonalityTemplate[];
}
