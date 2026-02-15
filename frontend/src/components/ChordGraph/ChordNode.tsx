import { memo } from 'react';
import { motion } from 'framer-motion';
import { useId } from 'react';
import type { ChordNode as ChordNodeType } from '../../types/chord';
import { getChordColor } from '../../utils/chordColors';
import { NoteLabels } from './OrbitingDots';
import ChordKeyboard from '../ChordKeyboard';

interface ChordNodeProps {
  node: ChordNodeType;
  x: number;
  y: number;
  role: 'previous' | 'current' | 'next';
  showNotes?: boolean;
  showKeyboard?: boolean;
  notes?: string[]; // Accept notes as prop from backend
  /** When a suggestion is played, animate from this position (slide up to center) */
  animateFromPosition?: { x: number; y: number };
}

/** Visual config for each role's sphere — iridescent soap bubble style. */
const ROLE_CONFIG = {
  current: {
    radius: 55,
    fontSize: 17,
    fontWeight: 700,
    bodyFill: 'url(#current-body)',
    pearlFill: 'url(#current-pearl)',
    iris2Fill: 'url(#current-iris2)',
    iris3Fill: 'url(#current-iris3)' as string | undefined,
    specFill: 'url(#current-spec)',
    spec2Fill: 'url(#current-spec2)',
    aoFill: 'url(#current-ao)',
    rimFill: 'url(#current-rim)',
    glowFill: 'url(#current-glow)',
    haloFilter: 'url(#sphere-halo)',
    clipId: 'clip-sphere-current',
    floatY: 6,
    floatDuration: 4,
    innerEdgeColor: 'rgba(255, 220, 240, 0.3)',
    causticColor: 'rgba(255, 255, 255, 0.8)',
    causticCount: 3,
    tintOpacity: 0.22,
  },
  next: {
    radius: 40,
    fontSize: 13,
    fontWeight: 600,
    bodyFill: 'url(#next-body)',
    pearlFill: 'url(#next-pearl)',
    iris2Fill: 'url(#next-iris2)',
    iris3Fill: undefined as string | undefined,
    specFill: 'url(#next-spec)',
    spec2Fill: 'url(#next-spec2)',
    aoFill: 'url(#next-ao)',
    rimFill: 'url(#next-rim)',
    glowFill: 'url(#next-glow)',
    haloFilter: 'url(#sphere-halo-next)',
    clipId: 'clip-sphere-next',
    floatY: 4,
    floatDuration: 5,
    innerEdgeColor: 'rgba(255, 215, 235, 0.25)',
    causticColor: 'rgba(255, 255, 255, 0.65)',
    causticCount: 2,
    tintOpacity: 0.18,
  },
  previous: {
    radius: 32,
    fontSize: 11,
    fontWeight: 500,
    bodyFill: 'url(#prev-body)',
    pearlFill: 'url(#prev-pearl)',
    iris2Fill: 'url(#prev-iris2)',
    iris3Fill: undefined as string | undefined,
    specFill: 'url(#prev-spec)',
    spec2Fill: 'url(#prev-spec2)',
    aoFill: 'url(#prev-ao)',
    rimFill: 'url(#prev-rim)',
    glowFill: 'url(#prev-glow)',
    haloFilter: 'url(#sphere-halo-prev)',
    clipId: 'clip-sphere-previous',
    floatY: 3,
    floatDuration: 6,
    innerEdgeColor: 'rgba(240, 220, 232, 0.2)',
    causticColor: 'rgba(255, 255, 255, 0.5)',
    causticCount: 1,
    tintOpacity: 0.12,
  },
};

/**
 * Animated ripple bands that sweep across the sphere surface.
 */
/** Simplified ripples — 2 ellipses, 1 animate each (was 4×3), no filter for perf. */
function SphereRipples({
  radius,
  color,
  strokeColor,
  clipId,
  seed,
}: {
  radius: number;
  color: string;
  strokeColor: string;
  clipId: string;
  seed: number;
}) {
  const ripples = [
    { rx: radius * 0.9, ry: radius * 0.1, yStart: -radius * 0.5, yEnd: radius * 0.5, dur: 7, delay: 0 },
    { rx: radius * 0.75, ry: radius * 0.08, yStart: radius * 0.4, yEnd: -radius * 0.4, dur: 8, delay: 2 },
  ];

  return (
    <g clipPath={`url(#${clipId})`}>
      {ripples.map((r, i) => (
        <ellipse key={i} cx={0} rx={r.rx} ry={r.ry} fill={color} stroke={strokeColor} strokeWidth={0.5} opacity={0.6}>
          <animate
            attributeName="cy"
            values={`${r.yStart};${r.yEnd};${r.yStart}`}
            dur={`${r.dur + seed * 0.3}s`}
            begin={`${r.delay}s`}
            repeatCount="indefinite"
          />
        </ellipse>
      ))}
    </g>
  );
}

