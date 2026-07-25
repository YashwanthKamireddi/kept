/**
 * Heirloom v3 — Kept's design tokens. THE single source of truth.
 *
 * "The family album, filmed." Two scenes, like cinema:
 *   COVER scenes (arrival, onboarding, listening) — lamplight-ink stage,
 *   gold-foil letterpress serif: opening a leather album in the evening.
 *   PAGE scenes (the album, reading) — warm letter paper with real grain.
 *
 * Laws:
 *   gold  = the storyteller's voice, and foil on covers. Nothing else.
 *   ember = the moment they are speaking. Nothing else.
 *   Every animation respects reduced motion. Every state is honest.
 */

export const color = {
  // Page scene (light)
  paper: "#F6F2E9",
  surface: "#EDE7D9",
  ink: "#232B3A",
  inkSoft: "#5A6474",
  hairline: "#DAD3C2",

  // Cover scene (dark)
  stage: "#14181F",
  stageRaised: "#1D242E",
  stageText: "#C7CDD8",
  foil: "#C9A24B",

  // Voice
  gold: "#A87B23",
  ember: "#8C3B2E",
} as const;

/** Semantic aliases — always mapped onto existing hues, never new ones. */
export const semantic = {
  consent: {
    granted: color.gold,
    pending: color.inkSoft,
    paused: color.inkSoft,
  },
  danger: color.ember,
  live: color.gold,
} as const;

/**
 * Type system — a printed heirloom, not a template.
 * - Fraunces: an old-style serif with hand-cut warmth (letterpress, not
 *   template Playfair) — the wordmark, names, chapter titles.
 * - Newsreader: an editorial reading serif; the stories read like a printed
 *   memoir. Its italic is reserved for the storyteller's exact words.
 * - Space Mono: the tape counter + audio timestamps — a cassette-deck nod,
 *   tying the type to the recorded-voice subject.
 */
export const font = {
  wordmark: "Fraunces_900Black",
  display: "Fraunces_700Bold",
  displaySoft: "Fraunces_600SemiBold",
  body: "Newsreader_400Regular",
  bodyMedium: "Newsreader_500Medium",
  bodyBold: "Newsreader_600SemiBold",
  quote: "Newsreader_400Regular_Italic", // her exact words
  mono: "SpaceMono_400Regular", // tape counter, timestamps
} as const;

/** Letterpress: foil that looks stamped into the cover, not painted on. */
export const letterpress = {
  textShadowColor: "rgba(0,0,0,0.55)",
  textShadowOffset: { width: 0, height: 1 },
  textShadowRadius: 1,
} as const;

export const type = {
  wordmark: {
    fontFamily: font.wordmark,
    fontSize: 56,
    lineHeight: 72,
    color: color.foil,
    ...letterpress,
  },
  chapterTitle: { fontFamily: font.display, fontSize: 32, lineHeight: 44, color: color.ink },
  sectionTitle: { fontFamily: font.displaySoft, fontSize: 21, lineHeight: 30, color: color.ink },
  coverName: {
    fontFamily: font.display,
    fontSize: 24,
    lineHeight: 36,
    color: color.foil,
    ...letterpress,
  },
  prose: { fontFamily: font.body, fontSize: 18, lineHeight: 32, color: color.ink },
  proseLarge: { fontFamily: font.quote, fontSize: 25, lineHeight: 40, color: color.paper },
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
  counter: {
    fontFamily: font.mono,
    fontSize: 14,
    color: color.gold,
    fontVariant: ["tabular-nums"] as const,
  },
} as const;

export const space = (n: number) => n * 4;

export const radius = { sheet: 16, cover: 12, seal: 999, pill: 999 } as const;

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

/** Motion timings — pages settle, threads draw, covers breathe. */
export const duration = {
  entrance: 550,
  stagger: 110,
  rule: 700,
  unfold: 700,
  breath: 2400,
  crossfade: 250,
} as const;

/** Material strengths. */
export const material = {
  grainOpacity: 0.05,
  lamplightTop: "#1B212C",
  vignette: "rgba(0,0,0,0.32)",
} as const;

// Back-compat alias for the v2 name; the sweep removes external uses.
export const motion = { entrance: duration.entrance, stagger: duration.stagger } as const;
