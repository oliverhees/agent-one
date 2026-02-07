export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  title?: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
  page: number;
  page_size: number;
}

export interface SendMessageRequest {
  content: string;
  conversation_id?: string;
}

export interface SSEConversationEvent {
  conversation_id: string;
  is_new: boolean;
}

export interface SSETokenEvent {
  content: string;
  index: number;
}

export interface SSEDoneEvent {
  message_id: string;
  conversation_id: string;
  total_tokens: number;
}

export interface SSEErrorEvent {
  detail: string;
  code: string;
}
