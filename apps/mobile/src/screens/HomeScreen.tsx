import React, { useCallback, useLayoutEffect, useState } from "react";
import {
  Animated,
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
import { color, font, radius, shadow, space, type } from "../design/tokens";
import { Entrance, DrawnRule, PressableScale, useBreath } from "../design/motion";
import { useApp } from "../state";
import { consentLine, strings } from "../design/copy";
import { Page } from "../design/materials";
import type { Chapter, Storyteller } from "../api/client";

type Props = NativeStackScreenProps<RootStackParamList, "Home">;

interface Shelf {
  storyteller: Storyteller;
  chapters: Chapter[];
  live: boolean;
}

/**
 * The page scene: albums resting on a paper table. Each storyteller is a
 * physical object — a dark cover with their name in gold foil, the pages
 * (chapters) peeking out beneath.
 */
export function HomeScreen({ navigation }: Props) {
  const { client, signOut } = useApp();
  const [shelves, setShelves] = useState<Shelf[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!client) return;
    setLoading(true);
    try {
      const storytellers = await client.listStorytellers();
      const withChapters = await Promise.all(
        storytellers.map(async (storyteller) => {
          const [chapters, sessions] = await Promise.all([
            client.listChapters(storyteller.id),
            client.listSessions(storyteller.id),
          ]);
          return {
            storyteller,
            chapters,
            live: sessions.some((s) => s.status === "in_progress"),
          };
        }),
      );
      setShelves(withChapters);
    } finally {
      setLoading(false);
    }
  }, [client]);

  useFocusEffect(
    useCallback(() => {
      void load();
      // While focused, keep the living covers honest.
      const poll = setInterval(() => void load(), 30_000);
      return () => clearInterval(poll);
    }, [load]),
  );

  useLayoutEffect(() => {
    navigation.setOptions({
      headerRight: () => (
        <Pressable
          accessibilityRole="button"
          onPress={() => navigation.navigate("AddStoryteller")}
          style={styles.headerBtn}
        >
          <Text style={styles.addButton}>Add</Text>
        </Pressable>
      ),
      headerLeft: () => (
        <Pressable
          accessibilityRole="button"
          onPress={() => void signOut()}
          style={styles.headerBtn}
        >
          <Text style={styles.signOut}>Sign out</Text>
        </Pressable>
      ),
    });
  }, [navigation, signOut]);

  return (
    <Page>
    <FlatList
      style={{ flex: 1 }}
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
            onOpenChapter={(chapterId) =>
              navigation.navigate("Chapter", {
                chapterId,
                storytellerName: item.storyteller.name,
              })
            }
            onOpenSessions={() =>
              navigation.navigate("Sessions", {
                storytellerId: item.storyteller.id,
                name: item.storyteller.name,
              })
            }
            onOpenThreads={() =>
              navigation.navigate("FollowUps", {
                storytellerId: item.storyteller.id,
                name: item.storyteller.name,
              })
            }
            onOpenSettings={() =>
              navigation.navigate("StorytellerSettings", {
                storytellerId: item.storyteller.id,
              })
            }
          />
        </Entrance>
      )}
      ListFooterComponent={
        shelves.length > 0 ? (
          <Entrance order={shelves.length} style={styles.footerBlock}>
            <PressableScale
              accessibilityRole="button"
              onPress={() => navigation.navigate("AddStoryteller")}
              style={styles.addAnother}
            >
              <Text style={styles.addAnotherText}>＋  Add another storyteller</Text>
            </PressableScale>
            <Text style={styles.brandFoot}>Kept</Text>
          </Entrance>
        ) : null
      }
    />
    </Page>
  );
}

