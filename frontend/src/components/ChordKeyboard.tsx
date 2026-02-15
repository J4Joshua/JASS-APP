const NOTE_DISPLAY: Record<string, string> = {
  C: "C", "C#": "C♯", Db: "D♭", D: "D", "D#": "D♯", Eb: "E♭",
  E: "E", F: "F", "F#": "F♯", Gb: "G♭", G: "G", "G#": "G♯",
  Ab: "A♭", A: "A", "A#": "A♯", Bb: "B♭", B: "B",
};

const WHITE_NOTES = ["C", "D", "E", "F", "G", "A", "B"];
const BLACK_NOTES = ["C#", "D#", "F#", "G#", "A#"];

/** Map flat names to sharps so both spellings light the correct key */
const FLAT_TO_SHARP: Record<string, string> = {
  Db: "C#", Eb: "D#", Gb: "F#", Ab: "G#", Bb: "A#",
};

function isNoteHighlighted(note: string, notes: string[]): boolean {
  if (notes.includes(note)) return true;
  const flat = Object.entries(FLAT_TO_SHARP).find(([, s]) => s === note)?.[0];
  return flat ? notes.includes(flat) : false;
}

const BLACK_KEY_POSITIONS: Record<string, number> = {
  "C#": 0, "D#": 1, "F#": 3, "G#": 4, "A#": 5,
};

const WHITE_KEY_WIDTH = 38;
const BLACK_KEY_WIDTH = 24;
const WHITE_KEY_HEIGHT = 120;
const BLACK_KEY_HEIGHT = 76;

interface ChordKeyboardProps {
  name: string;
  notes: string[];
  color: string;
  description: string;
  /** Compact mode for embedding below graph nodes */
  compact?: boolean;
  /** No card/rectangle - just the piano, no background or border */
  minimal?: boolean;
  /** Micro size for embedding below small spheres (next chords) */
  micro?: boolean;
  /** Scale factor (e.g. 1.2 = 20% bigger) */
  scale?: number;
}

export default function ChordKeyboard({ name, notes, color, description, compact = false, minimal = false, micro = false, scale = 1 }: ChordKeyboardProps) {
  const wkW = (micro ? 26 : compact ? 36 : WHITE_KEY_WIDTH) * scale;
  const bkW = (micro ? 16 : compact ? 22 : BLACK_KEY_WIDTH) * scale;
  const wkH = (micro ? 58 : compact ? 90 : WHITE_KEY_HEIGHT) * scale;
  const bkH = (micro ? 35 : compact ? 55 : BLACK_KEY_HEIGHT) * scale;
  const totalWidth = wkW * 7;

  return (
    <div
      className="font-[family-name:var(--font-patrick-hand)]"
      style={{
        padding: (micro ? 6 : compact ? 10 : minimal ? 12 : 20) * scale,
        ...(minimal
          ? { background: "transparent", border: "none" }
          : {
              borderRadius: 16,
              background: `linear-gradient(135deg, ${color}0A, ${color}14)`,
              border: `1px solid ${color}33`,
            }),
      }}
    >
      {/* Chord name */}
      <p
        className="font-extrabold tracking-tight text-center"
        style={{ color, fontSize: (micro ? 13 : compact ? 18 : 22) * scale, marginBottom: (micro ? 3 : compact ? 8 : 16) * scale }}
      >
        {name}
      </p>

      {/* Piano keyboard */}
      <div className="flex justify-center">
        <div
          className="relative"
          style={{ width: totalWidth, height: wkH }}
        >
          {/* White keys */}
          {WHITE_NOTES.map((note) => {
            const highlighted = isNoteHighlighted(note, notes);
            const whiteIndex = WHITE_NOTES.indexOf(note);
            return (
              <div
                key={note}
                className="absolute top-0 flex items-end justify-center rounded-b-md transition-all duration-200"
                style={{
                  left: whiteIndex * wkW + 1,
                  width: wkW - 2,
                  height: wkH,
                  background: highlighted
                    ? `linear-gradient(180deg, ${color}33 0%, ${color}88 100%)`
                    : "linear-gradient(180deg, #fefefe 0%, #e8e8e8 100%)",
                  border: `1px solid ${highlighted ? color : "#ccc"}`,
                  boxShadow: highlighted
                    ? `0 0 12px ${color}44, inset 0 -4px 8px rgba(0,0,0,0.08)`
                    : "inset 0 -4px 8px rgba(0,0,0,0.05), 1px 2px 3px rgba(0,0,0,0.1)",
                  zIndex: 1,
                  paddingBottom: 8 * scale,
                }}
              >
                {highlighted && (
                  <span
                    className="font-bold"
                    style={{ color, fontSize: 13 * scale }}
                  >
                    {NOTE_DISPLAY[note]}
                  </span>
                )}
              </div>
            );
          })}

          {/* Black keys */}
          {BLACK_NOTES.map((note) => {
            const highlighted = isNoteHighlighted(note, notes);
            const whitesBefore = BLACK_KEY_POSITIONS[note];
            const left = (whitesBefore + 1) * wkW - bkW / 2;
            return (
              <div
                key={note}
                className="absolute top-0 flex items-end justify-center rounded-b transition-all duration-200"
                style={{
                  left,
                  width: bkW,
                  height: bkH,
                  background: highlighted
                    ? `linear-gradient(180deg, ${color} 0%, ${color}dd 100%)`
                    : "linear-gradient(180deg, #2a2a2a 0%, #111 100%)",
                  border: `1px solid ${highlighted ? color : "#000"}`,
                  boxShadow: highlighted
                    ? `0 0 12px ${color}88, inset 0 -3px 6px rgba(0,0,0,0.3)`
                    : "inset 0 -3px 6px rgba(0,0,0,0.4), 2px 2px 4px rgba(0,0,0,0.5)",
                  zIndex: 2,
                  paddingBottom: 6 * scale,
                }}
              >
                {highlighted && (
                  <span className="font-bold text-white drop-shadow-sm" style={{ fontSize: 11 * scale }}>
                    {NOTE_DISPLAY[note]}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Note list - hide when compact or micro */}
      {!compact && !micro && (
        <p
          className="text-xs tracking-widest text-center mt-4"
          style={{ color }}
        >
          {notes.map((n) => NOTE_DISPLAY[n] || n).join(" · ")}
        </p>
      )}

      {/* Description - hide when compact or micro */}
      {!compact && !micro && (
        <p className="text-xs text-zinc-500 italic text-center mt-1">
          {description}
        </p>
      )}
    </div>
  );
}
