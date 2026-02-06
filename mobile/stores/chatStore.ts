import { create } from "zustand";
import { Message, Conversation } from "../types/chat";

// Placeholder für Phase 2
interface ChatState {
  conversations: Conversation[];
  activeConversation: Conversation | null;
  isLoading: boolean;
}

export const useChatStore = create<ChatState>((set) => ({
  conversations: [],
  activeConversation: null,
  isLoading: false,
}));
