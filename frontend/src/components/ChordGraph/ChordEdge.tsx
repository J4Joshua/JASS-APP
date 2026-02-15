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

  // Color based on variant — visible but subtle behind spheres
  const strokeColor = variant === 'next' ? 'rgba(216, 128, 176, 0.4)' : 'rgba(192, 144, 216, 0.4)';
  const strokeWidth = variant === 'next' ? 2.5 : 2;

  const pathTransition = { duration: 0.5, ease: 'easeOut' as const };

  return (
    <motion.g
      key={edgeKey}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Glow layer — subtle backdrop */}
      <motion.path
        d={pathD}
        fill="none"
        stroke={strokeColor}
        strokeWidth={strokeWidth + 6}
        strokeLinecap="round"
        opacity={0.3}
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={pathTransition}
      />
      {/* Main line — draws in behind the spheres */}
      <motion.path
        d={pathD}
        fill="none"
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        exit={{ pathLength: 0 }}
        transition={pathTransition}
      />
    </motion.g>
  );
}

export const ChordEdge = memo(ChordEdgeInner);
