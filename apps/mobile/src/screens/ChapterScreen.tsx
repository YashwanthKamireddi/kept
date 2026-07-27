import React, { useEffect, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../navigation";
import { color, font, space, type } from "../design/tokens";
import { Entrance, DrawnRule } from "../design/motion";
import { Page } from "../design/materials";
import { strings } from "../design/copy";
import { useApp } from "../state";
import type { ChapterDetail } from "../api/client";
import { VoiceSentence } from "../design/components/VoiceSentence";
import { TapeBar } from "../design/components/TapeBar";
import { Loading } from "../design/components/Loading";
import { ListeningRoom } from "../design/components/ListeningRoom";
import { KeepsakeCard } from "../design/components/KeepsakeCard";
import { useSpanPlayer } from "../design/useSpanPlayer";

type Props = NativeStackScreenProps<RootStackParamList, "Chapter">;

export function ChapterScreen({ route }: Props) {
  const { client } = useApp();
  const [chapter, setChapter] = useState<ChapterDetail | null>(null);
  const [roomOpen, setRoomOpen] = useState(false);
  const [keepsakeOpen, setKeepsakeOpen] = useState(false);
  const { span, select, playing, positionMs, unavailable } = useSpanPlayer(() =>
    setRoomOpen(false),
  );

  useEffect(() => {
    if (!client) return;
    void client.getChapter(route.params.chapterId).then(setChapter);
  }, [client, route.params.chapterId]);

  if (!chapter) return <Loading label="Opening the chapter…" />;

  const renderSentences = (
    paragraph: typeof chapter.paragraphs[number],
    pi: number,
    dropFirst: boolean,
  ) =>
    paragraph.map((sentence, si) => {
      const key = `${pi}:${si}`;
      const choose = () => select({ key, anchor: sentence.anchors[0], text: sentence.text });
      // The first letter of the opening paragraph is lifted into the drop cap;
      // the sentence keeps its full text for playback and keepsakes.
      const display =
        dropFirst && si === 0 ? { ...sentence, text: sentence.text.slice(1) } : sentence;
      return (
        <VoiceSentence
          key={key}
          sentence={display}
          playing={span?.key === key && playing}
          onPress={() => sentence.anchors.length > 0 && choose()}
          onLongPress={() => {
            if (sentence.anchors.length === 0) return;
            choose();
            setRoomOpen(true);
          }}
        />
      );
    });

  return (
    <Page>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Entrance order={0}>
          <Text style={[type.label, { color: color.gold }]}>Chapter {chapter.ordinal}</Text>
          <Text style={[type.chapterTitle, { marginTop: space(1) }]}>{chapter.title}</Text>
        </Entrance>
        <DrawnRule color={color.hairline} order={1} style={styles.rule} />
        {chapter.paragraphs.map((paragraph, pi) =>
          pi === 0 && paragraph[0]?.text ? (
            // Opening paragraph: a drop cap in the margin, top-aligned with the
            // first line (RN can't float text, so the initial hangs beside the
            // column rather than sitting above it).
            <Entrance key={pi} order={Math.min(pi + 2, 5)}>
              <View style={styles.firstPara}>
                <Text style={styles.dropCap}>{paragraph[0].text.charAt(0)}</Text>
                <Text style={[styles.paragraph, styles.firstParaText]}>
                  {renderSentences(paragraph, pi, true)}
                </Text>
              </View>
            </Entrance>
          ) : (
            <Entrance key={pi} order={Math.min(pi + 2, 5)}>
              <Text style={styles.paragraph}>{renderSentences(paragraph, pi, false)}</Text>
            </Entrance>
          ),
        )}
        <Entrance order={5} style={styles.closing}>
          <View style={styles.ornament}>
            <View style={styles.ornLine} />
            <View style={styles.ornDiamond} />
            <View style={styles.ornLine} />
          </View>
          <Text style={styles.colophon}>{strings.colophon}</Text>
        </Entrance>
      </ScrollView>
      {span && (
        <TapeBar
          playing={playing}
          positionMs={positionMs}
          label={`In their own voice — Chapter ${chapter.ordinal}`}
          unavailable={unavailable}
        />
      )}
      <ListeningRoom
        visible={roomOpen && span !== null && !unavailable}
        sentence={span?.text ?? ""}
        storytellerName={route.params.storytellerName ?? ""}
        playing={playing}
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
  firstPara: { flexDirection: "row", alignItems: "flex-start", marginBottom: space(5) },
  firstParaText: { flex: 1, marginBottom: 0 },
  dropCap: {
    fontFamily: font.display,
    fontSize: 60,
    lineHeight: 52,
    color: color.gold,
    marginRight: space(2),
    marginTop: -2,
  },
  closing: { alignItems: "center", gap: space(5), marginTop: space(8) },
  ornament: { flexDirection: "row", alignItems: "center", gap: space(3) },
  ornLine: { width: 36, height: 1, backgroundColor: color.hairline },
  ornDiamond: {
    width: 6,
    height: 6,
    backgroundColor: color.gold,
    transform: [{ rotate: "45deg" }],
  },
  colophon: {
    ...type.caption,
    color: color.gold,
    textAlign: "center",
    maxWidth: 300,
  },
});
