import React, { useCallback, useState } from "react";
import { FlatList, RefreshControl, StyleSheet, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../navigation";
import { color, font, space, type } from "../design/tokens";
import { Entrance, PressableScale } from "../design/motion";
import { useApp } from "../state";
import type { FollowUp } from "../api/client";

type Props = NativeStackScreenProps<RootStackParamList, "FollowUps">;

/**
 * Open threads: what the biographer is hoping to ask next. The keeper can
 * remove a thread so it is never raised — the family knows what's tender.
 */
export function FollowUpsScreen({ route }: Props) {
  const { client } = useApp();
  const [threads, setThreads] = useState<FollowUp[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!client) return;
    setLoading(true);
    try {
      const all = await client.listFollowUps(route.params.storytellerId);
      setThreads(all.filter((f) => f.status === "pending"));
    } finally {
      setLoading(false);
    }
  }, [client, route.params.storytellerId]);

  useFocusEffect(
    useCallback(() => {
      void load();
    }, [load]),
  );

  const remove = async (id: string) => {
    if (!client) return;
    await client.retireFollowUp(id);
    await load();
  };

  return (
    <FlatList
      style={styles.page}
      contentContainerStyle={styles.content}
      data={threads}
      keyExtractor={(f) => f.id}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
      ListHeaderComponent={
        <Entrance order={0}>
          <Text style={type.label}>
            What we hope to ask {route.params.name} next
          </Text>
          <Text style={[type.caption, { marginTop: space(2) }]}>
            Remove anything the family would rather leave untouched — it will
            never be raised on a call.
          </Text>
        </Entrance>
      }
      ListEmptyComponent={
        !loading ? (
          <Entrance order={1}>
            <Text style={[type.body, { color: color.inkSoft, marginTop: space(4) }]}>
              No open threads right now. New ones appear after each call.
            </Text>
          </Entrance>
        ) : null
      }
      renderItem={({ item, index }) => (
        <Entrance order={Math.min(index + 1, 6)}>
          <View style={styles.thread}>
            <View style={{ flex: 1, gap: space(1) }}>
              <Text style={type.body}>{item.question}</Text>
              {item.rationale ? <Text style={type.caption}>{item.rationale}</Text> : null}
            </View>
            <PressableScale
              accessibilityRole="button"
              accessibilityHint="This question will never be asked"
              onPress={() => remove(item.id)}
            >
              <Text style={styles.remove}>Remove</Text>
            </PressableScale>
          </View>
        </Entrance>
      )}
    />
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: color.paper },
  content: { padding: space(5), gap: space(3), paddingBottom: space(12) },
  thread: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: space(4),
    paddingVertical: space(3),
    borderBottomWidth: 1,
    borderBottomColor: color.hairline,
  },
  remove: { fontFamily: font.bodyMedium, fontSize: 14, color: color.ember },
});
