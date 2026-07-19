import React from "react";
import { View, type StyleProp, type ViewStyle } from "react-native";
import { color, radius, shadow, space } from "../tokens";

/** A sheet of warm paper resting on whatever scene it's placed in. */
export function PaperSheet({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <View
      style={[
        {
          backgroundColor: color.paper,
          borderRadius: radius.sheet,
          padding: space(6),
          gap: space(5),
          ...shadow.sheet,
        },
        style,
      ]}
    >
      {children}
    </View>
  );
}
