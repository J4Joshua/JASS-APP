import { AnimatePresence } from 'framer-motion';
import type { ChordGraphState } from '../../types/chord';
import { GlowDefs } from './GlowDefs';
import { ChordNodeComponent } from './ChordNode';
import { ChordEdge } from './ChordEdge';

interface ChordGraphProps {
  state: ChordGraphState;
  showNotes?: boolean;
  keyboardMode?: boolean;
  notesMap?: Record<string, string[]>; // Map chord IDs to their notes
  /** Live held notes from backend - used for current chord's piano keys (activates based on actual MIDI input) */
  activeNotes?: string[];
}

const VIEWBOX_W = 1000;
const VIEWBOX_H = 900;
const CENTER = { x: VIEWBOX_W / 2, y: 280 };

/**
 * Slot positions — current chord is centre,
 * next chords sit in a row below.
 */
const SLOT_POSITIONS = {
  'center': { x: 0, y: 0 },
  'next-0': { x: -270, y: 280 },
  'next-1': { x: 0, y: 280 },
  'next-2': { x: 270, y: 280 },
} as const;

type SlotId = keyof typeof SLOT_POSITIONS;

function getAbsPos(slot: SlotId) {
  return {
    x: CENTER.x + SLOT_POSITIONS[slot].x,
    y: CENTER.y + SLOT_POSITIONS[slot].y,
  };
}

/** Subtle floating particles for ambient depth. */
function AmbientParticles() {
  const particles = Array.from({ length: 20 }, (_, i) => {
    const isBright = i < 4;
    return {
      id: i,
      cx: Math.random() * VIEWBOX_W,
      cy: Math.random() * VIEWBOX_H,
      r: isBright ? 1.5 + Math.random() * 2 : 0.5 + Math.random() * 1,
      opacity: isBright ? 0.08 + Math.random() * 0.06 : 0.03 + Math.random() * 0.04,
      dur: 10 + Math.random() * 16,
      delay: Math.random() * 12,
      fill: isBright
        ? ['#f0a0c8', '#d880b0', '#e8b0d0', '#c890c0'][i % 4]
        : 'rgba(200, 180, 195, 0.5)',
    };
  });

  return (
    <g>
      {particles.map((p) => (
        <circle key={p.id} cx={p.cx} cy={p.cy} r={p.r} fill={p.fill} opacity={p.opacity}>
          <animate
            attributeName="opacity"
            values={`${p.opacity};${p.opacity * 1.8};${p.opacity}`}
            dur={`${p.dur}s`}
            begin={`${p.delay}s`}
            repeatCount="indefinite"
          />
          <animate
            attributeName="cy"
            values={`${p.cy};${p.cy - 8};${p.cy}`}
            dur={`${p.dur * 1.3}s`}
            begin={`${p.delay}s`}
            repeatCount="indefinite"
          />
        </circle>
      ))}
    </g>
  );
}

export function ChordGraph({
  state,
  showNotes = true,
  keyboardMode = false,
  notesMap = {},
  activeNotes,
}: ChordGraphProps) {
  const { current, next } = state;

  const allNodes = [
    { node: current, slot: 'center' as SlotId, role: 'current' as const },
    ...next.map((node, i) => ({
      node,
      slot: `next-${i}` as SlotId,
      role: 'next' as const,
    })),
  ];

  const centerPos = getAbsPos('center');
  const edges = [
    ...next.map((node, i) => ({
      key: `edge-next-${node.id}`,
      from: centerPos,
      to: getAbsPos(`next-${i}` as SlotId),
      variant: 'next' as const,
    })),
  ];

  return (
    <svg
      viewBox={`0 0 ${VIEWBOX_W} ${VIEWBOX_H}`}
      style={{
        width: '100%',
        height: '100%',
        display: 'block',
        position: 'relative',
        zIndex: 2,
      }}
      preserveAspectRatio="xMidYMid meet"
    >
      <GlowDefs />

      {/* Subtle radial rings */}
      <circle
        cx={CENTER.x}
        cy={CENTER.y}
        r={180}
        fill="none"
        stroke="rgba(200, 180, 195, 0.12)"
        strokeWidth={0.5}
      />
      <circle
        cx={CENTER.x}
        cy={CENTER.y}
        r={320}
        fill="none"
        stroke="rgba(200, 180, 195, 0.07)"
        strokeWidth={0.5}
        strokeDasharray="4 12"
      />

      {/* Direction label */}
      <text
        x={CENTER.x}
        y={CENTER.y + 220}
        fill="rgba(130, 100, 120, 0.3)"
        fontSize={10}
        fontWeight={500}
        fontFamily="'Plus Jakarta Sans', system-ui, sans-serif"
        letterSpacing={2}
        textAnchor="middle"
      >
        NEXT
      </text>

      {/* Floating ambient particles */}
      <AmbientParticles />

      {/* Edges layer */}
      <AnimatePresence mode="popLayout">
        {edges.map((edge) => (
          <ChordEdge
            key={edge.key}
            edgeKey={edge.key}
            fromX={edge.from.x}
            fromY={edge.from.y}
            toX={edge.to.x}
            toY={edge.to.y}
            variant={edge.variant}
          />
        ))}
      </AnimatePresence>

      {/* Nodes layer */}
      <AnimatePresence mode="popLayout">
        {allNodes.map(({ node, slot, role }) => {
          const pos = getAbsPos(slot);
          // Current chord: use live activeNotes from backend (actual held keys); others: use notesMap (chord spellings)
          const notes =
            role === "current" && activeNotes !== undefined
              ? activeNotes
              : (notesMap[node.chordId] || []);
          return (
            <ChordNodeComponent
              key={node.id}
              node={node}
              x={pos.x}
              y={pos.y}
              role={role}
              showNotes={showNotes}
              showKeyboard={keyboardMode}
              notes={notes}
            />
          );
        })}
      </AnimatePresence>
    </svg>
  );
}
