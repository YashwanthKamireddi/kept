import React, { useEffect, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../navigation";
import { color, font, space, type } from "../design/tokens";
import { Entrance, PressableScale } from "../design/motion";
import { Page } from "../design/materials";
import { Field } from "../design/components/Field";
import { useApp } from "../state";
import type { SearchResults } from "../api/client";

type Props = NativeStackScreenProps<RootStackParamList, "Search">;

/**
 * Find a story or a moment. One field searches two places at once: the written
 * book (family-visible chapters) and the storyteller's own recorded words. A
 * book hit opens that chapter; a spoken moment opens the conversation it came
 * from. Debounced so it searches as you think, not as you type.
 */
export function SearchScreen({ route, navigation }: Props) {
  const { client } = useApp();
  const { storytellerId, name } = route.params;
  const [q, setQ] = useState("");
  const [results, setResults] = useState<SearchResults | null>(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    if (!client) return;
    const needle = q.trim();
    if (needle.length < 2) {
      setResults(null);
      setSearching(false);
      return;
    }
    setSearching(true);
    const t = setTimeout(() => {
      client
        .search(storytellerId, needle)
        .then(setResults)
        .catch(() => setResults({ query: needle, chapters: [], moments: [] }))
        .finally(() => setSearching(false));
    }, 250);
    return () => clearTimeout(t);
  }, [q, client, storytellerId]);

  const typed = q.trim().length >= 2;
  const empty = results !== null && results.chapters.length === 0 && results.moments.length === 0;

  return (
    <Page>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="always">
        <Entrance order={0} style={styles.head}>
          <Text style={[type.label, { color: color.gold }]}>Search</Text>
          <Text style={type.chapterTitle}>{name}'s stories</Text>
        </Entrance>
        <Field label="A word, a person, a place" value={q} onChange={setQ} />

        {!typed && (
          <Text style={[type.caption, styles.note]}>
            Searches the written book and {name}'s own recorded words.
          </Text>
        )}
        {typed && searching && !results && (
          <Text style={[type.caption, styles.note]}>Looking…</Text>
        )}
        {empty && !searching && (
          <Text style={[type.body, styles.note]}>
            Nothing in {name}'s stories mentions “{q.trim()}” yet.
          </Text>
        )}

        {results && results.chapters.length > 0 && (
          <View style={styles.section}>
            <Text style={type.label}>In the book</Text>
            {results.chapters.map((c) => (
              <PressableScale
                key={c.chapter_id}
                accessibilityRole="button"
                onPress={() =>
                  navigation.navigate("Chapter", {
                    chapterId: c.chapter_id,
                    storytellerName: name,
                  })
                }
                style={styles.hit}
              >
                <Text style={styles.hitTitle}>
                  Chapter {c.ordinal} — {c.title}
                </Text>
                <Text style={[type.body, { color: color.inkSoft }]}>{c.snippet}</Text>
              </PressableScale>
            ))}
          </View>
        )}

        {results && results.moments.length > 0 && (
          <View style={styles.section}>
            <Text style={type.label}>In their own words</Text>
            {results.moments.map((m, i) => (
              <PressableScale
                key={`${m.session_id}:${i}`}
                accessibilityRole="button"
                onPress={() => navigation.navigate("Transcript", { sessionId: m.session_id })}
                style={styles.hit}
              >
                <Text style={[type.prose, styles.quote]}>“{m.snippet}”</Text>
                <Text style={styles.hitMeta}>From a conversation →</Text>
              </PressableScale>
            ))}
          </View>
        )}
      </ScrollView>
    </Page>
  );
}

const styles = StyleSheet.create({
  scroll: { padding: space(6), paddingBottom: space(16), gap: space(5) },
  head: { gap: space(1) },
  note: { color: color.inkSoft },
  section: { gap: space(3) },
  hit: {
    gap: space(1),
    paddingVertical: space(3),
    paddingHorizontal: space(4),
    borderRadius: 12,
    borderWidth: 1,
    borderColor: color.hairline,
    backgroundColor: color.paper,
  },
  hitTitle: {
    fontFamily: font.bodyBold,
    fontSize: 14,
    letterSpacing: 0.3,
    color: color.gold,
  },
  quote: { color: color.ink },
  hitMeta: {
    fontFamily: font.bodyMedium,
    fontSize: 12,
    letterSpacing: 0.4,
    color: color.gold,
    marginTop: space(1),
  },
});
