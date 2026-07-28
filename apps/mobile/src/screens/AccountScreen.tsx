import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { color, font, space, type } from "../design/tokens";
import { Entrance, PressableScale } from "../design/motion";
import { Page } from "../design/materials";
import { useApp } from "../state";

/** The "You" tab: who's keeping these stories, and the way out. Kept spare —
 * a masthead, one line that matters, and an ex-libris plate. */
export function AccountScreen() {
  const { signOut } = useApp();
  return (
    <Page>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Entrance order={0}>
          <Text style={type.sectionTitle}>You</Text>
          <View style={styles.masthead}>
            <View style={styles.ruleA} />
            <View style={styles.ruleB} />
          </View>
          <Text style={styles.dateline}>The keeper of these stories</Text>
        </Entrance>

        <Entrance order={1} style={styles.block}>
          <Text style={type.label}>Ownership</Text>
          <Text style={[type.body, { color: color.inkSoft }]}>
            Your family owns every recording. Erase any album from its Manage screen.
          </Text>
        </Entrance>

        <Entrance order={2}>
          <PressableScale
            accessibilityRole="button"
            onPress={() => void signOut()}
            style={styles.signOut}
          >
            <Text style={styles.signOutText}>Sign out</Text>
          </PressableScale>
        </Entrance>

        <Entrance order={3} style={styles.plate}>
          <View style={styles.plateRule} />
          <Text style={styles.brandFoot}>Kept</Text>
          <View style={styles.plateRule} />
        </Entrance>
      </ScrollView>
    </Page>
  );
}

const styles = StyleSheet.create({
  scroll: { padding: space(6), gap: space(7), paddingBottom: space(24) },
  // Same letterpress masthead as Home, for a consistent identity.
  masthead: { gap: 2, marginTop: space(1) },
  ruleA: { height: 1.5, backgroundColor: color.inkSoft, opacity: 0.35 },
  ruleB: { height: 1, backgroundColor: color.hairline },
  dateline: {
    fontFamily: font.bodyMedium,
    fontSize: 11,
    letterSpacing: 1.6,
    textTransform: "uppercase",
    color: color.inkSoft,
    marginTop: space(1),
  },
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
  // An ex-libris plate: the wordmark bracketed by two short ink rules.
  plate: {
    alignSelf: "center",
    alignItems: "center",
    gap: space(2),
    paddingHorizontal: space(8),
    paddingVertical: space(5),
    borderWidth: 1,
    borderColor: color.hairline,
    borderRadius: 4,
    marginTop: space(6),
  },
  plateRule: { width: 40, height: 1, backgroundColor: color.hairline },
  brandFoot: {
    fontFamily: font.wordmark,
    fontSize: 26,
    color: color.inkSoft,
    letterSpacing: 1,
  },
});
