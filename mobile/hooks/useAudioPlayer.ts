import { useState, useRef, useCallback } from "react";
import { Audio } from "expo-av";
import * as FileSystem from "expo-file-system";

interface UseAudioPlayerReturn {
  isPlaying: boolean;
  playAudio: (audioData: ArrayBuffer) => Promise<void>;
  stopAudio: () => Promise<void>;
}

export function useAudioPlayer(): UseAudioPlayerReturn {
  const [isPlaying, setIsPlaying] = useState(false);
  const soundRef = useRef<Audio.Sound | null>(null);

  const playAudio = useCallback(async (audioData: ArrayBuffer) => {
    try {
      // Stop any current playback
      if (soundRef.current) {
        await soundRef.current.unloadAsync();
      }

      // Write to temp file
      const base64 = btoa(
        new Uint8Array(audioData).reduce(
          (data, byte) => data + String.fromCharCode(byte),
          ""
        )
      );
      const fileUri = FileSystem.cacheDirectory + "alice_response.mp3";
      await FileSystem.writeAsStringAsync(fileUri, base64, {
        encoding: FileSystem.EncodingType.Base64,
      });

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        playsInSilentModeIOS: true,
      });

      const { sound } = await Audio.Sound.createAsync({ uri: fileUri });
      soundRef.current = sound;

      sound.setOnPlaybackStatusUpdate((status) => {
        if (status.isLoaded && status.didJustFinish) {
          setIsPlaying(false);
        }
      });

      setIsPlaying(true);
      await sound.playAsync();
    } catch (error) {
      console.error("Audio playback failed:", error);
      setIsPlaying(false);
    }
  }, []);

  const stopAudio = useCallback(async () => {
    if (soundRef.current) {
      await soundRef.current.stopAsync();
      setIsPlaying(false);
    }
  }, []);

  return { isPlaying, playAudio, stopAudio };
}