function Album({
  shelf,
  onOpenChapter,
  onOpenSessions,
  onOpenThreads,
  onOpenSettings,
}: {
  shelf: Shelf;
  onOpenChapter: (chapterId: string) => void;
  onOpenSessions: () => void;
  onOpenThreads: () => void;
  onOpenSettings: () => void;
}) {
  const { storyteller, chapters, live } = shelf;
  // Chapters arrive as every version; reason about the latest version per
  // ordinal so a superseded draft doesn't linger as "being checked".
  const latestByOrdinal = new Map<number, Chapter>();
  for (const c of chapters) {
    const seen = latestByOrdinal.get(c.ordinal);
    if (!seen || c.version > seen.version) latestByOrdinal.set(c.ordinal, c);
  }
  const latest = [...latestByOrdinal.values()].sort((a, b) => a.ordinal - b.ordinal);
  const visible = latest.filter((c) => c.status !== "draft");
  const checking = latest.some((c) => c.status === "draft");
  const breath = useBreath(live);
  const glow = breath.interpolate({ inputRange: [0.55, 1], outputRange: [0.1, 0] });
  return (
    <View style={styles.album}>
      <LinearGradient colors={["#1E2530", color.stage]} style={styles.cover}>
        <View style={styles.spine} />
        <View style={{ flex: 1, gap: space(1) }}>
          <Text style={styles.coverLabel}>
            {live ? strings.inConversation : consentLine(storyteller)}
          </Text>
          <Text style={type.coverName}>{storyteller.name}</Text>
        </View>
        {live && (
          <Animated.View
            pointerEvents="none"
            style={[StyleSheet.absoluteFill, { backgroundColor: color.foil, opacity: glow }]}
          />
        )}
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
        {checking && (
          <Text style={[type.caption, { color: color.gold, paddingVertical: space(1) }]}>
            A new chapter is being checked for faithfulness…
          </Text>
        )}
        <View style={styles.footer}>
          <PressableScale accessibilityRole="button" onPress={onOpenSessions}>
            <Text style={styles.footerLink}>Calls</Text>
          </PressableScale>
          <Text style={styles.footerDot}>·</Text>
          <PressableScale accessibilityRole="button" onPress={onOpenThreads}>
            <Text style={styles.footerLink}>Open threads</Text>
          </PressableScale>
          <Text style={styles.footerDot}>·</Text>
          <PressableScale accessibilityRole="button" onPress={onOpenSettings}>
            <Text style={styles.footerLink}>Manage</Text>
          </PressableScale>
        </View>
      </View>
    </View>
  );
}


const styles = StyleSheet.create({
  // flexGrow + centering: a lone album sits as a calm, centered composition
  // instead of pinned to the top over a big void; long lists still scroll.
  content: {
    padding: space(5),
    gap: space(6),
    paddingBottom: space(12),
    flexGrow: 1,
    justifyContent: "center",
  },
  empty: { alignItems: "center", gap: space(4) },
  emptyRule: { width: 56 },
  footerBlock: { alignItems: "center", gap: space(6), paddingTop: space(4) },
  addAnother: {
    borderWidth: 1,
    borderColor: color.hairline,
    borderStyle: "dashed",
    borderRadius: radius.cover,
    paddingVertical: space(4),
    paddingHorizontal: space(6),
    width: "100%",
    alignItems: "center",
  },
  addAnotherText: { fontFamily: font.bodyMedium, fontSize: 15, color: color.inkSoft },
  brandFoot: {
    fontFamily: font.display,
    fontSize: 20,
    color: color.hairline,
    letterSpacing: 1,
  },
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
  headerBtn: { paddingHorizontal: space(4), paddingVertical: space(2) },
  addButton: { fontFamily: font.bodyBold, fontSize: 16, color: color.gold },
  footer: {
    flexDirection: "row",
    alignItems: "center",
    gap: space(2),
    paddingVertical: space(3),
    borderTopWidth: 1,
    borderTopColor: color.hairline,
    marginTop: space(1),
  },
  footerLink: { fontFamily: font.bodyMedium, fontSize: 14, color: color.gold },
  footerDot: { color: color.hairline },
  signOut: { fontFamily: font.bodyMedium, fontSize: 14, color: color.inkSoft },
});
