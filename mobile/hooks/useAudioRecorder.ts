import { useState, useRef, useCallback } from "react";
import { Audio } from "expo-av";

const MIN_RECORDING_MS = 600; // Minimum recording duration to get valid audio

interface UseAudioRecorderReturn {
  isRecording: boolean;
  recordingDuration: number;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<string | null>; // Returns URI
  cancelRecording: () => Promise<void>;
}

export function useAudioRecorder(): UseAudioRecorderReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const recordingRef = useRef<Audio.Recording | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(0);

  const startRecording = useCallback(async () => {
    try {
      // Clean up any previous recording first
      if (recordingRef.current) {
        try {
          await recordingRef.current.stopAndUnloadAsync();
        } catch {}
        recordingRef.current = null;
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }

      const permission = await Audio.requestPermissionsAsync();
      if (!permission.granted) return;

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      recordingRef.current = recording;
      startTimeRef.current = Date.now();
      setIsRecording(true);
      setRecordingDuration(0);

      // Duration timer
      timerRef.current = setInterval(() => {
        setRecordingDuration((d) => d + 1);
      }, 1000);
    } catch (error) {
      console.error("Failed to start recording:", error);
    }
  }, []);

  const stopRecording = useCallback(async (): Promise<string | null> => {
    if (!recordingRef.current) return null;

    try {
      // Ensure minimum recording duration for valid audio data
      const elapsed = Date.now() - startTimeRef.current;
      if (elapsed < MIN_RECORDING_MS) {
        const remaining = MIN_RECORDING_MS - elapsed;
        await new Promise((resolve) => setTimeout(resolve, remaining));
      }

      if (timerRef.current) clearInterval(timerRef.current);

      await recordingRef.current.stopAndUnloadAsync();
      await Audio.setAudioModeAsync({ allowsRecordingIOS: false });

      const uri = recordingRef.current.getURI();
      recordingRef.current = null;
      setIsRecording(false);
      setRecordingDuration(0);
      return uri;
    } catch (error) {
      console.error("Failed to stop recording:", error);
      recordingRef.current = null;
      setIsRecording(false);
      setRecordingDuration(0);
      return null;
    }
  }, []);

  const cancelRecording = useCallback(async () => {
    if (!recordingRef.current) return;
    try {
      if (timerRef.current) clearInterval(timerRef.current);
      await recordingRef.current.stopAndUnloadAsync();
      recordingRef.current = null;
      setIsRecording(false);
      setRecordingDuration(0);
    } catch (error) {
      console.error("Failed to cancel recording:", error);
    }
  }, []);

  return { isRecording, recordingDuration, startRecording, stopRecording, cancelRecording };
}
