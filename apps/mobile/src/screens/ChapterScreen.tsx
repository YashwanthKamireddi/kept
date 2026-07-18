import React, { useEffect, useMemo, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useAudioPlayer, useAudioPlayerStatus } from "expo-audio";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../navigation";
import { color, space, type } from "../theme";
import { useApp } from "../state";
import type { Anchor, ChapterDetail } from "../api/client";
import { ZariSentence } from "../components/ZariSentence";
import { TapeBar } from "../components/TapeBar";

type Props = NativeStackScreenProps<RootStackParamList, "Chapter">;

interface PlayingSpan {
  key: string; // `${paragraph}:${sentence}`
  anchor: Anchor;
}

export function ChapterScreen({ route }: Props) {
  const { client } = useApp();
  const [chapter, setChapter] = useState<ChapterDetail | null>(null);
  const [span, setSpan] = useState<PlayingSpan | null>(null);
  const [unavailable, setUnavailable] = useState(false);

  const sourceUrl = useMemo(
    () => (span && client ? client.audioUrl(span.anchor.audio_key) : null),
    [span, client],
  );
  const player = useAudioPlayer(sourceUrl ?? undefined);
  const status = useAudioPlayerStatus(player);

  useEffect(() => {
    if (!client) return;
    void client.getChapter(route.params.chapterId).then(setChapter);
  }, [client, route.params.chapterId]);

  // Seek to the sentence's span when a new anchor is chosen.
  useEffect(() => {
    if (!span || !sourceUrl) return;
    setUnavailable(false);
    player.seekTo(span.anchor.t_start_ms / 1000);
    player.play();
  }, [span, sourceUrl, player]);

  // Stop at the end of the span; surface honest failure for unsynced audio.
  useEffect(() => {
    if (!span) return;
    if (status.playbackState === "error") {
      setUnavailable(true);
      return;
    }
    if (status.playing && status.currentTime * 1000 >= span.anchor.t_end_ms) {
      player.pause();
      setSpan(null);
    }
  }, [status, span, player]);

  if (!chapter) {
    return (
      <View style={[styles.page, styles.center]}>
        <Text style={type.caption}>Opening the chapter…</Text>
      </View>
    );
  }

  return (
    <View style={styles.page}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={type.label}>Chapter {chapter.ordinal}</Text>
        <Text style={[type.chapterTitle, { marginTop: space(1) }]}>{chapter.title}</Text>
        <View style={styles.rule} />
        {chapter.paragraphs.map((paragraph, pi) => (
          <Text key={pi} style={styles.paragraph}>
            {paragraph.map((sentence, si) => {
              const key = `${pi}:${si}`;
              return (
                <ZariSentence
                  key={key}
                  sentence={sentence}
                  playing={span?.key === key && status.playing}
                  onPress={() =>
                    sentence.anchors.length > 0 &&
                    setSpan({ key, anchor: sentence.anchors[0] })
                  }
                />
              );
            })}
          </Text>
        ))}
        <Text style={styles.colophon}>
          Every underlined sentence is anchored to her recorded voice.
        </Text>
      </ScrollView>
      {span && (
        <TapeBar
          playing={status.playing}
          positionMs={status.currentTime * 1000}
          label={`Her voice — chapter ${chapter.ordinal}`}
          unavailable={unavailable}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: color.paper },
  center: { alignItems: "center", justifyContent: "center" },
  scroll: { paddingHorizontal: space(6), paddingTop: space(6), paddingBottom: space(12) },
  rule: {
    height: 1,
    backgroundColor: color.hairline,
    marginVertical: space(5),
  },
  paragraph: { marginBottom: space(5) },
  colophon: {
    ...type.caption,
    color: color.zari,
    marginTop: space(6),
  },
});
