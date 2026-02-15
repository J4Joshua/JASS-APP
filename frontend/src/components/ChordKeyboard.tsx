const NOTE_DISPLAY: Record<string, string> = {
  C: "C", "C#": "C♯", Db: "D♭", D: "D", "D#": "D♯", Eb: "E♭",
  E: "E", F: "F", "F#": "F♯", Gb: "G♭", G: "G", "G#": "G♯",
  Ab: "A♭", A: "A", "A#": "A♯", Bb: "B♭", B: "B",
};

const WHITE_NOTES = ["C", "D", "E", "F", "G", "A", "B"];
const BLACK_NOTES = ["C#", "D#", "F#", "G#", "A#"];

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
}

export default function ChordKeyboard({ name, notes, color, description }: ChordKeyboardProps) {
  const totalWidth = WHITE_KEY_WIDTH * 7;

  return (
    <div
      className="rounded-2xl p-5 font-[family-name:var(--font-geist-mono)]"
      style={{
        background: `linear-gradient(135deg, ${color}0A, ${color}14)`,
        border: `1px solid ${color}33`,
      }}
    >
      {/* Chord name */}
      <p
        className="text-xl font-extrabold tracking-tight text-center mb-4"
        style={{ color }}
      >
        {name}
      </p>

      {/* Piano keyboard */}
      <div className="flex justify-center">
        <div
          className="relative"
          style={{ width: totalWidth, height: WHITE_KEY_HEIGHT }}
        >
          {/* White keys */}
          {WHITE_NOTES.map((note) => {
            const highlighted = notes.includes(note);
            const whiteIndex = WHITE_NOTES.indexOf(note);
            return (
              <div
                key={note}
                className="absolute top-0 flex items-end justify-center rounded-b-md transition-all duration-200"
                style={{
                  left: whiteIndex * WHITE_KEY_WIDTH + 1,
                  width: WHITE_KEY_WIDTH - 2,
                  height: WHITE_KEY_HEIGHT,
                  background: highlighted
                    ? `linear-gradient(180deg, ${color}33 0%, ${color}88 100%)`
                    : "linear-gradient(180deg, #fefefe 0%, #e8e8e8 100%)",
                  border: highlighted ? `2px solid ${color}` : "1px solid #ccc",
                  boxShadow: highlighted
                    ? `0 0 16px ${color}44, inset 0 -4px 8px rgba(0,0,0,0.08)`
                    : "inset 0 -4px 8px rgba(0,0,0,0.05), 1px 2px 3px rgba(0,0,0,0.1)",
                  zIndex: 1,
                  paddingBottom: 8,
                }}
              >
                {highlighted && (
                  <span
                    className="text-[11px] font-bold"
                    style={{ color }}
                  >
                    {NOTE_DISPLAY[note]}
                  </span>
                )}
              </div>
            );
          })}

          {/* Black keys */}
          {BLACK_NOTES.map((note) => {
            const highlighted = notes.includes(note);
            const whitesBefore = BLACK_KEY_POSITIONS[note];
            const left = (whitesBefore + 1) * WHITE_KEY_WIDTH - BLACK_KEY_WIDTH / 2;
            return (
              <div
                key={note}
                className="absolute top-0 flex items-end justify-center rounded-b transition-all duration-200"
                style={{
                  left,
                  width: BLACK_KEY_WIDTH,
                  height: BLACK_KEY_HEIGHT,
                  background: highlighted
                    ? `linear-gradient(180deg, ${color} 0%, ${color}dd 100%)`
                    : "linear-gradient(180deg, #2a2a2a 0%, #111 100%)",
                  border: highlighted ? `2px solid ${color}` : "1px solid #000",
                  boxShadow: highlighted
                    ? `0 0 12px ${color}88, inset 0 -3px 6px rgba(0,0,0,0.3)`
                    : "inset 0 -3px 6px rgba(0,0,0,0.4), 2px 2px 4px rgba(0,0,0,0.5)",
                  zIndex: 2,
                  paddingBottom: 6,
                }}
              >
                {highlighted && (
                  <span className="text-[9px] font-bold text-white drop-shadow-sm">
                    {NOTE_DISPLAY[note]}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Note list */}
      <p
        className="text-xs tracking-widest text-center mt-4"
        style={{ color }}
      >
        {notes.map((n) => NOTE_DISPLAY[n] || n).join(" · ")}
      </p>

      {/* Description */}
      <p className="text-xs text-zinc-500 italic text-center mt-1">
        {description}
      </p>
    </div>
  );
}
