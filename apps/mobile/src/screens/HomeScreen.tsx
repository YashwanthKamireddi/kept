import React, { useCallback, useLayoutEffect, useState } from "react";
import {
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { LinearGradient } from "expo-linear-gradient";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../navigation";
import { color, font, radius, shadow, space, type } from "../theme";
import { Entrance, DrawnRule, PressableScale } from "../components/motion";
import { useApp } from "../state";
import type { Chapter, Storyteller } from "../api/client";

type Props = NativeStackScreenProps<RootStackParamList, "Home">;

interface Shelf {
  storyteller: Storyteller;
  chapters: Chapter[];
}

/**
 * The page scene: albums resting on a paper table. Each storyteller is a
 * physical object — a dark cover with their name in gold foil, the pages
 * (chapters) peeking out beneath.
 */
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

  useFocusEffect(
    useCallback(() => {
      void load();
    }, [load]),
  );

  useLayoutEffect(() => {
    navigation.setOptions({
      headerRight: () => (
        <Pressable
          accessibilityRole="button"
          onPress={() => navigation.navigate("AddStoryteller")}
        >
          <Text style={styles.addButton}>Add</Text>
        </Pressable>
      ),
    });
  }, [navigation]);

  return (
    <FlatList
      style={styles.page}
      contentContainerStyle={styles.content}
      data={shelves}
      keyExtractor={(s) => s.storyteller.id}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
      ListEmptyComponent={
        !loading ? (
          <Entrance order={0} style={styles.empty}>
            <Text style={type.sectionTitle}>The album is waiting</Text>
            <DrawnRule color={color.gold} order={1} style={styles.emptyRule} />
            <Text style={[type.body, { color: color.inkSoft, textAlign: "center" }]}>
              Add your family's storyteller and we'll call to hear their first story.
            </Text>
          </Entrance>
        ) : null
      }
      renderItem={({ item, index }) => (
        <Entrance order={index}>
          <Album
            shelf={item}
            onOpenChapter={(chapterId) => navigation.navigate("Chapter", { chapterId })}
          />
        </Entrance>
      )}
    />
  );
}

function Album({
  shelf,
  onOpenChapter,
}: {
  shelf: Shelf;
  onOpenChapter: (chapterId: string) => void;
}) {
  const { storyteller, chapters } = shelf;
  const visible = chapters.filter((c) => c.status !== "draft");
  return (
    <View style={styles.album}>
      <LinearGradient colors={["#1E2530", color.stage]} style={styles.cover}>
        <View style={styles.spine} />
        <View style={{ flex: 1, gap: space(1) }}>
          <Text style={styles.coverLabel}>{consentLine(storyteller)}</Text>
          <Text style={type.coverName}>{storyteller.name}</Text>
        </View>
      </LinearGradient>

      <View style={styles.pages}>
        {visible.length === 0 ? (
          <Text style={[type.caption, { paddingVertical: space(2) }]}>
            Their first chapter will appear here after their first call.
          </Text>
        ) : (
          visible.map((chapter) => (
            <PressableScale
              key={chapter.id}
              accessibilityRole="button"
              onPress={() => onOpenChapter(chapter.id)}
              style={styles.chapterRow}
            >
              <Text style={styles.chapterOrdinal}>{chapter.ordinal}</Text>
              <Text style={[type.body, { flex: 1 }]} numberOfLines={1}>
                {chapter.title}
              </Text>
              <Text style={styles.chapterGo}>→</Text>
            </PressableScale>
          ))
        )}
      </View>
    </View>
  );
}

function consentLine(storyteller: Storyteller): string {
  switch (storyteller.consent) {
    case "granted":
      return "Recording with their blessing";
    case "pending":
      return "Awaiting their first call";
    case "declined":
    case "revoked":
      return "Paused at their request";
  }
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: color.paper },
  content: { padding: space(5), gap: space(6), paddingBottom: space(12) },
  empty: { alignItems: "center", gap: space(4), paddingTop: space(20) },
  emptyRule: { width: 56 },
  album: { borderRadius: radius.cover, ...shadow.cover },
  cover: {
    flexDirection: "row",
    gap: space(4),
    borderTopLeftRadius: radius.cover,
    borderTopRightRadius: radius.cover,
    padding: space(5),
    paddingVertical: space(6),
  },
  spine: { width: 3, borderRadius: 2, backgroundColor: color.foil, opacity: 0.9 },
  coverLabel: {
    fontFamily: font.bodyMedium,
    fontSize: 11,
    letterSpacing: 1.6,
    textTransform: "uppercase",
    color: color.stageText,
  },
  pages: {
    backgroundColor: color.paper,
    borderBottomLeftRadius: radius.cover,
    borderBottomRightRadius: radius.cover,
    borderWidth: 1,
    borderTopWidth: 0,
    borderColor: color.hairline,
    paddingHorizontal: space(5),
    paddingVertical: space(2),
  },
  chapterRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: space(3),
    paddingVertical: space(3),
  },
  chapterOrdinal: { fontFamily: font.displaySoft, fontSize: 16, color: color.gold },
  chapterGo: { fontFamily: font.body, fontSize: 16, color: color.hairline },
  addButton: { fontFamily: font.bodyBold, fontSize: 16, color: color.gold },
});
