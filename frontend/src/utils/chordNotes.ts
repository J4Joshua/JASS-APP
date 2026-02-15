/**
 * Parse a chord ID to extract the root note.
 *
 * Examples:
 * - "Cmaj7" → { root: "C", suffix: "maj7" }
 * - "F#m" → { root: "F#", suffix: "m" }
 * - "Bb" → { root: "Bb", suffix: "" }
 */
export function parseChord(chordId: string): { root: string; suffix: string } {
  // Match root note: A-G followed by optional sharp/flat
  const match = chordId.match(/^([A-G][#b]?)(.*)/);

  if (!match) {
    // Fallback for invalid chord names
    return { root: 'C', suffix: '' };
  }

  return {
    root: match[1],
    suffix: match[2],
  };
}
