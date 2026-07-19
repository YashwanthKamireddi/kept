import React from "react";
import { Modal, Pressable, Share, StyleSheet, Text, View } from "react-native";
import { color, font, radius, shadow, space, type } from "../tokens";
import { Lamplight } from "../materials";
import { PressableScale } from "../motion";
import { haptic } from "../haptics";

/**
 * A keepsake: one sentence of their voice, composed like a card worth
 * keeping. v1 shares the words; the rendered-image export follows.
 */
export function KeepsakeCard({
  visible,
  quote,
  storytellerName,
  onClose,
}: {
  visible: boolean;
  quote: string;
  storytellerName: string;
  onClose: () => void;
}) {
  const share = async () => {
    haptic.success();
    await Share.share({
      message: `“${quote}”\n— ${storytellerName || "a storyteller"}, in their own voice.\n\nKept · every family has a storyteller`,
    });
  };

  return (
    <Modal visible={visible} animationType="fade" transparent onRequestClose={onClose}>
      <Pressable style={{ flex: 1 }} onPress={onClose} accessibilityRole="button">
        <Lamplight style={styles.stagePad}>
          <View style={styles.card}>
            <View style={styles.thread} />
            <Text style={styles.quote}>“{quote}”</Text>
            {storytellerName ? (
              <Text style={type.label}>{storytellerName}</Text>
            ) : null}
            <View style={styles.glyph} accessibilityElementsHidden>
              {[10, 22, 15, 28, 12, 20, 9].map((h, i) => (
                <View key={i} style={[styles.glyphBar, { height: h }]} />
              ))}
            </View>
            <Text style={styles.mark}>Kept</Text>
          </View>
          <PressableScale accessibilityRole="button" onPress={share} style={styles.shareButton}>
            <Text style={styles.shareText}>Share this moment</Text>
          </PressableScale>
        </Lamplight>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  stagePad: { alignItems: "center", justifyContent: "center", padding: space(7), gap: space(6) },
  card: {
    width: "100%",
    maxWidth: 420,
    backgroundColor: color.paper,
    borderRadius: radius.sheet,
    padding: space(7),
    alignItems: "center",
    gap: space(4),
    ...shadow.sheet,
  },
  thread: { width: 42, height: 2, backgroundColor: color.gold },
  quote: {
    fontFamily: font.displaySoft,
    fontSize: 20,
    lineHeight: 32,
    color: color.ink,
    textAlign: "center",
  },
  glyph: { flexDirection: "row", alignItems: "center", gap: 3 },
  glyphBar: { width: 3, borderRadius: 2, backgroundColor: color.gold, opacity: 0.7 },
  mark: { fontFamily: font.display, fontSize: 16, color: color.gold },
  shareButton: {
    backgroundColor: color.foil,
    paddingHorizontal: space(6),
    paddingVertical: space(3),
    borderRadius: 10,
  },
  shareText: { fontFamily: font.bodyBold, fontSize: 15, color: color.stage },
});
