"use client";

/**
 * Layered background with mesh gradients, responsive isometric grid,
 * and subtle floating orbs. Clean white base with neutral accents.
 */

export function Background() {
  // Isometric grid parameters
  const gridSize = 40;
  const cos30 = Math.cos(Math.PI / 6);
  const sin30 = Math.sin(Math.PI / 6);

  const gridLines: string[] = [];
  const extent = 3000;

  for (let i = -60; i <= 60; i++) {
    const offset = i * gridSize;
    const x1 = -extent * cos30 + offset * cos30;
    const y1 = -extent * sin30 + offset * sin30;
    const x2 = extent * cos30 + offset * cos30;
    const y2 = extent * sin30 + offset * sin30;
    gridLines.push(`M${x1},${y1} L${x2},${y2}`);

    const x3 = extent * cos30 + offset * cos30;
    const y3 = -extent * sin30 + offset * sin30;
    const x4 = -extent * cos30 + offset * cos30;
    const y4 = extent * sin30 + offset * sin30;
    gridLines.push(`M${x3},${y3} L${x4},${y4}`);
  }

  return (
    <>
      {/* Base mesh gradient — richer, deeper feel */}
      <div
        className="background-base"
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 0,
          pointerEvents: "none",
          background: `
            linear-gradient(160deg, #ffffff 0%, #fafafa 25%, #f5f5f5 50%, #f0f0f0 100%),
            linear-gradient(220deg, rgba(250, 250, 250, 0.6) 0%, transparent 45%),
            linear-gradient(120deg, rgba(245, 245, 245, 0.4) 0%, transparent 50%)
          `,
        }}
      />

      {/* Subtle animated gradient orb (top-left) */}
      <div
        className="background-orb background-orb-1"
        style={{
          position: "fixed",
          width: "clamp(320px, 45vw, 520px)",
          height: "clamp(320px, 45vw, 520px)",
          top: "-10%",
          left: "-5%",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(248, 248, 250, 0.4) 0%, rgba(240, 240, 245, 0.15) 40%, transparent 70%)",
          filter: "blur(40px)",
          zIndex: 0,
          pointerEvents: "none",
        }}
      />

      {/* Subtle animated gradient orb (bottom-right) */}
      <div
        className="background-orb background-orb-2"
        style={{
          position: "fixed",
          width: "clamp(280px, 40vw, 480px)",
          height: "clamp(280px, 40vw, 480px)",
          bottom: "-8%",
          right: "-5%",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(245, 245, 248, 0.35) 0%, rgba(235, 235, 240, 0.12) 45%, transparent 70%)",
          filter: "blur(45px)",
          zIndex: 0,
          pointerEvents: "none",
        }}
      />

      {/* Center warmth orb */}
      <div
        className="background-orb background-orb-3"
        style={{
          position: "fixed",
          width: "clamp(400px, 55vw, 600px)",
          height: "clamp(400px, 55vw, 600px)",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          borderRadius: "50%",
          background: "radial-gradient(ellipse 80% 60% at center, rgba(245, 245, 248, 0.15) 0%, rgba(238, 238, 242, 0.06) 50%, transparent 75%)",
          filter: "blur(50px)",
          zIndex: 0,
          pointerEvents: "none",
        }}
      />

      {/* Isometric diamond grid — centered via SVG viewBox */}
      <svg
        style={{
          position: "fixed",
          inset: 0,
          width: "100%",
          height: "100%",
          zIndex: 0,
          pointerEvents: "none",
          opacity: 0.32,
        }}
        viewBox="0 0 1920 1080"
        preserveAspectRatio="xMidYMid slice"
      >
        <g transform="translate(960, 540)">
          <path d={gridLines.join(" ")} fill="none" stroke="#d4d4d8" strokeWidth={0.6} />
        </g>
      </svg>

      {/* Pink/coral radial glow in centre — stronger accent */}
      <div
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 0,
          pointerEvents: "none",
          background: "radial-gradient(ellipse 80% 50% at 50% 42%, rgba(248, 248, 250, 0.12) 0%, rgba(242, 242, 245, 0.05) 55%, transparent 75%)",
        }}
      />

      {/* Soft vignette */}
      <div
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 0,
          pointerEvents: "none",
          background: "radial-gradient(ellipse 90% 85% at 50% 50%, transparent 35%, rgba(220, 220, 225, 0.15) 100%)",
        }}
      />

      {/* Subtle noise texture overlay for depth */}
      <div
        className="background-noise"
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 0,
          pointerEvents: "none",
          opacity: 0.025,
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
        }}
      />
    </>
  );
}
