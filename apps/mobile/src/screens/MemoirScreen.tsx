import React, { useEffect, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../navigation";
import { color, font, space, type } from "../design/tokens";
import { Entrance, DrawnRule } from "../design/motion";
import { Page } from "../design/materials";
import { strings } from "../design/copy";
import { useApp } from "../state";
import type { Memoir, Sentence } from "../api/client";
import { VoiceSentence } from "../design/components/VoiceSentence";
import { TapeBar } from "../design/components/TapeBar";
import { Loading } from "../design/components/Loading";
import { ListeningRoom } from "../design/components/ListeningRoom";
import { KeepsakeCard } from "../design/components/KeepsakeCard";
import { useSpanPlayer } from "../design/useSpanPlayer";

type Props = NativeStackScreenProps<RootStackParamList, "Memoir">;

/**
 * The book, read as a book — every verified chapter, in order, on one
 * continuous page. Each chapter opens with a drop cap; every underlined
 * sentence still plays in the storyteller's own recorded voice. This is the
 * keepsake the whole product exists to produce.
 */
export function MemoirScreen({ route }: Props) {
  const { client } = useApp();
  const [memoir, setMemoir] = useState<Memoir | null>(null);
  const [roomOpen, setRoomOpen] = useState(false);
  const [keepsakeOpen, setKeepsakeOpen] = useState(false);
  const { span, select, playing, positionMs, unavailable } = useSpanPlayer(() =>
    setRoomOpen(false),
  );

  useEffect(() => {
    if (!client) return;
    void client.getMemoir(route.params.storytellerId).then(setMemoir);
  }, [client, route.params.storytellerId]);

  if (!memoir) return <Loading label="Gathering the book…" />;

  const empty = memoir.chapters.length === 0;
  // Which chapter is speaking, for the tape label (spans key as `${ordinal}:…`).
  const playingOrdinal = span ? span.key.split(":")[0] : null;

  const renderSentences = (ordinal: number, paragraph: Sentence[], pi: number, dropFirst: boolean) =>
    paragraph.map((sentence, si) => {
      const key = `${ordinal}:${pi}:${si}`;
      const choose = () => select({ key, anchor: sentence.anchors[0], text: sentence.text });
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
        <Entrance order={0} style={styles.titlePage}>
          <Text style={[type.label, { color: color.gold }]}>The memoir of</Text>
          <Text style={[type.chapterTitle, styles.titleName]}>{memoir.name}</Text>
          <DrawnRule color={color.hairline} order={1} style={styles.titleRule} />
          {!empty && (
            <Text style={[type.caption, { color: color.inkSoft }]}>
              {memoir.chapters.length} chapter{memoir.chapters.length === 1 ? "" : "s"}, in their
              own words
            </Text>
          )}
        </Entrance>

        {empty ? (
          <Entrance order={2} style={styles.emptyBlock}>
            <Text style={[type.body, { color: color.inkSoft, textAlign: "center" }]}>
              The book begins after their first call.
            </Text>
          </Entrance>
        ) : (
          memoir.chapters.map((ch, ci) => (
            <View key={ch.ordinal} style={styles.chapter}>
              <Entrance order={Math.min(ci + 2, 6)} style={styles.chapterHead}>
                <Text style={[type.label, { color: color.gold }]}>Chapter {ch.ordinal}</Text>
                <Text style={[type.chapterTitle, { marginTop: space(1) }]}>{ch.title}</Text>
              </Entrance>
              {ch.paragraphs.map((paragraph, pi) =>
                pi === 0 && paragraph[0]?.text ? (
                  <View key={pi} style={styles.firstPara}>
                    <Text style={styles.dropCap}>{paragraph[0].text.charAt(0)}</Text>
                    <Text style={[styles.paragraph, styles.firstParaText]}>
                      {renderSentences(ch.ordinal, paragraph, pi, true)}
                    </Text>
                  </View>
                ) : (
                  <Text key={pi} style={styles.paragraph}>
                    {renderSentences(ch.ordinal, paragraph, pi, false)}
                  </Text>
                ),
              )}
            </View>
          ))
        )}

        {!empty && (
          <Entrance order={6} style={styles.closing}>
            <View style={styles.ornament}>
              <View style={styles.ornLine} />
              <View style={styles.ornDiamond} />
              <View style={styles.ornLine} />
            </View>
            <Text style={styles.colophon}>{strings.colophon}</Text>
          </Entrance>
        )}
      </ScrollView>
      {span && (
        <TapeBar
          playing={playing}
          positionMs={positionMs}
          label={`In their own voice — Chapter ${playingOrdinal}`}
          unavailable={unavailable}
        />
      )}
      <ListeningRoom
        visible={roomOpen && span !== null && !unavailable}
        sentence={span?.text ?? ""}
        storytellerName={route.params.name ?? memoir.name}
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
        storytellerName={route.params.name ?? memoir.name}
        onClose={() => setKeepsakeOpen(false)}
      />
    </Page>
  );
}

const styles = StyleSheet.create({
  scroll: { paddingHorizontal: space(6), paddingTop: space(6), paddingBottom: space(16) },
  titlePage: { alignItems: "center", gap: space(2), paddingVertical: space(8) },
  titleName: { textAlign: "center" },
  titleRule: { width: 56, marginVertical: space(2) },
  emptyBlock: { paddingTop: space(8) },
  chapter: { marginTop: space(10) },
  chapterHead: { marginBottom: space(5) },
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
  closing: { alignItems: "center", gap: space(5), marginTop: space(10) },
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
