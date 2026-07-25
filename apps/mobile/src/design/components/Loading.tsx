import React from "react";
import { Animated, StyleSheet, Text } from "react-native";
import { color, space, type } from "../tokens";
import { useBreath } from "../motion";
import { Page } from "../materials";

/**
 * The single loading state for the whole app: a small gold mark breathing on
 * paper, with one honest line of what's opening. Replaces bare "Loading…"
 * text, which read like an unfinished screen. Still under reduced motion —
 * useBreath holds steady — so it degrades to a calm dot.
 */
export function Loading({ label }: { label?: string }) {
  const breath = useBreath(true, 0.3);
  return (
    <Page style={styles.center}>
      <Animated.View style={[styles.mark, { opacity: breath }]} />
      {label ? <Text style={[type.caption, styles.label]}>{label}</Text> : null}
    </Page>
  );
}

const styles = StyleSheet.create({
  center: { alignItems: "center", justifyContent: "center" },
  mark: { width: 10, height: 10, borderRadius: 999, backgroundColor: color.gold },
  label: { marginTop: space(4), color: color.inkSoft },
});
