/**
 * QWERTY keyboard mapping to MIDI notes (C4=60 through B4=71).
 * Layout: A S D F G H J = C D E F G A B (white keys)
 *         W E   T Y U   = C# D#  F# G# A# (black keys)
 */
export const KEY_TO_MIDI: Record<string, number> = {
  a: 60,  // C
  w: 61,  // C#
  s: 62,  // D
  e: 63,  // D#
  d: 64,  // E
  f: 65,  // F
  t: 66,  // F#
  g: 67,  // G
  y: 68,  // G#
  h: 69,  // A
  u: 70,  // A#
  j: 71,  // B
};

const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const NOTE_TO_PC: Record<string, number> = Object.fromEntries(
  NOTE_NAMES.map((n, i) => [n.toLowerCase(), i])
);

export function midiToNoteName(midi: number): string {
  return NOTE_NAMES[midi % 12];
}

export function midiNotesToNames(midiNotes: number[]): string[] {
  return [...new Set(midiNotes.map(midiToNoteName))];
}

/** Convert note names (e.g. ["F", "A", "C"]) to MIDI numbers in middle octave. */
export function noteNamesToMidi(noteNames: string[]): number[] {
  return noteNames.map((n) => {
    const key = n.length > 1 ? n.toLowerCase() : n.charAt(0).toLowerCase();
    return 60 + (NOTE_TO_PC[key] ?? 0);
  });
}
