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
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { Audio } from "expo-av";
import * as FileSystem from "expo-file-system";
import { useAuthStore } from "../../../stores/authStore";
import api from "../../../services/api";

type SessionStatus = "connecting" | "listening" | "thinking" | "speaking" | "error" | "ended";

interface TranscriptEntry {
  role: "user" | "assistant";
  text: string;
  timestamp: Date;
}

export default function LiveConversationScreen() {
  const [status, setStatus] = useState<SessionStatus>("connecting");
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const isRecordingRef = useRef(false);
  const scrollViewRef = useRef<ScrollView>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const recordingRef = useRef<Audio.Recording | null>(null);
  const soundRef = useRef<Audio.Sound | null>(null);

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
  const connectWebSocket = useCallback(async () => {
    if (!token) {
      setStatus("error");
      return;
    }

    try {
      const baseUrl = api.defaults.baseURL || "http://localhost:8000/api/v1";
      const wsUrl = baseUrl.replace(/^http/, "ws").replace(/\/api\/v1$/, "") + "/api/v1/voice/live?token=" + token;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("listening");
        startContinuousRecording();
      };

      ws.onmessage = async (event: MessageEvent) => {
        if (typeof event.data === "string") {
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
          try {
            const arrayBuffer = await event.data.arrayBuffer();
            await playAudioResponse(arrayBuffer);
          } catch (e) {
            console.error("Audio playback failed:", e);
          }
        }
      };

      ws.onerror = () => {
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

      setIsRecording(true);
      isRecordingRef.current = true;
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

      // Record for ~500ms then stop and send
      await new Promise(resolve => setTimeout(resolve, 500));

      if (recordingRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
        await recordingRef.current.stopAndUnloadAsync();
        const uri = recordingRef.current.getURI();
        recordingRef.current = null;

        if (uri) {
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
        if (isRecordingRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
          setTimeout(recordChunk, 50);
        }
      }
    } catch (error) {
      if (isRecordingRef.current) {
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
    isRecordingRef.current = false;
    if (recordingRef.current) {
      try {
        await recordingRef.current.stopAndUnloadAsync();
      } catch {}
      recordingRef.current = null;
    }
  };

  // End session
  const endSession = async () => {
    await stopRecording();

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
