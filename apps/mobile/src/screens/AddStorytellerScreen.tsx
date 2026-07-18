import React, { useMemo, useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../navigation";
import { color, font, space, type } from "../theme";
import { Entrance, PressableScale } from "../components/motion";
import { useApp } from "../state";

type Props = NativeStackScreenProps<RootStackParamList, "AddStoryteller">;

// Universal coverage; launch-wedge languages included, not privileged.
const LANGUAGES = [
  { tag: "en", label: "English" },
  { tag: "es", label: "Español" },
  { tag: "pt", label: "Português" },
  { tag: "fr", label: "Français" },
  { tag: "ar", label: "العربية" },
  { tag: "zh", label: "中文" },
  { tag: "vi", label: "Tiếng Việt" },
  { tag: "hi-IN", label: "हिन्दी" },
  { tag: "te-IN", label: "తెలుగు" },
  { tag: "ta-IN", label: "தமிழ்" },
] as const;

function firstCallOptions(): { key: string; label: string; at: Date }[] {
  const at = (daysAhead: number, hour: number) => {
    const d = new Date();
    d.setDate(d.getDate() + daysAhead);
    d.setHours(hour, 0, 0, 0);
    return d;
  };
  const saturday = new Date();
  saturday.setDate(saturday.getDate() + ((6 - saturday.getDay() + 7) % 7 || 7));
  saturday.setHours(10, 0, 0, 0);
  return [
    { key: "tomorrow-am", label: "Tomorrow morning", at: at(1, 10) },
    { key: "tomorrow-pm", label: "Tomorrow evening", at: at(1, 18) },
    { key: "weekend", label: "Saturday morning", at: saturday },
  ];
}

export function AddStorytellerScreen({ navigation }: Props) {
  const { client } = useApp();
  const [name, setName] = useState("");
  const [addressAs, setAddressAs] = useState("");
  const [phone, setPhone] = useState("");
  const [language, setLanguage] = useState<string>("en");
  const [callKey, setCallKey] = useState("tomorrow-am");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const options = useMemo(firstCallOptions, []);
  const ready = name.trim() && addressAs.trim() && /^\+\d{7,15}$/.test(phone.trim());

  const submit = async () => {
    if (!client) return;
    setBusy(true);
    setError("");
    try {
      const chosen = options.find((o) => o.key === callKey) ?? options[0];
      await client.createStoryteller({
        name: name.trim(),
        address_as: addressAs.trim(),
        phone_e164: phone.trim(),
        language,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        next_call_at: chosen.at.toISOString(),
        cadence_days: 7,
      });
      navigation.goBack();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.page}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView contentContainerStyle={styles.scroll}>
        <Entrance order={0}>
          <Text style={type.sectionTitle}>Who tells the stories in your family?</Text>
        </Entrance>

        <Entrance order={1} style={{ gap: space(5) }}>
          <Field label="Their name" value={name} onChange={setName} placeholder="Rosa Almeida" />
          <Field
            label="How should we address them on the call?"
            value={addressAs}
            onChange={setAddressAs}
            placeholder="Grandma Rosa"
          />
          <Field
            label="Phone number"
            value={phone}
            onChange={setPhone}
            placeholder="+15551234567"
            keyboard="phone-pad"
          />
        </Entrance>

        <Entrance order={2}>
          <Text style={[type.label, { marginBottom: space(2) }]}>
            The language they tell stories in
          </Text>
          <View style={styles.chips}>
            {LANGUAGES.map((l) => (
              <Chip
                key={l.tag}
                label={l.label}
                selected={language === l.tag}
                onPress={() => setLanguage(l.tag)}
              />
            ))}
          </View>
        </Entrance>

        <Entrance order={3}>
          <Text style={[type.label, { marginBottom: space(2) }]}>First call</Text>
          <View style={styles.chips}>
            {options.map((o) => (
              <Chip
                key={o.key}
                label={o.label}
                selected={callKey === o.key}
                onPress={() => setCallKey(o.key)}
              />
            ))}
          </View>
        </Entrance>

        <Entrance order={4} style={{ gap: space(4) }}>
          <Text style={type.caption}>
            Calls repeat weekly. On the first call we introduce ourselves and ask for
            their blessing before anything is recorded — they can always say no.
          </Text>
          {error ? <Text style={styles.error}>{error}</Text> : null}
          <PressableScale
            accessibilityRole="button"
            onPress={submit}
            disabled={!ready || busy}
            style={[styles.button, (!ready || busy) && { opacity: 0.4 }]}
          >
            <Text style={styles.buttonText}>
              {busy ? "Adding to the album…" : "Add storyteller"}
            </Text>
          </PressableScale>
        </Entrance>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  keyboard,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  keyboard?: "phone-pad";
}) {
  return (
    <View style={{ gap: space(1) }}>
      <Text style={type.label}>{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChange}
        placeholder={placeholder}
        placeholderTextColor={color.hairline}
        keyboardType={keyboard}
        style={styles.input}
      />
    </View>
  );
}

function Chip({
  label,
  selected,
  onPress,
}: {
  label: string;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected }}
      onPress={onPress}
      style={[styles.chip, selected && styles.chipSelected]}
    >
      <Text style={[styles.chipText, selected && styles.chipTextSelected]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: color.paper },
  scroll: { padding: space(6), gap: space(5), paddingBottom: space(12) },
  input: {
    borderBottomWidth: 1,
    borderBottomColor: color.hairline,
    paddingVertical: space(2),
    fontFamily: font.body,
    fontSize: 17,
    color: color.ink,
  },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: space(2) },
  chip: {
    paddingHorizontal: space(3),
    paddingVertical: space(2),
    borderRadius: 999,
    borderWidth: 1,
    borderColor: color.hairline,
    backgroundColor: color.paper,
  },
  chipSelected: { borderColor: color.gold, backgroundColor: color.surface },
  chipText: { fontFamily: font.bodyMedium, fontSize: 14, color: color.inkSoft },
  chipTextSelected: { color: color.ink },
  error: { ...type.caption, color: color.ember },
  button: {
    backgroundColor: color.ink,
    paddingVertical: space(4),
    alignItems: "center",
    borderRadius: 6,
    marginTop: space(2),
  },
  buttonText: { fontFamily: font.bodyBold, fontSize: 16, color: color.paper },
});
