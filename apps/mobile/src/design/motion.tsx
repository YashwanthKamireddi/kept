import React, { useEffect, useRef, useState } from "react";
import {
  AccessibilityInfo,
  Animated,
  Easing,
  Platform,
  Pressable,
  type PressableProps,
  type StyleProp,
  type ViewStyle,
} from "react-native";
import { duration } from "./tokens";

/**
 * The motion language: pages settle, threads draw themselves, objects give
 * under the finger, covers breathe while a story is being told.
 *
 * Web note: useNativeDriver is a native-only optimization — on react-native-web
 * it's unsupported and makes transforms/opacity glitchy. So every animation
 * uses the native driver on device and the JS driver (smooth, RAF-based) on
 * web. Motion is also tuned subtler + snappier on web so it reads like a
 * polished site, not a phone app straining in a browser. Reduced motion wins
 * everywhere.
 */

const WEB = Platform.OS === "web";
const NATIVE = !WEB;

/** The one place any component decides the Animated driver: native on device,
 * JS/RAF on web (where the native driver is unsupported and glitchy). Import
 * this instead of hardcoding `useNativeDriver: true` in local animations. */
export const NATIVE_DRIVER = NATIVE;

// Per-surface motion tuning: richer on device, crisp on web.
const RISE = WEB ? 8 : 16;
const ENTER_MS = WEB ? 360 : duration.entrance;
const STAGGER_MS = WEB ? 55 : duration.stagger;

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
      duration: ENTER_MS,
      delay: order * STAGGER_MS,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: NATIVE,
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
                outputRange: [RISE, 0],
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
      delay: order * STAGGER_MS,
      easing: Easing.out(Easing.quad),
      useNativeDriver: NATIVE,
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
      useNativeDriver: NATIVE,
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
          useNativeDriver: NATIVE,
        }),
        Animated.timing(value, {
          toValue: 1,
          duration: duration.breath,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: NATIVE,
        }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [active, low, value]);

  return value;
}

/** A letter opening. On device it tips forward in 3D; on web (where 3D
 * rotateX is janky) and under reduced motion it's a clean fade-and-settle. */
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
  const flat = reduceMotion || WEB;
  const progress = useRef(new Animated.Value(flat ? (open ? 1 : 0) : 0)).current;

  // Read the latest callback through a ref instead of the effect's dependency
  // array. A parent re-rendering for unrelated reasons (e.g. a sibling audio
  // hook ticking) recreates onSettled every time; if that identity were a
  // dependency, every such re-render would restart this animation from
  // scratch and the "finished" callback would never fire — the reveal would
  // hang forever. Only `open` flipping should (re)start the animation.
  const onSettledRef = useRef(onSettled);
  onSettledRef.current = onSettled;
  const startedFor = useRef<boolean | null>(null);

  useEffect(() => {
    if (startedFor.current === open) return;
    startedFor.current = open;
    Animated.timing(progress, {
      toValue: open ? 1 : 0,
      duration: flat ? duration.crossfade : duration.unfold,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: NATIVE,
    }).start(({ finished }) => {
      if (finished && open) onSettledRef.current?.();
    });
  }, [open, progress, flat]);

  const transform = flat
    ? [
        {
          translateY: progress.interpolate({ inputRange: [0, 1], outputRange: [10, 0] }),
        },
      ]
    : [
        { perspective: 900 },
        {
          rotateX: progress.interpolate({
            inputRange: [0, 1],
            outputRange: ["-70deg", "0deg"],
          }) as unknown as string,
        },
      ];

  return (
    <Animated.View style={[style, { opacity: progress, transform }]}>
      {children}
    </Animated.View>
  );
}
