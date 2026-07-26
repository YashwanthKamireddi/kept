import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { getFocusedRouteNameFromRoute } from "@react-navigation/native";
import type { BottomTabBarProps } from "@react-navigation/bottom-tabs";
import { color, font, space } from "../tokens";
import { PressableScale } from "../motion";

// The deep ink the dock is cut from (ties into the dark cover scenes).
const BAR_TOP = "#242D3A";
const BAR_BOTTOM = "#151A22";

/**
 * The one place you move through the app: a solid, floating ink dock —
 * Albums · Add · You. (A translucent "glass" bar turned muddy over the flat
 * paper; a crisp dark dock reads premium and high-contrast instead.)
 */
export function BottomNav({ state, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();
  const active = state.routes[state.index]?.name;

  // Top-level nav only: show on the Albums root (Home) and the You tab; hide
  // on every pushed detail screen, which carries its own back button.
  const focusedInner = getFocusedRouteNameFromRoute(state.routes[state.index]) ?? "Home";
  if (active === "Albums" && focusedInner !== "Home") return null;

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
      <LinearGradient colors={[BAR_TOP, BAR_BOTTOM]} start={{ x: 0, y: 0 }} end={{ x: 0, y: 1 }} style={styles.bar}>
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
      </LinearGradient>
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
    <PressableScale accessibilityRole="button" onPress={onPress} style={styles.item}>
      {children}
      <Text style={[styles.label, { color: active ? color.foil : color.stageText }]}>{label}</Text>
      <View style={[styles.dot, active && styles.dotOn]} />
    </PressableScale>
  );
}

function AlbumGlyph({ active }: { active: boolean }) {
  const c = active ? color.foil : color.stageText;
  return (
    <View style={{ width: 22, height: 18, borderWidth: 2, borderColor: c, borderRadius: 3 }}>
      <View
        style={{ position: "absolute", left: 4, top: 2, bottom: 2, width: 2, backgroundColor: c }}
      />
    </View>
  );
}

function PersonGlyph({ active }: { active: boolean }) {
  const c = active ? color.foil : color.stageText;
  return (
    <View style={{ width: 22, height: 19, alignItems: "center" }}>
      <View style={{ width: 8, height: 8, borderRadius: 4, borderWidth: 2, borderColor: c }} />
      <View
        style={{
          width: 18,
          height: 9,
          borderTopLeftRadius: 9,
          borderTopRightRadius: 9,
          borderWidth: 2,
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
    height: 68,
    paddingHorizontal: space(8),
    borderRadius: 26,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.08)", // a lit top edge
    // deep float above the paper
    shadowColor: "#0B0E13",
    shadowOpacity: 0.4,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 14 },
    elevation: 14,
  },
  item: { alignItems: "center", gap: 5, minWidth: 60, paddingVertical: space(2) },
  label: {
    fontFamily: font.bodyMedium,
    fontSize: 11,
    letterSpacing: 1.4,
    textTransform: "uppercase",
  },
  dot: { width: 4, height: 4, borderRadius: 2, backgroundColor: "transparent" },
  dotOn: { backgroundColor: color.foil },
  addWrap: { marginTop: -10 }, // raised, like a proper dock action
  addCircle: {
    width: 54,
    height: 54,
    borderRadius: 999,
    backgroundColor: color.foil,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 3,
    borderColor: BAR_BOTTOM, // ring separates it from the bar for a raised read
    shadowColor: color.foil,
    shadowOpacity: 0.5,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 4 },
    elevation: 10,
  },
  addPlus: { fontFamily: font.body, fontSize: 28, lineHeight: 32, color: BAR_BOTTOM },
});
