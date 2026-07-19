/**
 * Haptic language: one soft tap when her voice begins (a heartbeat), a light
 * touch when the seal opens. Nothing else — restraint is the design.
 * No-ops silently on web and on devices without haptics.
 */

import * as Haptics from "expo-haptics";
import { Platform } from "react-native";

function safe(fn: () => Promise<unknown>): void {
  if (Platform.OS === "web") return;
  void fn().catch(() => {});
}

export const haptic = {
  voiceStart: () => safe(() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Soft)),
  sealOpen: () => safe(() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)),
  success: () => safe(() => Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success)),
} as const;
