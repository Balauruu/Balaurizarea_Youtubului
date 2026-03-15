---
estimated_steps: 6
estimated_files: 6
---

# T01: Scaffold Remotion Node.js project with map compositions

**Slice:** S04 — Remotion Animation Skill
**Milestone:** M002

## Description

Create a self-contained Remotion Node.js project under `.claude/skills/animation/remotion/` that renders animated location maps as .mp4 clips. A single `MapComposition` React component handles all 4 VISUAL_STYLE_GUIDE map variations (Illustrated Map, 3D Geographic, Region Highlight, Connection Arc) via a `variant` prop. The composition accepts locations, connections, title, and duration via `--props=props.json`. This task retires the "Remotion scaffold" risk — npm install succeeds and a real render produces a valid .mp4.

## Steps

1. Create `package.json` with pinned Remotion deps (`remotion`, `@remotion/cli`, `@remotion/bundler`, `react`, `react-dom`) and TypeScript. Pin exact versions to avoid breaking changes.
2. Create `tsconfig.json` for Remotion (JSX react-jsx, module ESNext, strict mode).
3. Create `src/Root.tsx` — registers the MapComposition with `<Composition>` (id: "MapComposition", width: 1920, height: 1080, fps: 30, defaultProps with sample locations).
4. Create `src/MapComposition.tsx` — single component handling all 4 variants. Uses `useCurrentFrame()`, `spring()`, `interpolate()` for animated marker entry, label fade-in, and connection arc drawing. Neon-on-black style (glowing dots, bold labels on dark background). SVG-based rendering for markers, lines, labels.
5. Create `src/index.ts` entry point that calls `registerRoot(Root)`.
6. Run `npm install` in the Remotion project directory. Create a `test-props.json` and verify `npx remotion render` produces a valid .mp4 output.

## Must-Haves

- [ ] package.json with pinned Remotion + React + TypeScript deps
- [ ] MapComposition accepts props: `variant`, `locations[]`, `connections[]`, `title`, `duration`
- [ ] 1920×1080 resolution, 30fps configured in Composition registration
- [ ] Neon-on-black visual style (glowing markers, bold labels, dark background)
- [ ] Animated entry: markers spring in, labels fade, connection arcs draw
- [ ] `npm install` succeeds without interactive prompts
- [ ] `npx remotion render` produces a valid .mp4 from test props

## Verification

- `cd .claude/skills/animation/remotion && npx remotion render src/index.ts MapComposition out/test.mp4 --props=test-props.json` exits 0 and produces a file > 0 bytes
- Output file is valid .mp4 (can verify with `ffprobe` or file size check)

## Observability Impact

- Signals added: Remotion render stdout/stderr captured during render — errors include frame number and composition details
- How a future agent inspects this: run `npx remotion render` manually with test-props.json to verify the scaffold still works
- Failure state exposed: npm install errors, TypeScript compilation errors, render errors all surface via process exit code + stderr

## Inputs

- S04-RESEARCH.md — Remotion CLI render syntax, props passing, version pinning guidance
- `context/visual-references/Mexico's Most Disturbing Cult/VISUAL_STYLE_GUIDE.md` lines 276-311 — Location Map building block spec (4 variations, production constraints)

## Expected Output

- `.claude/skills/animation/remotion/package.json` — Remotion project manifest with pinned deps
- `.claude/skills/animation/remotion/tsconfig.json` — TypeScript config
- `.claude/skills/animation/remotion/src/Root.tsx` — Composition registration
- `.claude/skills/animation/remotion/src/MapComposition.tsx` — Map animation component (4 variants)
- `.claude/skills/animation/remotion/src/index.ts` — Entry point
- `.claude/skills/animation/remotion/out/test.mp4` — Proof that render works (gitignored)
