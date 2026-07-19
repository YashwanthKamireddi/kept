import React, { useEffect, useRef } from "react";
import { Animated, Easing, Modal, Pressable, StyleSheet, Text, View } from "react-native";
import { color, space, type } from "../tokens";
import { Lamplight } from "../materials";
import { useReduceMotion } from "../motion";

/**
 * The lights go down. While the storyteller speaks, everything disappears
 * except their words, their name, and a breathing thread of sound.
 * Tap anywhere to return to the page.
 */
export function ListeningRoom({
  visible,
  sentence,
  storytellerName,
  playing,
  onClose,
}: {
  visible: boolean;
  sentence: string;
  storytellerName: string;
  playing: boolean;
  onClose: () => void;
}) {
  return (
    <Modal visible={visible} animationType="fade" transparent onRequestClose={onClose}>
      <Pressable style={{ flex: 1 }} onPress={onClose} accessibilityRole="button">
        <Lamplight style={styles.room}>
          <Waveform playing={playing} />
          <Text style={styles.sentence}>{sentence}</Text>
          {storytellerName ? (
            <Text style={[type.coverName, styles.name]}>{storytellerName}</Text>
          ) : null}
          <Text style={styles.hint}>tap anywhere to return</Text>
        </Lamplight>
      </Pressable>
    </Modal>
  );
}

const BAR_COUNT = 7;

function Waveform({ playing }: { playing: boolean }) {
  const reduce = useReduceMotion();
  const bars = useRef(
    Array.from({ length: BAR_COUNT }, () => new Animated.Value(0.4)),
  ).current;

  useEffect(() => {
    if (!playing || reduce) {
      bars.forEach((b) => b.setValue(0.5));
      return;
    }
    const loops = bars.map((bar, i) =>
      Animated.loop(
        Animated.sequence([
          Animated.timing(bar, {
            toValue: 1,
            duration: 340 + i * 55,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(bar, {
            toValue: 0.3,
            duration: 340 + ((BAR_COUNT - i) * 45),
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
        ]),
      ),
    );
    loops.forEach((l) => l.start());
    return () => loops.forEach((l) => l.stop());
  }, [playing, reduce, bars]);

  return (
    <View style={styles.wave} accessibilityElementsHidden>
      {bars.map((bar, i) => (
        <Animated.View key={i} style={[styles.bar, { transform: [{ scaleY: bar }] }]} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  room: {
    alignItems: "center",
    justifyContent: "center",
    padding: space(8),
    gap: space(6),
  },
  wave: {
    flexDirection: "row",
    alignItems: "center",
    gap: space(2),
    height: 44,
  },
  bar: {
    width: 3,
    height: 36,
    borderRadius: 2,
    backgroundColor: color.foil,
  },
  sentence: { ...type.proseLarge, textAlign: "center" },
  name: { fontSize: 18, lineHeight: 26 },
  hint: {
    ...type.caption,
    color: color.stageText,
    position: "absolute",
    bottom: space(12),
  },
});