/**
 * Tiny bright spots that simulate light caustics / internal refraction.
 */
/** Caustic highlights — static circles, no blur filter, no animate (was 2 animates per spot). */
function CausticHighlights({
  radius,
  color,
  count,
  seed,
}: {
  radius: number;
  color: string;
  count: number;
  seed: number;
}) {
  const spots = Array.from({ length: count }, (_, i) => {
    const angle = ((i * 137.5 + seed * 60) * Math.PI) / 180;
    const dist = radius * (0.2 + (i * 0.15));
    return { cx: Math.cos(angle) * dist, cy: Math.sin(angle) * dist, r: 1.2 + i * 0.4 };
  });

  return (
    <g>
      {spots.map((s, i) => (
        <circle key={i} cx={s.cx} cy={s.cy} r={s.r} fill={color} opacity={0.5} />
      ))}
    </g>
  );
}

function ChordNodeComponentInner({
  node,
  x,
  y,
  role,
  showNotes = true,
  showKeyboard = true,
  notes = [],
  animateFromPosition,
}: ChordNodeProps) {
  const config = ROLE_CONFIG[role];
  const { radius } = config;
  const opacity = role === 'previous' ? 0.75 : 1;
  const uid = useId();
  const seed = node.id.charCodeAt(0) % 5;

  // Get chord-specific colors
  const cc = getChordColor(node.chordId);

  // Unique gradient IDs for this chord instance
  const bodyGradId = `body-${uid}`;
  const glowGradId = `glow-${uid}`;
  const aoGradId = `ao-${uid}`;
  const rimGradId = `rim-${uid}`;
  const pearlGradId = `pearl-${uid}`;

  const labelColor = cc.text;
  const labelShadow = cc.light;
  const noteColor = cc.deep;
  const noteBg = `${cc.base}55`;
  const rippleColor = `${cc.base}44`;
  const rippleStroke = `${cc.deep}30`;
  const shadowColor = `${cc.deep}30`;
  const isSlidingUp = !!animateFromPosition;

  return (
    <motion.g
      style={{ willChange: isSlidingUp ? 'transform' : undefined }}
      initial={
        isSlidingUp
          ? { x: animateFromPosition.x, y: animateFromPosition.y, opacity: 1, scale: 1 }
          : { x, y, opacity: 0, scale: 0.98 }
      }
      animate={{ x, y, opacity, scale: 1 }}
      exit={{ x, y, opacity: 0, scale: 0.98 }}
      transition={{
        duration: isSlidingUp ? 0.4 : 0.22,
        ease: isSlidingUp ? [0.22, 0.61, 0.36, 1] : [0.4, 0, 0.2, 1],
      }}
    >
        <g>
          <animateTransform
            attributeName="transform"
            type="translate"
            values={`0,0; 0,${-config.floatY}; 0,0; 0,${config.floatY * 0.4}; 0,0`}
            dur={`${config.floatDuration}s`}
            repeatCount="indefinite"
          />

          {/* ── Inline defs: dynamic gradients using chord colour ── */}
          <defs>
            <radialGradient id={bodyGradId} cx="40%" cy="35%" r="65%">
              <stop offset="0%" stopColor="#ffffff" />
              <stop offset="20%" stopColor={cc.light} />
              <stop offset="50%" stopColor={cc.base} stopOpacity="0.9" />
              <stop offset="80%" stopColor={cc.deep} stopOpacity="0.85" />
              <stop offset="100%" stopColor={cc.deep} stopOpacity="0.7" />
            </radialGradient>

            <linearGradient id={pearlGradId} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={cc.light} stopOpacity="0" />
              <stop offset="30%" stopColor={cc.base} stopOpacity="0.25" />
              <stop offset="60%" stopColor={cc.light} stopOpacity="0.18" />
              <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
            </linearGradient>

            <radialGradient id={glowGradId} cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor={cc.base} stopOpacity="0.18" />
              <stop offset="50%" stopColor={cc.base} stopOpacity="0.08" />
              <stop offset="100%" stopColor={cc.deep} stopOpacity="0" />
            </radialGradient>

            <radialGradient id={aoGradId} cx="50%" cy="75%" r="50%">
              <stop offset="0%" stopColor={cc.deep} stopOpacity="0.22" />
              <stop offset="60%" stopColor={cc.deep} stopOpacity="0.08" />
              <stop offset="100%" stopColor={cc.deep} stopOpacity="0" />
            </radialGradient>

            <radialGradient id={rimGradId} cx="50%" cy="50%" r="50%">
              <stop offset="80%" stopColor="#ffffff" stopOpacity="0" />
              <stop offset="92%" stopColor={cc.light} stopOpacity="0.25" />
              <stop offset="100%" stopColor={cc.base} stopOpacity="0.35" />
            </radialGradient>
          </defs>

          {/* ── Outer glow halo ── */}
          <circle
            cx={0}
            cy={0}
            r={radius * 1.35}
            fill={`url(#${glowGradId})`}
            filter={config.haloFilter}
          />

          {/* ── Ground shadow — single animate for perf ── */}
          <ellipse
            cx={0}
            cy={radius + 12}
            rx={radius * 0.65}
            ry={radius * 0.15}
            fill={shadowColor}
            filter="url(#sphere-ground-shadow)"
          >
            <animate
              attributeName="opacity"
              values="1;0.85;1"
              dur={`${config.floatDuration}s`}
              repeatCount="indefinite"
            />
          </ellipse>

          {/* ── Sphere body ── */}
          <g filter={`url(#sphere-distort-${role})`}>
            <circle cx={0} cy={0} r={radius} fill={`url(#${bodyGradId})`} />
            <circle cx={0} cy={0} r={radius} fill={`url(#${pearlGradId})`} style={{ mixBlendMode: 'screen' }} />
            {config.iris2Fill && (
              <circle cx={0} cy={0} r={radius} fill={config.iris2Fill} style={{ mixBlendMode: 'screen' }} opacity={0.5} />
            )}
            {config.iris3Fill && (
              <circle cx={0} cy={0} r={radius} fill={config.iris3Fill} style={{ mixBlendMode: 'screen' }} opacity={0.4} />
            )}
            <SphereRipples
              radius={radius}
              color={rippleColor}
              strokeColor={rippleStroke}
              clipId={config.clipId}
              seed={seed}
            />
            <circle cx={0} cy={0} r={radius} fill={`url(#${aoGradId})`} />
            <circle cx={0} cy={0} r={radius} fill={`url(#${rimGradId})`} />
            <circle cx={0} cy={0} r={radius} fill={config.specFill} />
            <circle cx={0} cy={0} r={radius} fill={config.spec2Fill} />
            <CausticHighlights
              radius={radius}
              color={config.causticColor}
              count={config.causticCount}
              seed={seed}
            />
            <circle
              cx={0}
              cy={0}
              r={radius - 0.8}
              fill="none"
              stroke={`${cc.light}50`}
              strokeWidth={1.2}
            />
          </g>

          {/* ── Chord label ── */}
          <text
            textAnchor="middle"
            dominantBaseline="central"
            fill={labelColor}
            fontSize={config.fontSize}
            fontWeight={config.fontWeight}
            fontFamily="'Plus Jakarta Sans', system-ui, sans-serif"
            style={{
              pointerEvents: 'none',
              userSelect: 'none',
              textShadow: `0 0 8px ${labelShadow}`,
            }}
            letterSpacing={0.5}
            y={0}
          >
            {node.chordId}
          </text>

          {/* ── Note labels ── */}
          {showNotes && notes.length > 0 && (
            <NoteLabels
              notes={notes}
              radius={radius}
              role={role}
              noteColor={noteColor}
              noteBg={noteBg}
            />
          )}

          {/* Probability badge for next chords */}
          {role === 'next' && node.probability !== undefined && (
            <g>
              <rect
                x={-14}
                y={radius + 6}
                width={28}
                height={16}
                rx={8}
                fill={`${cc.base}30`}
                stroke={`${cc.deep}50`}
                strokeWidth={0.5}
              />
              <text
                x={0}
                y={radius + 14}
                textAnchor="middle"
                dominantBaseline="central"
                fill={cc.text}
                fontSize={8}
                fontWeight={600}
                fontFamily="'Plus Jakarta Sans', system-ui, sans-serif"
                style={{ pointerEvents: 'none', userSelect: 'none' }}
              >
                {Math.round(node.probability * 100)}%
              </text>
            </g>
          )}

          {/* Chord keyboard below sphere */}
          {showKeyboard && (role === 'current' || role === 'next') && (
            <foreignObject
              x={role === 'current' ? -135 : -135}
              y={radius + (role === 'current' ? 14 : 28)}
              width={role === 'current' ? 270 : 270}
              height={role === 'current' ? 120 : 115}
              style={{ overflow: 'visible' }}
              xmlns="http://www.w3.org/1999/xhtml"
            >
              <div style={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
                <ChordKeyboard
                  name={node.chordId}
                  notes={notes}
                  color={cc.base}
                  description={role === 'next' ? '' : `Notes: ${notes.join(' - ')}`}
                  compact={true}
                  minimal
                  micro={false}
                />
              </div>
            </foreignObject>
          )}
        </g>
      </motion.g>
  );
}

export const ChordNodeComponent = memo(ChordNodeComponentInner);
