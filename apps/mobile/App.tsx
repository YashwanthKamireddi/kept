import React from "react";
import { useWindowDimensions, View } from "react-native";
import { NavigationContainer, DefaultTheme } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { StatusBar } from "expo-status-bar";
import { useFonts } from "expo-font";
import {
  Fraunces_600SemiBold,
  Fraunces_700Bold,
  Fraunces_900Black,
} from "@expo-google-fonts/fraunces";
import {
  Newsreader_400Regular,
  Newsreader_400Regular_Italic,
  Newsreader_500Medium,
  Newsreader_600SemiBold,
} from "@expo-google-fonts/newsreader";
import { SpaceMono_400Regular } from "@expo-google-fonts/space-mono";
import { AppStateProvider, useApp } from "./src/state";
import { SignInScreen } from "./src/screens/SignInScreen";
import { HomeScreen } from "./src/screens/HomeScreen";
import { ChapterScreen } from "./src/screens/ChapterScreen";
import { AddStorytellerScreen } from "./src/screens/AddStorytellerScreen";
import { SessionsScreen } from "./src/screens/SessionsScreen";
import { TranscriptScreen } from "./src/screens/TranscriptScreen";
import { FollowUpsScreen } from "./src/screens/FollowUpsScreen";
import { StorytellerSettingsScreen } from "./src/screens/StorytellerSettingsScreen";
import { PortraitScreen } from "./src/screens/PortraitScreen";
import { AccountScreen } from "./src/screens/AccountScreen";
import { ErrorBoundary } from "./src/design/components/ErrorBoundary";
import { BottomNav } from "./src/design/components/BottomNav";
import type { RootStackParamList } from "./src/navigation";
import { color, font } from "./src/design/tokens";

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator();

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

function AlbumsStack() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: color.paper },
        headerTitleStyle: { fontFamily: font.displaySoft, color: color.ink },
        headerTintColor: color.gold,
        headerShadowVisible: false,
      }}
    >
      <Stack.Screen name="Home" component={HomeScreen} options={{ headerShown: false }} />
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
      <Stack.Screen
        name="Portrait"
        component={PortraitScreen}
        options={{ title: "", animation: "fade_from_bottom" }}
      />
    </Stack.Navigator>
  );
}

function Root() {
  const { client, ready } = useApp();
  if (!ready) return null; // restoring a persisted session
  if (!client) return <SignInScreen />;
  return (
    <Tab.Navigator
      tabBar={(props) => <BottomNav {...props} />}
      screenOptions={{ headerShown: false, sceneStyle: { backgroundColor: color.paper } }}
    >
      <Tab.Screen name="Albums" component={AlbumsStack} />
      <Tab.Screen name="You" component={AccountScreen} />
    </Tab.Navigator>
  );
}

export default function App() {
  const [fontsLoaded] = useFonts({
    Fraunces_600SemiBold,
    Fraunces_700Bold,
    Fraunces_900Black,
    Newsreader_400Regular,
    Newsreader_400Regular_Italic,
    Newsreader_500Medium,
    Newsreader_600SemiBold,
    SpaceMono_400Regular,
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
