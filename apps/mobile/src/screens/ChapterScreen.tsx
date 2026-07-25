import React, { useEffect, useRef, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useAudioPlayer, useAudioPlayerStatus } from "expo-audio";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../navigation";
import { color, font, space, type } from "../design/tokens";
import { Entrance, DrawnRule } from "../design/motion";
import { Page } from "../design/materials";
import { strings } from "../design/copy";
import { play } from "../design/sound";
import { haptic } from "../design/haptics";
import { useApp } from "../state";
import type { Anchor, ChapterDetail } from "../api/client";
import { VoiceSentence } from "../design/components/VoiceSentence";
import { TapeBar } from "../design/components/TapeBar";
import { Loading } from "../design/components/Loading";
import { ListeningRoom } from "../design/components/ListeningRoom";
import { KeepsakeCard } from "../design/components/KeepsakeCard";

type Props = NativeStackScreenProps<RootStackParamList, "Chapter">;

interface PlayingSpan {
  key: string; // `${paragraph}:${sentence}`
  anchor: Anchor;
  text: string;
}

export function ChapterScreen({ route }: Props) {
  const { client } = useApp();
  const [chapter, setChapter] = useState<ChapterDetail | null>(null);
  const [span, setSpan] = useState<PlayingSpan | null>(null);
  const [roomOpen, setRoomOpen] = useState(false);
  const [keepsakeOpen, setKeepsakeOpen] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const [sourceUrl, setSourceUrl] = useState<string | null>(null);
  const wasPlaying = useRef(false);

  // Ask the server for a short-lived playback URL when a sentence is chosen.
  useEffect(() => {
    if (!span || !client) {
      setSourceUrl(null);
      return;
    }
    setUnavailable(false);
    client
      .resolveAudioUrl(span.anchor.audio_key)
      .then(setSourceUrl)
      .catch(() => setUnavailable(true));
  }, [span, client]);

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

  // The moment her voice actually starts: tape click + one soft heartbeat.
  useEffect(() => {
    if (status.playing && !wasPlaying.current) {
      play("tape_start");
      haptic.voiceStart();
    }
    wasPlaying.current = status.playing;
  }, [status.playing]);

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
      setRoomOpen(false);
    }
  }, [status, span, player]);

  if (!chapter) return <Loading label="Opening the chapter…" />;

  return (
    <Page>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Entrance order={0}>
          <Text style={[type.label, { color: color.gold }]}>Chapter {chapter.ordinal}</Text>
          <Text style={[type.chapterTitle, { marginTop: space(1) }]}>{chapter.title}</Text>
        </Entrance>
        <DrawnRule color={color.hairline} order={1} style={styles.rule} />
        {chapter.paragraphs.map((paragraph, pi) => (
          <Entrance key={pi} order={Math.min(pi + 2, 5)}>
            <Text style={styles.paragraph}>
              {/* A raised initial opens the chapter, like a printed book. The
                  letter is lifted out of the first sentence and drawn large;
                  the sentence stays tappable and its full text is preserved
                  for playback and keepsakes. */}
              {pi === 0 && paragraph[0]?.text ? (
                <Text style={styles.dropCap}>{paragraph[0].text.charAt(0)}</Text>
              ) : null}
              {paragraph.map((sentence, si) => {
                const key = `${pi}:${si}`;
                const select = () =>
                  setSpan({ key, anchor: sentence.anchors[0], text: sentence.text });
                const display =
                  pi === 0 && si === 0
                    ? { ...sentence, text: sentence.text.slice(1) }
                    : sentence;
                return (
                  <VoiceSentence
                    key={key}
                    sentence={display}
                    playing={span?.key === key && status.playing}
                    onPress={() => sentence.anchors.length > 0 && select()}
                    onLongPress={() => {
                      if (sentence.anchors.length === 0) return;
                      select();
                      setRoomOpen(true);
                    }}
                  />
                );
              })}
            </Text>
          </Entrance>
        ))}
        <Entrance order={5}>
          <Text style={styles.colophon}>{strings.colophon}</Text>
        </Entrance>
      </ScrollView>
      {span && (
        <TapeBar
          playing={status.playing}
          positionMs={status.currentTime * 1000}
          label={`In their own voice — Chapter ${chapter.ordinal}`}
          unavailable={unavailable}
        />
      )}
      <ListeningRoom
        visible={roomOpen && span !== null && !unavailable}
        sentence={span?.text ?? ""}
        storytellerName={route.params.storytellerName ?? ""}
        playing={status.playing}
        onClose={() => setRoomOpen(false)}
        onKeepsake={() => {
          setRoomOpen(false);
          setKeepsakeOpen(true);
        }}
      />
      <KeepsakeCard
        visible={keepsakeOpen && span !== null}
        quote={span?.text ?? ""}
        storytellerName={route.params.storytellerName ?? ""}
        onClose={() => setKeepsakeOpen(false)}
      />
    </Page>
  );
}

const styles = StyleSheet.create({
  scroll: { paddingHorizontal: space(6), paddingTop: space(6), paddingBottom: space(12) },
  rule: { marginVertical: space(5) },
  paragraph: { marginBottom: space(5) },
  dropCap: {
    fontFamily: font.display,
    fontSize: 52,
    lineHeight: 44,
    color: color.gold,
  },
  colophon: {
    ...type.caption,
    color: color.gold,
    marginTop: space(6),
  },
});
