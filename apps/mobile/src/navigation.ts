export type RootStackParamList = {
  Home: undefined;
  Chapter: { chapterId: string; storytellerName?: string };
  AddStoryteller: undefined;
  Sessions: { storytellerId: string; name: string };
  Transcript: { sessionId: string };
  FollowUps: { storytellerId: string; name: string };
  StorytellerSettings: { storytellerId: string };
};
