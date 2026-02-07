import { Tabs, useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { TouchableOpacity, View, Text, Image, useColorScheme } from "react-native";
import { useChatStore } from "../../stores/chatStore";

export default function TabsLayout() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";
  const router = useRouter();
  const { startNewConversation } = useChatStore();

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
      <Tabs.Screen
        name="chat"
        options={{
          title: "Chat mit Alice",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="chatbubble-outline" size={size} color={color} />
          ),
          headerLeft: () => (
            <View style={{ flexDirection: "row", alignItems: "center", marginLeft: 16, gap: 16 }}>
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
            <View style={{ marginRight: 12 }}>
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
        }}
      />
      <Tabs.Screen
        name="tasks"
        options={{
          title: "Aufgaben",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="checkbox-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="brain"
        options={{
          title: "Brain",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="bulb-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="dashboard"
        options={{
          title: "Dashboard",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="analytics-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: "Einstellungen",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="settings-outline" size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}
