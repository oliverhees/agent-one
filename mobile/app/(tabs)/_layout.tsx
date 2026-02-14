import { useEffect } from "react";
import { Tabs, useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { TouchableOpacity, View, Image, useColorScheme } from "react-native";
import { useChatStore } from "../../stores/chatStore";
import { useModuleStore } from "../../stores/moduleStore";

type TabConfig = {
  name: string;
  title: string;
  icon: keyof typeof Ionicons.glyphMap;
  /** If set, tab is shown only when at least one of these modules is active */
  requiredModules?: string[];
};

const TAB_CONFIG: TabConfig[] = [
  { name: "chat", title: "Chat mit Alice", icon: "chatbubble-outline" },
  { name: "tasks", title: "Aufgaben", icon: "checkbox-outline" },
  { name: "brain", title: "Brain", icon: "bulb-outline" },
  {
    name: "dashboard",
    title: "Dashboard",
    icon: "analytics-outline",
    requiredModules: ["adhs", "wellness", "productivity"],
  },
  {
    name: "wellness",
    title: "Wellness",
    icon: "heart-outline",
    requiredModules: ["wellness"],
  },
  { name: "settings", title: "Einstellungen", icon: "settings-outline" },
];

export default function TabsLayout() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";
  const router = useRouter();
  const { startNewConversation } = useChatStore();
  const { activeModules, fetchModules } = useModuleStore();

  useEffect(() => {
    fetchModules();
  }, []);

  const isTabVisible = (tab: TabConfig): boolean => {
    if (!tab.requiredModules) return true;
    return tab.requiredModules.some((m) => activeModules.includes(m));
  };

  return (
    <Tabs
      screenOptions={{
        headerShown: true,
        tabBarActiveTintColor: "#0284c7",
        tabBarInactiveTintColor: "#9ca3af",
        tabBarHideOnKeyboard: true,
        tabBarStyle: {
          backgroundColor: isDark ? "#111827" : "#ffffff",
          borderTopColor: isDark ? "#374151" : "#e5e7eb",
        },
        headerStyle: {
          backgroundColor: isDark ? "#111827" : "#ffffff",
        },
        headerTintColor: isDark ? "#ffffff" : "#111827",
      }}
    >
      {TAB_CONFIG.map((tab) => (
        <Tabs.Screen
          key={tab.name}
          name={tab.name}
          options={{
            title: tab.title,
            href: isTabVisible(tab) ? undefined : null,
            tabBarIcon: ({ color, size }) => (
              <Ionicons name={tab.icon} size={size} color={color} />
            ),
            ...(tab.name === "chat"
              ? {
                  headerLeft: () => (
                    <View
                      style={{
                        flexDirection: "row",
                        alignItems: "center",
                        marginLeft: 16,
                        gap: 16,
                      }}
                    >
                      <TouchableOpacity
                        onPress={() => router.push("/(tabs)/chat/history")}
                        accessibilityLabel="Chat-Verlauf"
                      >
                        <Ionicons
                          name="time-outline"
                          size={24}
                          color={isDark ? "#ffffff" : "#111827"}
                        />
                      </TouchableOpacity>
                      <TouchableOpacity
                        onPress={startNewConversation}
                        accessibilityLabel="Neuer Chat"
                      >
                        <Ionicons
                          name="add-circle-outline"
                          size={24}
                          color={isDark ? "#ffffff" : "#111827"}
                        />
                      </TouchableOpacity>
                    </View>
                  ),
                  headerRight: () => (
                    <View
                      style={{
                        flexDirection: "row",
                        alignItems: "center",
                        marginRight: 12,
                        gap: 10,
                      }}
                    >
                      <TouchableOpacity
                        onPress={() => router.push("/(tabs)/chat/live")}
                        accessibilityLabel="Live-Gespraech starten"
                        style={{
                          width: 36,
                          height: 36,
                          borderRadius: 18,
                          alignItems: "center",
                          justifyContent: "center",
                          backgroundColor: isDark ? "#1e293b" : "#f1f5f9",
                        }}
                      >
                        <Ionicons name="radio" size={20} color="#0284c7" />
                      </TouchableOpacity>
                      <Image
                        source={require("../../assets/alice-avatar.png")}
                        style={{
                          width: 52,
                          height: 52,
                          borderRadius: 26,
                          borderWidth: 2.5,
                          borderColor: "#0284c7",
                          marginTop: 4,
                        }}
                      />
                    </View>
                  ),
                }
              : {}),
          }}
        />
      ))}
    </Tabs>
  );
}
