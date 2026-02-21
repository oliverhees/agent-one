import { useEffect, useRef, useCallback } from "react";
import { AppState, Platform } from "react-native";
import { Audio } from "expo-av";
import * as FileSystem from "expo-file-system";
import { Asset } from "expo-asset";
import { useWakeWordStore } from "../stores/wakeWordStore";

// ONNX Runtime - only available in Dev Client
let InferenceSession: any = null;
let OnnxTensor: any = null;
try {
  const onnx = require("onnxruntime-react-native");
  InferenceSession = onnx.InferenceSession;
  OnnxTensor = onnx.Tensor;
} catch {
  // Not available in Expo Go
}

// Fallback: document directory for manually placed models
const MODEL_DIR = `${FileSystem.documentDirectory}wakeword_models/`;

interface UseWakeWordOptions {
  onDetected: () => void;
  onError?: (error: Error) => void;
}

export function useWakeWord({ onDetected, onError }: UseWakeWordOptions) {
  const melSessionRef = useRef<any>(null);
  const embSessionRef = useRef<any>(null);
  const wakeSessionRef = useRef<any>(null);
  const recordingRef = useRef<Audio.Recording | null>(null);
  const isRecordingRef = useRef(false);
  const appStateRef = useRef(AppState.currentState);

  // Buffers for the 3-stage pipeline
  const melBufferRef = useRef<number[][]>([]);
  const embeddingBufferRef = useRef<number[][]>([]);

  const { enabled, sensitivity, isListening, setIsListening, setModelLoaded } =
    useWakeWordStore();

  // Load a single ONNX model - try bundled asset first, then document directory
  const loadModel = async (
    assetModule: any,
    fallbackFilename: string
  ): Promise<any> => {
    // Try bundled asset first
    try {
      const asset = Asset.fromModule(assetModule);
      await asset.downloadAsync();
      if (asset.localUri) {
        return await InferenceSession.create(asset.localUri);
      }
    } catch (e) {
      console.warn("Bundled asset load failed, trying document dir:", e);
    }

    // Fallback: document directory
    const fallbackPath = MODEL_DIR + fallbackFilename;
    const info = await FileSystem.getInfoAsync(fallbackPath);
    if (info.exists) {
      return await InferenceSession.create(fallbackPath);
    }

    return null;
  };

  // Load all 3 ONNX models
  const loadModels = useCallback(async () => {
    if (!InferenceSession) {
      console.warn("ONNX Runtime not available - native build required");
      return false;
    }

    try {
      const [melSession, embSession, wakeSession] = await Promise.all([
        loadModel(
          require("../assets/wakewords/melspectrogram.onnx"),
          "melspectrogram.onnx"
        ),
        loadModel(
          require("../assets/wakewords/embedding_model.onnx"),
          "embedding_model.onnx"
        ),
        loadModel(
          require("../assets/wakewords/hey_alice.onnx"),
          "hey_alice.onnx"
        ),
      ]);

      if (!melSession || !embSession || !wakeSession) {
        console.warn(
          "Could not load all ONNX models. Ensure model files are bundled or placed in",
          MODEL_DIR
        );
        return false;
      }

      melSessionRef.current = melSession;
      embSessionRef.current = embSession;
      wakeSessionRef.current = wakeSession;

      setModelLoaded(true);
      console.log("All ONNX wake word models loaded successfully");
      return true;
    } catch (error) {
      console.warn("Failed to load ONNX models:", error);
      onError?.(
        error instanceof Error ? error : new Error(String(error))
      );
      return false;
    }
  }, [onError, setModelLoaded]);

  // Process audio frame through the 3-stage ONNX pipeline
  const processAudioFrame = useCallback(
    async (audioData: Float32Array) => {
      if (!melSessionRef.current) return;

      // Split audio into 80ms frames (1280 samples at 16kHz)
      const frameSize = 1280;
      for (let offset = 0; offset + frameSize <= audioData.length; offset += frameSize) {
        const frameData = audioData.slice(offset, offset + frameSize);

        try {
          // Stage 1: Mel Spectrogram
          const inputTensor = new OnnxTensor("float32", frameData, [1, frameSize]);
          const melResult = await melSessionRef.current.run({ input: inputTensor });
          const melOutput = melResult.output.data;
          const processedMel = new Float32Array(melOutput.length);
          for (let i = 0; i < melOutput.length; i++) {
            processedMel[i] = melOutput[i] / 10.0 + 2.0;
          }
          melBufferRef.current.push(Array.from(processedMel));

          // Stage 2: Embedding (when 76+ mel frames accumulated)
          if (melBufferRef.current.length >= 76 && embSessionRef.current) {
            const melFrames = melBufferRef.current.slice(-76);
            const flatMel = new Float32Array(melFrames.flat());
            const numMelBins = melFrames[0].length;
            const embInput = new OnnxTensor("float32", flatMel, [1, 76, numMelBins]);
            const embResult = await embSessionRef.current.run({ input: embInput });

            // Deep copy to avoid ONNX buffer reuse issues
            const embedding = new Float32Array(embResult.output.data);
            embeddingBufferRef.current.push(Array.from(embedding));

            // Slide mel buffer forward by 8 frames
            melBufferRef.current = melBufferRef.current.slice(8);
          }

          // Stage 3: Classification (when 16+ embeddings accumulated)
          if (embeddingBufferRef.current.length >= 16 && wakeSessionRef.current) {
            const last16 = embeddingBufferRef.current.slice(-16);
            const flat = new Float32Array(last16.flat());
            const embDim = last16[0].length;
            const classInput = new OnnxTensor("float32", flat, [1, 16, embDim]);
            const classResult = await wakeSessionRef.current.run({ input: classInput });

            const score = classResult.output.data[0];
            if (score > sensitivity) {
              onDetected();
              // Reset buffers after detection
              melBufferRef.current = [];
              embeddingBufferRef.current = [];
            }

            // Keep only last 16 embeddings
            if (embeddingBufferRef.current.length > 16) {
              embeddingBufferRef.current = embeddingBufferRef.current.slice(-16);
            }
          }
        } catch (error) {
          console.warn("ONNX inference error:", error);
        }
      }
    },
    [sensitivity, onDetected]
  );

  // Record a chunk, process it, then record next
  const recordChunk = useCallback(async () => {
    if (!isRecordingRef.current) return;

    try {
      const { recording } = await Audio.Recording.createAsync({
        android: {
          extension: ".wav",
          outputFormat: 2,
          audioEncoder: 1,
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 256000,
        },
        ios: {
          extension: ".wav",
          audioQuality: 96,
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 256000,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
          outputFormat: "linearPCM" as any,
        },
        web: {},
      });

      recordingRef.current = recording;

      // Record for ~500ms
      await new Promise((resolve) => setTimeout(resolve, 500));

      if (!isRecordingRef.current) {
        try {
          await recording.stopAndUnloadAsync();
        } catch {}
        recordingRef.current = null;
        return;
      }

      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      recordingRef.current = null;

      if (uri) {
        // Read WAV file as base64 and convert to PCM Float32
        const base64Data = await FileSystem.readAsStringAsync(uri, {
          encoding: FileSystem.EncodingType.Base64,
        });

        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }

        // Skip WAV header (44 bytes) and convert 16-bit PCM to float32
        const pcmData = new Int16Array(bytes.buffer, 44);
        const float32Data = new Float32Array(pcmData.length);
        for (let i = 0; i < pcmData.length; i++) {
          float32Data[i] = pcmData[i] / 32768.0;
        }

        await processAudioFrame(float32Data);

        // Clean up temp file
        try {
          await FileSystem.deleteAsync(uri);
        } catch {}
      }

      // Continue recording if still active
      if (isRecordingRef.current) {
        setTimeout(recordChunk, 50);
      }
    } catch (error) {
      if (isRecordingRef.current) {
        setTimeout(recordChunk, 200);
      }
    }
  }, [processAudioFrame]);

  const start = useCallback(async () => {
    if (!InferenceSession) {
      console.warn("ONNX Runtime not available - native build required");
      return;
    }

    if (isRecordingRef.current) {
      return; // Already running
    }

    // Load models if not loaded yet
    if (!melSessionRef.current || !embSessionRef.current || !wakeSessionRef.current) {
      const loaded = await loadModels();
      if (!loaded) return;
    }

    try {
      const permission = await Audio.requestPermissionsAsync();
      if (!permission.granted) {
        console.warn("Audio permission not granted");
        return;
      }

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      // Reset buffers
      melBufferRef.current = [];
      embeddingBufferRef.current = [];

      isRecordingRef.current = true;
      setIsListening(true);
      recordChunk();
    } catch (error) {
      console.error("Failed to start wake word detection:", error);
      onError?.(error instanceof Error ? error : new Error(String(error)));
    }
  }, [loadModels, recordChunk, setIsListening, onError]);

  const stop = useCallback(async () => {
    isRecordingRef.current = false;
    if (recordingRef.current) {
      try {
        await recordingRef.current.stopAndUnloadAsync();
      } catch {}
      recordingRef.current = null;
    }
    setIsListening(false);
  }, [setIsListening]);

  // AppState handling - pause in background, resume in foreground
  useEffect(() => {
    const subscription = AppState.addEventListener("change", (nextAppState) => {
      if (
        appStateRef.current === "active" &&
        nextAppState.match(/inactive|background/)
      ) {
        // Going to background - pause recording
        if (isRecordingRef.current) {
          isRecordingRef.current = false;
          if (recordingRef.current) {
            recordingRef.current.stopAndUnloadAsync().catch(console.error);
            recordingRef.current = null;
          }
        }
      } else if (
        appStateRef.current.match(/inactive|background/) &&
        nextAppState === "active"
      ) {
        // Coming to foreground - resume if enabled
        if (enabled && !isRecordingRef.current && melSessionRef.current) {
          isRecordingRef.current = true;
          recordChunk();
        }
      }
      appStateRef.current = nextAppState;
    });

    return () => subscription.remove();
  }, [enabled, recordChunk]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isRecordingRef.current = false;
      if (recordingRef.current) {
        recordingRef.current.stopAndUnloadAsync().catch(() => {});
        recordingRef.current = null;
      }
      // Release ONNX sessions
      if (melSessionRef.current) {
        try {
          melSessionRef.current.release();
        } catch {}
        melSessionRef.current = null;
      }
      if (embSessionRef.current) {
        try {
          embSessionRef.current.release();
        } catch {}
        embSessionRef.current = null;
      }
      if (wakeSessionRef.current) {
        try {
          wakeSessionRef.current.release();
        } catch {}
        wakeSessionRef.current = null;
      }
      setModelLoaded(false);
    };
  }, []);

  return { start, stop, isListening };
}
