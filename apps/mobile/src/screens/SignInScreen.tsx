import React, { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { color, font, space, type } from "../theme";
import { DEFAULT_BASE_URL, useApp } from "../state";

export function SignInScreen() {
  const { signIn } = useApp();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [familyName, setFamilyName] = useState("");
  const [baseUrl, setBaseUrl] = useState(DEFAULT_BASE_URL);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const submit = async () => {
    setBusy(true);
    setError("");
    try {
      await signIn(baseUrl, email.trim(), name.trim(), familyName.trim());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not reach the server");
    } finally {
      setBusy(false);
    }
  };

  const ready = email.includes("@") && name.length > 0 && familyName.length > 0;

  return (
    <KeyboardAvoidingView
      style={styles.page}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <Text style={styles.wordmark}>Katha</Text>
      <Text style={styles.thesis}>
        Every family has a storyteller.{"\n"}Keep her voice.
      </Text>

      <View style={styles.form}>
        <Field label="Your name" value={name} onChange={setName} />
        <Field label="Email" value={email} onChange={setEmail} keyboard="email-address" />
        <Field label="Family name" value={familyName} onChange={setFamilyName} />
        <Field label="Server (dev)" value={baseUrl} onChange={setBaseUrl} keyboard="url" />
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <Pressable
          accessibilityRole="button"
          onPress={submit}
          disabled={!ready || busy}
          style={({ pressed }) => [
            styles.button,
            (!ready || busy) && { opacity: 0.4 },
            pressed && { opacity: 0.8 },
          ]}
        >
          <Text style={styles.buttonText}>{busy ? "Opening the album…" : "Begin"}</Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

function Field({
  label,
  value,
  onChange,
  keyboard,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  keyboard?: "email-address" | "url";
}) {
  return (
    <View style={{ gap: space(1) }}>
      <Text style={type.label}>{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChange}
        keyboardType={keyboard}
        autoCapitalize={keyboard ? "none" : "words"}
        style={styles.input}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  page: {
    flex: 1,
    backgroundColor: color.paper,
    paddingHorizontal: space(7),
    justifyContent: "center",
  },
  wordmark: { fontFamily: font.display, fontSize: 44, color: color.ink },
  thesis: {
    ...type.sectionTitle,
    color: color.inkSoft,
    marginTop: space(2),
    marginBottom: space(10),
  },
  form: { gap: space(5) },
  input: {
    borderBottomWidth: 1,
    borderBottomColor: color.hairline,
    paddingVertical: space(2),
    fontFamily: font.body,
    fontSize: 17,
    color: color.ink,
  },
  error: { ...type.caption, color: color.madder },
  button: {
    backgroundColor: color.ink,
    paddingVertical: space(4),
    alignItems: "center",
    borderRadius: 6,
    marginTop: space(3),
  },
  buttonText: { fontFamily: font.bodyBold, fontSize: 16, color: color.paper },
});
