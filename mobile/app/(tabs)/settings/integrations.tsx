import { useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Alert,
  useColorScheme,
  TextInput,
  ActivityIndicator,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useCalendarStore } from "../../../stores/calendarStore";
import { useWebhookStore } from "../../../stores/webhookStore";
import { useN8nStore } from "../../../stores/n8nStore";
import { calendarApi } from "../../../services/calendar";
import * as WebBrowser from "expo-web-browser";

export default function IntegrationsScreen() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";

  const { status, fetchStatus, disconnect } = useCalendarStore();
  const { webhooks, fetchWebhooks, createWebhook, deleteWebhook } = useWebhookStore();
  const { workflows, fetchWorkflows, createWorkflow, deleteWorkflow } = useN8nStore();

  const [showAddWebhook, setShowAddWebhook] = useState(false);
  const [webhookName, setWebhookName] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");

  const [showAddWorkflow, setShowAddWorkflow] = useState(false);
  const [workflowName, setWorkflowName] = useState("");
  const [workflowUrl, setWorkflowUrl] = useState("");

  useEffect(() => {
    fetchStatus();
    fetchWebhooks();
    fetchWorkflows();
  }, []);

  const handleGoogleConnect = async () => {
    try {
      const { auth_url } = await calendarApi.getAuthUrl();
      await WebBrowser.openBrowserAsync(auth_url);
      fetchStatus();
    } catch {
      Alert.alert("Fehler", "Google-Verbindung konnte nicht gestartet werden.");
    }
  };

  const handleDisconnect = () => {
    Alert.alert("Kalender trennen?", "Alle synchronisierten Events werden entfernt.", [
      { text: "Abbrechen", style: "cancel" },
      {
        text: "Trennen",
        style: "destructive",
        onPress: async () => {
          await disconnect();
        },
      },
    ]);
  };

  const handleAddWebhook = async () => {
    if (!webhookName || !webhookUrl) return;
    await createWebhook({ name: webhookName, url: webhookUrl, direction: "outgoing" });
    setWebhookName("");
    setWebhookUrl("");
    setShowAddWebhook(false);
  };

  const handleAddWorkflow = async () => {
    if (!workflowName || !workflowUrl) return;
    await createWorkflow({ name: workflowName, webhook_url: workflowUrl });
    setWorkflowName("");
    setWorkflowUrl("");
    setShowAddWorkflow(false);
  };

  const bg = isDark ? "#111827" : "#f9fafb";
  const cardBg = isDark ? "#1f2937" : "#ffffff";
  const textPrimary = isDark ? "#f9fafb" : "#111827";
  const textSecondary = isDark ? "#9ca3af" : "#6b7280";
  const accent = "#0284c7";
  const border = isDark ? "#374151" : "#e5e7eb";

  return (
    <ScrollView style={{ flex: 1, backgroundColor: bg }}>
      <View style={{ padding: 16, gap: 20 }}>
        {/* Google Calendar Section */}
        <View style={{ backgroundColor: cardBg, borderRadius: 12, padding: 16, gap: 12 }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
            <Ionicons name="calendar-outline" size={24} color={accent} />
            <Text style={{ fontSize: 18, fontWeight: "600", color: textPrimary }}>
              Google Calendar
            </Text>
          </View>

          {status?.connected ? (
            <View style={{ gap: 8 }}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                <Ionicons name="checkmark-circle" size={18} color="#22c55e" />
                <Text style={{ color: "#22c55e", fontWeight: "500" }}>Verbunden</Text>
              </View>
              {status.last_synced && (
                <Text style={{ color: textSecondary, fontSize: 13 }}>
                  Letzter Sync: {new Date(status.last_synced).toLocaleString("de-DE")}
                </Text>
              )}
              <TouchableOpacity
                onPress={handleDisconnect}
                style={{
                  backgroundColor: "#ef4444",
                  borderRadius: 8,
                  padding: 10,
                  alignItems: "center",
                  marginTop: 4,
                }}
              >
                <Text style={{ color: "#fff", fontWeight: "600" }}>Trennen</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <TouchableOpacity
              onPress={handleGoogleConnect}
              style={{
                backgroundColor: accent,
                borderRadius: 8,
                padding: 12,
                alignItems: "center",
              }}
            >
              <Text style={{ color: "#fff", fontWeight: "600" }}>Mit Google verbinden</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Webhooks Section */}
        <View style={{ backgroundColor: cardBg, borderRadius: 12, padding: 16, gap: 12 }}>
          <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
              <Ionicons name="git-network-outline" size={24} color={accent} />
              <Text style={{ fontSize: 18, fontWeight: "600", color: textPrimary }}>Webhooks</Text>
            </View>
            <TouchableOpacity onPress={() => setShowAddWebhook(!showAddWebhook)}>
              <Ionicons name={showAddWebhook ? "close" : "add-circle-outline"} size={24} color={accent} />
            </TouchableOpacity>
          </View>

          {showAddWebhook && (
            <View style={{ gap: 8, padding: 8, backgroundColor: bg, borderRadius: 8 }}>
              <TextInput
                placeholder="Name"
                placeholderTextColor={textSecondary}
                value={webhookName}
                onChangeText={setWebhookName}
                style={{ backgroundColor: cardBg, borderRadius: 6, padding: 10, color: textPrimary, borderWidth: 1, borderColor: border }}
              />
              <TextInput
                placeholder="URL"
                placeholderTextColor={textSecondary}
                value={webhookUrl}
                onChangeText={setWebhookUrl}
                style={{ backgroundColor: cardBg, borderRadius: 6, padding: 10, color: textPrimary, borderWidth: 1, borderColor: border }}
              />
              <TouchableOpacity onPress={handleAddWebhook} style={{ backgroundColor: accent, borderRadius: 6, padding: 10, alignItems: "center" }}>
                <Text style={{ color: "#fff", fontWeight: "600" }}>Hinzufuegen</Text>
              </TouchableOpacity>
            </View>
          )}

          {webhooks.length === 0 ? (
            <Text style={{ color: textSecondary, fontSize: 14 }}>Keine Webhooks konfiguriert</Text>
          ) : (
            webhooks.map((wh) => (
              <View key={wh.id} style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingVertical: 8, borderTopWidth: 1, borderTopColor: border }}>
                <View style={{ flex: 1 }}>
                  <Text style={{ color: textPrimary, fontWeight: "500" }}>{wh.name}</Text>
                  <Text style={{ color: textSecondary, fontSize: 12 }}>{wh.direction} - {wh.url.slice(0, 30)}...</Text>
                </View>
                <TouchableOpacity onPress={() => deleteWebhook(wh.id)}>
                  <Ionicons name="trash-outline" size={20} color="#ef4444" />
                </TouchableOpacity>
              </View>
            ))
          )}
        </View>

        {/* n8n Workflows Section */}
        <View style={{ backgroundColor: cardBg, borderRadius: 12, padding: 16, gap: 12 }}>
          <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
              <Ionicons name="flash-outline" size={24} color={accent} />
              <Text style={{ fontSize: 18, fontWeight: "600", color: textPrimary }}>n8n Workflows</Text>
            </View>
            <TouchableOpacity onPress={() => setShowAddWorkflow(!showAddWorkflow)}>
              <Ionicons name={showAddWorkflow ? "close" : "add-circle-outline"} size={24} color={accent} />
            </TouchableOpacity>
          </View>

          {showAddWorkflow && (
            <View style={{ gap: 8, padding: 8, backgroundColor: bg, borderRadius: 8 }}>
              <TextInput
                placeholder="Workflow Name"
                placeholderTextColor={textSecondary}
                value={workflowName}
                onChangeText={setWorkflowName}
                style={{ backgroundColor: cardBg, borderRadius: 6, padding: 10, color: textPrimary, borderWidth: 1, borderColor: border }}
              />
              <TextInput
                placeholder="Webhook URL"
                placeholderTextColor={textSecondary}
                value={workflowUrl}
                onChangeText={setWorkflowUrl}
                style={{ backgroundColor: cardBg, borderRadius: 6, padding: 10, color: textPrimary, borderWidth: 1, borderColor: border }}
              />
              <TouchableOpacity onPress={handleAddWorkflow} style={{ backgroundColor: accent, borderRadius: 6, padding: 10, alignItems: "center" }}>
                <Text style={{ color: "#fff", fontWeight: "600" }}>Hinzufuegen</Text>
              </TouchableOpacity>
            </View>
          )}

          {workflows.length === 0 ? (
            <Text style={{ color: textSecondary, fontSize: 14 }}>Keine Workflows registriert</Text>
          ) : (
            workflows.map((wf) => (
              <View key={wf.id} style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingVertical: 8, borderTopWidth: 1, borderTopColor: border }}>
                <View style={{ flex: 1 }}>
                  <Text style={{ color: textPrimary, fontWeight: "500" }}>{wf.name}</Text>
                  <Text style={{ color: textSecondary, fontSize: 12 }}>
                    {wf.execution_count} Ausfuehrungen
                    {wf.last_executed_at ? ` | Zuletzt: ${new Date(wf.last_executed_at).toLocaleString("de-DE")}` : ""}
                  </Text>
                </View>
                <TouchableOpacity onPress={() => deleteWorkflow(wf.id)}>
                  <Ionicons name="trash-outline" size={20} color="#ef4444" />
                </TouchableOpacity>
              </View>
            ))
          )}
        </View>
      </View>
    </ScrollView>
  );
}
