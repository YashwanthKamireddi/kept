/**
 * Heirloom v2 — "the family album, filmed."
 *
 * Two scenes, like cinema:
 *   COVER scenes (arrival, onboarding) — a deep lamplight-ink stage with
 *   gold-foil serif type: opening a leather album in the evening.
 *   PAGE scenes (the album, reading) — warm letter paper in daylight.
 *
 * Gold belongs to the storyteller's voice and to foil on covers; ember marks
 * the moment they are speaking. Spend boldness nowhere else.
 */

export const color = {
  // Page scene (light)
  paper: "#F6F2E9",
  surface: "#EDE7D9",
  ink: "#232B3A",
  inkSoft: "#5A6474",
  hairline: "#DAD3C2",

  // Cover scene (dark)
  stage: "#14181F", // lamplight ink — cover backgrounds
  stageSoft: "#1D242E", // raised elements on the stage
  stageText: "#C7CDD8", // secondary text on the stage
  foil: "#C9A24B", // gold foil on covers (brighter than page gold)

  // Voice
  gold: "#A87B23", // voice underlines & accents on paper
  ember: "#8C3B2E", // the playing voice, nothing else
} as const;

export const font = {
  display: "Martel_800ExtraBold",
  displaySoft: "Martel_600SemiBold",
  body: "Mukta_400Regular",
  bodyMedium: "Mukta_500Medium",
  bodyBold: "Mukta_700Bold",
} as const;

export const type = {
  wordmark: { fontFamily: font.display, fontSize: 56, lineHeight: 72, color: color.foil },
  chapterTitle: { fontFamily: font.display, fontSize: 32, lineHeight: 44, color: color.ink },
  sectionTitle: { fontFamily: font.displaySoft, fontSize: 21, lineHeight: 30, color: color.ink },
  coverName: { fontFamily: font.display, fontSize: 24, lineHeight: 36, color: color.foil },
  prose: { fontFamily: font.body, fontSize: 18, lineHeight: 33, color: color.ink },
  label: {
    fontFamily: font.bodyMedium,
    fontSize: 12,
    lineHeight: 17,
    letterSpacing: 1.6,
    textTransform: "uppercase" as const,
    color: color.inkSoft,
  },
  body: { fontFamily: font.body, fontSize: 16, lineHeight: 25, color: color.ink },
  caption: { fontFamily: font.body, fontSize: 13, lineHeight: 19, color: color.inkSoft },
} as const;

export const space = (n: number) => n * 4;

export const radius = { sheet: 16, cover: 12, pill: 999 } as const;

/** One shadow language: paper objects resting on a table. */
export const shadow = {
  sheet: {
    shadowColor: color.stage,
    shadowOpacity: 0.22,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 12 },
    elevation: 8,
  },
  cover: {
    shadowColor: color.stage,
    shadowOpacity: 0.28,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 8 },
    elevation: 6,
  },
} as const;

export const motion = {
  entrance: 550, // ms — screens settle like a page laid down
  stagger: 110, // ms between siblings
} as const;
