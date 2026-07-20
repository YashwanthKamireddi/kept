import React from "react";
import { useWindowDimensions, View } from "react-native";
import { NavigationContainer, DefaultTheme } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";
import {
  useFonts,
  Martel_600SemiBold,
  Martel_800ExtraBold,
} from "@expo-google-fonts/martel";
import { Mukta_400Regular, Mukta_500Medium, Mukta_700Bold } from "@expo-google-fonts/mukta";
import { AppStateProvider, useApp } from "./src/state";
import { SignInScreen } from "./src/screens/SignInScreen";
import { HomeScreen } from "./src/screens/HomeScreen";
import { ChapterScreen } from "./src/screens/ChapterScreen";
import { AddStorytellerScreen } from "./src/screens/AddStorytellerScreen";
import { SessionsScreen } from "./src/screens/SessionsScreen";
import { TranscriptScreen } from "./src/screens/TranscriptScreen";
import { FollowUpsScreen } from "./src/screens/FollowUpsScreen";
import { StorytellerSettingsScreen } from "./src/screens/StorytellerSettingsScreen";
import { ErrorBoundary } from "./src/design/components/ErrorBoundary";
import type { RootStackParamList } from "./src/navigation";
import { color, font } from "./src/design/tokens";

const Stack = createNativeStackNavigator<RootStackParamList>();

const theme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    background: color.paper,
    card: color.paper,
    text: color.ink,
    primary: color.gold,
    border: color.hairline,
  },
};

/**
 * Kept is a phone-shaped app. On a wide browser, center it as one intentional
 * column on the lamplight stage instead of letting every screen sprawl
 * edge-to-edge. On a real phone (narrow) this is a no-op full-bleed frame.
 */
const PHONE_MAX_WIDTH = 460;

function ResponsiveFrame({ children }: { children: React.ReactNode }) {
  const { width } = useWindowDimensions();
  const wide = width > PHONE_MAX_WIDTH + 40;
  return (
    <View style={{ flex: 1, backgroundColor: color.stage, alignItems: "center" }}>
      <View
        style={{
          flex: 1,
          width: "100%",
          maxWidth: wide ? PHONE_MAX_WIDTH : undefined,
          overflow: "hidden",
          ...(wide
            ? {
                shadowColor: "#000",
                shadowOpacity: 0.35,
                shadowRadius: 40,
                shadowOffset: { width: 0, height: 0 },
              }
            : {}),
        }}
      >
        {children}
      </View>
    </View>
  );
}

function Root() {
  const { client, ready } = useApp();
  if (!ready) return null; // restoring a persisted session
  if (!client) return <SignInScreen />;
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: color.paper },
        headerTitleStyle: { fontFamily: font.displaySoft, color: color.ink },
        headerTintColor: color.gold,
        headerShadowVisible: false,
      }}
    >
      <Stack.Screen
        name="Home"
        component={HomeScreen}
        options={{ title: "The Album", headerLargeTitle: true }}
      />
      <Stack.Screen
        name="Chapter"
        component={ChapterScreen}
        options={{ title: "", animation: "fade_from_bottom" }}
      />
      <Stack.Screen
        name="AddStoryteller"
        component={AddStorytellerScreen}
        options={{ title: "New storyteller", presentation: "modal" }}
      />
      <Stack.Screen name="Sessions" component={SessionsScreen} options={{ title: "Calls" }} />
      <Stack.Screen
        name="Transcript"
        component={TranscriptScreen}
        options={{ title: "", animation: "fade_from_bottom" }}
      />
      <Stack.Screen
        name="FollowUps"
        component={FollowUpsScreen}
        options={{ title: "Open threads" }}
      />
      <Stack.Screen
        name="StorytellerSettings"
        component={StorytellerSettingsScreen}
        options={{ title: "Manage" }}
      />
    </Stack.Navigator>
  );
}

export default function App() {
  const [fontsLoaded] = useFonts({
    Martel_600SemiBold,
    Martel_800ExtraBold,
    Mukta_400Regular,
    Mukta_500Medium,
    Mukta_700Bold,
  });
  if (!fontsLoaded) return null;
  return (
    <ErrorBoundary>
      <AppStateProvider>
        <ResponsiveFrame>
          <NavigationContainer theme={theme}>
            <StatusBar style="dark" />
            <Root />
          </NavigationContainer>
        </ResponsiveFrame>
      </AppStateProvider>
    </ErrorBoundary>
  );
}
