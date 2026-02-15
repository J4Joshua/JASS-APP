/**
 * Note labels that appear around the chord sphere.
 * Each note gets a small badge positioned in a circle around the bubble.
 */

interface NoteLabelsProps {
  notes: string[];
  radius: number;
  role: 'previous' | 'current' | 'next';
  noteColor: string;
  noteBg: string;
}

export function NoteLabels({ notes, radius, role, noteColor, noteBg }: NoteLabelsProps) {
  // Different orbit radius based on role
  const orbitRadius = role === 'current' ? radius + 32 : radius + 26;
  const fontSize = role === 'current' ? 9 : 7;
  const badgeSize = role === 'current' ? 18 : 14;

  return (
    <g>
      {notes.map((note, i) => {
        // Distribute notes evenly around the circle
        const angle = (i / notes.length) * 2 * Math.PI - Math.PI / 2;
        const x = Math.cos(angle) * orbitRadius;
        const y = Math.sin(angle) * orbitRadius;

        return (
          <g key={`${note}-${i}`}>
            {/* Note badge background */}
            <circle
              cx={x}
              cy={y}
              r={badgeSize / 2}
              fill={noteBg}
              stroke={noteColor}
              strokeWidth={0.5}
            />
            {/* Note label */}
            <text
              x={x}
              y={y}
              textAnchor="middle"
              dominantBaseline="central"
              fill={noteColor}
              fontSize={fontSize}
              fontWeight={600}
              fontFamily="'Plus Jakarta Sans', system-ui, sans-serif"
              style={{ pointerEvents: 'none', userSelect: 'none' }}
            >
              {note}
            </text>
          </g>
        );
      })}
    </g>
  );
}
