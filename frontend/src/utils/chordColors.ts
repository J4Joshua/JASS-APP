import { parseChord } from './chordNotes';

/**
 * Chord-root-based color palette.
 *
 * Each of the 12 chromatic notes gets a unique soft pastel color
 * that harmonises with the app's purple / lavender / pink theme.
 * Colours flow gently around the colour wheel while staying light
 * and airy — no harsh or saturated tones.
 */

export interface ChordColorSet {
  /** Main pastel accent (e.g. for fills, block faces) */
  base: string;
  /** Slightly deeper version for strokes / secondary fills */
  deep: string;
  /** Very light tint for backgrounds / subtle highlights */
  light: string;
  /** Dark version for text labels */
  text: string;
}

const ROOT_COLORS: Record<string, ChordColorSet> = {
  C:    { base: '#dda0d0', deep: '#c080b0', light: '#f6e4f4', text: '#6a2860' },
  'C#': { base: '#c89ce8', deep: '#a878d0', light: '#ecd8f8', text: '#502868' },
  D:    { base: '#a8a8f0', deep: '#8484d8', light: '#dcdcfa', text: '#383078' },
  'D#': { base: '#90b8f0', deep: '#6c98d8', light: '#d4e4fa', text: '#284070' },
  E:    { base: '#88cce8', deep: '#60acd0', light: '#d0eef8', text: '#205060' },
  F:    { base: '#80d4cc', deep: '#58b8b0', light: '#ccf0ec', text: '#185850' },
  'F#': { base: '#8cdcac', deep: '#64c488', light: '#d0f4e0', text: '#1c5838' },
  G:    { base: '#a4d898', deep: '#80c070', light: '#dcf2d4', text: '#2c5020' },
  'G#': { base: '#c8d48c', deep: '#a8b868', light: '#eef0d0', text: '#444c18' },
  A:    { base: '#e8c88c', deep: '#d0a860', light: '#f8ecd4', text: '#5c4418' },
  'A#': { base: '#f0b090', deep: '#d89068', light: '#fae4d4', text: '#643420' },
  B:    { base: '#eca0a8', deep: '#d47c88', light: '#f8dce0', text: '#682830' },
};

/** Normalise flat notes to their sharp equivalents for lookup. */
const FLAT_TO_SHARP: Record<string, string> = {
  Db: 'C#',
  Eb: 'D#',
  Fb: 'E',
  Gb: 'F#',
  Ab: 'G#',
  Bb: 'A#',
  Cb: 'B',
};

function normalizeRoot(root: string): string {
  return FLAT_TO_SHARP[root] ?? root;
}

const DEFAULT_COLORS: ChordColorSet = {
  base: '#ccc0d4',
  deep: '#a898b0',
  light: '#e8e0f0',
  text: '#504060',
};

/**
 * Get the colour set for any chord id (e.g. "Cmaj", "F#m7", "Bb").
 * Colour is determined entirely by the root note.
 */
export function getChordColor(chordId: string): ChordColorSet {
  const { root } = parseChord(chordId);
  return ROOT_COLORS[normalizeRoot(root)] ?? DEFAULT_COLORS;
}

/**
 * Get just the base accent colour for a chord — handy one-liner.
 */
export function chordAccent(chordId: string): string {
  return getChordColor(chordId).base;
}

export { ROOT_COLORS };
