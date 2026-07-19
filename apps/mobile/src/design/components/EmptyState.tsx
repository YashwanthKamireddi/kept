import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { color, space, type } from "../tokens";
import { DrawnRule, Entrance } from "../motion";

/** An empty screen is an invitation to act — never a dead end. */
export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <Entrance order={0} style={styles.wrap}>
      <Text style={type.sectionTitle}>{title}</Text>
      <DrawnRule color={color.gold} order={1} style={styles.rule} />
      <Text style={[type.body, styles.body]}>{body}</Text>
    </Entrance>
  );
}

const styles = StyleSheet.create({
  wrap: { alignItems: "center", gap: space(4), paddingTop: space(20) },
  rule: { width: 56 },
  body: { color: color.inkSoft, textAlign: "center" },
});
