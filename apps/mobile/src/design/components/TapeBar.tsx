import React, { useEffect, useRef } from "react";
import { Animated, Easing, StyleSheet, Text, View } from "react-native";
import { color, font, space } from "../tokens";
import { NATIVE_DRIVER } from "../motion";

/**
 * The cassette. Kept keeps a voice, so the player is a tape: two reels that
 * turn while they speak, gold tape strung between them, a hand-written label,
 * and a Space-Mono counter. Honest states only — before a recording has
 * synced, the reels rest and the counter reads --:--.
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
  const spin = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!playing) {
      spin.stopAnimation();
      return;
    }
    const loop = Animated.loop(
      Animated.timing(spin, {
        toValue: 1,
        duration: 2600,
        easing: Easing.linear,
        useNativeDriver: NATIVE_DRIVER,
      }),
    );
    loop.start();
    return () => loop.stop();
  }, [playing, spin]);

  const rotate = spin.interpolate({ inputRange: [0, 1], outputRange: ["0deg", "360deg"] });

  const seconds = Math.floor(positionMs / 1000);
  const counter = `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(
    seconds % 60,
  ).padStart(2, "0")}`;

  return (
    <View style={styles.deck}>
      <View style={styles.shell}>
        <View style={styles.labelStrip}>
          <Text style={styles.written} numberOfLines={1}>
            {unavailable ? "not yet synced" : label}
          </Text>
        </View>
        <View style={styles.window}>
          <Reel rotate={rotate} />
          <View style={styles.tape} />
          <Reel rotate={rotate} />
        </View>
        <Text style={styles.counter}>{unavailable ? "--:--" : counter}</Text>
      </View>
    </View>
  );
}

/** One spool: a foil ring with a hub and six teeth, turned as one piece. */
function Reel({ rotate }: { rotate: Animated.AnimatedInterpolation<string> }) {
  return (
    <Animated.View style={[styles.reel, { transform: [{ rotate }] }]}>
      <View style={styles.spoke} />
      <View style={[styles.spoke, { transform: [{ rotate: "60deg" }] }]} />
      <View style={[styles.spoke, { transform: [{ rotate: "120deg" }] }]} />
      <View style={styles.hub} />
    </Animated.View>
  );
}

const REEL = 34;

const styles = StyleSheet.create({
  deck: {
    backgroundColor: color.ink,
    paddingHorizontal: space(5),
    paddingTop: space(4),
    paddingBottom: space(7),
  },
  shell: {
    backgroundColor: color.stageRaised,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.06)",
    paddingHorizontal: space(4),
    paddingVertical: space(3),
  },
  labelStrip: {
    backgroundColor: color.paper,
    borderRadius: 4,
    paddingHorizontal: space(3),
    paddingVertical: space(1),
    marginBottom: space(3),
  },
  written: { fontFamily: font.quote, fontSize: 14, color: color.ink },
  window: { flexDirection: "row", alignItems: "center", gap: space(3) },
  reel: {
    width: REEL,
    height: REEL,
    borderRadius: 999,
    borderWidth: 2,
    borderColor: color.foil,
    alignItems: "center",
    justifyContent: "center",
  },
  spoke: { position: "absolute", width: 2, height: REEL - 6, backgroundColor: "rgba(201,162,75,0.55)" },
  hub: { width: 9, height: 9, borderRadius: 999, backgroundColor: color.foil },
  tape: { flex: 1, height: 2, backgroundColor: color.gold },
  counter: {
    fontFamily: font.mono,
    fontSize: 13,
    color: color.foil,
    fontVariant: ["tabular-nums"],
    alignSelf: "flex-end",
    marginTop: space(2),
  },
});
