import React, { useEffect, useRef } from "react";
import { Animated, StyleSheet, Text, View } from "react-native";
import { color, duration, font, radius, shadow, space, type } from "../tokens";
import { Lamplight } from "../materials";
import { Unfold, useReduceMotion, NATIVE_DRIVER } from "../motion";
import { play } from "../sound";
import { haptic } from "../haptics";

/**
 * A chapter arrives as a letter: a paper envelope under lamplight with a
 * gold seal, then it crossfades into the reader. The card is on screen from
 * the very first frame — no blank hold before it — and the handoff to the
 * reader is driven by a plain timer, not an Animated completion callback, so
 * it can never hang waiting on one.
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
  const fade = useRef(new Animated.Value(1)).current;
  const openedRef = useRef(false);

  const finish = () => {
    if (openedRef.current) return;
    openedRef.current = true;
    onOpened();
  };

  useEffect(() => {
    play("seal_open");
    haptic.sealOpen();
    const settle = setTimeout(() => {
      Animated.timing(fade, {
        toValue: 0,
        duration: duration.crossfade,
        useNativeDriver: NATIVE_DRIVER,
      }).start(({ finished }) => {
        if (finished) finish();
      });
    }, reduce ? 150 : 650);
    // Belt and suspenders: whatever happens above, never leave the reader
    // stuck behind this card for more than a couple seconds.
    const safety = setTimeout(finish, 2400);
    return () => {
      clearTimeout(settle);
      clearTimeout(safety);
    };
  }, [reduce]);

  return (
    <Animated.View style={[StyleSheet.absoluteFill, { opacity: fade, zIndex: 10 }]}>
      <Lamplight style={styles.center}>
        <Unfold open style={styles.envelope}>
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
