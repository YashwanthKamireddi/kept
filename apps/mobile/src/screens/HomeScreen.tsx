import React, { useCallback, useEffect, useState } from "react";
import {
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../navigation";
import { color, font, space, type } from "../theme";
import { useApp } from "../state";
import type { Chapter, Storyteller } from "../api/client";

type Props = NativeStackScreenProps<RootStackParamList, "Home">;

interface Shelf {
  storyteller: Storyteller;
  chapters: Chapter[];
}

export function HomeScreen({ navigation }: Props) {
  const { client } = useApp();
  const [shelves, setShelves] = useState<Shelf[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!client) return;
    setLoading(true);
    try {
      const storytellers = await client.listStorytellers();
      const withChapters = await Promise.all(
        storytellers.map(async (storyteller) => ({
          storyteller,
          chapters: await client.listChapters(storyteller.id),
        })),
      );
      setShelves(withChapters);
    } finally {
      setLoading(false);
    }
  }, [client]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <FlatList
      style={styles.page}
      contentContainerStyle={{ padding: space(5), gap: space(5) }}
      data={shelves}
      keyExtractor={(s) => s.storyteller.id}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
      ListEmptyComponent={
        <View style={styles.empty}>
          <Text style={type.sectionTitle}>The album is waiting</Text>
          <Text style={[type.body, { color: color.inkSoft, textAlign: "center" }]}>
            Add a storyteller from the web console to schedule her first call.
          </Text>
        </View>
      }
      renderItem={({ item }) => (
        <AlbumCard
          shelf={item}
          onOpenChapter={(chapterId) =>
            navigation.navigate("Chapter", { chapterId })
          }
        />
      )}
    />
  );
}

function AlbumCard({
  shelf,
  onOpenChapter,
}: {
  shelf: Shelf;
  onOpenChapter: (chapterId: string) => void;
}) {
  const { storyteller, chapters } = shelf;
  const visible = chapters.filter((c) => c.status !== "draft");
  return (
    <View style={styles.card}>
      <View style={styles.spine} />
      <View style={{ flex: 1, padding: space(4), gap: space(2) }}>
        <Text style={type.label}>{consentLine(storyteller)}</Text>
        <Text style={styles.albumName}>{storyteller.name}</Text>
        {visible.length === 0 ? (
          <Text style={type.caption}>
            Her first chapter will appear here after her first call.
          </Text>
        ) : (
          visible.map((chapter) => (
            <Pressable
              key={chapter.id}
              accessibilityRole="button"
              onPress={() => onOpenChapter(chapter.id)}
              style={({ pressed }) => [styles.chapterRow, pressed && { opacity: 0.7 }]}
            >
              <Text style={styles.chapterOrdinal}>{chapter.ordinal}</Text>
              <Text style={[type.body, { flex: 1 }]} numberOfLines={1}>
                {chapter.title}
              </Text>
            </Pressable>
          ))
        )}
      </View>
    </View>
  );
}

function consentLine(storyteller: Storyteller): string {
  switch (storyteller.consent) {
    case "granted":
      return "Recording with her blessing";
    case "pending":
      return "Awaiting her first call";
    case "declined":
    case "revoked":
      return "Paused at her request";
  }
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: color.paper },
  empty: { alignItems: "center", gap: space(2), paddingTop: space(20) },
  card: {
    flexDirection: "row",
    backgroundColor: color.inland,
    borderRadius: 6,
    overflow: "hidden",
  },
  spine: { width: 6, backgroundColor: color.zari },
  albumName: { fontFamily: font.display, fontSize: 26, color: color.ink },
  chapterRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: space(3),
    paddingVertical: space(2),
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: color.hairline,
  },
  chapterOrdinal: { fontFamily: font.displaySoft, fontSize: 16, color: color.zari },
});
