import { memo } from 'react';
import { motion } from 'framer-motion';

interface ChordEdgeProps {
  edgeKey: string;
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
  variant: 'previous' | 'next';
}

function ChordEdgeInner({ edgeKey, fromX, fromY, toX, toY, variant }: ChordEdgeProps) {
  // Calculate control points for a smooth curve
  const dx = toX - fromX;
  const dy = toY - fromY;
  const midX = fromX + dx / 2;
  const midY = fromY + dy / 2;

  // Curved path (quadratic bezier)
  const pathD = `M ${fromX},${fromY} Q ${midX},${midY - 40} ${toX},${toY}`;

  // Color based on variant
  const strokeColor = variant === 'next' ? 'rgba(216, 128, 176, 0.25)' : 'rgba(192, 144, 216, 0.25)';
  const strokeWidth = variant === 'next' ? 2 : 1.5;

  return (
    <motion.g
      key={edgeKey}
      initial={{ opacity: 0, pathLength: 0 }}
      animate={{ opacity: 1, pathLength: 1 }}
      exit={{ opacity: 0, pathLength: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
    >
      {/* Glow layer — no filter for perf */}
      <motion.path
        d={pathD}
        fill="none"
        stroke={strokeColor}
        strokeWidth={strokeWidth + 4}
        strokeLinecap="round"
        opacity={0.25}
      />
      {/* Main line */}
      <motion.path
        d={pathD}
        fill="none"
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeDasharray="4 8"
      />
    </motion.g>
  );
}

export const ChordEdge = memo(ChordEdgeInner);
