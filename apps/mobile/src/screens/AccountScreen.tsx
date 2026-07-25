import React from "react";
import { ScrollView, StyleSheet, Text } from "react-native";
import { color, font, space, type } from "../design/tokens";
import { Entrance, PressableScale } from "../design/motion";
import { Page } from "../design/materials";
import { strings } from "../design/copy";
import { useApp } from "../state";

/** The "You" tab: who's keeping these stories, and the way out. */
export function AccountScreen() {
  const { signOut } = useApp();
  return (
    <Page>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Entrance order={0}>
          <Text style={type.sectionTitle}>You</Text>
          <Text style={[type.caption, { color: color.inkSoft }]}>The keeper of these stories</Text>
        </Entrance>

        <Entrance order={1} style={styles.block}>
          <Text style={type.label}>How Kept works</Text>
          <Text style={[type.body, { color: color.inkSoft }]}>{strings.consentFootnote}</Text>
          <Text style={[type.body, { color: color.inkSoft }]}>
            Your family owns every recording. You can erase any album, and everything in it,
            from that storyteller's Manage screen.
          </Text>
        </Entrance>

        <Entrance order={2} style={styles.block}>
          <PressableScale accessibilityRole="button" onPress={() => void signOut()} style={styles.signOut}>
            <Text style={styles.signOutText}>Sign out</Text>
          </PressableScale>
        </Entrance>

        <Entrance order={3}>
          <Text style={styles.brandFoot}>Kept</Text>
        </Entrance>
      </ScrollView>
    </Page>
  );
}

const styles = StyleSheet.create({
  scroll: { padding: space(6), gap: space(7), paddingBottom: space(24) },
  block: { gap: space(3) },
  signOut: {
    alignSelf: "flex-start",
    borderWidth: 1,
    borderColor: color.hairline,
    paddingHorizontal: space(5),
    paddingVertical: space(3),
    borderRadius: 12,
  },
  signOutText: { fontFamily: font.bodyMedium, fontSize: 15, color: color.inkSoft },
  brandFoot: {
    fontFamily: font.wordmark,
    fontSize: 22,
    color: color.hairline,
    textAlign: "center",
    letterSpacing: 1,
  },
});
