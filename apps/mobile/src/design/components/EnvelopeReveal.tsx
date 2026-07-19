import React, { useEffect, useRef, useState } from "react";
import { Animated, StyleSheet, Text, View } from "react-native";
import { color, duration, font, radius, shadow, space, type } from "../tokens";
import { Lamplight } from "../materials";
import { Unfold, useReduceMotion } from "../motion";
import { play } from "../sound";
import { haptic } from "../haptics";

/**
 * A chapter arrives as a letter: a paper envelope under lamplight, a gold
 * seal, then it unfolds into the reader. The whole ceremony is ~1.6s and
 * collapses to a quick crossfade under reduced motion.
 */
export function EnvelopeReveal({
  ordinal,
  title,
  onOpened,
}: {
  ordinal: number;
  title: string;
  onOpened: () => void;
}) {
  const reduce = useReduceMotion();
  const [open, setOpen] = useState(false);
  const fade = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    const hold = setTimeout(() => {
      play("seal_open");
      haptic.sealOpen();
      setOpen(true);
    }, reduce ? 150 : 550);
    return () => clearTimeout(hold);
  }, [reduce]);

  const settled = () => {
    Animated.timing(fade, {
      toValue: 0,
      duration: duration.crossfade,
      delay: 350,
      useNativeDriver: true,
    }).start(({ finished }) => {
      if (finished) onOpened();
    });
  };

  return (
    <Animated.View style={[StyleSheet.absoluteFill, { opacity: fade, zIndex: 10 }]}>
      <Lamplight style={styles.center}>
        <Unfold open={open} onSettled={settled} style={styles.envelope}>
          <View style={styles.flap} />
          <View style={styles.seal}>
            <Text style={styles.sealMark}>K</Text>
          </View>
          <Text style={type.label}>Chapter {ordinal}</Text>
          <Text style={styles.title} numberOfLines={3}>
            {title}
          </Text>
        </Unfold>
      </Lamplight>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  center: { alignItems: "center", justifyContent: "center", padding: space(8) },
  envelope: {
    width: "100%",
    maxWidth: 420,
    backgroundColor: color.paper,
    borderRadius: radius.sheet,
    padding: space(7),
    paddingTop: space(10),
    alignItems: "center",
    gap: space(2),
    ...shadow.sheet,
  },
  flap: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    height: space(6),
    backgroundColor: color.surface,
    borderTopLeftRadius: radius.sheet,
    borderTopRightRadius: radius.sheet,
  },
  seal: {
    position: "absolute",
    top: space(3),
    alignSelf: "center",
    width: 40,
    height: 40,
    borderRadius: radius.seal,
    backgroundColor: color.gold,
    alignItems: "center",
    justifyContent: "center",
    ...shadow.cover,
  },
  sealMark: { fontFamily: font.display, fontSize: 20, color: color.paper },
  title: {
    fontFamily: font.display,
    fontSize: 24,
    lineHeight: 34,
    color: color.ink,
    textAlign: "center",
  },
});
