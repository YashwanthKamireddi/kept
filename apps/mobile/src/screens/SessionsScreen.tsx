import React, { useCallback, useState } from "react";
import { FlatList, RefreshControl, StyleSheet, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../navigation";
import { color, font, space, type } from "../design/tokens";
import { Entrance, PressableScale } from "../design/motion";
import { useApp } from "../state";
import { fmtDate, sessionStatusLine } from "../design/copy";
import { Page } from "../design/materials";
import type { Session } from "../api/client";

type Props = NativeStackScreenProps<RootStackParamList, "Sessions">;

// A call becomes a tape only if it actually produced a conversation.
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
            <Text style={[type.caption, { color: color.inkSoft }]}>with {route.params.name}</Text>
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
            {readable(item) ? (
              <CassetteCard
                session={item}
                onPress={() => navigation.navigate("Transcript", { sessionId: item.id })}
              />
            ) : (
              <QuietRow session={item} />
            )}
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

/** A recorded conversation as a cassette resting on the page — the date hand
 * labeled, its length on the counter. Tap it to read the transcript. */
function CassetteCard({ session, onPress }: { session: Session; onPress: () => void }) {
  const secs = session.duration_seconds || 0;
  const counter =
    secs > 0
      ? `${String(Math.floor(secs / 60)).padStart(2, "0")}:${String(secs % 60).padStart(2, "0")}`
      : "--:--";
  const date = fmtDate(session.started_at) || "A conversation";
  return (
    <PressableScale accessibilityRole="button" onPress={onPress} style={styles.cassette}>
      <View style={styles.labelStrip}>
        <Text style={styles.written} numberOfLines={1}>
          {date}
        </Text>
      </View>
      <View style={styles.window}>
        <Reel />
        <View style={styles.tape} />
        <Reel />
        <Text style={styles.counter}>{counter}</Text>
      </View>
    </PressableScale>
  );
}

/** A call that left no recording — no tape to show, just an honest line. */
function QuietRow({ session }: { session: Session }) {
  return (
    <View style={styles.quiet}>
      <View style={styles.quietDot} />
      <Text style={[type.caption, { flex: 1 }]}>{sessionStatusLine(session)}</Text>
    </View>
  );
}

const REEL = 30;

/** A spool at rest: foil ring, six teeth, a hub. */
function Reel() {
  return (
    <View style={styles.reel}>
      <View style={styles.spoke} />
      <View style={[styles.spoke, { transform: [{ rotate: "60deg" }] }]} />
      <View style={[styles.spoke, { transform: [{ rotate: "120deg" }] }]} />
      <View style={styles.hub} />
    </View>
  );
}

const styles = StyleSheet.create({
  content: { padding: space(5), gap: space(4), paddingBottom: space(12) },
  header: { gap: space(1), paddingBottom: space(2) },
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

  cassette: {
    backgroundColor: color.stageRaised,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.06)",
    paddingHorizontal: space(4),
    paddingVertical: space(3),
  },
  labelStrip: {
    backgroundColor: color.paper,
    borderRadius: 4,
    paddingHorizontal: space(3),
    paddingVertical: space(1),
    marginBottom: space(3),
    alignSelf: "flex-start",
    minWidth: 96,
  },
  written: { fontFamily: font.quote, fontSize: 14, color: color.ink },
  window: { flexDirection: "row", alignItems: "center", gap: space(3) },
  reel: {
    width: REEL,
    height: REEL,
    borderRadius: 999,
    borderWidth: 2,
    borderColor: color.foil,
    alignItems: "center",
    justifyContent: "center",
  },
  spoke: { position: "absolute", width: 2, height: REEL - 6, backgroundColor: "rgba(201,162,75,0.55)" },
  hub: { width: 8, height: 8, borderRadius: 999, backgroundColor: color.foil },
  tape: { flex: 1, height: 2, backgroundColor: color.gold },
  counter: {
    fontFamily: font.mono,
    fontSize: 13,
    color: color.foil,
    fontVariant: ["tabular-nums"],
  },

  quiet: {
    flexDirection: "row",
    alignItems: "center",
    gap: space(3),
    paddingVertical: space(2),
    paddingHorizontal: space(1),
  },
  quietDot: {
    width: 8,
    height: 8,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: color.hairline,
    backgroundColor: color.paper,
  },
});
