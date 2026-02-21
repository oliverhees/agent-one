import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { Card } from "../../../components/ui/Card";
import { Button } from "../../../components/ui/Button";
import { agentApi, EmailConfig, EmailConfigCreate } from "../../../services/agents";

export default function EmailConfigScreen() {
  const [existingConfig, setExistingConfig] = useState<EmailConfig | null>(null);
  const [formData, setFormData] = useState({
    smtp_host: "",
    smtp_port: "",
    smtp_user: "",
    smtp_password: "",
    imap_host: "",
    imap_port: "",
    imap_user: "",
    imap_password: "",
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const config = await agentApi.getEmailConfig();
      setExistingConfig(config);

      if (config) {
        setFormData({
          smtp_host: config.smtp_host,
          smtp_port: config.smtp_port.toString(),
          smtp_user: config.smtp_user,
          smtp_password: "", // Don't show existing password
          imap_host: config.imap_host,
          imap_port: config.imap_port.toString(),
          imap_user: config.imap_user,
          imap_password: "", // Don't show existing password
        });
      }
    } catch (error) {
      console.error("Failed to load email config:", error);
      Alert.alert("Fehler", "Konfiguration konnte nicht geladen werden.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    // Validation
    if (!formData.smtp_host.trim() || !formData.smtp_port.trim() || !formData.smtp_user.trim()) {
      Alert.alert("Fehler", "SMTP Host, Port und Benutzer sind erforderlich.");
      return;
    }

    if (!formData.imap_host.trim() || !formData.imap_port.trim() || !formData.imap_user.trim()) {
      Alert.alert("Fehler", "IMAP Host, Port und Benutzer sind erforderlich.");
      return;
    }

    // Password required only if no existing config or user wants to change it
    if (!existingConfig && (!formData.smtp_password.trim() || !formData.imap_password.trim())) {
      Alert.alert("Fehler", "Passwörter sind beim ersten Speichern erforderlich.");
      return;
    }

    const smtpPort = parseInt(formData.smtp_port, 10);
    const imapPort = parseInt(formData.imap_port, 10);

    if (isNaN(smtpPort) || isNaN(imapPort)) {
      Alert.alert("Fehler", "Ports müssen gültige Zahlen sein.");
      return;
    }

    setIsSaving(true);
    try {
      const payload: EmailConfigCreate = {
        smtp_host: formData.smtp_host.trim(),
        smtp_port: smtpPort,
        smtp_user: formData.smtp_user.trim(),
        smtp_password: formData.smtp_password.trim() || "••••••", // Keep existing if not changed
        imap_host: formData.imap_host.trim(),
        imap_port: imapPort,
        imap_user: formData.imap_user.trim(),
        imap_password: formData.imap_password.trim() || "••••••", // Keep existing if not changed
      };

      const savedConfig = await agentApi.saveEmailConfig(payload);
      setExistingConfig(savedConfig);

      // Clear password fields after successful save
      setFormData({
        ...formData,
        smtp_password: "",
        imap_password: "",
      });

      Alert.alert("Erfolg", "Email-Konfiguration wurde gespeichert.");
    } catch (error) {
      console.error("Failed to save email config:", error);
      Alert.alert("Fehler", "Konfiguration konnte nicht gespeichert werden.");
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <View className="flex-1 bg-gray-50 dark:bg-gray-900 items-center justify-center">
        <ActivityIndicator size="large" color="#0284c7" />
      </View>
    );
  }

  return (
    <View className="flex-1 bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <View className="bg-white dark:bg-gray-800 px-4 py-3 flex-row items-center border-b border-gray-200 dark:border-gray-700">
        <TouchableOpacity
          onPress={() => router.back()}
          className="mr-3"
          accessibilityLabel="Zurueck"
        >
          <Ionicons name="arrow-back" size={24} color="#0284c7" />
        </TouchableOpacity>
        <Text className="text-xl font-semibold text-gray-900 dark:text-white">
          Email-Agent Konfiguration
        </Text>
      </View>

      <ScrollView className="flex-1" keyboardShouldPersistTaps="handled">
        <View className="p-6">
          {/* Status Badge */}
          {existingConfig && (
            <View className="mb-4 flex-row items-center bg-green-50 dark:bg-green-900/30 px-4 py-3 rounded-lg">
              <Ionicons
                name={existingConfig.is_active ? "checkmark-circle" : "close-circle"}
                size={20}
                color={existingConfig.is_active ? "#16a34a" : "#dc2626"}
                style={{ marginRight: 8 }}
              />
              <Text className="text-green-700 dark:text-green-400 font-medium">
                {existingConfig.is_active ? "Email-Agent ist aktiv" : "Email-Agent ist inaktiv"}
              </Text>
            </View>
          )}

          {/* Info Box */}
          <View className="mb-6 bg-blue-50 dark:bg-blue-900/30 px-4 py-3 rounded-lg">
            <Text className="text-blue-700 dark:text-blue-400 text-sm">
              Der Email-Agent benötigt SMTP (zum Senden) und IMAP (zum Empfangen) Zugangsdaten.
              {existingConfig && " Lasse die Passwort-Felder leer, um die bestehenden zu behalten."}
            </Text>
          </View>

          {/* SMTP Configuration Card */}
          <Card className="mb-4">
            <View className="flex-row items-center mb-4">
              <Ionicons
                name="send-outline"
                size={24}
                color="#0284c7"
                style={{ marginRight: 10 }}
              />
              <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                SMTP Konfiguration (Ausgehend)
              </Text>
            </View>

            <View className="mb-4">
              <Text className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Host
              </Text>
              <TextInput
                className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-3 text-gray-900 dark:text-white"
                placeholder="z.B. smtp.gmail.com"
                placeholderTextColor="#9ca3af"
                value={formData.smtp_host}
                onChangeText={(text) => setFormData({ ...formData, smtp_host: text })}
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            <View className="mb-4">
              <Text className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Port
              </Text>
              <TextInput
                className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-3 text-gray-900 dark:text-white"
                placeholder="z.B. 587"
                placeholderTextColor="#9ca3af"
                value={formData.smtp_port}
                onChangeText={(text) => setFormData({ ...formData, smtp_port: text })}
                keyboardType="numeric"
              />
            </View>

            <View className="mb-4">
              <Text className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Benutzer
              </Text>
              <TextInput
                className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-3 text-gray-900 dark:text-white"
                placeholder="z.B. deine@email.com"
                placeholderTextColor="#9ca3af"
                value={formData.smtp_user}
                onChangeText={(text) => setFormData({ ...formData, smtp_user: text })}
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="email-address"
              />
            </View>

            <View>
              <Text className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Passwort
              </Text>
              <TextInput
                className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-3 text-gray-900 dark:text-white"
                placeholder={existingConfig ? "••••••" : "SMTP Passwort"}
                placeholderTextColor="#9ca3af"
                value={formData.smtp_password}
                onChangeText={(text) => setFormData({ ...formData, smtp_password: text })}
                secureTextEntry
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>
          </Card>

          {/* IMAP Configuration Card */}
          <Card className="mb-6">
            <View className="flex-row items-center mb-4">
              <Ionicons
                name="mail-outline"
                size={24}
                color="#0284c7"
                style={{ marginRight: 10 }}
              />
              <Text className="text-lg font-semibold text-gray-900 dark:text-white">
                IMAP Konfiguration (Eingehend)
              </Text>
            </View>

            <View className="mb-4">
              <Text className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Host
              </Text>
              <TextInput
                className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-3 text-gray-900 dark:text-white"
                placeholder="z.B. imap.gmail.com"
                placeholderTextColor="#9ca3af"
                value={formData.imap_host}
                onChangeText={(text) => setFormData({ ...formData, imap_host: text })}
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            <View className="mb-4">
              <Text className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Port
              </Text>
              <TextInput
                className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-3 text-gray-900 dark:text-white"
                placeholder="z.B. 993"
                placeholderTextColor="#9ca3af"
                value={formData.imap_port}
                onChangeText={(text) => setFormData({ ...formData, imap_port: text })}
                keyboardType="numeric"
              />
            </View>

            <View className="mb-4">
              <Text className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Benutzer
              </Text>
              <TextInput
                className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-3 text-gray-900 dark:text-white"
                placeholder="z.B. deine@email.com"
                placeholderTextColor="#9ca3af"
                value={formData.imap_user}
                onChangeText={(text) => setFormData({ ...formData, imap_user: text })}
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="email-address"
              />
            </View>

            <View>
              <Text className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Passwort
              </Text>
              <TextInput
                className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-3 text-gray-900 dark:text-white"
                placeholder={existingConfig ? "••••••" : "IMAP Passwort"}
                placeholderTextColor="#9ca3af"
                value={formData.imap_password}
                onChangeText={(text) => setFormData({ ...formData, imap_password: text })}
                secureTextEntry
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>
          </Card>

          {/* Save Button */}
          <Button
            title="Konfiguration speichern"
            onPress={handleSave}
            isLoading={isSaving}
          />
        </View>
      </ScrollView>
    </View>
  );
}
