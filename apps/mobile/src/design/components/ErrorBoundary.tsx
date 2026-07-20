import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { color, font, space, type } from "../tokens";
import { PressableScale } from "../motion";

/**
 * Catches render errors anywhere below it so a single bad screen never blanks
 * the whole app. Failure is a moment for direction, not mood: it says plainly
 * what to do (try again), in the interface's voice. Kept in the page scene so
 * it never feels like a crash screen.
 */
interface State {
  error: Error | null;
}

export class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  State
> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error) {
    // In production this is where a crash reporter would receive the error.
    console.error("ErrorBoundary caught:", error);
  }

  reset = () => this.setState({ error: null });

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <View style={styles.page}>
        <Text style={type.sectionTitle}>Something didn't open</Text>
        <View style={styles.rule} />
        <Text style={[type.body, styles.body]}>
          This page ran into a problem. Nothing was lost — your family's
          stories are safe. Try again in a moment.
        </Text>
        <PressableScale accessibilityRole="button" onPress={this.reset} style={styles.button}>
          <Text style={styles.buttonText}>Try again</Text>
        </PressableScale>
      </View>
    );
  }
}

const styles = StyleSheet.create({
  page: {
    flex: 1,
    backgroundColor: color.paper,
    alignItems: "center",
    justifyContent: "center",
    padding: space(8),
    gap: space(4),
  },
  rule: { width: 56, height: 1, backgroundColor: color.gold },
  body: { color: color.inkSoft, textAlign: "center" },
  button: {
    backgroundColor: color.ink,
    paddingHorizontal: space(6),
    paddingVertical: space(3),
    borderRadius: 10,
    marginTop: space(2),
  },
  buttonText: { fontFamily: font.bodyBold, fontSize: 15, color: color.paper },
});
