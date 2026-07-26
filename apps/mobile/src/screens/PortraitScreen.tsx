import React, { useEffect, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../navigation";
import { color, space, type } from "../design/tokens";
import { Entrance, DrawnRule } from "../design/motion";
import { Page } from "../design/materials";
import { Loading } from "../design/components/Loading";
import { useApp } from "../state";
import type { Portrait } from "../api/client";

type Props = NativeStackScreenProps<RootStackParamList, "Portrait">;

interface Item {
  title: string;
  detail: string;
}
interface Section {
  heading: string;
  items: Item[];
  text: string[];
}

/** Parse the pipeline's Life-Brief markdown (## sections, - **Name** — detail)
 * into something we can set in the design system. Defensive: anything it
 * doesn't recognize falls through as a plain line. */
function parseBrief(md: string): Section[] {
  const sections: Section[] = [];
  let cur: Section | null = null;
  for (const raw of md.split("\n")) {
    const line = raw.trim();
    if (line.startsWith("## ")) {
      cur = { heading: line.slice(3).trim(), items: [], text: [] };
      sections.push(cur);
    } else if (line.startsWith("# ") || !line) {
      continue; // top title / blank
    } else if (cur) {
      if (line.startsWith("- ")) {
        const body = line.slice(2);
        const m = body.match(/^\*\*(.+?)\*\*\s*(.*)$/);
        if (m) {
          const detail = m[2]
            .replace(/^\(.*?\)\s*/, "") // drop the (alias)
            .replace(/^[—–-]\s*/, "") // drop the leading dash
            .trim();
          cur.items.push({ title: m[1].trim(), detail });
        } else {
          cur.items.push({ title: "", detail: body.replace(/\*\*/g, "") });
        }
      } else {
        cur.text.push(line.replace(/\*\*/g, ""));
      }
    }
  }
  return sections;
}

export function PortraitScreen({ route }: Props) {
  const { client } = useApp();
  const [portrait, setPortrait] = useState<Portrait | null>(null);

  useEffect(() => {
    if (!client) return;
    void client.getPortrait(route.params.storytellerId).then(setPortrait);
  }, [client, route.params.storytellerId]);

  if (!portrait) return <Loading label="Turning the pages…" />;

  const sections = parseBrief(portrait.life_brief);
  const empty = sections.length === 0;

  return (
    <Page>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Entrance order={0} style={styles.header}>
          <Text style={[type.label, { color: color.gold }]}>A portrait</Text>
          <Text style={type.chapterTitle}>{route.params.name}</Text>
          <Text style={[type.caption, { color: color.inkSoft }]}>
            Drawn, over time, from their own stories.
          </Text>
        </Entrance>
        <DrawnRule color={color.hairline} order={1} style={styles.rule} />

        {empty ? (
          <Entrance order={2} style={styles.emptyBlock}>
            <Text style={[type.body, { color: color.inkSoft, textAlign: "center" }]}>
              Their portrait will fill in as they share more stories — the people, places, and
              moments that keep coming up.
            </Text>
          </Entrance>
        ) : (
          sections.map((s, i) => (
            <Entrance key={s.heading + i} order={Math.min(i + 2, 6)} style={styles.section}>
              <Text style={type.label}>{s.heading}</Text>
              {s.items.map((it, j) => (
                <View key={j} style={styles.item}>
                  {it.title ? <Text style={styles.itemTitle}>{it.title}</Text> : null}
                  {it.detail ? (
                    <Text style={[type.body, { color: color.inkSoft }]}>{it.detail}</Text>
                  ) : null}
                </View>
              ))}
              {s.text.map((t, j) => (
                <Text key={`t${j}`} style={[type.body, { color: color.inkSoft }]}>
                  {t}
                </Text>
              ))}
            </Entrance>
          ))
        )}
      </ScrollView>
    </Page>
  );
}

const styles = StyleSheet.create({
  scroll: { padding: space(6), paddingBottom: space(16), gap: space(6) },
  header: { gap: space(1) },
  rule: { marginTop: space(1) },
  emptyBlock: { paddingTop: space(8) },
  section: { gap: space(3) },
  item: { gap: 2 },
  itemTitle: { ...type.body, fontFamily: type.sectionTitle.fontFamily, color: color.ink },
});
