import React from "react";
import { Platform, Pressable, StyleSheet, Text, View } from "react-native";
import { BlurView } from "expo-blur";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { getFocusedRouteNameFromRoute } from "@react-navigation/native";
import type { BottomTabBarProps } from "@react-navigation/bottom-tabs";
import { color, font, space } from "../tokens";
import { PressableScale } from "../motion";

// Immersive/modal inner screens where the floating bar would intrude.
const HIDE_ON = ["Chapter", "Transcript", "AddStoryteller"];

/**
 * The one place you move through the app: a floating glass bar over the paper.
 * Albums (your shelf) · Add (a new storyteller) · You (the keeper). Replaces
 * the scattered header buttons — one nav, said once.
 */
export function BottomNav({ state, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();
  const active = state.routes[state.index]?.name;

  // Hide the bar on immersive reads / the add modal.
  const focusedInner = getFocusedRouteNameFromRoute(state.routes[state.index]) ?? "Home";
  if (active === "Albums" && HIDE_ON.includes(focusedInner)) return null;

  const nav = navigation as unknown as {
    emit: typeof navigation.emit;
    navigate: (name: string, params?: object) => void;
  };

  const go = (name: string) => {
    const route = state.routes.find((r) => r.name === name);
    if (!route) return;
    const event = navigation.emit({ type: "tabPress", target: route.key, canPreventDefault: true });
    if (active !== name && !event.defaultPrevented) nav.navigate(name);
  };

  const addStoryteller = () => nav.navigate("Albums", { screen: "AddStoryteller" });

  return (
    <View style={[styles.wrap, { bottom: insets.bottom + space(3) }]} pointerEvents="box-none">
      <BlurView intensity={Platform.OS === "web" ? 24 : 40} tint="dark" style={styles.bar}>
        <NavItem label="Albums" active={active === "Albums"} onPress={() => go("Albums")}>
          <AlbumGlyph active={active === "Albums"} />
        </NavItem>

        <PressableScale accessibilityRole="button" onPress={addStoryteller} style={styles.addWrap}>
          <View style={styles.addCircle}>
            <Text style={styles.addPlus}>＋</Text>
          </View>
        </PressableScale>

        <NavItem label="You" active={active === "You"} onPress={() => go("You")}>
          <PersonGlyph active={active === "You"} />
        </NavItem>
      </BlurView>
    </View>
  );
}

function NavItem({
  label,
  active,
  onPress,
  children,
}: {
  label: string;
  active: boolean;
  onPress: () => void;
  children: React.ReactNode;
}) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={styles.item}>
      {children}
      <Text style={[styles.label, { color: active ? color.foil : color.stageText }]}>{label}</Text>
    </Pressable>
  );
}

function AlbumGlyph({ active }: { active: boolean }) {
  const c = active ? color.foil : color.stageText;
  return (
    <View style={{ width: 22, height: 18, borderWidth: 1.6, borderColor: c, borderRadius: 3 }}>
      <View
        style={{ position: "absolute", left: 4, top: 2, bottom: 2, width: 1.6, backgroundColor: c }}
      />
    </View>
  );
}

function PersonGlyph({ active }: { active: boolean }) {
  const c = active ? color.foil : color.stageText;
  return (
    <View style={{ width: 22, height: 19, alignItems: "center" }}>
      <View style={{ width: 8, height: 8, borderRadius: 4, borderWidth: 1.6, borderColor: c }} />
      <View
        style={{
          width: 18,
          height: 9,
          borderTopLeftRadius: 9,
          borderTopRightRadius: 9,
          borderWidth: 1.6,
          borderBottomWidth: 0,
          borderColor: c,
          marginTop: 2,
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { position: "absolute", left: space(5), right: space(5), alignItems: "center" },
  bar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    width: "100%",
    height: 66,
    paddingHorizontal: space(7),
    borderRadius: 30,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "rgba(201,162,75,0.22)", // faint foil hairline
    backgroundColor: "rgba(20,24,31,0.62)", // ink glass tint under the blur
    // floats above the paper
    shadowColor: "#000",
    shadowOpacity: 0.28,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 10 },
  },
  item: { alignItems: "center", gap: 4, minWidth: 56, paddingVertical: space(1) },
  label: {
    fontFamily: font.bodyMedium,
    fontSize: 10,
    letterSpacing: 1.2,
    textTransform: "uppercase",
  },
  addWrap: { alignItems: "center", justifyContent: "center" },
  addCircle: {
    width: 48,
    height: 48,
    borderRadius: 999,
    backgroundColor: color.foil,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: color.foil,
    shadowOpacity: 0.4,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
  },
  addPlus: { fontFamily: font.body, fontSize: 26, lineHeight: 30, color: color.stage },
});
