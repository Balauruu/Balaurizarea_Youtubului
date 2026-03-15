---
id: T01
parent: S04
milestone: M002
provides:
  - Self-contained Remotion Node.js project that renders animated map .mp4 clips from props JSON
  - MapComposition component handling all 4 VISUAL_STYLE_GUIDE map variants
key_files:
  - .claude/skills/animation/remotion/package.json
  - .claude/skills/animation/remotion/src/MapComposition.tsx
  - .claude/skills/animation/remotion/src/Root.tsx
key_decisions:
  - Used calculateMetadata to derive durationInFrames from props.durationSeconds — allows Python CLI to control clip length via props JSON without hardcoding frame counts
  - Single MapComposition component with variant prop + PALETTES lookup instead of 4 separate components — reduces duplication, all variants share the same animation logic
  - SVG-based rendering (not canvas) — composable, debuggable, works reliably in Remotion's headless Chrome
  - Neon-on-black as default for all variants with per-variant color palettes — illustrated-map uses gold/red tones, 3d-geographic uses cyan/pink, region-highlight uses blue, connection-arc uses green/yellow
patterns_established:
  - Remotion props contract: {variant, title, locations[{name,x,y}], connections[{from,to}], durationSeconds}
  - Normalized coordinates (0-1) with padding conversion in component — Python CLI doesn't need to know pixel dimensions
observability_surfaces:
  - "npx remotion render src/index.ts MapComposition out/test.mp4 --props=test-props.json" — smoke test render command
  - Render stdout shows frame progress, stderr surfaces TypeScript/React errors with frame numbers
duration: 20m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Scaffold Remotion Node.js project with map compositions

**Scaffolded self-contained Remotion project under `.claude/skills/animation/remotion/` — npm install succeeds, smoke render produces valid 1920×1080 h264 .mp4 at 30fps.**

## What Happened

Created a Remotion Node.js project with pinned v4.0.435 deps (remotion, @remotion/cli, @remotion/bundler, react 18.3.1, TypeScript 5.7.3). The project has a single `MapComposition` component that handles all 4 VISUAL_STYLE_GUIDE map variations via a `variant` prop with per-variant neon color palettes.

The component uses SVG rendering with Remotion animation primitives:
- `spring()` for marker entry (damped bounce)
- `interpolate()` for label fade-in with cubic easing slide
- Progressive stroke-dashoffset for connection arc drawing
- Region outline polygon with progressive reveal
- Pulsing glow effect on markers via sine wave

`calculateMetadata` derives `durationInFrames` from `props.durationSeconds`, so the Python CLI can control clip duration through the props JSON file.

Max 3 locations enforced per VISUAL_STYLE_GUIDE rule (`.slice(0, 3)`).

## Verification

- `npm install` — 212 packages installed, no errors
- `npx remotion render src/index.ts MapComposition out/test.mp4 --props=test-props.json` — exit 0, rendered 180/180 frames
- `ffprobe` confirms: 1920×1080, h264 High profile, 30fps, 6.000s duration, 180 frames, 432.9 kB
- Slice-level checks: `python -m animation load/status` — expected failure (CLI not yet built, T02)

## Diagnostics

- Run `cd .claude/skills/animation/remotion && npx remotion render src/index.ts MapComposition out/test.mp4 --props=test-props.json` to verify scaffold still works
- Render errors include frame number and composition ID in stderr
- TypeScript compilation errors surface during bundling phase (before frame rendering starts)
- First render downloads Chrome Headless Shell (~108MB) and caches it; subsequent renders skip this

## Deviations

None.

## Known Issues

- Font rendering uses Arial/Helvetica system fallback — Remotion headless Chrome resolves these, but custom brand fonts would need `@remotion/google-fonts` or CSS `@font-face` loading (not needed for this milestone)
- Region outline is a static simplified polygon, not geographic — matches the "stylized not accurate" aesthetic from VISUAL_STYLE_GUIDE

## Files Created/Modified

- `.claude/skills/animation/remotion/package.json` — Remotion project manifest with pinned v4.0.435 deps
- `.claude/skills/animation/remotion/tsconfig.json` — TypeScript config (react-jsx, ESNext, strict)
- `.claude/skills/animation/remotion/src/index.ts` — Entry point calling registerRoot
- `.claude/skills/animation/remotion/src/Root.tsx` — Composition registration with calculateMetadata for dynamic duration
- `.claude/skills/animation/remotion/src/MapComposition.tsx` — Map animation component (4 variants, SVG rendering, spring/interpolate animations)
- `.claude/skills/animation/remotion/test-props.json` — Test props for smoke render verification
- `.claude/skills/animation/remotion/.gitignore` — Ignores node_modules, out, dist, .remotion
