import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { getFocusedRouteNameFromRoute } from "@react-navigation/native";
import type { BottomTabBarProps } from "@react-navigation/bottom-tabs";
import { color, font, space } from "../tokens";
import { PressableScale } from "../motion";

const BAR_TOP = "#242D3A";
const BAR_BOTTOM = "#151A22";

/**
 * The one place you move through the app: a solid floating ink dock in three
 * even slots — Albums · Add · You. The active tab lights up with a soft foil
 * pill; the + sits centered as the primary action.
 */
export function BottomNav({ state, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();
  const active = state.routes[state.index]?.name;

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
        <View style={styles.slot}>
          <NavItem label="Albums" active={active === "Albums"} onPress={() => go("Albums")} glyph="album" />
        </View>
        <View style={styles.slot}>
          <PressableScale accessibilityRole="button" accessibilityLabel="Add a storyteller" onPress={addStoryteller}>
            <View style={styles.addCircle}>
              <Text style={styles.addPlus}>＋</Text>
            </View>
          </PressableScale>
        </View>
        <View style={styles.slot}>
          <NavItem label="You" active={active === "You"} onPress={() => go("You")} glyph="person" />
        </View>
      </LinearGradient>
    </View>
  );
}

function NavItem({
  label,
  active,
  onPress,
  glyph,
}: {
  label: string;
  active: boolean;
  onPress: () => void;
  glyph: "album" | "person";
}) {
  return (
    <PressableScale
      accessibilityRole="button"
      onPress={onPress}
      style={[styles.item, active && styles.itemActive]}
    >
      {glyph === "album" ? <AlbumGlyph active={active} /> : <PersonGlyph active={active} />}
      <Text style={[styles.label, { color: active ? color.foil : color.stageText }]}>{label}</Text>
    </PressableScale>
  );
}

function AlbumGlyph({ active }: { active: boolean }) {
  const c = active ? color.foil : color.stageText;
  return (
    <View style={{ width: 21, height: 17, borderWidth: 2, borderColor: c, borderRadius: 3 }}>
      <View style={{ position: "absolute", left: 4, top: 2, bottom: 2, width: 2, backgroundColor: c }} />
    </View>
  );
}

function PersonGlyph({ active }: { active: boolean }) {
  const c = active ? color.foil : color.stageText;
  return (
    <View style={{ width: 21, height: 17, alignItems: "center" }}>
      <View style={{ width: 7, height: 7, borderRadius: 4, borderWidth: 2, borderColor: c }} />
      <View
        style={{
          width: 16,
          height: 8,
          borderTopLeftRadius: 8,
          borderTopRightRadius: 8,
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
    width: "100%",
    height: 72,
    paddingHorizontal: space(3),
    borderRadius: 24,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.07)",
    shadowColor: "#0B0E13",
    shadowOpacity: 0.38,
    shadowRadius: 22,
    shadowOffset: { width: 0, height: 12 },
    elevation: 14,
  },
  slot: { flex: 1, alignItems: "center", justifyContent: "center" },
  item: {
    alignItems: "center",
    gap: 5,
    paddingVertical: space(2),
    paddingHorizontal: space(3),
    borderRadius: 14,
  },
  itemActive: { backgroundColor: "rgba(201,162,75,0.14)" }, // lit foil pill
  label: {
    fontFamily: font.bodyMedium,
    fontSize: 10,
    letterSpacing: 1.3,
    textTransform: "uppercase",
  },
  addCircle: {
    width: 50,
    height: 50,
    borderRadius: 999,
    backgroundColor: color.foil,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: color.foil,
    shadowOpacity: 0.32,
    shadowRadius: 9,
    shadowOffset: { width: 0, height: 3 },
    elevation: 8,
  },
  addPlus: { fontFamily: font.body, fontSize: 26, lineHeight: 30, color: BAR_BOTTOM },
});
