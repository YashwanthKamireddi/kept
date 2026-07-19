import React, { useEffect, useRef, useState } from "react";
import {
  AccessibilityInfo,
  Animated,
  Easing,
  Pressable,
  type PressableProps,
  type StyleProp,
  type ViewStyle,
} from "react-native";
import { duration } from "./tokens";

/**
 * The motion language: pages settle, threads draw themselves, objects give
 * under the finger, covers breathe while a story is being told. Every
 * primitive honors reduced motion — stillness is a first-class rendering.
 */

let reduceMotion = false;
AccessibilityInfo.isReduceMotionEnabled?.().then((v) => {
  reduceMotion = Boolean(v);
});

export function useReduceMotion(): boolean {
  const [value] = useState(reduceMotion);
  return value;
}

/** Staggered fade-and-rise: content settles like a page laid on a table. */
export function Entrance({
  order = 0,
  children,
  style,
}: {
  order?: number;
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  const progress = useRef(new Animated.Value(reduceMotion ? 1 : 0)).current;

  useEffect(() => {
    if (reduceMotion) return;
    Animated.timing(progress, {
      toValue: 1,
      duration: duration.entrance,
      delay: order * duration.stagger,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: true,
    }).start();
  }, [order, progress]);

  return (
    <Animated.View
      style={[
        style,
        {
          opacity: progress,
          transform: [
            {
              translateY: progress.interpolate({
                inputRange: [0, 1],
                outputRange: [16, 0],
              }),
            },
          ],
        },
      ]}
    >
      {children}
    </Animated.View>
  );
}

/** A hairline that draws itself from left to right. */
export function DrawnRule({
  color: ruleColor,
  style,
  order = 0,
}: {
  color: string;
  style?: StyleProp<ViewStyle>;
  order?: number;
}) {
  const progress = useRef(new Animated.Value(reduceMotion ? 1 : 0)).current;

  useEffect(() => {
    if (reduceMotion) return;
    Animated.timing(progress, {
      toValue: 1,
      duration: duration.rule,
      delay: order * duration.stagger,
      easing: Easing.out(Easing.quad),
      useNativeDriver: true,
    }).start();
  }, [order, progress]);

  return (
    <Animated.View
      style={[
        { height: 1, backgroundColor: ruleColor, transform: [{ scaleX: progress }] },
        { transformOrigin: "left" as never },
        style,
      ]}
    />
  );
}

/** Pressable with a gentle spring press — objects, not buttons. */
export function PressableScale({
  children,
  style,
  ...props
}: PressableProps & { style?: StyleProp<ViewStyle>; children: React.ReactNode }) {
  const scale = useRef(new Animated.Value(1)).current;

  const to = (value: number) =>
    Animated.spring(scale, {
      toValue: value,
      speed: 30,
      bounciness: 6,
      useNativeDriver: true,
    }).start();

  return (
    <Pressable
      {...props}
      onPressIn={(e) => {
        if (!reduceMotion) to(0.975);
        props.onPressIn?.(e);
      }}
      onPressOut={(e) => {
        if (!reduceMotion) to(1);
        props.onPressOut?.(e);
      }}
    >
      <Animated.View style={[style, { transform: [{ scale }] }]}>{children}</Animated.View>
    </Pressable>
  );
}

/** A slow lamplight breath — for a cover while its story is being told.
 * Returns an opacity value in [low, 1]. Still (1) under reduced motion. */
export function useBreath(active: boolean, low = 0.55): Animated.Value {
  const value = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (!active || reduceMotion) {
      value.setValue(1);
      return;
    }
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(value, {
          toValue: low,
          duration: duration.breath,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(value, {
          toValue: 1,
          duration: duration.breath,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [active, low, value]);

  return value;
}

/** An envelope-style unfold: content tips forward into view like a letter
 * being opened. Under reduced motion it is a plain crossfade. */
export function Unfold({
  open,
  children,
  style,
  onSettled,
}: {
  open: boolean;
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
  onSettled?: () => void;
}) {
  const progress = useRef(new Animated.Value(reduceMotion ? (open ? 1 : 0) : 0)).current;

  useEffect(() => {
    Animated.timing(progress, {
      toValue: open ? 1 : 0,
      duration: reduceMotion ? duration.crossfade : duration.unfold,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: true,
    }).start(({ finished }) => {
      if (finished && open) onSettled?.();
    });
  }, [open, progress, onSettled]);

  const rotateX = reduceMotion
    ? "0deg"
    : (progress.interpolate({
        inputRange: [0, 1],
        outputRange: ["-70deg", "0deg"],
      }) as unknown as string);

  return (
    <Animated.View
      style={[
        style,
        {
          opacity: progress,
          transform: [{ perspective: 900 }, { rotateX }],
        },
      ]}
    >
      {children}
    </Animated.View>
  );
}
