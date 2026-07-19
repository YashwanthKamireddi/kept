import React, { useCallback, useState } from "react";
import { FlatList, RefreshControl, StyleSheet, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../navigation";
import { color, font, space, type } from "../design/tokens";
import { Entrance, PressableScale } from "../design/motion";
import { useApp } from "../state";
import { sessionStatusLine, sessionSubLine } from "../design/copy";
import { Page } from "../design/materials";
import type { Session } from "../api/client";

type Props = NativeStackScreenProps<RootStackParamList, "Sessions">;

export function SessionsScreen({ route, navigation }: Props) {
  const { client } = useApp();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!client) return;
    setLoading(true);
    try {
      setSessions(await client.listSessions(route.params.storytellerId));
    } finally {
      setLoading(false);
    }
  }, [client, route.params.storytellerId]);

  useFocusEffect(
    useCallback(() => {
      void load();
    }, [load]),
  );

  const readable = (s: Session) => ["completed", "dropped"].includes(s.status);

  return (
    <Page>
    <FlatList
      style={{ flex: 1 }}
      contentContainerStyle={styles.content}
      data={sessions}
      keyExtractor={(s) => s.id}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
      ListHeaderComponent={
        <Entrance order={0}>
          <Text style={type.label}>Conversations with {route.params.name}</Text>
        </Entrance>
      }
      ListEmptyComponent={
        !loading ? (
          <Entrance order={1}>
            <Text style={[type.body, { color: color.inkSoft, marginTop: space(4) }]}>
              No calls yet — the first one is on its way.
            </Text>
          </Entrance>
        ) : null
      }
      renderItem={({ item, index }) => (
        <Entrance order={Math.min(index + 1, 6)}>
          <PressableScale
            accessibilityRole={readable(item) ? "button" : undefined}
            disabled={!readable(item)}
            onPress={() => navigation.navigate("Transcript", { sessionId: item.id })}
            style={styles.row}
          >
            <View style={{ flex: 1, gap: 2 }}>
              <Text style={type.body}>{sessionStatusLine(item)}</Text>
              <Text style={type.caption}>{sessionSubLine(item)}</Text>
            </View>
            {readable(item) ? <Text style={styles.go}>→</Text> : null}
          </PressableScale>
        </Entrance>
      )}
    />
    </Page>
  );
}


const styles = StyleSheet.create({
  content: { padding: space(5), gap: space(2), paddingBottom: space(12) },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: space(3),
    paddingVertical: space(3),
    borderBottomWidth: 1,
    borderBottomColor: color.hairline,
  },
  go: { fontFamily: font.body, fontSize: 16, color: color.gold },
});
