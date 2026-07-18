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
import { motion } from "../theme";

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
      duration: motion.entrance,
      delay: order * motion.stagger,
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
      duration: 700,
      delay: order * motion.stagger,
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
