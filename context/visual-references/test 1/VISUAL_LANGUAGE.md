# VISUAL_LANGUAGE.md
> Extracted from: *Mexico's Most Disturbing Cult* (UnnamedTV reference video)
> Analysis method: 20 frames sampled at 1-minute intervals across 20:28 runtime

---

## 1. Color Palette

### Core Colors
| Role | Color | Hex | Notes |
|------|-------|-----|-------|
| Primary background | Pure black | `#000000` | Default canvas for everything |
| Secondary background | Dark navy | `#050A14` | Chapter title cards, subtle tint |
| Archival footage tint | Desaturated gray | — | All historical footage is grayscale |
| Accent — Blood | Deep crimson → bright red | `#8B0000` → `#CC0000` | Stinger words, VHS static transitions |
| Accent — Signal | Phosphor teal / cyan | `#00B8B8` / `#4ECDC4` | Location labels, some chapter titles |
| Accent — Heat | Amber → orange gradient | `#E87722` → `#FFB347` | Secondary/lower-hierarchy labels |
| Text — Primary | Warm white | `#F0F0F0` | Quote cards, body text overlays |
| Ghost / Silhouette | Near-white with bloom | `#EEEEEE` + glow | Inverted human figure animations |
| VHS static — Red | Crimson noise | `#5C0000` base | Chapter break static screens |
| VHS static — Teal | Teal noise | `#1B4F6B` base | Mid-video glitch transitions |

### Color Rules
- Black is the default. Color is used as **punctuation**, not fill.
- Red = danger, violence, death. Appears on words like "CRUEL", "CRUEL", section-break statics.
- Teal = cold authority, geography, chapter numbers. Clinical, not warm.
- Never use warm yellow, green, or blue. The palette is deliberately **cold and analog**.
- Crimson and teal are **never used simultaneously** on the same element — they alternate by narrative context.

---

## 2. Typography

### Font Roles
| Element | Style | Case | Color | Effect |
|---------|-------|------|-------|--------|
| Date stamps (intro) | Bold serif numerals | N/A | White | VHS scan lines behind text |
| Location labels | Bold block sans-serif | ALL CAPS | Teal + red chromatic split | Chromatic aberration offset |
| Keyword stingers | Heavy serif or slab-serif | ALL CAPS | Red w/ glow | Phosphor bloom, vertical VHS distortion |
| Chapter titles | Mixed serif italic + number prefix | Title Case | Red/orange on dark blue | Subtle RGB split, scan lines |
| Quote cards | Serif (Georgia-style) | Sentence case | Warm white | Centered, radial vignette glow |
| Concept label pairs | Bold uppercase | ALL CAPS | Teal (top) / Red-orange (bottom) | Separated by sine wave animation |
| Scrolling archive text | Serif, slightly blurred | Sentence case | Off-white | Slow horizontal scroll, textured bg |
| Source documents on screen | Native UI / print reproduction | Mixed | Native | Unedited, shown as found |

### Typography Rules
- Quote cards: **centered both axes**, maximum 3 lines, quotation marks always included.
- Location labels: **corner-anchored** — top-right + bottom-left simultaneously for geographic context.
- Keyword stingers: **left-aligned** on dark bg, large scale (fills ~40% frame width), used to punctuate emotional beats.
- Chapter titles: always numbered (e.g., `5. Truth: 2024`), number in non-italic, title word in italic serif.
- Never combine more than 2 font styles in a single frame.

---

## 3. Animation Styles

### 3.1 VHS Glitch / Scan Lines
- **Description:** Full-frame horizontal tracking artifacts, color bleed, signal noise.
- **Use:** Opening title cards, transition screens, stinger moments.
- **Implementation:** Horizontal scanline overlay (opacity ~40%), random horizontal jitter on text (2–4px), slight vertical desync on footage clips.
- **Variants:**
  - *Date stamp card* — static bg with scan lines, single large date in serif white.
  - *Full-screen static* — entire frame becomes animated noise, red or teal tint.

### 3.2 Chromatic Aberration Text
- **Description:** RGB channel offset on text, primarily teal on the left offset + slight red on right.
- **Use:** Location labels, chapter titles, any "broadcast" or "archival" text context.
- **Implementation:** Duplicate text layer, teal offset -3px horizontal, red offset +3px, main layer white at 80% opacity.

