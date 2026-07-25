import React, { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { color, font, radius, shadow, space, type } from "../design/tokens";
import { Entrance, PressableScale } from "../design/motion";
import { Field } from "../design/components/Field";
import { Lamplight } from "../design/materials";
import { strings } from "../design/copy";
import { DEFAULT_BASE_URL, useApp } from "../state";

/**
 * The cover scene. Arriving should feel like opening a leather album in
 * lamplight: a dark stage, a gold-foil wordmark, then a sheet of warm paper
 * rising to meet you. The form lives ON the paper — never floating in void.
 */
export function SignInScreen() {
  const { signIn } = useApp();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [familyName, setFamilyName] = useState("");
  const [baseUrl, setBaseUrl] = useState(DEFAULT_BASE_URL);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [showServer, setShowServer] = useState(false);

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
    <Lamplight>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
        >
          <Entrance order={0}>
            <Text style={type.wordmark}>Kept</Text>
          </Entrance>
          <Entrance order={1}>
            <Text style={styles.thesis}>{strings.thesis}</Text>
          </Entrance>

          <Entrance order={3} style={styles.sheetWrap}>
            <View style={styles.sheet}>
              <Field label="Your name" value={name} onChange={setName} />
              <Field label="Email" value={email} onChange={setEmail} keyboard="email-address" />
              <Field label="Family name" value={familyName} onChange={setFamilyName} />
              {showServer ? (
                <Field label="Server" value={baseUrl} onChange={setBaseUrl} keyboard="url" />
              ) : null}
              {error ? <Text style={styles.error}>{error}</Text> : null}
              <PressableScale
                accessibilityRole="button"
                onPress={submit}
                disabled={!ready || busy}
                style={[styles.button, (!ready || busy) && { opacity: 0.4 }]}
              >
                <Text style={styles.buttonText}>
                  {busy ? "Opening the album…" : "Begin"}
                </Text>
              </PressableScale>
            </View>
          </Entrance>

          <Entrance order={4}>
            <Text style={styles.footnote}>
              {strings.consentFootnote}
            </Text>
            {!showServer ? (
              <PressableScale
                accessibilityRole="button"
                onPress={() => setShowServer(true)}
                style={styles.advancedHit}
              >
                <Text style={styles.advanced}>Advanced</Text>
              </PressableScale>
            ) : null}
          </Entrance>
        </ScrollView>
      </KeyboardAvoidingView>
    </Lamplight>
  );
}


const styles = StyleSheet.create({
  scroll: {
    flexGrow: 1,
    justifyContent: "center",
    paddingHorizontal: space(6),
    paddingVertical: space(12),
    maxWidth: 560,
    width: "100%",
    alignSelf: "center",
  },
  thesis: {
    fontFamily: font.displaySoft,
    fontSize: 20,
    lineHeight: 32,
    color: color.stageText,
    marginTop: space(2),
  },
  sheetWrap: { marginTop: space(9) },
  sheet: {
    backgroundColor: color.paper,
    borderRadius: radius.sheet,
    padding: space(6),
    gap: space(5),
    ...shadow.sheet,
  },
  error: { ...type.caption, color: color.ember },
  button: {
    backgroundColor: color.ink,
    paddingVertical: space(4),
    alignItems: "center",
    borderRadius: 10,
    marginTop: space(2),
  },
  buttonText: { fontFamily: font.bodyBold, fontSize: 16, color: color.paper },
  footnote: {
    ...type.caption,
    color: color.stageText,
    textAlign: "center",
    marginTop: space(6),
  },
  advancedHit: { alignSelf: "center", paddingVertical: space(2), paddingHorizontal: space(3) },
  advanced: {
    fontFamily: font.bodyMedium,
    fontSize: 12,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: color.stageText,
    opacity: 0.6,
  },
});
