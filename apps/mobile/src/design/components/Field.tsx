import React from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";
import { color, font, space, type } from "../tokens";

export function Field({
  label,
  value,
  onChange,
  placeholder,
  keyboard,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  keyboard?: "email-address" | "url" | "phone-pad";
}) {
  return (
    <View style={{ gap: space(1) }}>
      <Text style={type.label}>{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChange}
        placeholder={placeholder}
        placeholderTextColor={color.hairline}
        keyboardType={keyboard}
        autoCapitalize={keyboard ? "none" : "words"}
        style={styles.input}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  input: {
    borderBottomWidth: 1,
    borderBottomColor: color.hairline,
    paddingVertical: space(2),
    fontFamily: font.body,
    fontSize: 17,
    color: color.ink,
  },
});
