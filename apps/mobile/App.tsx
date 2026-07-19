import React from "react";
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
import type { RootStackParamList } from "./src/navigation";
import { color, font } from "./src/theme";

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
    <AppStateProvider>
      <NavigationContainer theme={theme}>
        <StatusBar style="dark" />
        <Root />
      </NavigationContainer>
    </AppStateProvider>
  );
}
