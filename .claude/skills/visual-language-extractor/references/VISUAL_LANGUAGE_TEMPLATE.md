# VISUAL_LANGUAGE.md
> Visual Implementation Guide for: *[Insert Video Name Here]*
> Purpose: To serve as a definitive guide for recreating this specific visual style programmatically.

---

## 1. Core Visual Identity & Color Palette

### Colors
| Role | Color | Hex | Implementation Notes |
|------|-------|-----|----------------------|
| Primary Background | [e.g., Pure black] | `[Hex Code]` | [e.g., Use as base layer for all scenes] |
| Secondary Background | [e.g., Dark navy] | `[Hex Code]` | [Description] |
| Accent 1 | [e.g., Deep crimson] | `[Hex Code]` | [Description] |
| Text — Primary | [e.g., Warm white] | `[Hex Code]` | [Description] |

### Global Aesthetic Rules
- [Rule 1, e.g., High contrast, desaturated look]
- [Rule 2, e.g., Colors are used strictly for emphasis, never decoration]

---

## 2. Layered Asset Hierarchy

The visual composition is structured in strict layers.

### Layer 1: Backgrounds / Environment
- **Base Style:** [e.g., Solid black, or slow-moving topographical map]
- **Implementation:** [How to recreate, e.g., `<AbsoluteFill style={{backgroundColor: 'black'}}>`]
- **Rules:** [e.g., Backgrounds must never distract from the main subject]

### Layer 2: Main Elements / Subjects
- **Primary Assets:** [e.g., Archival photography, 3D text objects, cutout portraits]
- **Treatment:** [e.g., Black and white conversion, high contrast]
- **Motion/Animation:** [e.g., Slow Ken Burns effect (1.0x to 1.1x scale over 10 seconds)]

### Layer 3: Overlays / Global Filters
- **Filter Stack (Bottom to Top):**
  1. [e.g., Vignette: 50% opacity, radial gradient]
  2. [e.g., Film Grain: 15% opacity, animated noise]
  3. [e.g., Scanlines: Horizontal lines, 10% opacity, blend mode overlay]
- **Implementation:** [e.g., Global overlay components applied over the entire sequence]

### Layer 4: Typography / UI
- **Primary Font:** [e.g., Courier New, Bold, Uppercase]
- **Placement:** [e.g., Dead center for quotes, bottom-left for date stamps]
- **Text Animation:** [e.g., Typewriter effect, 2 frames per character]

---

## 3. Transition Rules

| Transition Type | Trigger/Usage | Duration | Implementation |
|-----------------|---------------|----------|----------------|
| [e.g., Hard cut] | [e.g., Standard scene change] | [e.g., 0 frames] | [e.g., Abrupt sequence change] |
| [e.g., Fade to Black] | [e.g., End of chapter] | [e.g., 30 frames] | [e.g., Opacity interpolation] |

---

## 4. Strict Constraints (What NOT to Do)

- [e.g., No easing on camera moves — use linear interpolation only]
- [e.g., No drop shadows on text]
- [e.g., No bright or neon colors outside of the defined palette]
- [e.g., No cross-dissolves between scenes unless specified]
