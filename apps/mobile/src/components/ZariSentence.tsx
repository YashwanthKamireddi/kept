import React from "react";
import { Text } from "react-native";
import { color, type } from "../theme";
import type { Sentence } from "../api/client";

/**
 * The signature element: a sentence carrying her actual voice wears a zari
 * thread — a fine gold underline. While she speaks it, the ink turns madder.
 * Bridges (pure narrative) wear nothing: the reader can SEE which words are
 * anchored to real audio. Fidelity, made visible.
 */
export function ZariSentence({
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
      accessibilityHint={anchored ? "Plays this sentence in her voice" : undefined}
      onPress={anchored ? onPress : undefined}
      suppressHighlighting
      style={[
        type.prose,
        anchored && {
          textDecorationLine: "underline",
          textDecorationColor: color.zari,
          textDecorationStyle: "solid",
        },
        playing && { color: color.madder },
      ]}
    >
      {sentence.text}{" "}
    </Text>
  );
}
