import { create } from "zustand";
import { Message, Conversation } from "../types/chat";
import { chatApi } from "../services/chatApi";

interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  streamingContent: string; // accumulates tokens during streaming
  error: string | null;

  loadConversations: () => Promise<void>;
  loadMessages: (conversationId: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  startNewConversation: () => void;
  selectConversation: (id: string) => void;
  clearError: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  activeConversationId: null,
  messages: [],
  isLoading: false,
  isStreaming: false,
  streamingContent: "",
  error: null,

  loadConversations: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await chatApi.listConversations();
      set({ conversations: data.conversations, isLoading: false });
    } catch (error: any) {
      console.error("Failed to load conversations:", error);
      set({
        error: error.message || "Fehler beim Laden der Konversationen",
        isLoading: false,
      });
    }
  },

  loadMessages: async (conversationId: string) => {
    set({ isLoading: true, error: null, activeConversationId: conversationId });
    try {
      const messages = await chatApi.getMessages(conversationId);
      set({ messages, isLoading: false });
    } catch (error: any) {
      console.error("Failed to load messages:", error);
      set({
        error: error.message || "Fehler beim Laden der Nachrichten",
        isLoading: false,
      });
    }
  },

  sendMessage: async (content: string) => {
    const { activeConversationId } = get();

    // Add user message to local state immediately
    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: activeConversationId || "",
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMessage],
      isStreaming: true,
      streamingContent: "",
      error: null,
    }));

    try {
      await chatApi.sendMessageStream(
        {
          content,
          conversation_id: activeConversationId || undefined,
        },
        {
          onConversation: (data) => {
            // Update active conversation ID if this is a new conversation
            if (data.is_new) {
              set({ activeConversationId: data.conversation_id });
              // Reload conversations to get the new one
              get().loadConversations();
            }
          },
          onToken: (data) => {
            // Accumulate streaming tokens
            set((state) => ({
              streamingContent: state.streamingContent + data.content,
            }));
          },
          onDone: (data) => {
            // Finalize the assistant message
            const assistantMessage: Message = {
              id: data.message_id,
              conversation_id: data.conversation_id,
              role: "assistant",
              content: get().streamingContent,
              created_at: new Date().toISOString(),
            };

            set((state) => ({
              messages: [...state.messages, assistantMessage],
              isStreaming: false,
              streamingContent: "",
            }));
          },
          onError: (data) => {
            console.error("SSE error:", data);
            set({
              error: data.detail || "Fehler beim Senden der Nachricht",
              isStreaming: false,
              streamingContent: "",
            });
          },
        }
      );
    } catch (error: any) {
      console.error("Failed to send message:", error);
      set({
        error: error.message || "Fehler beim Senden der Nachricht",
        isStreaming: false,
        streamingContent: "",
      });
    }
  },

  startNewConversation: () => {
    set({
      activeConversationId: null,
      messages: [],
      error: null,
    });
  },

  selectConversation: (id: string) => {
    get().loadMessages(id);
  },

  clearError: () => set({ error: null }),
}));