### 3.3 Particle / Stipple Maps
- **Description:** Geographic shapes (countries, states) rendered as animated dot/particle fields. Country silhouette in stippled dark texture; highlighted region in bright white.
- **Use:** Any geographic context — locations, travel, borders.
- **Key traits:**
  - Pure black background.
  - Country body = dark gray stipple dots, slightly animated (subtle drift).
  - Highlighted state/region = white or near-white fill, high contrast.
  - Location name labels at opposite corners (see typography rules).

### 3.4 Sine Wave Separator
- **Description:** Two animated sinusoidal curves (one red, one white/pink) scrolling horizontally, crossing each other.
- **Use:** Separates paired concept labels (e.g., "PRIESTS" above / "LEADERS" below). Implies tension or duality.
- **Implementation:** Two offset sine waves, amplitude ~15% frame height, phase offset 180°, red `#CC0000` + white `#DDDDDD`.

### 3.5 Phosphor Glow Text
- **Description:** Ambient bloom/outer glow around keyword text, simulating CRT phosphor decay.
- **Use:** All colored keyword stingers, particularly red words on black.
- **Implementation:** Gaussian blur layer of same text behind at 30–50% opacity, same color. Radius ~8px.

### 3.6 Inverted Silhouette Figures
- **Description:** Human figures shown as pure glowing white cutouts on pure black — overexposed/inverted effect. Strong bloom/halo around edges.
- **Use:** People who are anonymous, unknown, or presented as archetypes rather than individuals.
- **Implementation:** Source footage desaturated → levels crushed to near-white → outer glow added. Not animated — held still.

### 3.7 Shadow / Silhouette Animation
- **Description:** Scenes depicted as animated dark silhouettes against a gray sky — animated shadow-puppet aesthetic. Reminiscent of old illustrated films or cut-paper animation.
- **Use:** Historical scenes where no real footage exists. Implies atmosphere over documentation.
- **Visual signature:** Palm trees, human figures, structures as black flat shapes. Sky is light gray, not white.

### 3.8 ASCII / Symbol Rain
- **Description:** Background filled with streams of `@`, `#`, `&`, `*`, `/`, `.` characters in rows. 2–3 keywords ("Spiritist", "Manual") appear in a different color (teal/red) embedded in the noise.
- **Use:** Representing forbidden documents, esoteric manuals, hidden information, coded language.
- **Color:** Characters in dim teal (`#1A3A3A`), highlight keywords in bright teal or red.

### 3.9 Document / Newspaper Pan
- **Description:** Scanned newspaper or historical document shown as full-frame or letterboxed image, with slow Ken Burns zoom-in or horizontal pan.
- **Use:** Source citation, historical evidence, newspaper clippings.
- **Presentation:** Black letterbox bars on left and right (~15% each side) to imply scan/film format. No color correction — kept in original black & white print quality.

### 3.10 Screen Recording as Evidence
- **Description:** Real websites (Wikipedia, archive.org, Google Books) shown as live screen recordings — unaltered, native UI visible.
- **Use:** Source transparency moments — showing the actual research trail.
- **Framing:** Full screen, no overlay or annotation. Implies "I'm showing you exactly where this comes from."

---

## 4. Transition Rules

| Transition Type | Trigger | Duration |
|-----------------|---------|----------|
| Hard cut to black | Standard clip change | 0 frames |
| Black frame hold | Gravity/silence moment (death, revelation) | 0.5–1.5 sec |
| Full-screen red VHS static | Major chapter break | 1.5–3 sec |
| Full-screen teal VHS static | Mid-chapter tonal shift | 1–2 sec |
| Glitch cut (single frame distortion) | Shock moment lead-in | 1–3 frames |
| Slow fade to black | End of act, elegiac moment | 1–2 sec |

### Transition Rules
- **Never use wipes, slides, or cross-dissolves.** All transitions are cuts or static screens.
- VHS static screens are **full beats** — they hold long enough to register, not just flash.
- Black holds are used like **silence in music** — purposeful, not accidental.
- Color of static (red vs. teal) is **not random** — red = violence/danger chapter, teal = mystery/authority chapter.

