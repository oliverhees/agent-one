import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  useColorScheme,
  StatusBar,
  Animated,
  Easing,
  Platform,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";
import { Audio } from "expo-av";
import { File as ExpoFile, Paths } from "expo-file-system";
import { useAuthStore } from "../../../stores/authStore";
import { useChatStore } from "../../../stores/chatStore";
import api from "../../../services/api";

type SessionStatus = "connecting" | "listening" | "thinking" | "speaking" | "error" | "ended";

interface TranscriptEntry {
  role: "user" | "assistant";
  text: string;
  timestamp: Date;
}

export default function LiveConversationScreen() {
  const { fromWakeWord } = useLocalSearchParams<{ fromWakeWord?: string }>();
  const [status, setStatus] = useState<SessionStatus>("connecting");
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const isRecordingRef = useRef(false);
  const scrollViewRef = useRef<ScrollView>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const recordingRef = useRef<Audio.Recording | null>(null);
  const soundRef = useRef<Audio.Sound | null>(null);
  const conversationIdRef = useRef<string | null>(null);

  // Auth token for WebSocket
  const token = useAuthStore((s) => s.accessToken);

  // Animated values (React Native built-in Animated API)
  const orbScale = useRef(new Animated.Value(1)).current;
  const orbOpacity = useRef(new Animated.Value(0.8)).current;
  const pulseScale = useRef(new Animated.Value(1)).current;
  const pulseOpacity = useRef(new Animated.Value(0)).current;
  const ringRotation = useRef(new Animated.Value(0)).current;

  // Track running animations for cleanup
  const animationsRef = useRef<Animated.CompositeAnimation[]>([]);

  const stopAnimations = () => {
    animationsRef.current.forEach(a => a.stop());
    animationsRef.current = [];
  };

  // Update orb animation based on status
  useEffect(() => {
    stopAnimations();
    orbScale.setValue(1);
    pulseScale.setValue(1);
    pulseOpacity.setValue(0);
    ringRotation.setValue(0);

    switch (status) {
      case "listening": {
        // Gentle breathing animation
        const breathe = Animated.loop(
          Animated.sequence([
            Animated.timing(orbScale, { toValue: 1.05, duration: 2000, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
            Animated.timing(orbScale, { toValue: 1.0, duration: 2000, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
          ])
        );
        // Slow ring rotation
        const rotate = Animated.loop(
          Animated.timing(ringRotation, { toValue: 1, duration: 8000, easing: Easing.linear, useNativeDriver: true })
        );
        animationsRef.current = [breathe, rotate];
        breathe.start();
        rotate.start();
        break;
      }
      case "thinking": {
        // Fast pulsing
        const pulse = Animated.loop(
          Animated.sequence([
            Animated.timing(orbScale, { toValue: 1.15, duration: 300, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
            Animated.timing(orbScale, { toValue: 0.95, duration: 300, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
          ])
        );
        // Fast ring rotation
        const rotate = Animated.loop(
          Animated.timing(ringRotation, { toValue: 1, duration: 2000, easing: Easing.linear, useNativeDriver: true })
        );
        animationsRef.current = [pulse, rotate];
        pulse.start();
        rotate.start();
        break;
      }
      case "speaking": {
        // Active speaking animation
        const speak = Animated.loop(
          Animated.sequence([
            Animated.timing(orbScale, { toValue: 1.2, duration: 200, easing: Easing.out(Easing.ease), useNativeDriver: true }),
            Animated.timing(orbScale, { toValue: 1.0, duration: 400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
          ])
        );
        // Pulse ring expanding outward
        const pulseRing = Animated.loop(
          Animated.parallel([
            Animated.sequence([
              Animated.timing(pulseScale, { toValue: 1.0, duration: 0, useNativeDriver: true }),
              Animated.timing(pulseScale, { toValue: 1.5, duration: 800, easing: Easing.out(Easing.ease), useNativeDriver: true }),
            ]),
            Animated.sequence([
              Animated.timing(pulseOpacity, { toValue: 0.6, duration: 0, useNativeDriver: true }),
              Animated.timing(pulseOpacity, { toValue: 0, duration: 800, easing: Easing.out(Easing.ease), useNativeDriver: true }),
            ]),
          ])
        );
        animationsRef.current = [speak, pulseRing];
        speak.start();
        pulseRing.start();
        break;
      }
      default:
        Animated.timing(orbScale, { toValue: 1, duration: 300, useNativeDriver: true }).start();
        break;
    }

    return () => stopAnimations();
  }, [status]);

  // Interpolate ring rotation to degrees
  const ringRotationDeg = ringRotation.interpolate({
    inputRange: [0, 1],
    outputRange: ["0deg", "360deg"],
  });

  // Scroll transcript to bottom
  useEffect(() => {
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);
  }, [transcript]);

  // Connect WebSocket
  const refreshAccessToken = useAuthStore((s) => s.refreshAccessToken);
  const connectWebSocket = useCallback(async () => {
    if (!token) {
      setStatus("error");
      return;
    }

    try {
      // Refresh token before WebSocket connect (WS doesn't use axios interceptor)
      let wsToken = token;
      try {
        await refreshAccessToken();
        wsToken = useAuthStore.getState().accessToken || token;
        console.log("[Voice] Token refreshed for WebSocket");
      } catch (e) {
        console.warn("[Voice] Token refresh failed, using current token:", e);
      }

      const baseUrl = api.defaults.baseURL || "http://localhost:8000/api/v1";
      const wsUrl = baseUrl.replace(/^http/, "ws").replace(/\/api\/v1$/, "") + "/api/v1/voice/live?token=" + wsToken + (fromWakeWord === "true" ? "&wake_word=true" : "");

      const ws = new WebSocket(wsUrl);
      ws.binaryType = "arraybuffer"; // React Native needs this for binary messages
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("[Voice] WebSocket connected, starting recording...");
        setStatus("listening");
        startContinuousRecording();
      };

      ws.onmessage = async (event: MessageEvent) => {
        if (typeof event.data === "string") {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === "session_start" && msg.conversation_id) {
              conversationIdRef.current = msg.conversation_id;
              console.log("[Voice] Session started, conversation:", msg.conversation_id);
            } else if (msg.type === "status") {
              setStatus(msg.status as SessionStatus);
              // If server says "listening" but we're not recording, restart
              if (msg.status === "listening" && !isRecordingRef.current && !isRestartingRef.current) {
                console.log("[Voice] Server says listening but not recording, restarting");
                restartRecordingAfterPlayback();
              }
            } else if (msg.type === "transcript") {
              setTranscript(prev => [...prev, {
                role: msg.role,
                text: msg.text,
                timestamp: new Date(),
              }]);
            } else if (msg.type === "audio_response" && msg.data) {
              // TTS audio as base64 JSON (fallback)
              try {
                await playAudioFromBase64(msg.data);
              } catch (e) {
                console.error("Audio playback failed:", e);
              }
            } else if (msg.type === "error") {
              console.error("Server error:", msg.message);
            }
          } catch (e) {
            console.error("Failed to parse WS message:", e);
          }
        } else if (event.data instanceof ArrayBuffer) {
          // Binary TTS audio from server (ArrayBuffer in React Native)
          console.log(`[Voice] Received binary audio: ${event.data.byteLength} bytes`);
          try {
            // Write bytes directly to file (no slow base64 conversion)
            const bytes = new Uint8Array(event.data);
            await playAudioFromBytes(bytes);
          } catch (e) {
            console.error("[Voice] Binary audio playback failed:", e);
          }
        } else {
          console.log("[Voice] Unknown message type:", typeof event.data);
        }
      };

      ws.onerror = (e: any) => {
        console.error("[Voice] WebSocket error:", e?.message || e);
        setStatus("error");
      };

      ws.onclose = (e: any) => {
        console.log("[Voice] WebSocket closed:", e?.code, e?.reason);
        setStatus("ended");
        stopRecording();
      };
    } catch (error) {
      console.error("Failed to connect:", error);
      setStatus("error");
    }
  }, [token]);

  // Client-side VAD constants (metering-based)
  const SPEECH_THRESHOLD_DB = -30;  // Above this = speech detected
  const SILENCE_THRESHOLD_DB = -38; // Below this = silence detected
  const SILENCE_DURATION_MS = 1200; // 1.2s of silence after speech triggers send
  const METERING_INTERVAL_MS = 200; // Metering poll interval

  // VAD state refs
  const speechDetectedRef = useRef(false);
  const silenceStartRef = useRef<number | null>(null);
  const isProcessingUtteranceRef = useRef(false);

  // Start continuous recording with metering-based VAD
  const startContinuousRecording = async () => {
    try {
      console.log("[Voice] Requesting audio permission...");
      const permission = await Audio.requestPermissionsAsync();
      if (!permission.granted) {
        console.error("[Voice] Audio permission DENIED");
        return;
      }
      console.log("[Voice] Audio permission granted");

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      setIsRecording(true);
      isRecordingRef.current = true;
      console.log("[Voice] Starting continuous recording with client-side VAD (Platform: " + Platform.OS + ")");
      startNewRecording();
    } catch (error) {
      console.error("[Voice] Failed to start recording:", error);
    }
  };

  // Start a new recording session with metering for VAD
  const startNewRecording = async () => {
    if (!isRecordingRef.current) return;
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.log("[Voice] startNewRecording: WebSocket not open, skipping");
      return;
    }

    // Clean up any existing recording first (Expo only allows one at a time)
    if (recordingRef.current) {
      try {
        await recordingRef.current.stopAndUnloadAsync();
      } catch {}
      recordingRef.current = null;
    }

    try {
      speechDetectedRef.current = false;
      silenceStartRef.current = null;
      isProcessingUtteranceRef.current = false;

      const { recording } = await Audio.Recording.createAsync(
        {
          ...Audio.RecordingOptionsPresets.HIGH_QUALITY,
          isMeteringEnabled: true,
        },
        (status) => {
          if (!status.isRecording || status.metering === undefined) return;
          if (isProcessingUtteranceRef.current) return;

          const db = status.metering;

          if (db > SPEECH_THRESHOLD_DB) {
            // Speech detected
            speechDetectedRef.current = true;
            silenceStartRef.current = null;
          } else if (speechDetectedRef.current && db < SILENCE_THRESHOLD_DB) {
            // Silence after speech
            if (silenceStartRef.current === null) {
              silenceStartRef.current = Date.now();
            } else if (Date.now() - silenceStartRef.current > SILENCE_DURATION_MS) {
              // Long enough silence → send complete utterance
              console.log("[Voice] VAD: Silence detected after speech, sending utterance");
              isProcessingUtteranceRef.current = true;
              handleUtteranceComplete();
            }
          }
        },
        METERING_INTERVAL_MS
      );

      recordingRef.current = recording;
      console.log("[Voice] Recording started with metering VAD");
    } catch (error) {
      console.error("[Voice] Failed to start recording:", error);
      // Don't retry in a tight loop - wait for next trigger
    }
  };

  // Handle complete utterance: stop recording, send full audio file to server
  const handleUtteranceComplete = async () => {
    const recording = recordingRef.current;
    if (!recording) {
      isProcessingUtteranceRef.current = false;
      return;
    }
    recordingRef.current = null;

    try {
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();

      if (uri && wsRef.current?.readyState === WebSocket.OPEN) {
        const file = new ExpoFile(uri);
        const base64Data = await file.base64();

        console.log(`[Voice] Sending complete utterance: ${base64Data.length} base64 chars (m4a)`);

        // Send as audio_complete (server skips VAD, sends directly to Whisper)
        wsRef.current.send(JSON.stringify({
          type: "audio_complete",
          data: base64Data,
          format: "m4a",
        }));

        try { file.delete(); } catch {}
      }

      // Don't restart recording here - playAudioFromBytes will restart
      // after the server response audio finishes playing.
      // Starting recording here would immediately be stopped by playAudioFromBytes.
    } catch (error) {
      console.error("[Voice] handleUtteranceComplete error:", error);
      isProcessingUtteranceRef.current = false;
      if (isRecordingRef.current) {
        setTimeout(startNewRecording, 500);
      }
    }
  };

  // Guard against double-restart
  const isRestartingRef = useRef(false);

  const restartRecordingAfterPlayback = async () => {
    if (isRestartingRef.current) return;
    isRestartingRef.current = true;
    try {
      console.log("[Voice] Restarting recording after playback");
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });
      setIsRecording(true);
      isRecordingRef.current = true;
      await startNewRecording();
    } catch (e) {
      console.error("[Voice] restartRecordingAfterPlayback error:", e);
    } finally {
      isRestartingRef.current = false;
    }
  };

  // Play TTS audio from raw bytes (fast path - no base64 overhead)
  const playAudioFromBytes = async (audioBytes: Uint8Array) => {
    try {
      console.log(`[Voice] Playing audio: ${audioBytes.length} bytes`);

      if (soundRef.current) {
        try { await soundRef.current.unloadAsync(); } catch {}
        soundRef.current = null;
      }

      if (isRecordingRef.current) {
        await stopRecording();
      }

      // Write bytes directly to file (skips slow base64 conversion)
      const responseFile = new ExpoFile(Paths.cache, "alice_live_response.mp3");
      responseFile.write(audioBytes);

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        playsInSilentModeIOS: true,
      });

      const { sound } = await Audio.Sound.createAsync({ uri: responseFile.uri });
      soundRef.current = sound;

      // Safety timer: if didJustFinish never fires, restart recording anyway
      const safetyTimer = setTimeout(() => {
        console.warn("[Voice] Safety timer: playback callback never fired, restarting recording");
        restartRecordingAfterPlayback();
      }, 30000); // 30s max audio length

      let didRestart = false;
      sound.setOnPlaybackStatusUpdate(async (playbackStatus) => {
        if (!playbackStatus.isLoaded) return;
        if (playbackStatus.didJustFinish && !didRestart) {
          didRestart = true;
          clearTimeout(safetyTimer);
          console.log("[Voice] Audio playback finished, restarting recording");
          restartRecordingAfterPlayback();
        }
      });

      await sound.playAsync();
    } catch (error) {
      console.error("Audio playback failed:", error);
      restartRecordingAfterPlayback();
    }
  };

  // Play TTS audio from base64 string (fallback for JSON audio_response)
  const playAudioFromBase64 = async (base64Audio: string) => {
    try {
      const binaryString = atob(base64Audio);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      await playAudioFromBytes(bytes);
    } catch (error) {
      console.error("Audio base64 playback failed:", error);
    }
  };

  // Stop recording and fully release the Recording object
  const stopRecording = async () => {
    setIsRecording(false);
    isRecordingRef.current = false;
    const rec = recordingRef.current;
    recordingRef.current = null;
    if (rec) {
      try {
        const status = await rec.getStatusAsync();
        if (status.isRecording) {
          await rec.stopAndUnloadAsync();
        }
      } catch {
        // Force unload even if status check fails
        try { await rec.stopAndUnloadAsync(); } catch {}
      }
    }
  };

  // End session and navigate to conversation
  const endSession = async () => {
    await stopRecording();

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "end" }));
      wsRef.current.close();
    }

    if (soundRef.current) {
      try { await soundRef.current.unloadAsync(); } catch {}
    }

    // Select the voice conversation so chat screen shows it
    const convId = conversationIdRef.current;
    if (convId) {
      const store = useChatStore.getState();
      store.selectConversation(convId);
    }

    router.back();
  };

  // Connect on mount
  useEffect(() => {
    connectWebSocket();

    return () => {
      isRecordingRef.current = false;
      stopRecording();
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (soundRef.current) {
        soundRef.current.unloadAsync().catch(() => {});
      }
    };
  }, []);

  // Status text + color
  const getStatusInfo = () => {
    switch (status) {
      case "connecting": return { text: "Verbinde...", color: "#f59e0b" };
      case "listening": return { text: "Ich hoere zu...", color: "#22c55e" };
      case "thinking": return { text: "Denke nach...", color: "#3b82f6" };
      case "speaking": return { text: "ALICE spricht...", color: "#0284c7" };
      case "error": return { text: "Fehler", color: "#ef4444" };
      case "ended": return { text: "Beendet", color: "#6b7280" };
    }
  };

  const statusInfo = getStatusInfo();

  // Orb colors based on status
  const getOrbColor = () => {
    switch (status) {
      case "listening": return "#0284c7";
      case "thinking": return "#8b5cf6";
      case "speaking": return "#06b6d4";
      default: return "#6b7280";
    }
  };

  const orbColor = getOrbColor();

  return (
    <View style={{ flex: 1, backgroundColor: "#0f172a" }}>
      <StatusBar barStyle="light-content" />

      {/* Top Bar */}
      <View style={{ paddingTop: 60, paddingHorizontal: 20, flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
        <Text style={{ color: "#ffffff", fontSize: 18, fontWeight: "600" }}>
          Live-Gespraech
        </Text>
        <TouchableOpacity
          onPress={endSession}
          style={{
            backgroundColor: "#dc2626",
            paddingHorizontal: 20,
            paddingVertical: 10,
            borderRadius: 20,
          }}
        >
          <Text style={{ color: "#ffffff", fontWeight: "600" }}>Beenden</Text>
        </TouchableOpacity>
      </View>

      {/* Orb Area */}
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
        {/* Pulse ring (visible during speaking) */}
        <Animated.View
          style={{
            position: "absolute",
            width: 200,
            height: 200,
            borderRadius: 100,
            borderWidth: 2,
            borderColor: orbColor,
            transform: [{ scale: pulseScale }],
            opacity: pulseOpacity,
          }}
        />

        {/* Rotating ring */}
        <Animated.View
          style={{
            position: "absolute",
            width: 220,
            height: 220,
            borderRadius: 110,
            borderWidth: 1,
            borderColor: "transparent",
            borderTopColor: orbColor,
            borderBottomColor: orbColor,
            opacity: 0.5,
            transform: [{ rotate: ringRotationDeg }],
          }}
        />

        {/* Main orb */}
        <Animated.View
          style={{
            width: 160,
            height: 160,
            borderRadius: 80,
            backgroundColor: orbColor,
            shadowColor: orbColor,
            shadowOffset: { width: 0, height: 0 },
            shadowOpacity: 0.5,
            shadowRadius: 30,
            elevation: 20,
            alignItems: "center",
            justifyContent: "center",
            transform: [{ scale: orbScale }],
          }}
        >
          <Ionicons
            name={status === "listening" ? "mic" : status === "speaking" ? "volume-high" : "ellipsis-horizontal"}
            size={48}
            color="#ffffff"
          />
        </Animated.View>

        {/* Status text */}
        <View style={{ marginTop: 32 }}>
          <Text style={{ color: statusInfo.color, fontSize: 16, fontWeight: "500", textAlign: "center" }}>
            {statusInfo.text}
          </Text>
        </View>
      </View>

      {/* Transcript area */}
      <View style={{ maxHeight: 200, paddingHorizontal: 20, paddingBottom: 40 }}>
        <ScrollView
          ref={scrollViewRef}
          showsVerticalScrollIndicator={false}
          style={{ maxHeight: 180 }}
        >
          {transcript.map((entry, idx) => (
            <View key={idx} style={{ marginBottom: 8 }}>
              <Text style={{
                color: entry.role === "user" ? "rgba(255,255,255,0.5)" : "rgba(255,255,255,0.8)",
                fontSize: 14,
                fontStyle: entry.role === "user" ? "italic" : "normal",
              }}>
                {entry.role === "user" ? "Du: " : "ALICE: "}
                {entry.text}
              </Text>
            </View>
          ))}
        </ScrollView>
      </View>
    </View>
  );
}
