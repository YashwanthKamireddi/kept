import React, { useCallback, useState } from "react";
import { FlatList, RefreshControl, StyleSheet, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../navigation";
import { color, font, space, type } from "../design/tokens";
import { Entrance, PressableScale } from "../design/motion";
import { Field } from "../design/components/Field";
import { Page } from "../design/materials";
import { haptic } from "../design/haptics";
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
  const [question, setQuestion] = useState("");
  const [sending, setSending] = useState(false);

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

  const ask = async () => {
    if (!client || question.trim().length < 5) return;
    setSending(true);
    try {
      await client.createFollowUp(route.params.storytellerId, question.trim());
      haptic.success();
      setQuestion("");
      await load();
    } finally {
      setSending(false);
    }
  };

  return (
    <Page>
    <FlatList
      style={{ flex: 1 }}
      contentContainerStyle={styles.content}
      data={threads}
      keyExtractor={(f) => f.id}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
      ListHeaderComponent={
        <Entrance order={0} style={{ gap: space(4), marginBottom: space(4) }}>
          <Text style={type.label}>
            What we hope to ask {route.params.name} next
          </Text>
          <Field
            label="Ask them something"
            value={question}
            onChange={setQuestion}
            placeholder="What songs did your mother sing?"
          />
          <PressableScale
            accessibilityRole="button"
            onPress={ask}
            disabled={sending || question.trim().length < 5}
            style={[styles.askButton, (sending || question.trim().length < 5) && { opacity: 0.4 }]}
          >
            <Text style={styles.askText}>
              {sending ? "Adding to the threads…" : "Add to the next calls"}
            </Text>
          </PressableScale>
          <Text style={type.caption}>
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
              {item.asked_by_name ? (
                <Text style={[type.caption, { color: color.gold }]}>
                  Asked by {item.asked_by_name}
                </Text>
              ) : null}
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
    </Page>
  );
}

const styles = StyleSheet.create({
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
  askButton: {
    backgroundColor: color.ink,
    paddingVertical: space(3),
    alignItems: "center",
    borderRadius: 10,
  },
  askText: { fontFamily: font.bodyBold, fontSize: 15, color: color.paper },
});
