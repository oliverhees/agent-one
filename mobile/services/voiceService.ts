import * as FileSystem from "expo-file-system/legacy";
import api from "./api";
import config from "../constants/config";
import { getSecure, STORAGE_KEYS } from "../utils/storage";

export interface TranscribeResponse {
  text: string;
}

export const voiceService = {
  /**
   * Transcribe audio file to text.
   * Uses FileSystem.uploadAsync — Expo's native upload API that handles file URIs correctly.
   */
  async transcribe(audioUri: string, mimeType: string = "audio/m4a"): Promise<string> {
    const token = await getSecure(STORAGE_KEYS.ACCESS_TOKEN);

    console.log("[Voice] Transcribing audio from:", audioUri);

    // uploadType: 1 = MULTIPART (enum may not be exported in all SDK versions)
    const result = await FileSystem.uploadAsync(
      `${config.apiUrl}/voice/transcribe`,
      audioUri,
      {
        httpMethod: "POST",
        uploadType: 1,
        fieldName: "file",
        mimeType,
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    console.log("[Voice] Upload response status:", result.status);

    if (result.status < 200 || result.status >= 300) {
      throw new Error(`Transcription failed (${result.status}): ${result.body}`);
    }

    const data: TranscribeResponse = JSON.parse(result.body);
    return data.text;
  },

  /**
   * Synthesize text to speech, returns audio URL (blob)
   */
  async synthesize(text: string): Promise<ArrayBuffer> {
    const response = await api.post("/voice/synthesize", { text }, {
      responseType: "arraybuffer",
      timeout: 30000,
    });
    return response.data;
  },
};
