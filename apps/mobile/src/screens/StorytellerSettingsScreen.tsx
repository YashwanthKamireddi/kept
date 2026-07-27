import React, { useCallback, useState } from "react";
import { Alert, Platform, ScrollView, StyleSheet, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../navigation";
import { color, font, space, type } from "../design/tokens";
import { Entrance, PressableScale } from "../design/motion";
import { Page } from "../design/materials";
import { Loading } from "../design/components/Loading";
import { haptic } from "../design/haptics";
import { languageName, nextCallLine } from "../design/copy";
import { useApp } from "../state";
import type { ConsentStatus, Storyteller } from "../api/client";

type Props = NativeStackScreenProps<RootStackParamList, "StorytellerSettings">;

// Keeper-facing consent actions, phrased as human choices, not state names.
function consentAction(consent: ConsentStatus): { to: ConsentStatus; label: string } | null {
  switch (consent) {
    case "granted":
      return { to: "revoked", label: "Pause recording" };
    case "revoked":
    case "declined":
      return { to: "granted", label: "Resume recording" };
    case "pending":
      return null; // set on the first call, not here
  }
}

function consentLine(consent: ConsentStatus): string {
  switch (consent) {
    case "granted":
      return "Recording with their blessing.";
    case "pending":
      return "We'll ask for their blessing on the first call.";
    case "declined":
    case "revoked":
      return "Paused — no calls until you resume.";
  }
}

export function StorytellerSettingsScreen({ route, navigation }: Props) {
  const { client } = useApp();
  const [st, setSt] = useState<Storyteller | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (!client) return;
    setSt(await client.getStoryteller(route.params.storytellerId));
  }, [client, route.params.storytellerId]);

  useFocusEffect(
    useCallback(() => {
      void load();
    }, [load]),
  );

  const toggleConsent = async () => {
    if (!client || !st) return;
    const action = consentAction(st.consent);
    if (!action) return;
    setBusy(true);
    try {
      await client.setConsent(st.id, action.to);
      haptic.success();
      await load();
    } finally {
      setBusy(false);
    }
  };

  const confirmErase = () => {
    if (!st) return;
    const run = async () => {
      if (!client) return;
      setBusy(true);
      try {
        await client.eraseStoryteller(st.id);
        haptic.success();
        navigation.navigate("Home");
      } finally {
        setBusy(false);
      }
    };
    // Web has no native Alert dialog; guard the destructive action anyway.
    if (Platform.OS === "web") {
      // eslint-disable-next-line no-alert
      if (confirm(`Permanently delete ${st.name}'s album and every recording? This cannot be undone.`))
        void run();
      return;
    }
    Alert.alert(
      `Delete ${st.name}'s album?`,
      "This permanently removes every chapter, conversation, and recording. It cannot be undone.",
      [
        { text: "Cancel", style: "cancel" },
        { text: "Delete everything", style: "destructive", onPress: () => void run() },
      ],
    );
  };

  if (!st) return <Loading label="Opening…" />;

  const action = consentAction(st.consent);

  return (
    <Page>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Entrance order={0}>
          <Text style={type.sectionTitle}>{st.name}</Text>
        </Entrance>

        <Entrance order={1} style={styles.block}>
          <Text style={type.label}>In this album</Text>
          <NavRow
            label="Open threads"
            onPress={() =>
              navigation.navigate("FollowUps", { storytellerId: st.id, name: st.name })
            }
          />
          <NavRow
            label="Search stories"
            onPress={() =>
              navigation.navigate("Search", { storytellerId: st.id, name: st.name })
            }
          />
        </Entrance>

        <Entrance order={2} style={styles.block}>
          <Text style={type.label}>Recording</Text>
          <Text style={[type.body, { color: color.inkSoft }]}>{consentLine(st.consent)}</Text>
          {action && (
            <PressableScale
              accessibilityRole="button"
              onPress={toggleConsent}
              disabled={busy}
              style={[styles.secondary, busy && { opacity: 0.4 }]}
            >
              <Text style={styles.secondaryText}>{action.label}</Text>
            </PressableScale>
          )}
        </Entrance>

        <Entrance order={3} style={styles.block}>
          <Text style={type.label}>Calls</Text>
          <Text style={[type.body, { color: color.inkSoft }]}>
            Every {st.cadence_days} days, in {languageName(st.language)}.
          </Text>
          {st.consent === "granted" && nextCallLine(st.next_call_at) && (
            <Text style={styles.nextCall}>{nextCallLine(st.next_call_at)}</Text>
          )}
        </Entrance>

        <Entrance order={4} style={[styles.block, styles.danger]}>
          <Text style={type.label}>Erase</Text>
          <Text style={[type.caption, { color: color.inkSoft }]}>
            Delete {st.name}'s album and every recording, forever. This can't be undone.
          </Text>
          <PressableScale
            accessibilityRole="button"
            onPress={confirmErase}
            disabled={busy}
            style={[styles.dangerButton, busy && { opacity: 0.4 }]}
          >
            <Text style={styles.dangerText}>Delete everything</Text>
          </PressableScale>
        </Entrance>
      </ScrollView>
    </Page>
  );
}

function NavRow({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <PressableScale accessibilityRole="button" onPress={onPress} style={styles.navRow}>
      <Text style={styles.navRowText}>{label}</Text>
      <Text style={styles.navRowArrow}>→</Text>
    </PressableScale>
  );
}

const styles = StyleSheet.create({
  scroll: { padding: space(6), gap: space(7), paddingBottom: space(12) },
  block: { gap: space(2) },
  navRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: space(3),
    borderBottomWidth: 1,
    borderBottomColor: color.hairline,
  },
  navRowText: { fontFamily: font.body, fontSize: 17, color: color.ink },
  navRowArrow: { fontFamily: font.body, fontSize: 16, color: color.gold },
  nextCall: { fontFamily: font.bodyMedium, fontSize: 14, color: color.gold },
  secondary: {
    alignSelf: "flex-start",
    borderWidth: 1,
    borderColor: color.gold,
    paddingHorizontal: space(4),
    paddingVertical: space(2),
    borderRadius: 10,
    marginTop: space(1),
  },
  secondaryText: { fontFamily: font.bodyMedium, fontSize: 15, color: color.gold },
  danger: {
    borderTopWidth: 1,
    borderTopColor: color.hairline,
    paddingTop: space(6),
  },
  dangerButton: {
    alignSelf: "flex-start",
    borderWidth: 1,
    borderColor: color.ember,
    paddingHorizontal: space(4),
    paddingVertical: space(2),
    borderRadius: 10,
    marginTop: space(1),
  },
  dangerText: { fontFamily: font.bodyMedium, fontSize: 15, color: color.ember },
});
