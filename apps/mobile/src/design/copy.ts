/**
 * The writing system. Rules, applied everywhere:
 * - Plain verbs, sentence case, no filler, no exclamation marks.
 * - The storyteller is "they" unless the family's own words say otherwise.
 * - States are honest: never pretend, never apologize vaguely, always say
 *   what happened and what happens next.
 * Glossary: storyteller, keeper, album, chapter, open thread, blessing.
 */

import type { Session, Storyteller } from "../api/client";

export function consentLine(storyteller: Storyteller): string {
  switch (storyteller.consent) {
    case "granted":
      return "Recording with their blessing";
    case "pending":
      return "Awaiting their first call";
    case "declined":
    case "revoked":
      return "Paused at their request";
  }
}

export function fmtDate(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

// Human language names for the tags the app offers (BCP-47 → endonym-ish).
// Falls back to the raw tag so an unknown language never shows blank.
const LANGUAGE_NAMES: Record<string, string> = {
  en: "English",
  es: "Spanish",
  pt: "Portuguese",
  fr: "French",
  ar: "Arabic",
  zh: "Chinese",
  vi: "Vietnamese",
  "hi-IN": "Hindi",
  "te-IN": "Telugu",
  "ta-IN": "Tamil",
};

export function languageName(tag: string): string {
  return LANGUAGE_NAMES[tag] ?? LANGUAGE_NAMES[tag.split("-")[0]] ?? tag;
}

export function sessionStatusLine(s: Session): string {
  // A date prefix only when we actually have one — no dangling em-dash.
  const withDate = (iso: string | null, tail: string, bare: string) => {
    const d = fmtDate(iso);
    return d ? `${d} — ${tail}` : bare;
  };
  switch (s.status) {
    case "completed":
      return withDate(s.started_at, "a conversation", "A conversation");
    case "in_progress":
      return "Happening right now";
    case "dropped":
      return withDate(s.started_at, "the line dropped", "The line dropped");
    case "no_answer":
      return withDate(s.scheduled_at, "no answer", "No answer");
    case "failed":
      return withDate(s.scheduled_at, "couldn't connect", "Couldn't connect");
    default: {
      const d = fmtDate(s.scheduled_at);
      return d ? `Scheduled for ${d}` : "Scheduled";
    }
  }
}

export function sessionSubLine(s: Session): string {
  switch (s.status) {
    case "completed": {
      const m = Math.max(1, Math.round(s.duration_seconds / 60));
      return `${m} minute${m === 1 ? "" : "s"} · tap to read`;
    }
    case "dropped":
      return "We'll pick up where they left off";
    case "no_answer":
      return "We'll try again at the next scheduled time";
    default:
      return "";
  }
}

export const strings = {
  thesis: "Every family has a storyteller.\nKeep their voice.",
  consentFootnote: "Stories are recorded only with the storyteller's spoken blessing.",
  colophon: "Every underlined sentence is anchored to the storyteller's recorded voice.",
  unsyncedRecording: "This recording hasn't synced yet",
  inConversation: "In conversation",
} as const;
