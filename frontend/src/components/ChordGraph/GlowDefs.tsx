/**
 * SVG filter and gradient definitions for the iridescent sphere effects.
 *
 * These are shared across all chord nodes and edges, so they're defined
 * once at the top of the SVG and referenced by id.
 */

export function GlowDefs() {
  return (
    <defs>
      {/* ── Blur filters ────────────────────────────────────────── */}

      {/* Ground shadow blur */}
      <filter id="sphere-ground-shadow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur in="SourceAlpha" stdDeviation="3" />
        <feOffset dx="0" dy="1" />
        <feComponentTransfer>
          <feFuncA type="linear" slope="0.3" />
        </feComponentTransfer>
        <feMerge>
          <feMergeNode />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>

      {/* Outer halo blur for current chord */}
      <filter id="sphere-halo" x="-100%" y="-100%" width="300%" height="300%">
        <feGaussianBlur in="SourceGraphic" stdDeviation="12" />
      </filter>

      {/* Halo for next chords (smaller) */}
      <filter id="sphere-halo-next" x="-100%" y="-100%" width="300%" height="300%">
        <feGaussianBlur in="SourceGraphic" stdDeviation="8" />
      </filter>

      {/* Halo for previous chords (smaller) */}
      <filter id="sphere-halo-prev" x="-100%" y="-100%" width="300%" height="300%">
        <feGaussianBlur in="SourceGraphic" stdDeviation="6" />
      </filter>

      {/* Ripple blur */}
      <filter id="ripple-blur">
        <feGaussianBlur in="SourceGraphic" stdDeviation="0.8" />
      </filter>

      {/* Caustic highlight blur */}
      <filter id="caustic-blur">
        <feGaussianBlur in="SourceGraphic" stdDeviation="1.2" />
      </filter>

      {/* ── Distortion filters (liquid wobble) ──────────────────── */}

      {/* Current chord distortion */}
      <filter id="sphere-distort-current">
        <feTurbulence
          type="fractalNoise"
          baseFrequency="0.015"
          numOctaves="2"
          seed="42"
        >
          <animate
            attributeName="baseFrequency"
            values="0.015;0.018;0.015"
            dur="8s"
            repeatCount="indefinite"
          />
        </feTurbulence>
        <feDisplacementMap in="SourceGraphic" scale="2.5" />
      </filter>

      {/* Next chord distortion */}
      <filter id="sphere-distort-next">
        <feTurbulence
          type="fractalNoise"
          baseFrequency="0.018"
          numOctaves="2"
          seed="73"
        >
          <animate
            attributeName="baseFrequency"
            values="0.018;0.021;0.018"
            dur="9s"
            repeatCount="indefinite"
          />
        </feTurbulence>
        <feDisplacementMap in="SourceGraphic" scale="2" />
      </filter>

      {/* Previous chord distortion */}
      <filter id="sphere-distort-previous">
        <feTurbulence
          type="fractalNoise"
          baseFrequency="0.02"
          numOctaves="1"
          seed="91"
        />
        <feDisplacementMap in="SourceGraphic" scale="1.5" />
      </filter>

      {/* ── Gradient definitions (static, role-based) ──────────── */}

      {/* Current chord gradients */}
      <radialGradient id="current-body" cx="42%" cy="35%" r="68%">
        <stop offset="0%" stopColor="#ffffff" />
        <stop offset="25%" stopColor="#f8e8f4" />
        <stop offset="55%" stopColor="#e8c0dc" />
        <stop offset="85%" stopColor="#d8a0d0" />
        <stop offset="100%" stopColor="#c890c0" stopOpacity="0.85" />
      </radialGradient>

      <linearGradient id="current-pearl" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#ffffff" stopOpacity="0" />
        <stop offset="35%" stopColor="#f0d0e8" stopOpacity="0.3" />
        <stop offset="65%" stopColor="#e8b8dc" stopOpacity="0.2" />
        <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
      </linearGradient>

      <linearGradient id="current-iris2" x1="100%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stopColor="#d8b0e0" stopOpacity="0" />
        <stop offset="40%" stopColor="#c898d0" stopOpacity="0.25" />
        <stop offset="100%" stopColor="#b888c0" stopOpacity="0" />
      </linearGradient>

      <linearGradient id="current-iris3" x1="0%" y1="100%" x2="100%" y2="0%">
        <stop offset="0%" stopColor="#e8a0c8" stopOpacity="0" />
        <stop offset="50%" stopColor="#d888b8" stopOpacity="0.18" />
        <stop offset="100%" stopColor="#c080a8" stopOpacity="0" />
      </linearGradient>

      <radialGradient id="current-spec" cx="35%" cy="30%" r="25%">
        <stop offset="0%" stopColor="#ffffff" stopOpacity="0.85" />
        <stop offset="40%" stopColor="#ffffff" stopOpacity="0.4" />
        <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
      </radialGradient>

      <radialGradient id="current-spec2" cx="60%" cy="25%" r="18%">
        <stop offset="0%" stopColor="#ffffff" stopOpacity="0.6" />
        <stop offset="50%" stopColor="#f8f0fc" stopOpacity="0.25" />
        <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
      </radialGradient>

      <radialGradient id="current-ao" cx="50%" cy="80%" r="55%">
        <stop offset="0%" stopColor="#c080b0" stopOpacity="0.25" />
        <stop offset="65%" stopColor="#a868a0" stopOpacity="0.12" />
        <stop offset="100%" stopColor="#906090" stopOpacity="0" />
      </radialGradient>

      <radialGradient id="current-rim" cx="50%" cy="50%" r="50%">
        <stop offset="78%" stopColor="#ffffff" stopOpacity="0" />
        <stop offset="90%" stopColor="#f8e8f4" stopOpacity="0.3" />
        <stop offset="100%" stopColor="#e8d0e8" stopOpacity="0.4" />
      </radialGradient>

      <radialGradient id="current-glow" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stopColor="#e8a0d0" stopOpacity="0.2" />
        <stop offset="50%" stopColor="#d888c0" stopOpacity="0.1" />
        <stop offset="100%" stopColor="#c870b0" stopOpacity="0" />
      </radialGradient>

      {/* Next chord gradients (slightly smaller, cooler tones) */}
      <radialGradient id="next-body" cx="40%" cy="35%" r="65%">
        <stop offset="0%" stopColor="#ffffff" />
        <stop offset="30%" stopColor="#f0e8f8" />
        <stop offset="60%" stopColor="#d8c0e8" />
        <stop offset="90%" stopColor="#c0a0d8" />
        <stop offset="100%" stopColor="#b090c8" stopOpacity="0.8" />
      </radialGradient>

      <linearGradient id="next-pearl" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#ffffff" stopOpacity="0" />
        <stop offset="40%" stopColor="#e8d0f0" stopOpacity="0.25" />
        <stop offset="100%" stopColor="#d8b8e8" stopOpacity="0" />
      </linearGradient>

      <linearGradient id="next-iris2" x1="100%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stopColor="#c8a8e0" stopOpacity="0" />
        <stop offset="50%" stopColor="#b898d0" stopOpacity="0.2" />
        <stop offset="100%" stopColor="#a888c0" stopOpacity="0" />
      </linearGradient>

      <radialGradient id="next-spec" cx="32%" cy="28%" r="22%">
        <stop offset="0%" stopColor="#ffffff" stopOpacity="0.75" />
        <stop offset="50%" stopColor="#ffffff" stopOpacity="0.3" />
        <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
      </radialGradient>

      <radialGradient id="next-spec2" cx="58%" cy="22%" r="15%">
        <stop offset="0%" stopColor="#ffffff" stopOpacity="0.5" />
        <stop offset="60%" stopColor="#f0e8f8" stopOpacity="0.2" />
        <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
      </radialGradient>

      <radialGradient id="next-ao" cx="50%" cy="75%" r="50%">
        <stop offset="0%" stopColor="#b080c0" stopOpacity="0.2" />
        <stop offset="70%" stopColor="#9868b0" stopOpacity="0.1" />
        <stop offset="100%" stopColor="#8060a0" stopOpacity="0" />
      </radialGradient>

      <radialGradient id="next-rim" cx="50%" cy="50%" r="50%">
        <stop offset="80%" stopColor="#ffffff" stopOpacity="0" />
        <stop offset="92%" stopColor="#e8d8f0" stopOpacity="0.25" />
        <stop offset="100%" stopColor="#d8c8e8" stopOpacity="0.35" />
      </radialGradient>

      <radialGradient id="next-glow" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stopColor="#d8a0e0" stopOpacity="0.18" />
        <stop offset="60%" stopColor="#c888d0" stopOpacity="0.08" />
        <stop offset="100%" stopColor="#b870c0" stopOpacity="0" />
      </radialGradient>

      {/* Previous chord gradients (smaller, more muted) */}
      <radialGradient id="prev-body" cx="40%" cy="35%" r="60%">
        <stop offset="0%" stopColor="#f8f4fc" />
        <stop offset="40%" stopColor="#e0d0e8" />
        <stop offset="80%" stopColor="#c8b0d0" />
        <stop offset="100%" stopColor="#b098c0" stopOpacity="0.75" />
      </radialGradient>

      <linearGradient id="prev-pearl" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#ffffff" stopOpacity="0" />
        <stop offset="50%" stopColor="#e0d0e8" stopOpacity="0.2" />
        <stop offset="100%" stopColor="#d0c0e0" stopOpacity="0" />
      </linearGradient>

      <linearGradient id="prev-iris2" x1="100%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stopColor="#c0a0d0" stopOpacity="0" />
        <stop offset="60%" stopColor="#b090c0" stopOpacity="0.15" />
        <stop offset="100%" stopColor="#a080b0" stopOpacity="0" />
      </linearGradient>

      <radialGradient id="prev-spec" cx="30%" cy="26%" r="20%">
        <stop offset="0%" stopColor="#ffffff" stopOpacity="0.6" />
        <stop offset="60%" stopColor="#ffffff" stopOpacity="0.2" />
        <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
      </radialGradient>

      <radialGradient id="prev-spec2" cx="55%" cy="20%" r="12%">
        <stop offset="0%" stopColor="#ffffff" stopOpacity="0.4" />
        <stop offset="70%" stopColor="#f0e8f4" stopOpacity="0.15" />
        <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
      </radialGradient>

      <radialGradient id="prev-ao" cx="50%" cy="70%" r="45%">
        <stop offset="0%" stopColor="#a870b0" stopOpacity="0.15" />
        <stop offset="75%" stopColor="#9060a0" stopOpacity="0.08" />
        <stop offset="100%" stopColor="#805090" stopOpacity="0" />
      </radialGradient>

      <radialGradient id="prev-rim" cx="50%" cy="50%" r="50%">
        <stop offset="82%" stopColor="#ffffff" stopOpacity="0" />
        <stop offset="94%" stopColor="#e0d0e8" stopOpacity="0.2" />
        <stop offset="100%" stopColor="#d0c0e0" stopOpacity="0.3" />
      </radialGradient>

      <radialGradient id="prev-glow" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stopColor="#d098d8" stopOpacity="0.15" />
        <stop offset="65%" stopColor="#c080c8" stopOpacity="0.06" />
        <stop offset="100%" stopColor="#b068b8" stopOpacity="0" />
      </radialGradient>

      {/* ── Clipping paths for sphere ripples ──────────────────── */}

      <clipPath id="clip-sphere-current">
        <circle cx="0" cy="0" r="55" />
      </clipPath>

      <clipPath id="clip-sphere-next">
        <circle cx="0" cy="0" r="40" />
      </clipPath>

      <clipPath id="clip-sphere-previous">
        <circle cx="0" cy="0" r="32" />
      </clipPath>
    </defs>
  );
}
