import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
  Easing,
} from "remotion";

// --- Types ---

export type MapVariant =
  | "illustrated-map"
  | "3d-geographic"
  | "region-highlight"
  | "connection-arc";

export interface LocationPoint {
  name: string;
  /** Normalized X position (0-1, left to right) */
  x: number;
  /** Normalized Y position (0-1, top to bottom) */
  y: number;
}

export interface Connection {
  from: number;
  to: number;
}

export interface MapCompositionProps {
  variant: MapVariant;
  title: string;
  locations: LocationPoint[];
  connections: Connection[];
  durationSeconds?: number;
}

// --- Color palettes per variant ---

const PALETTES: Record<MapVariant, { bg: string; glow: string; label: string; accent: string; grid: string }> = {
  "illustrated-map": {
    bg: "#0a0a0a",
    glow: "#e8c547",
    label: "#f5f0e1",
    accent: "#c4392d",
    grid: "#1a1a14",
  },
  "3d-geographic": {
    bg: "#050510",
    glow: "#00ffcc",
    label: "#e0e0e0",
    accent: "#ff3366",
    grid: "#0a0a20",
  },
  "region-highlight": {
    bg: "#080808",
    glow: "#00ccff",
    label: "#ffffff",
    accent: "#00ccff",
    grid: "#111118",
  },
  "connection-arc": {
    bg: "#060612",
    glow: "#66ff33",
    label: "#d0d0d0",
    accent: "#ffcc00",
    grid: "#0d0d1a",
  },
};

// --- Sub-components ---

/** Animated grid background for depth */
const GridBackground: React.FC<{ color: string; frame: number; fps: number }> = ({
  color,
  frame,
  fps,
}) => {
  const opacity = interpolate(frame, [0, fps * 0.5], [0, 0.3], {
    extrapolateRight: "clamp",
  });
  const lines: React.ReactElement[] = [];

  // Vertical lines
  for (let x = 0; x <= 1920; x += 120) {
    lines.push(
      <line
        key={`v-${x}`}
        x1={x}
        y1={0}
        x2={x}
        y2={1080}
        stroke={color}
        strokeWidth={0.5}
      />
    );
  }
  // Horizontal lines
  for (let y = 0; y <= 1080; y += 120) {
    lines.push(
      <line
        key={`h-${y}`}
        x1={0}
        y1={y}
        x2={1920}
        y2={y}
        stroke={color}
        strokeWidth={0.5}
      />
    );
  }

  return <g opacity={opacity}>{lines}</g>;
};

/** Glowing marker dot with spring animation */
const GlowingMarker: React.FC<{
  cx: number;
  cy: number;
  color: string;
  delay: number;
  frame: number;
  fps: number;
}> = ({ cx, cy, color, delay, frame, fps }) => {
  const scale = spring({
    frame: frame - delay,
    fps,
    config: { damping: 12, stiffness: 120, mass: 0.8 },
  });

  const pulsePhase = Math.max(0, frame - delay - fps * 0.3);
  const pulse = 1 + Math.sin(pulsePhase * 0.15) * 0.15;

  return (
    <g transform={`translate(${cx}, ${cy}) scale(${scale})`}>
      {/* Outer glow */}
      <circle
        r={28 * pulse}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        opacity={0.25}
      />
      {/* Mid glow */}
      <circle r={18 * pulse} fill={color} opacity={0.15} />
      {/* Core */}
      <circle r={8} fill={color} />
      {/* Bright center */}
      <circle r={3} fill="#ffffff" opacity={0.9} />
    </g>
  );
};

