import api from "./api";

export interface TranscribeResponse {
  text: string;
}

export const voiceService = {
  /**
   * Transcribe audio file to text
   */
  async transcribe(audioUri: string, mimeType: string = "audio/m4a"): Promise<string> {
    const formData = new FormData();
    formData.append("file", {
      uri: audioUri,
      type: mimeType,
      name: "recording.m4a",
    } as any);

    const response = await api.post<TranscribeResponse>("/api/v1/voice/transcribe", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 30000,
    });
    return response.data.text;
  },

  /**
   * Synthesize text to speech, returns audio URL (blob)
   */
  async synthesize(text: string): Promise<ArrayBuffer> {
    const response = await api.post("/api/v1/voice/synthesize", { text }, {
      responseType: "arraybuffer",
      timeout: 30000,
    });
    return response.data;
  },
};
