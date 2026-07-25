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

const readable = (s: Session) => ["completed", "dropped"].includes(s.status);

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

  // Real summary from the calls themselves — no invented numbers.
  const totalSeconds = sessions.reduce((sum, s) => sum + (s.duration_seconds || 0), 0);
  const minutes = totalSeconds > 0 ? Math.max(1, Math.round(totalSeconds / 60)) : 0;

  return (
    <Page>
      <FlatList
        style={{ flex: 1 }}
        contentContainerStyle={styles.content}
        data={sessions}
        keyExtractor={(s) => s.id}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
        ListHeaderComponent={
          <Entrance order={0} style={styles.header}>
            <Text style={type.sectionTitle}>Conversations</Text>
            <Text style={[type.caption, { color: color.inkSoft }]}>
              with {route.params.name}
            </Text>
            {sessions.length > 0 && (
              <View style={styles.stats}>
                <Stat value={String(sessions.length)} label={sessions.length === 1 ? "call" : "calls"} />
                {minutes > 0 && (
                  <>
                    <View style={styles.statDivider} />
                    <Stat value={String(minutes)} label={minutes === 1 ? "minute kept" : "minutes kept"} />
                  </>
                )}
              </View>
            )}
          </Entrance>
        }
        ListEmptyComponent={
          !loading ? (
            <Entrance order={1} style={styles.empty}>
              <Text style={[type.body, { color: color.inkSoft, textAlign: "center" }]}>
                No calls yet — the first one is on its way.
              </Text>
            </Entrance>
          ) : null
        }
        renderItem={({ item, index }) => (
          <Entrance order={Math.min(index + 1, 6)}>
            <TimelineRow
              session={item}
              isFirst={index === 0}
              isLast={index === sessions.length - 1}
              onPress={() =>
                readable(item) &&
                navigation.navigate("Transcript", { sessionId: item.id })
              }
            />
          </Entrance>
        )}
      />
    </Page>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

/** One call as a node on a vertical thread — the album's growing history. */
function TimelineRow({
  session,
  isFirst,
  isLast,
  onPress,
}: {
  session: Session;
  isFirst: boolean;
  isLast: boolean;
  onPress: () => void;
}) {
  const canRead = readable(session);
  return (
    <View style={styles.row}>
      <View style={styles.rail}>
        <View style={[styles.railSeg, isFirst && styles.railHidden]} />
        <View style={[styles.dot, canRead ? styles.dotFilled : styles.dotHollow]} />
        <View style={[styles.railSeg, styles.railGrow, isLast && styles.railHidden]} />
      </View>
      <PressableScale
        accessibilityRole={canRead ? "button" : undefined}
        disabled={!canRead}
        onPress={onPress}
        style={styles.rowContent}
      >
        <Text style={type.body}>{sessionStatusLine(session)}</Text>
        <Text style={type.caption}>{sessionSubLine(session)}</Text>
      </PressableScale>
      {canRead ? <Text style={styles.go}>→</Text> : null}
    </View>
  );
}

const DOT = 12;

const styles = StyleSheet.create({
  content: { padding: space(5), paddingBottom: space(12) },
  header: { gap: space(1), paddingBottom: space(3) },
  stats: { flexDirection: "row", alignItems: "center", gap: space(5), paddingTop: space(4) },
  stat: { gap: 2 },
  statValue: {
    fontFamily: font.display,
    fontSize: 30,
    lineHeight: 34,
    color: color.ink,
    fontVariant: ["tabular-nums"],
  },
  statLabel: {
    fontFamily: font.bodyMedium,
    fontSize: 11,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: color.inkSoft,
  },
  statDivider: { width: 1, height: 34, backgroundColor: color.hairline },
  empty: { paddingTop: space(10), alignItems: "center" },
  row: { flexDirection: "row", alignItems: "stretch", gap: space(3) },
  rail: { width: DOT, alignItems: "center" },
  railSeg: { width: 2, height: space(3), backgroundColor: color.hairline },
  railGrow: { flex: 1 },
  railHidden: { backgroundColor: "transparent" },
  dot: {
    width: DOT,
    height: DOT,
    borderRadius: 999,
    borderWidth: 2,
  },
  dotFilled: { backgroundColor: color.gold, borderColor: color.gold },
  dotHollow: { backgroundColor: color.paper, borderColor: color.hairline },
  rowContent: { flex: 1, gap: 2, paddingBottom: space(5) },
  go: { fontFamily: font.body, fontSize: 16, color: color.gold, paddingTop: space(3) },
});
