/**
 * Clean light background with subtle isometric diamond grid.
 * Cool lavender / pink aesthetic to match iridescent bubble theme.
 */

export function Background() {
  // Isometric grid parameters
  const gridSize = 40;
  const cos30 = Math.cos(Math.PI / 6);
  const sin30 = Math.sin(Math.PI / 6);

  // Build diamond grid lines for the SVG pattern
  // We create a diamond (isometric) grid by drawing two sets of parallel lines
  const gridLines: string[] = [];
  const extent = 3000; // large enough to cover the viewport

  for (let i = -60; i <= 60; i++) {
    const offset = i * gridSize;
    // Lines going top-right to bottom-left (iso-x axis)
    const x1 = -extent * cos30 + offset * cos30;
    const y1 = -extent * sin30 + offset * sin30;
    const x2 = extent * cos30 + offset * cos30;
    const y2 = extent * sin30 + offset * sin30;
    gridLines.push(`M${x1},${y1} L${x2},${y2}`);

    // Lines going top-left to bottom-right (iso-y axis)
    const x3 = extent * cos30 + offset * cos30;
    const y3 = -extent * sin30 + offset * sin30;
    const x4 = -extent * cos30 + offset * cos30;
    const y4 = extent * sin30 + offset * sin30;
    gridLines.push(`M${x3},${y3} L${x4},${y4}`);
  }

  return (
    <>
      {/* Base cool lavender */}
      <div
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 0,
          background: 'linear-gradient(160deg, #f4f0f8 0%, #ede8f2 40%, #e8e2ee 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Isometric diamond grid */}
      <svg
        style={{
          position: 'fixed',
          inset: 0,
          width: '100%',
          height: '100%',
          zIndex: 0,
          pointerEvents: 'none',
          opacity: 0.35,
        }}
        preserveAspectRatio="xMidYMid slice"
      >
        <g transform="translate(960, 500)">
          <path
            d={gridLines.join(' ')}
            fill="none"
            stroke="#c4b8d0"
            strokeWidth={0.5}
          />
        </g>
      </svg>

      {/* Subtle pink radial glow in centre */}
      <div
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 0,
          pointerEvents: 'none',
          background: 'radial-gradient(ellipse at 50% 45%, rgba(216, 128, 176, 0.08) 0%, transparent 60%)',
        }}
      />

      {/* Soft vignette (darken edges subtly) */}
      <div
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 0,
          pointerEvents: 'none',
          background: 'radial-gradient(ellipse at 50% 50%, transparent 40%, rgba(200, 190, 210, 0.25) 100%)',
        }}
      />
    </>
  );
}
