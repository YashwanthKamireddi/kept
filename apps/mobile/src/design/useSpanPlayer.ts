import { useEffect, useRef, useState } from "react";
import { useAudioPlayer, useAudioPlayerStatus } from "expo-audio";
import { useApp } from "../state";
import type { Anchor } from "../api/client";
import { play } from "./sound";
import { haptic } from "./haptics";

export interface PlayingSpan {
  key: string; // caller-owned identity, e.g. `${chapter}:${paragraph}:${sentence}`
  anchor: Anchor;
  text: string;
}

/**
 * The voice-thread playback engine, shared by every reader (a single chapter,
 * the whole memoir). Choose a sentence's span and it resolves a short-lived
 * playback URL, seeks to the exact word, plays only that span, and stops at its
 * end — with a tape click + soft heartbeat the moment their voice starts, and
 * an honest `unavailable` flag when a recording hasn't synced. `onEnd` fires
 * once a span finishes so the caller can close any listening surface it opened.
 */
export function useSpanPlayer(onEnd?: () => void) {
  const { client } = useApp();
  const [span, setSpan] = useState<PlayingSpan | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  const [sourceUrl, setSourceUrl] = useState<string | null>(null);
  const wasPlaying = useRef(false);
  const onEndRef = useRef(onEnd);
  onEndRef.current = onEnd;

  // Ask the server for a short-lived playback URL when a sentence is chosen.
  useEffect(() => {
    if (!span || !client) {
      setSourceUrl(null);
      return;
    }
    setUnavailable(false);
    client
      .resolveAudioUrl(span.anchor.audio_key)
      .then(setSourceUrl)
      .catch(() => setUnavailable(true));
  }, [span, client]);

  const player = useAudioPlayer(sourceUrl ?? undefined);
  const status = useAudioPlayerStatus(player);

  // Seek to the sentence's span when a new anchor is chosen.
  useEffect(() => {
    if (!span || !sourceUrl) return;
    setUnavailable(false);
    player.seekTo(span.anchor.t_start_ms / 1000);
    player.play();
  }, [span, sourceUrl, player]);

  // The moment their voice actually starts: tape click + one soft heartbeat.
  useEffect(() => {
    if (status.playing && !wasPlaying.current) {
      play("tape_start");
      haptic.voiceStart();
    }
    wasPlaying.current = status.playing;
  }, [status.playing]);

  // Stop at the end of the span; surface honest failure for unsynced audio.
  useEffect(() => {
    if (!span) return;
    if (status.playbackState === "error") {
      setUnavailable(true);
      return;
    }
    if (status.playing && status.currentTime * 1000 >= span.anchor.t_end_ms) {
      player.pause();
      setSpan(null);
      onEndRef.current?.();
    }
  }, [status, span, player]);

  return {
    span,
    select: (next: PlayingSpan) => setSpan(next),
    clear: () => setSpan(null),
    playing: status.playing,
    positionMs: status.currentTime * 1000,
    unavailable,
  };
}