---

## 5. Framing & Composition

### Archival Footage
- Always **letterboxed**: black bars on left and right sides (~15% each), simulating 4:3 → 16:9 conversion.
- Footage is **desaturated** — no color archival footage is used without desaturation.
- Slow push-in or static hold. No fast cuts within archival clips.
- **Low exposure by default** — footage is darkened 20–40% to reduce distraction.

### Text Cards (Quotes)
- Full black background, no texture.
- Text centered horizontally and vertically.
- Subtle **radial vignette glow** behind text block (white at 10–15% opacity, Gaussian blur ~80px radius).
- No other visual elements in frame.
- Quote cards hold for full read time + ~1 second.

### Animated Graphics
- All graphic animations: pure black background unless the animation itself defines the space (maps, ASCII fields).
- No gradients in backgrounds — solid black only.
- Graphic elements are **center-weighted** or use **diagonal corner anchoring** for labels.

---

## 6. Visual Asset Taxonomy

Every scene in the video uses exactly one of these asset types:

| # | Asset Type | Visual Signature | Context |
|---|-----------|-----------------|---------|
| 1 | Archival footage | B&W, letterboxed, film grain | Historical events |
| 2 | Animated map | Particle stipple, black bg, white highlight | Geography / location intro |
| 3 | VHS static screen | Full-frame noise, red or teal | Chapter breaks |
| 4 | Quote card | White serif on black, centered | Direct source quotes |
| 5 | Keyword stinger | Large colored text on black, glow | Emotional beat punctuation |
| 6 | Chapter title card | Numbered + italic title, dark blue bg | Section headers |
| 7 | ASCII code field | Symbol rain with embedded keywords | Forbidden/esoteric documents |
| 8 | Silhouette animation | Flat shadow figures, gray sky | Scenes with no real footage |
| 9 | Glowing silhouette | Overexposed white figures, black bg | Anonymous subjects, archetypes |
| 10 | Document pan | B&W newspaper/photo, letterboxed | Physical evidence |
| 11 | Screen recording | Native web UI, unaltered | Source transparency |
| 12 | Concept label pair | Two keywords + sine wave separator | Category/role definitions |
| 13 | Pure black frame | Nothing | Silence, weight |

---

## 7. Remotion Implementation Notes

### Components to Build
- `<VHSStatic color="red|teal" />` — full-screen animated noise with scan lines
- `<DateStampCard date="YYYY/MM/DD" />` — VHS bg + large serif date
- `<LocationMap country="MX" highlight="Tamaulipas" labels={[...]} />` — particle stipple map
- `<QuoteCard text="..." />` — black bg, centered serif, radial glow
- `<KeywordStinger word="CRUEL" color="red" />` — large text + glow + VHS distortion
- `<ChapterTitle number={5} title="Truth" year={2024} />` — numbered chapter card
- `<ConceptPair top="PRIESTS" bottom="LEADERS" />` — two labels + sine wave separator
- `<SilhouetteReveal src="..." />` — inverted white figure on black with bloom
- `<ArchivalClip src="..." />` — letterbox mask + desaturate + darken filter
- `<ASCIIField keywords={["Spiritist", "Manual"]} />` — animated @ symbol rain

### Global Filter Stack (apply to all non-text content)
1. Subtle scanline overlay texture (2px stripes, 8% opacity)
2. Slight film grain noise (3–5% opacity, animated)
3. Vignette (radial gradient, black 40% → transparent, outer 20% of frame)
4. These three stack on **every clip** — they define the overall aesthetic unity.

---

## 8. What NOT to Do

- No color footage (unless shown as screen recording evidence)
- No bright backgrounds — never white, yellow, or light gray canvas
- No smooth corporate motion graphics — no easing curves that feel "designed"
- No talking-head footage or presenter on screen
- No lower-thirds / news-style name tags
- No emoji, icons, or infographic-style charts
- No background music visualization or waveform bars
- No zoom transitions, push transitions, or slide transitions
- No color grading that adds warmth — the palette stays cold

---

*Reference video: Mexico's Most Disturbing Cult — XAY4gFv-2Dc (20:28)*
*Analyzed: 2026-03-08*
