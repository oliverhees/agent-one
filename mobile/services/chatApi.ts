import api from "./api";
import config from "../constants/config";
import { getSecure, STORAGE_KEYS } from "../utils/storage";
import {
  ConversationListResponse,
  Message,
  SendMessageRequest,
  SSEConversationEvent,
  SSETokenEvent,
  SSEDoneEvent,
  SSEErrorEvent,
} from "../types/chat";

export const chatApi = {
  /**
   * List all conversations
   */
  listConversations: async (): Promise<ConversationListResponse> => {
    const response = await api.get<ConversationListResponse>(
      "/chat/conversations"
    );
    return response.data;
  },

  /**
   * Get messages for a specific conversation
   */
  getMessages: async (conversationId: string): Promise<Message[]> => {
    const response = await api.get<Message[]>(
      `/chat/conversations/${conversationId}/messages`
    );
    return response.data;
  },

  /**
   * Send a message with SSE streaming via XMLHttpRequest
   * (React Native doesn't support ReadableStream/response.body)
   */
  sendMessageStream: async (
    request: SendMessageRequest,
    callbacks: {
      onConversation?: (data: SSEConversationEvent) => void;
      onToken?: (data: SSETokenEvent) => void;
      onDone?: (data: SSEDoneEvent) => void;
      onError?: (data: SSEErrorEvent) => void;
    }
  ): Promise<void> => {
    const token = await getSecure(STORAGE_KEYS.ACCESS_TOKEN);
    if (!token) {
      throw new Error("No access token available");
    }

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${config.apiUrl}/chat/message`);
      xhr.setRequestHeader("Content-Type", "application/json");
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);

      let lastIndex = 0;

      const parseSSEChunk = (text: string) => {
        const lines = text.split("\n");
        for (const line of lines) {
          if (!line.trim()) continue;

          if (line.startsWith("data:")) {
            const dataStr = line.substring(5).trim();
            try {
              const data = JSON.parse(dataStr);

              if (data.conversation_id && data.is_new !== undefined) {
                callbacks.onConversation?.(data as SSEConversationEvent);
              } else if (data.content !== undefined && data.index !== undefined) {
                callbacks.onToken?.(data as SSETokenEvent);
              } else if (data.message_id && data.total_tokens !== undefined) {
                callbacks.onDone?.(data as SSEDoneEvent);
              } else if (data.detail && data.code) {
                callbacks.onError?.(data as SSEErrorEvent);
              }
            } catch {
              // Skip unparseable lines
            }
          }
        }
      };

      xhr.onprogress = () => {
        const newData = xhr.responseText.substring(lastIndex);
        lastIndex = xhr.responseText.length;
        if (newData) parseSSEChunk(newData);
      };

      xhr.onload = () => {
        // Parse any remaining data
        const remaining = xhr.responseText.substring(lastIndex);
        if (remaining) parseSSEChunk(remaining);

        if (xhr.status >= 200 && xhr.status < 300) {
          resolve();
        } else {
          try {
            const errData = JSON.parse(xhr.responseText);
            reject(new Error(errData.detail || `HTTP ${xhr.status}`));
          } catch {
            reject(new Error(`HTTP ${xhr.status}`));
          }
        }
      };

      xhr.onerror = () => {
        reject(new Error("Netzwerkfehler beim Senden der Nachricht"));
      };

      xhr.ontimeout = () => {
        reject(new Error("Zeitüberschreitung beim Senden der Nachricht"));
      };

      xhr.timeout = 60000;
      xhr.send(JSON.stringify(request));
    });
  },
};
