export type RootStackParamList = {
  Home: undefined;
  Chapter: { chapterId: string };
  AddStoryteller: undefined;
  Sessions: { storytellerId: string; name: string };
  Transcript: { sessionId: string };
  FollowUps: { storytellerId: string; name: string };
};
