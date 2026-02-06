// Placeholder für Phase 2
export interface Message {
  id: string;
  content: string;
  role: "user" | "assistant";
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}
