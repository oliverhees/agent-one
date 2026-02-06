import React, { useState } from "react";
import { View, Text, TouchableOpacity, Switch } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";
import { PersonalityRule } from "../../types/personality";

interface RuleEditorProps {
  rules: PersonalityRule[];
  onChange: (rules: PersonalityRule[]) => void;
}

export const RuleEditor: React.FC<RuleEditorProps> = ({ rules, onChange }) => {
  const [newRuleText, setNewRuleText] = useState("");

  const addRule = () => {
    const trimmed = newRuleText.trim();
    if (trimmed && rules.length < 20) {
      onChange([...rules, { text: trimmed, enabled: true }]);
      setNewRuleText("");
    }
  };

  const toggleRule = (index: number) => {
    const updated = [...rules];
    updated[index] = { ...updated[index], enabled: !updated[index].enabled };
    onChange(updated);
  };

  const removeRule = (index: number) => {
    onChange(rules.filter((_, i) => i !== index));
  };

  return (
    <View>
      <Text className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Regeln ({rules.length}/20)
      </Text>

      {rules.map((rule, index) => (
        <View
          key={rule.id ?? index}
          className="flex-row items-center bg-white dark:bg-gray-800 rounded-lg px-3 py-2 mb-2 border border-gray-200 dark:border-gray-700"
        >
          <Switch
            value={rule.enabled}
            onValueChange={() => toggleRule(index)}
            trackColor={{ false: "#d1d5db", true: "#0284c7" }}
            thumbColor="#ffffff"
          />
          <Text
            className={`flex-1 ml-2 text-sm ${
              rule.enabled
                ? "text-gray-900 dark:text-white"
                : "text-gray-400 dark:text-gray-500"
            }`}
            numberOfLines={2}
          >
            {rule.text}
          </Text>
          <TouchableOpacity
            onPress={() => removeRule(index)}
            className="ml-2 p-1"
            accessibilityLabel={`Regel "${rule.text}" entfernen`}
          >
            <Ionicons name="close-circle" size={20} color="#ef4444" />
          </TouchableOpacity>
        </View>
      ))}

      <View className="flex-row items-center mt-1">
        <View className="flex-1 mr-2">
          <Input
            placeholder="Neue Regel hinzufuegen..."
            value={newRuleText}
            onChangeText={setNewRuleText}
            onSubmitEditing={addRule}
            returnKeyType="done"
            accessibilityLabel="Neue Regel"
          />
        </View>
        <Button
          title="+"
          onPress={addRule}
          className="px-4 py-3"
          disabled={!newRuleText.trim() || rules.length >= 20}
        />
      </View>
    </View>
  );
};
