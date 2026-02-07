import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  useColorScheme,
  StatusBar,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withRepeat,
  withTiming,
  withSequence,
  Easing,
  cancelAnimation,
} from "react-native-reanimated";
import { Audio } from "expo-av";
import { useAuthStore } from "../../../stores/authStore";
import api from "../../../services/api";

type SessionStatus = "connecting" | "listening" | "thinking" | "speaking" | "error" | "ended";

interface TranscriptEntry {
  role: "user" | "assistant";
  text: string;
  timestamp: Date;
}

export default function LiveConversationScreen() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";

  const [status, setStatus] = useState<SessionStatus>("connecting");
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const recordingRef = useRef<Audio.Recording | null>(null);
  const soundRef = useRef<Audio.Sound | null>(null);

  // Auth token for WebSocket
  const token = useAuthStore((s) => s.accessToken);

  // Orb animation values
  const orbScale = useSharedValue(1);
  const orbOpacity = useSharedValue(0.8);
  const pulseScale = useSharedValue(1);
  const ringRotation = useSharedValue(0);

  // Animated styles for the orb
  const orbAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: orbScale.value }],
    opacity: orbOpacity.value,
  }));

  const pulseAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: pulseScale.value }],
    opacity: 1 - (pulseScale.value - 1) * 2, // Fade out as it grows
  }));

  const ringAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${ringRotation.value}deg` }],
  }));

  // Update orb animation based on status
  useEffect(() => {
    cancelAnimation(orbScale);
    cancelAnimation(pulseScale);
    cancelAnimation(ringRotation);

    switch (status) {
      case "listening":
        // Gentle breathing animation
        orbScale.value = withRepeat(
          withSequence(
            withTiming(1.05, { duration: 2000, easing: Easing.inOut(Easing.ease) }),
            withTiming(1.0, { duration: 2000, easing: Easing.inOut(Easing.ease) })
          ),
          -1
        );
        // Slow ring rotation
        ringRotation.value = withRepeat(
          withTiming(360, { duration: 8000, easing: Easing.linear }),
          -1
        );
        break;

      case "thinking":
        // Fast pulsing
        orbScale.value = withRepeat(
          withSequence(
            withTiming(1.15, { duration: 300, easing: Easing.inOut(Easing.ease) }),
            withTiming(0.95, { duration: 300, easing: Easing.inOut(Easing.ease) })
          ),
          -1
        );
        // Fast ring rotation
        ringRotation.value = withRepeat(
          withTiming(360, { duration: 2000, easing: Easing.linear }),
          -1
        );
        break;

      case "speaking":
        // Active speaking animation
        orbScale.value = withRepeat(
          withSequence(
            withTiming(1.2, { duration: 200, easing: Easing.out(Easing.ease) }),
            withTiming(1.0, { duration: 400, easing: Easing.inOut(Easing.ease) })
          ),
          -1
        );
        // Pulse ring
        pulseScale.value = withRepeat(
          withSequence(
            withTiming(1.0, { duration: 0 }),
            withTiming(1.5, { duration: 800, easing: Easing.out(Easing.ease) })
          ),
          -1
        );
        break;

      default:
        orbScale.value = withTiming(1);
        break;
    }
  }, [status]);

  // Scroll transcript to bottom
  useEffect(() => {
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);
  }, [transcript]);

  // Connect WebSocket
  const connectWebSocket = useCallback(async () => {
    if (!token) {
      setStatus("error");
      return;
    }

    try {
      // Get base URL from api instance
      const baseUrl = api.defaults.baseURL || "http://localhost:8000/api/v1";
      const wsUrl = baseUrl.replace(/^http/, "ws").replace(/\/api\/v1$/, "") + "/api/v1/voice/live?token=" + token;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("listening");
        startContinuousRecording();
      };

      ws.onmessage = async (event) => {
        if (typeof event.data === "string") {
          // JSON message
          try {
            const msg = JSON.parse(event.data);

            if (msg.type === "status") {
              setStatus(msg.status as SessionStatus);
            } else if (msg.type === "transcript") {
              setTranscript(prev => [...prev, {
                role: msg.role,
                text: msg.text,
                timestamp: new Date(),
              }]);
            } else if (msg.type === "error") {
              console.error("Server error:", msg.message);
            }
          } catch (e) {
            console.error("Failed to parse WS message:", e);
          }
        } else if (event.data instanceof Blob) {
          // Binary audio data - play it
          try {
            const arrayBuffer = await event.data.arrayBuffer();
            await playAudioResponse(arrayBuffer);
          } catch (e) {
            console.error("Audio playback failed:", e);
          }
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setStatus("error");
      };

      ws.onclose = () => {
        setStatus("ended");
        stopRecording();
      };
    } catch (error) {
      console.error("Failed to connect:", error);
      setStatus("error");
    }
  }, [token]);

  // Start continuous recording and send chunks
  const startContinuousRecording = async () => {
    try {
      const permission = await Audio.requestPermissionsAsync();
      if (!permission.granted) return;

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      // Note: In Expo, continuous chunk streaming requires a workaround
      // We use recording with periodic stop/restart to get chunks
      setIsRecording(true);
      recordChunk();
    } catch (error) {
      console.error("Failed to start recording:", error);
    }
  };

  // Record a chunk and send it, then record next
  const recordChunk = async () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    try {
      const { recording } = await Audio.Recording.createAsync({
        android: {
          extension: ".wav",
          outputFormat: 2, // THREE_GPP → but we want WAV-like
          audioEncoder: 1, // AMR_NB
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 256000,
        },
        ios: {
          extension: ".wav",
          audioQuality: 96, // Audio.IOSAudioQuality.MEDIUM
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

      // Record for ~500ms then stop and send
      await new Promise(resolve => setTimeout(resolve, 500));

      if (recordingRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
        await recordingRef.current.stopAndUnloadAsync();
        const uri = recordingRef.current.getURI();
        recordingRef.current = null;

        if (uri) {
          // Read file and send as binary
          const FileSystem = require("expo-file-system");
          const base64Data = await FileSystem.readAsStringAsync(uri, {
            encoding: FileSystem.EncodingType.Base64,
          });

          // Convert base64 to binary
          const binaryString = atob(base64Data);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }

          wsRef.current.send(bytes.buffer);

          // Clean up temp file
          try { await FileSystem.deleteAsync(uri); } catch {}
        }

        // Continue recording if still active
        if (isRecording && wsRef.current?.readyState === WebSocket.OPEN) {
          // Small delay to prevent rapid loop
          setTimeout(recordChunk, 50);
        }
      }
    } catch (error) {
      // Recording might fail if we're stopping
      if (isRecording) {
        setTimeout(recordChunk, 200);
      }
    }
  };

  // Play TTS audio response
  const playAudioResponse = async (audioData: ArrayBuffer) => {
    try {
      if (soundRef.current) {
        await soundRef.current.unloadAsync();
      }

      const FileSystem = require("expo-file-system");
      const base64 = btoa(
        new Uint8Array(audioData).reduce(
          (data, byte) => data + String.fromCharCode(byte),
          ""
        )
      );
      const fileUri = FileSystem.cacheDirectory + "alice_live_response.mp3";
      await FileSystem.writeAsStringAsync(fileUri, base64, {
        encoding: FileSystem.EncodingType.Base64,
      });

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        playsInSilentModeIOS: true,
      });

      const { sound } = await Audio.Sound.createAsync({ uri: fileUri });
      soundRef.current = sound;

      sound.setOnPlaybackStatusUpdate((playbackStatus) => {
        if (playbackStatus.isLoaded && playbackStatus.didJustFinish) {
          setStatus("listening");
        }
      });

      await sound.playAsync();
    } catch (error) {
      console.error("Audio playback failed:", error);
    }
  };

  // Stop recording
  const stopRecording = async () => {
    setIsRecording(false);
    if (recordingRef.current) {
      try {
        await recordingRef.current.stopAndUnloadAsync();
      } catch {}
      recordingRef.current = null;
    }
  };

  // End session
  const endSession = async () => {
    stopRecording();

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "end" }));
      wsRef.current.close();
    }

    if (soundRef.current) {
      try { await soundRef.current.unloadAsync(); } catch {}
    }

    router.back();
  };

  // Connect on mount
  useEffect(() => {
    connectWebSocket();

    return () => {
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
      case "listening": return { text: "Ich höre zu...", color: "#22c55e" };
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

  return (
    <View style={{ flex: 1, backgroundColor: "#0f172a" }}>
      <StatusBar barStyle="light-content" />

      {/* Top Bar */}
      <View style={{ paddingTop: 60, paddingHorizontal: 20, flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
        <Text style={{ color: "#ffffff", fontSize: 18, fontWeight: "600" }}>
          Live-Gespräch
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
        {/* Pulse ring */}
        <Animated.View
          style={[
            pulseAnimatedStyle,
            {
              position: "absolute",
              width: 200,
              height: 200,
              borderRadius: 100,
              borderWidth: 2,
              borderColor: getOrbColor(),
            },
          ]}
        />

        {/* Rotating ring */}
        <Animated.View
          style={[
            ringAnimatedStyle,
            {
              position: "absolute",
              width: 220,
              height: 220,
              borderRadius: 110,
              borderWidth: 1,
              borderColor: "transparent",
              borderTopColor: getOrbColor(),
              borderBottomColor: getOrbColor(),
              opacity: 0.5,
            },
          ]}
        />

        {/* Main orb */}
        <Animated.View
          style={[
            orbAnimatedStyle,
            {
              width: 160,
              height: 160,
              borderRadius: 80,
              backgroundColor: getOrbColor(),
              shadowColor: getOrbColor(),
              shadowOffset: { width: 0, height: 0 },
              shadowOpacity: 0.5,
              shadowRadius: 30,
              elevation: 20,
              alignItems: "center",
              justifyContent: "center",
            },
          ]}
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

      {/* Transcript area (semi-transparent, scrollable) */}
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
