import React, { useEffect, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../navigation";
import { color, font, space, type } from "../design/tokens";
import { Entrance, DrawnRule } from "../design/motion";
import { Page } from "../design/materials";
import { Loading } from "../design/components/Loading";
import { TapeBar } from "../design/components/TapeBar";
import { useSpanPlayer } from "../design/useSpanPlayer";
import { useApp } from "../state";
import type { Life, LifeMoment } from "../api/client";

type Props = NativeStackScreenProps<RootStackParamList, "Portrait">;

/**
 * The living portrait. Not a bio card — the people, places, and things a life
 * kept returning to, each carrying the words the storyteller actually spoke.
 * Their words wear the italic reserved for their exact voice; where a recording
 * exists, the line plays in it. Assembled from the life graph, never invented.
 */
export function PortraitScreen({ route }: Props) {
  const { client } = useApp();
  const [life, setLife] = useState<Life | null>(null);
  const { span, select, playing, positionMs, unavailable } = useSpanPlayer();

  useEffect(() => {
    if (!client) return;
    void client.getLife(route.params.storytellerId).then(setLife);
  }, [client, route.params.storytellerId]);

  if (!life) return <Loading label="Drawing the portrait…" />;

  const empty = life.groups.length === 0;

  return (
    <Page>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Entrance order={0} style={styles.header}>
          <Text style={[type.label, { color: color.gold }]}>A portrait</Text>
          <Text style={type.chapterTitle}>{route.params.name ?? life.name}</Text>
          <Text style={[type.caption, { color: color.inkSoft }]}>
            The people and places they carried — in their own words.
          </Text>
        </Entrance>
        <DrawnRule color={color.hairline} order={1} style={styles.rule} />

        {empty ? (
          <Entrance order={2} style={styles.emptyBlock}>
            <Text style={[type.body, { color: color.inkSoft, textAlign: "center" }]}>
              Their portrait fills in as they share more stories.
            </Text>
          </Entrance>
        ) : (
          life.groups.map((group, gi) => (
            <Entrance key={group.kind} order={Math.min(gi + 2, 6)} style={styles.group}>
              <Text style={styles.groupLabel}>{group.label}</Text>
              {group.entities.map((entity, ei) => (
                <View key={entity.name + ei} style={styles.entity}>
                  <Text style={styles.entityName}>{entity.name}</Text>
                  {entity.summary ? (
                    <Text style={[type.body, { color: color.inkSoft }]}>{entity.summary}</Text>
                  ) : null}
                  {entity.moments.map((moment, mi) => {
                    const key = `${gi}:${ei}:${mi}`;
                    return (
                      <SpokenLine
                        key={key}
                        moment={moment}
                        playing={span?.key === key && playing}
                        onPlay={() =>
                          moment.anchor &&
                          select({ key, anchor: moment.anchor, text: moment.quote })
                        }
                      />
                    );
                  })}
                </View>
              ))}
            </Entrance>
          ))
        )}
      </ScrollView>
      {span && (
        <TapeBar
          playing={playing}
          positionMs={positionMs}
          label={`In their own voice — ${route.params.name ?? life.name}`}
          unavailable={unavailable}
        />
      )}
    </Page>
  );
}

/** One thing the storyteller said, set apart with a gold thread. When a
 * recording exists it plays in their voice; otherwise it simply reads as
 * their words — the thread is honest either way. */
function SpokenLine({
  moment,
  playing,
  onPlay,
}: {
  moment: LifeMoment;
  playing: boolean;
  onPlay: () => void;
}) {
  const anchored = moment.anchor !== null;
  return (
    <View style={styles.moment}>
      <View style={[styles.thread, playing && { backgroundColor: color.ember }]} />
      <Text
        accessibilityRole={anchored ? "button" : undefined}
        accessibilityHint={anchored ? "Plays this in the storyteller's voice" : undefined}
        onPress={anchored ? onPlay : undefined}
        suppressHighlighting
        style={[
          styles.quote,
          anchored && { textDecorationLine: "underline", textDecorationColor: color.gold },
          playing && { color: color.ember },
        ]}
      >
        “{moment.quote}”
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  scroll: { padding: space(6), paddingBottom: space(20), gap: space(6) },
  header: { gap: space(1) },
  rule: { marginTop: space(1) },
  emptyBlock: { paddingTop: space(8) },
  group: { gap: space(4) },
  groupLabel: {
    fontFamily: font.displaySoft,
    fontSize: 20,
    lineHeight: 28,
    color: color.ink,
  },
  entity: { gap: space(2), paddingLeft: space(1) },
  entityName: {
    fontFamily: font.bodyBold,
    fontSize: 17,
    letterSpacing: 0.3,
    color: color.gold,
  },
  moment: { flexDirection: "row", gap: space(3), marginTop: space(1) },
  thread: { width: 2, borderRadius: 2, backgroundColor: color.gold, opacity: 0.85 },
  quote: {
    flex: 1,
    fontFamily: font.quote,
    fontSize: 19,
    lineHeight: 31,
    color: color.ink,
  },
});
