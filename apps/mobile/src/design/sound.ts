/**
 * Sound design: four synthesized sounds, each tied to one moment.
 *   tape_start  — her voice begins (paired with a soft haptic)
 *   paper_turn  — chapter navigation
 *   seal_open   — the envelope opens
 *   arrival     — a new chapter has arrived
 * Always subtle, one persisted mute toggle, silent failures (sound is
 * seasoning, never load-bearing).
 */

import AsyncStorage from "@react-native-async-storage/async-storage";
import { createAudioPlayer, type AudioPlayer } from "expo-audio";

const MUTE_KEY = "kept.sound.muted";

const SOURCES = {
  tape_start: require("../../assets/sounds/tape_start.wav"),
  paper_turn: require("../../assets/sounds/paper_turn.wav"),
  seal_open: require("../../assets/sounds/seal_open.wav"),
  arrival: require("../../assets/sounds/arrival.wav"),
} as const;

export type SoundName = keyof typeof SOURCES;

let muted = false;
void AsyncStorage.getItem(MUTE_KEY).then((v) => {
  muted = v === "1";
});

const players = new Map<SoundName, AudioPlayer>();

export function play(name: SoundName): void {
  if (muted) return;
  try {
    let player = players.get(name);
    if (!player) {
      player = createAudioPlayer(SOURCES[name]);
      player.volume = 0.55;
      players.set(name, player);
    }
    player.seekTo(0);
    player.play();
  } catch {
    // Sound must never break the experience.
  }
}

export function isMuted(): boolean {
  return muted;
}

export async function setMuted(value: boolean): Promise<void> {
  muted = value;
  await AsyncStorage.setItem(MUTE_KEY, value ? "1" : "0");
}
