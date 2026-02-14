import { useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  useColorScheme,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useCalendarStore } from "../../../stores/calendarStore";
import { useRouter } from "expo-router";

export default function CalendarScreen() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";
  const router = useRouter();

  const { status, todayEvents, isLoading, fetchStatus, fetchTodayEvents, sync } =
    useCalendarStore();

  useEffect(() => {
    fetchStatus();
    fetchTodayEvents();
  }, []);

  const bg = isDark ? "#111827" : "#f9fafb";
  const cardBg = isDark ? "#1f2937" : "#ffffff";
  const textPrimary = isDark ? "#f9fafb" : "#111827";
  const textSecondary = isDark ? "#9ca3af" : "#6b7280";
  const accent = "#0284c7";

  if (status && !status.connected) {
    return (
      <View style={{ flex: 1, backgroundColor: bg, justifyContent: "center", alignItems: "center", padding: 24 }}>
        <Ionicons name="calendar-outline" size={64} color={textSecondary} />
        <Text style={{ fontSize: 20, fontWeight: "600", color: textPrimary, marginTop: 16, textAlign: "center" }}>
          Kalender nicht verbunden
        </Text>
        <Text style={{ fontSize: 14, color: textSecondary, marginTop: 8, textAlign: "center" }}>
          Verbinde deinen Google Calendar in den Einstellungen.
        </Text>
        <TouchableOpacity
          onPress={() => router.push("/(tabs)/settings/integrations")}
          style={{ marginTop: 20, backgroundColor: accent, borderRadius: 8, paddingHorizontal: 20, paddingVertical: 12 }}
        >
          <Text style={{ color: "#fff", fontWeight: "600" }}>Zu den Einstellungen</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: bg }}
      refreshControl={<RefreshControl refreshing={isLoading} onRefresh={sync} />}
    >
      <View style={{ padding: 16, gap: 12 }}>
        <Text style={{ fontSize: 22, fontWeight: "700", color: textPrimary }}>
          Heute
        </Text>

        {todayEvents.length === 0 ? (
          <View style={{ backgroundColor: cardBg, borderRadius: 12, padding: 24, alignItems: "center", gap: 8 }}>
            <Ionicons name="sunny-outline" size={40} color={textSecondary} />
            <Text style={{ color: textSecondary, fontSize: 16 }}>Keine Termine heute</Text>
          </View>
        ) : (
          todayEvents.map((event) => (
            <View key={event.id} style={{ backgroundColor: cardBg, borderRadius: 12, padding: 16, gap: 6 }}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
                <Ionicons
                  name={event.is_all_day ? "sunny-outline" : "time-outline"}
                  size={18}
                  color={accent}
                />
                <Text style={{ fontSize: 16, fontWeight: "600", color: textPrimary, flex: 1 }}>
                  {event.title}
                </Text>
              </View>

              {!event.is_all_day && (
                <Text style={{ color: textSecondary, fontSize: 13, marginLeft: 26 }}>
                  {new Date(event.start_time).toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" })}
                  {" - "}
                  {new Date(event.end_time).toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" })}
                </Text>
              )}

              {event.is_all_day && (
                <Text style={{ color: textSecondary, fontSize: 13, marginLeft: 26 }}>Ganztaegig</Text>
              )}

              {event.location && (
                <View style={{ flexDirection: "row", alignItems: "center", gap: 6, marginLeft: 26 }}>
                  <Ionicons name="location-outline" size={14} color={textSecondary} />
                  <Text style={{ color: textSecondary, fontSize: 13 }}>{event.location}</Text>
                </View>
              )}
            </View>
          ))
        )}
      </View>
    </ScrollView>
  );
}
