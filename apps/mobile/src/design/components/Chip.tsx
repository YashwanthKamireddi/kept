import React from "react";
import { Pressable, StyleSheet, Text } from "react-native";
import { color, font, radius, space } from "../tokens";

export function Chip({
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
      style={[styles.chip, selected && styles.selected]}
    >
      <Text style={[styles.text, selected && styles.textSelected]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  chip: {
    paddingHorizontal: space(3),
    paddingVertical: space(2),
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: color.hairline,
    backgroundColor: color.paper,
  },
  selected: { borderColor: color.gold, backgroundColor: color.surface },
  text: { fontFamily: font.bodyMedium, fontSize: 14, color: color.inkSoft },
  textSelected: { color: color.ink },
});
