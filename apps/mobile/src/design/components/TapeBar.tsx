import React, { useEffect, useRef } from "react";
import { Animated, StyleSheet, Text, View } from "react-native";
import { color, font, space } from "../tokens";
import { NATIVE_DRIVER } from "../motion";

/**
 * The cassette bar: shown while the storyteller speaks. A gold thread shimmers
 * across the deck; the counter runs like a tape counter. Honest states only —
 * when a recording hasn't synced yet, it says so instead of pretending.
 */
export function TapeBar({
  playing,
  positionMs,
  label,
  unavailable,
}: {
  playing: boolean;
  positionMs: number;
  label: string;
  unavailable?: boolean;
}) {
  const shimmer = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!playing) return;
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, { toValue: 1, duration: 900, useNativeDriver: NATIVE_DRIVER }),
        Animated.timing(shimmer, { toValue: 0.35, duration: 900, useNativeDriver: NATIVE_DRIVER }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [playing, shimmer]);

  const seconds = Math.floor(positionMs / 1000);
  const counter = `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(
    seconds % 60,
  ).padStart(2, "0")}`;

  return (
    <View style={styles.deck}>
      <Animated.View
        style={[styles.thread, { opacity: playing ? shimmer : 0.25 }]}
      />
      <View style={styles.row}>
        <Text style={styles.counter}>{unavailable ? "--:--" : counter}</Text>
        <Text style={styles.label} numberOfLines={1}>
          {unavailable ? "This recording hasn't synced yet" : label}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  deck: {
    backgroundColor: color.ink,
    paddingHorizontal: space(5),
    paddingTop: space(3),
    paddingBottom: space(7),
  },
  thread: { height: 2, backgroundColor: color.gold, marginBottom: space(3) },
  row: { flexDirection: "row", alignItems: "center", gap: space(3) },
  counter: {
    fontFamily: font.bodyBold,
    fontSize: 15,
    color: color.gold,
    fontVariant: ["tabular-nums"],
  },
  label: { fontFamily: font.body, fontSize: 14, color: color.paper, flex: 1 },
});
