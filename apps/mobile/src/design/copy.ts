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

export function sessionStatusLine(s: Session): string {
  switch (s.status) {
    case "completed":
      return `${fmtDate(s.started_at)} — a conversation`;
    case "in_progress":
      return "Happening right now";
    case "dropped":
      return `${fmtDate(s.started_at)} — the line dropped`;
    case "no_answer":
      return `${fmtDate(s.scheduled_at)} — no answer`;
    case "failed":
      return `${fmtDate(s.scheduled_at)} — couldn't connect`;
    default:
      return `Scheduled for ${fmtDate(s.scheduled_at)}`;
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