/** Animated label that fades in after the marker */
const AnimatedLabel: React.FC<{
  x: number;
  y: number;
  text: string;
  color: string;
  delay: number;
  frame: number;
  fps: number;
  align?: "left" | "right";
}> = ({ x, y, text, color, delay, frame, fps, align = "left" }) => {
  const labelDelay = delay + Math.floor(fps * 0.25);
  const opacity = interpolate(frame - labelDelay, [0, fps * 0.3], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const slideX = interpolate(frame - labelDelay, [0, fps * 0.3], [20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  const offsetX = align === "right" ? x - 20 - slideX : x + 20 + slideX;
  const anchor = align === "right" ? "end" : "start";

  return (
    <g opacity={opacity}>
      <text
        x={offsetX}
        y={y + 5}
        fill={color}
        fontFamily="Arial, Helvetica, sans-serif"
        fontWeight="bold"
        fontSize={28}
        textAnchor={anchor}
        style={{
          textShadow: `0 0 12px ${color}, 0 0 24px ${color}`,
        }}
      >
        {text.toUpperCase()}
      </text>
    </g>
  );
};

/** Connection arc that draws progressively */
const ConnectionArc: React.FC<{
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  color: string;
  delay: number;
  frame: number;
  fps: number;
}> = ({ x1, y1, x2, y2, color, delay, frame, fps }) => {
  const progress = interpolate(frame - delay, [0, fps * 0.8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // Curved arc — control point above the midpoint
  const mx = (x1 + x2) / 2;
  const my = Math.min(y1, y2) - 80;
  const path = `M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`;

  // Approximate arc length for dash animation
  const dx = x2 - x1;
  const dy = y2 - y1;
  const arcLen = Math.sqrt(dx * dx + dy * dy) * 1.3;

  return (
    <g>
      {/* Trail glow */}
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth={4}
        opacity={0.2}
        strokeDasharray={arcLen}
        strokeDashoffset={arcLen * (1 - progress)}
      />
      {/* Main arc */}
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth={2}
        opacity={0.8}
        strokeDasharray={arcLen}
        strokeDashoffset={arcLen * (1 - progress)}
      />
    </g>
  );
};

/** Stylized region outline (simplified polygon) */
const RegionOutline: React.FC<{
  color: string;
  frame: number;
  fps: number;
}> = ({ color, frame, fps }) => {
  const drawProgress = interpolate(frame, [0, fps * 0.6], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // Simplified abstract region shape centered on canvas
  const points =
    "700,350 780,280 900,260 1020,290 1100,340 1150,420 1180,520 1160,620 1100,700 1000,740 880,760 760,730 680,660 660,560 670,450";
  const pathLen = 1800; // approximate

  return (
    <g>
      <polygon
        points={points}
        fill="none"
        stroke={color}
        strokeWidth={2}
        opacity={0.5}
        strokeDasharray={pathLen}
        strokeDashoffset={pathLen * (1 - drawProgress)}
      />
      <polygon
        points={points}
        fill={color}
        opacity={0.03 * drawProgress}
      />
    </g>
  );
};

/** Title text at the bottom */
const TitleOverlay: React.FC<{
  title: string;
  color: string;
  frame: number;
  fps: number;
  totalFrames: number;
}> = ({ title, color, frame, fps, totalFrames }) => {
  const fadeIn = interpolate(frame, [fps * 0.5, fps * 1.0], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(
    frame,
    [totalFrames - fps * 0.5, totalFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const opacity = Math.min(fadeIn, fadeOut);

  return (
    <text
      x={960}
      y={980}
      fill={color}
      fontFamily="Arial, Helvetica, sans-serif"
      fontWeight="bold"
      fontSize={42}
      textAnchor="middle"
      opacity={opacity}
      style={{
        textShadow: `0 0 16px ${color}, 0 0 32px ${color}`,
      }}
    >
      {title.toUpperCase()}
    </text>
  );
};

// --- Main Composition ---

export const MapComposition: React.FC<MapCompositionProps> = ({
  variant,
  title,
  locations,
  connections,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width, height } = useVideoConfig();
  const palette = PALETTES[variant];

  // Clamp to max 3 locations per VISUAL_STYLE_GUIDE rule
  const visibleLocations = locations.slice(0, 3);

  // Convert normalized coordinates (0-1) to pixel positions with padding
  const padX = 200;
  const padY = 150;
  const toPixel = (loc: LocationPoint) => ({
    px: padX + loc.x * (width - 2 * padX),
    py: padY + loc.y * (height - 2 * padY),
  });

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: palette.bg,
        overflow: "hidden",
        position: "relative",
      }}
    >
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Grid background */}
        <GridBackground color={palette.grid} frame={frame} fps={fps} />

        {/* Region outline for region-highlight and illustrated-map variants */}
        {(variant === "region-highlight" || variant === "illustrated-map") && (
          <RegionOutline color={palette.accent} frame={frame} fps={fps} />
        )}

        {/* Connection arcs */}
        {connections.map((conn, i) => {
          const fromLoc = visibleLocations[conn.from];
          const toLoc = visibleLocations[conn.to];
          if (!fromLoc || !toLoc) return null;
          const from = toPixel(fromLoc);
          const to = toPixel(toLoc);
          return (
            <ConnectionArc
              key={`conn-${i}`}
              x1={from.px}
              y1={from.py}
              x2={to.px}
              y2={to.py}
              color={palette.accent}
              delay={Math.floor(fps * 0.8)}
              frame={frame}
              fps={fps}
            />
          );
        })}

        {/* Location markers */}
        {visibleLocations.map((loc, i) => {
          const { px, py } = toPixel(loc);
          const delay = Math.floor(fps * 0.3) + i * Math.floor(fps * 0.2);
          const labelAlign = loc.x > 0.6 ? "right" : "left";
          return (
            <g key={`loc-${i}`}>
              <GlowingMarker
                cx={px}
                cy={py}
                color={palette.glow}
                delay={delay}
                frame={frame}
                fps={fps}
              />
              <AnimatedLabel
                x={px}
                y={py}
                text={loc.name}
                color={palette.label}
                delay={delay}
                frame={frame}
                fps={fps}
                align={labelAlign}
              />
            </g>
          );
        })}

        {/* Title overlay */}
        <TitleOverlay
          title={title}
          color={palette.label}
          frame={frame}
          fps={fps}
          totalFrames={durationInFrames}
        />
      </svg>
    </div>
  );
};
