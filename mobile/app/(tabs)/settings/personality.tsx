import React, { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Alert,
  Modal,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { Card } from "../../../components/ui/Card";
import { Button } from "../../../components/ui/Button";
import { Input } from "../../../components/ui/Input";
import { LoadingSpinner } from "../../../components/ui/LoadingSpinner";
import { TraitSlider } from "../../../components/personality/TraitSlider";
import { TemplateCard } from "../../../components/personality/TemplateCard";
import { RuleEditor } from "../../../components/personality/RuleEditor";
import {
  usePersonalityProfiles,
  usePersonalityTemplates,
  useCreateProfile,
  useUpdateProfile,
  useDeleteProfile,
  useActivateProfile,
} from "../../../hooks/usePersonality";
import {
  Traits,
  PersonalityRule,
  PersonalityProfile,
  PersonalityTemplate,
} from "../../../types/personality";

const DEFAULT_TRAITS: Traits = {
  formality: 50,
  humor: 50,
  strictness: 50,
  empathy: 50,
  verbosity: 50,
};

const TRAIT_CONFIG: {
  key: keyof Traits;
  label: string;
  minLabel: string;
  maxLabel: string;
}[] = [
  { key: "formality", label: "Foermlichkeit", minLabel: "Locker", maxLabel: "Formell" },
  { key: "humor", label: "Humor", minLabel: "Ernst", maxLabel: "Witzig" },
  { key: "strictness", label: "Strenge", minLabel: "Nachsichtig", maxLabel: "Streng" },
  { key: "empathy", label: "Empathie", minLabel: "Sachlich", maxLabel: "Einfuehlsam" },
  { key: "verbosity", label: "Ausfuehrlichkeit", minLabel: "Kurz", maxLabel: "Ausfuehrlich" },
];

export default function PersonalityScreen() {
  const { data: profilesData, isLoading: profilesLoading } =
    usePersonalityProfiles();
  const { data: templatesData, isLoading: templatesLoading } =
    usePersonalityTemplates();

  const createProfile = useCreateProfile();
  const updateProfile = useUpdateProfile();
  const deleteProfile = useDeleteProfile();
  const activateProfile = useActivateProfile();

  const [showModal, setShowModal] = useState(false);
  const [editingProfile, setEditingProfile] =
    useState<PersonalityProfile | null>(null);

  // Form state
  const [name, setName] = useState("");
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(
    null
  );
  const [traits, setTraits] = useState<Traits>(DEFAULT_TRAITS);
  const [rules, setRules] = useState<PersonalityRule[]>([]);
  const [customInstructions, setCustomInstructions] = useState("");

  const profiles = profilesData?.items ?? [];
  const templates = templatesData?.items ?? [];

  const openCreate = () => {
    setEditingProfile(null);
    setName("");
    setSelectedTemplateId(null);
    setTraits(DEFAULT_TRAITS);
    setRules([]);
    setCustomInstructions("");
    setShowModal(true);
  };

  const openEdit = (profile: PersonalityProfile) => {
    setEditingProfile(profile);
    setName(profile.name);
    setSelectedTemplateId(profile.template_id);
    setTraits(profile.traits);
    setRules(profile.rules);
    setCustomInstructions(profile.custom_instructions ?? "");
    setShowModal(true);
  };

  const handleSelectTemplate = (template: PersonalityTemplate) => {
    setSelectedTemplateId(template.id);
    setTraits(template.traits);
    if (template.rules) {
      setRules(template.rules.map((r) => ({ text: r.text, enabled: r.enabled })));
    }
  };

  const handleTraitChange = (key: keyof Traits, value: number) => {
    setTraits((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = () => {
    if (!name.trim()) {
      Alert.alert("Fehler", "Bitte gib einen Namen ein.");
      return;
    }

    const data = {
      name: name.trim(),
      ...(selectedTemplateId && { template_id: selectedTemplateId }),
      traits,
      rules: rules.map((r) => ({ text: r.text, enabled: r.enabled })),
      custom_instructions: customInstructions.trim() || undefined,
    };

    if (editingProfile) {
      updateProfile.mutate(
        { id: editingProfile.id, data },
        { onSuccess: () => setShowModal(false) }
      );
    } else {
      createProfile.mutate(data, { onSuccess: () => setShowModal(false) });
    }
  };

  const handleActivate = (id: string) => {
    activateProfile.mutate(id);
  };

  const handleDelete = (profile: PersonalityProfile) => {
    if (profile.is_active) {
      Alert.alert(
        "Nicht moeglich",
        "Das aktive Profil kann nicht geloescht werden. Aktiviere zuerst ein anderes Profil."
      );
      return;
    }
    Alert.alert("Profil loeschen", `"${profile.name}" wirklich loeschen?`, [
      { text: "Abbrechen", style: "cancel" },
      {
        text: "Loeschen",
        style: "destructive",
        onPress: () => deleteProfile.mutate(profile.id),
      },
    ]);
  };

  if (profilesLoading || templatesLoading) {
    return <LoadingSpinner message="Persoenlichkeit wird geladen..." />;
  }

  return (
    <View className="flex-1 bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <View className="flex-row items-center px-4 pt-4 pb-2">
        <TouchableOpacity
          onPress={() => router.back()}
          className="p-2 mr-2"
          accessibilityLabel="Zurueck"
        >
          <Ionicons name="arrow-back" size={24} color="#0284c7" />
        </TouchableOpacity>
        <Text className="text-xl font-bold text-gray-900 dark:text-white flex-1">
          Persoenlichkeit
        </Text>
        <TouchableOpacity
          onPress={openCreate}
          className="p-2"
          accessibilityLabel="Neues Profil erstellen"
        >
          <Ionicons name="add-circle-outline" size={24} color="#0284c7" />
        </TouchableOpacity>
      </View>

      <ScrollView className="flex-1 px-4">
        {/* Profiles */}
        <Text className="text-base font-semibold text-gray-900 dark:text-white mb-3">
          Deine Profile
        </Text>

        {profiles.length === 0 ? (
          <Card className="mb-4 items-center py-8">
            <Ionicons name="person-outline" size={48} color="#9ca3af" />
            <Text className="text-gray-500 dark:text-gray-400 mt-2 text-center">
              Noch keine Profile erstellt
            </Text>
            <Text className="text-gray-400 dark:text-gray-500 text-sm text-center mt-1">
              Erstelle ein Profil, um ALICEs Persoenlichkeit anzupassen
            </Text>
          </Card>
        ) : (
          profiles.map((profile) => (
            <Card key={profile.id} className="mb-3">
              <View className="flex-row items-center justify-between">
                <View className="flex-1">
                  <View className="flex-row items-center">
                    <Text className="text-base font-medium text-gray-900 dark:text-white">
                      {profile.name}
                    </Text>
                    {profile.is_active && (
                      <View className="ml-2 px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900">
                        <Text className="text-xs font-medium text-green-700 dark:text-green-300">
                          Aktiv
                        </Text>
                      </View>
                    )}
                  </View>
                  {profile.template_name && (
                    <Text className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                      Basiert auf: {profile.template_name}
                    </Text>
                  )}
                </View>
                <View className="flex-row gap-1">
                  {!profile.is_active && (
                    <TouchableOpacity
                      onPress={() => handleActivate(profile.id)}
                      className="p-2"
                      accessibilityLabel="Profil aktivieren"
                    >
                      <Ionicons
                        name="radio-button-off"
                        size={20}
                        color="#0284c7"
                      />
                    </TouchableOpacity>
                  )}
                  <TouchableOpacity
                    onPress={() => openEdit(profile)}
                    className="p-2"
                    accessibilityLabel="Profil bearbeiten"
                  >
                    <Ionicons
                      name="create-outline"
                      size={20}
                      color="#6b7280"
                    />
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={() => handleDelete(profile)}
                    className="p-2"
                    accessibilityLabel="Profil loeschen"
                  >
                    <Ionicons
                      name="trash-outline"
                      size={20}
                      color="#ef4444"
                    />
                  </TouchableOpacity>
                </View>
              </View>
            </Card>
          ))
        )}

        {/* Templates Preview */}
        <Text className="text-base font-semibold text-gray-900 dark:text-white mt-4 mb-3">
          Vorlagen
        </Text>
        <Text className="text-sm text-gray-500 dark:text-gray-400 mb-3">
          Starte mit einer Vorlage und passe sie an deine Beduerfnisse an.
        </Text>
        {templates.map((template) => (
          <TemplateCard
            key={template.id}
            template={template}
            onSelect={(t) => {
              handleSelectTemplate(t);
              setName(t.name);
              setEditingProfile(null);
              setShowModal(true);
            }}
          />
        ))}

        <View className="h-8" />
      </ScrollView>

      {/* Create/Edit Modal */}
      <Modal
        visible={showModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowModal(false)}
      >
        <View className="flex-1 bg-gray-50 dark:bg-gray-900">
          {/* Modal Header */}
          <View className="flex-row items-center justify-between px-4 pt-4 pb-2 border-b border-gray-200 dark:border-gray-800">
            <TouchableOpacity
              onPress={() => setShowModal(false)}
              className="p-2"
              accessibilityLabel="Abbrechen"
            >
              <Text className="text-primary-600 text-base">Abbrechen</Text>
            </TouchableOpacity>
            <Text className="text-base font-semibold text-gray-900 dark:text-white">
              {editingProfile ? "Profil bearbeiten" : "Neues Profil"}
            </Text>
            <TouchableOpacity
              onPress={handleSave}
              className="p-2"
              accessibilityLabel="Speichern"
              disabled={createProfile.isPending || updateProfile.isPending}
            >
              <Text className="text-primary-600 text-base font-semibold">
                {createProfile.isPending || updateProfile.isPending
                  ? "..."
                  : "Fertig"}
              </Text>
            </TouchableOpacity>
          </View>

          <ScrollView className="flex-1 px-4 pt-4">
            {/* Name */}
            <Input
              label="Profilname *"
              placeholder="z.B. Mein Coach"
              value={name}
              onChangeText={setName}
              accessibilityLabel="Profilname"
            />

            {/* Templates (only for new profiles) */}
            {!editingProfile && templates.length > 0 && (
              <View className="mb-4">
                <Text className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Vorlage (optional)
                </Text>
                <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                  {templates.map((t) => (
                    <TouchableOpacity
                      key={t.id}
                      onPress={() => handleSelectTemplate(t)}
                      className={`mr-2 px-3 py-2 rounded-lg border ${
                        selectedTemplateId === t.id
                          ? "border-primary-600 bg-primary-50 dark:bg-primary-900"
                          : "border-gray-300 dark:border-gray-700"
                      }`}
                    >
                      <Text
                        className={`text-sm ${
                          selectedTemplateId === t.id
                            ? "text-primary-700 dark:text-primary-300 font-medium"
                            : "text-gray-600 dark:text-gray-400"
                        }`}
                      >
                        {t.name}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>
            )}

            {/* Traits */}
            <Text className="text-base font-semibold text-gray-900 dark:text-white mb-3">
              Persoenlichkeits-Traits
            </Text>
            {TRAIT_CONFIG.map((config) => (
              <TraitSlider
                key={config.key}
                label={config.label}
                value={traits[config.key]}
                onValueChange={(v) => handleTraitChange(config.key, v)}
                minLabel={config.minLabel}
                maxLabel={config.maxLabel}
              />
            ))}

            {/* Rules */}
            <Text className="text-base font-semibold text-gray-900 dark:text-white mt-2 mb-3">
              Regeln
            </Text>
            <RuleEditor rules={rules} onChange={setRules} />

            {/* Custom Instructions */}
            <View className="mt-4 mb-8">
              <Input
                label="Zusaetzliche Anweisungen"
                placeholder="Weitere Anweisungen fuer ALICE..."
                value={customInstructions}
                onChangeText={setCustomInstructions}
                multiline
                numberOfLines={4}
                className="min-h-[100px] text-top"
                accessibilityLabel="Zusaetzliche Anweisungen"
              />
            </View>
          </ScrollView>
        </View>
      </Modal>
    </View>
  );
}
