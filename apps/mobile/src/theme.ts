/**
 * Heirloom — the design tokens.
 *
 * Grounded in the universal material of family archives: letter paper,
 * fountain-pen ink, gold thread. Gold belongs to the storyteller's voice;
 * ember marks the moment they are speaking. Spend boldness nowhere else.
 */

export const color = {
  paper: "#F5F1E8", // aged letter paper — app background
  surface: "#E4EAEE", // airmail-blue tint — cards & structural surfaces
  ink: "#232B3A", // fountain-pen blue-black — primary text
  inkSoft: "#5A6474", // faded ink — secondary text
  gold: "#A87B23", // gold thread — voice underlines, accents
  ember: "#8C3B2E", // the playing voice, nothing else
  hairline: "#D8D2C4", // album-page rule lines
} as const;

export const font = {
  display: "Martel_800ExtraBold",
  displaySoft: "Martel_600SemiBold",
  body: "Mukta_400Regular",
  bodyMedium: "Mukta_500Medium",
  bodyBold: "Mukta_700Bold",
} as const;

export const type = {
  chapterTitle: { fontFamily: font.display, fontSize: 30, lineHeight: 40, color: color.ink },
  sectionTitle: { fontFamily: font.displaySoft, fontSize: 20, lineHeight: 28, color: color.ink },
  prose: { fontFamily: font.body, fontSize: 18, lineHeight: 32, color: color.ink },
  label: {
    fontFamily: font.bodyMedium,
    fontSize: 13,
    lineHeight: 18,
    letterSpacing: 1.2,
    textTransform: "uppercase" as const,
    color: color.inkSoft,
  },
  body: { fontFamily: font.body, fontSize: 16, lineHeight: 24, color: color.ink },
  caption: { fontFamily: font.body, fontSize: 13, lineHeight: 18, color: color.inkSoft },
} as const;

export const space = (n: number) => n * 4;

export const radius = { card: 6, pill: 999 } as const;
