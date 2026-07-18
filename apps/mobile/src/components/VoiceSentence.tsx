import React from "react";
import { Text } from "react-native";
import { color, type } from "../theme";
import type { Sentence } from "../api/client";

/**
 * The signature element: a sentence carrying the storyteller's actual voice
 * wears a fine gold thread — tap it and they speak it. While it plays, the
 * ink turns ember. Bridges (pure narrative) wear nothing: the reader can SEE
 * which words are anchored to real audio. Fidelity, made visible.
 */
export function VoiceSentence({
  sentence,
  playing,
  onPress,
}: {
  sentence: Sentence;
  playing: boolean;
  onPress?: () => void;
}) {
  const anchored = sentence.anchors.length > 0;
  return (
    <Text
      accessibilityRole={anchored ? "button" : undefined}
      accessibilityHint={anchored ? "Plays this sentence in the storyteller's voice" : undefined}
      onPress={anchored ? onPress : undefined}
      suppressHighlighting
      style={[
        type.prose,
        anchored && {
          textDecorationLine: "underline",
          textDecorationColor: color.gold,
          textDecorationStyle: "solid",
        },
        playing && { color: color.ember },
      ]}
    >
      {sentence.text}{" "}
    </Text>
  );
}
