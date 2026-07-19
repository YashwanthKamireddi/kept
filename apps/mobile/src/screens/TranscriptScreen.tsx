import React, { useEffect, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../navigation";
import { color, font, space, type } from "../design/tokens";
import { Entrance, DrawnRule } from "../design/motion";
import { useApp } from "../state";
import type { SessionDetail } from "../api/client";

type Props = NativeStackScreenProps<RootStackParamList, "Transcript">;

/**
 * The raw conversation, presented like correspondence: the storyteller's
 * words in full ink with a gold thread in the margin (it is their voice);
 * the biographer's questions quieter, set back.
 */
export function TranscriptScreen({ route }: Props) {
  const { client } = useApp();
  const [session, setSession] = useState<SessionDetail | null>(null);

  useEffect(() => {
    if (!client) return;
    void client.getSession(route.params.sessionId).then(setSession);
  }, [client, route.params.sessionId]);

  if (!session) {
    return (
      <View style={[styles.page, styles.center]}>
        <Text style={type.caption}>Opening the conversation…</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.page} contentContainerStyle={styles.content}>
      <Entrance order={0}>
        <Text style={[type.label, { color: color.gold }]}>The conversation</Text>
      </Entrance>
      <DrawnRule color={color.hairline} order={1} style={{ marginVertical: space(4) }} />
      {session.segments.map((seg, i) => (
        <Entrance key={seg.id} order={Math.min(i + 2, 6)}>
          {seg.speaker === "storyteller" ? (
            <View style={styles.storyteller}>
              <Text style={type.prose}>{seg.text}</Text>
            </View>
          ) : (
            <Text style={styles.biographer}>{seg.text}</Text>
          )}
        </Entrance>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: color.paper },
  center: { alignItems: "center", justifyContent: "center" },
  content: { padding: space(6), paddingBottom: space(12), gap: space(4) },
  storyteller: {
    borderLeftWidth: 2,
    borderLeftColor: color.gold,
    paddingLeft: space(4),
  },
  biographer: {
    fontFamily: font.body,
    fontSize: 15,
    lineHeight: 24,
    color: color.inkSoft,
    paddingLeft: space(10),
  },
});
