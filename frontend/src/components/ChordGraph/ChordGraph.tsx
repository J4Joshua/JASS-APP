import { AnimatePresence } from 'framer-motion';
import type { ChordGraphState } from '../../types/chord';
import { GlowDefs } from './GlowDefs';
import { ChordNodeComponent } from './ChordNode';
import { ChordEdge } from './ChordEdge';

interface ChordGraphProps {
  state: ChordGraphState;
  previousState?: ChordGraphState | null;
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

/** Subtle floating particles — memoized with fixed seed to avoid re-creating on each render. */
const AMBIENT_PARTICLES = (() => {
  const seed = (s: number) => (((s * 9301 + 49297) % 233280) / 233280);
  let s = 12345;
  return Array.from({ length: 12 }, (_, i) => {
    s = seed(s) * 233280;
    const cx = seed(s) * VIEWBOX_W;
    s = seed(s) * 233280;
    const cy = seed(s) * VIEWBOX_H;
    const isBright = i < 3;
    return {
      id: i,
      cx,
      cy,
      r: isBright ? 1.5 : 0.8,
      opacity: isBright ? 0.1 : 0.04,
      dur: 12 + (i % 5) * 2,
      delay: (i % 7) * 1.5,
      fill: isBright
        ? ['#f0a0c8', '#d880b0', '#e8b0d0'][i % 3]
        : 'rgba(200, 180, 195, 0.5)',
    };
  });
})();

function AmbientParticles() {
  return (
    <g>
      {AMBIENT_PARTICLES.map((p) => (
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
  previousState,
  showNotes = true,
  keyboardMode = false,
  notesMap = {},
  activeNotes,
}: ChordGraphProps) {
  const { current, next } = state;

  // When a suggestion is played, it becomes current — find which slot it came from for slide-up animation
  const promotedFrom =
    previousState &&
    current.chordId !== previousState.current.chordId &&
    previousState.next.some((n) => n.chordId === current.chordId)
      ? previousState.next.findIndex((n) => n.chordId === current.chordId)
      : -1;
  const centerPos = getAbsPos('center');
  const promotedInitialPosition =
    promotedFrom >= 0 ? getAbsPos(`next-${promotedFrom}` as SlotId) : undefined;

  const allNodes = [
    { node: current, slot: 'center' as SlotId, role: 'current' as const },
    ...next.map((node, i) => ({
      node,
      slot: `next-${i}` as SlotId,
      role: 'next' as const,
    })),
  ];

  const edges = next.map((node, i) => ({
    key: `edge-next-${i}`,
    from: centerPos,
    to: getAbsPos(`next-${i}` as SlotId),
    variant: 'next' as const,
  }));

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

      {/* Nodes layer — stable keys (slot + chordId) so only changed chords animate */}
      <AnimatePresence mode="popLayout">
        {allNodes.map(({ node, slot, role }) => {
          const pos = getAbsPos(slot);
          // Current chord: use live activeNotes when available; otherwise fall back to notesMap (covers initial load + first chord)
          const notes =
            role === "current"
              ? ((activeNotes?.length ?? 0) > 0 ? (activeNotes ?? []) : (notesMap[node.chordId] || []))
              : (notesMap[node.chordId] || []);
          const isPromoted = role === 'current' && promotedFrom >= 0 && promotedInitialPosition;
          return (
            <ChordNodeComponent
              key={`${slot}-${node.chordId}`}
              node={node}
              x={pos.x}
              y={pos.y}
              role={role}
              showNotes={showNotes}
              showKeyboard={keyboardMode}
              notes={notes}
              animateFromPosition={isPromoted ? promotedInitialPosition : undefined}
            />
          );
        })}
      </AnimatePresence>
    </svg>
  );
}
