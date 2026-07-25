import React from "react";
import { Image, StyleSheet, View, type StyleProp, type ViewStyle } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { color, material } from "./tokens";

/**
 * Materials — what makes the surfaces physical instead of flat color.
 * PaperGrain lies over page scenes; Lamplight stages the cover scenes.
 * Both are pure decoration: pointerEvents none, invisible to screen readers.
 */

const GRAIN_URI =
  "data:image/png;base64,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";

export function PaperGrain() {
  return (
    <View style={[StyleSheet.absoluteFill, { pointerEvents: "none" }]}>
      <Image
        source={{ uri: GRAIN_URI }}
        resizeMode="repeat"
        style={[StyleSheet.absoluteFill, { opacity: material.grainOpacity }]}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      />
    </View>
  );
}

/** A page-scene wrapper: paper + grain. */
export function Page({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <View style={[{ flex: 1, backgroundColor: color.paper }, style]}>
      {children}
      <PaperGrain />
    </View>
  );
}

/** A cover-scene wrapper: lamplight gradient falling onto the stage. */
export function Lamplight({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <LinearGradient colors={[material.lamplightTop, color.stage]} style={[{ flex: 1 }, style]}>
      {children}
    </LinearGradient>
  );
}
