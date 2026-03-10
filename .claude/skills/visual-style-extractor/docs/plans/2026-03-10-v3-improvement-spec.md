# Visual Style Extractor v3 — Improvement Spec

> Comparative analysis of VISUAL_STYLE_GUIDE.md (skill output) vs VISUAL_LANGUAGE.md (manual prompt output)
> Date: 2026-03-10

---

## 1. Executive Summary

The current skill produces a **data-rich but structurally flat** output (20 individual asset types in a single list). The manually-prompted VISUAL_LANGUAGE.md produces a **prescriptive, hierarchically organized** document that is more actionable for downstream agents. This spec proposes restructuring the output into hierarchical asset categories with richer per-subtype entries, fixing potential dedup issues, and adding progress visualization.

---

## 2. Side-by-Side Comparison

### What VISUAL_STYLE_GUIDE.md (skill) does well
- Quantitative data per asset type (proportion, frequency, duration ranges)
- Frame-level examples with IDs (traceable back to source)
- Shotlist `visual_type` mapping for Agent 1.4
- "When to use" narrative triggers (intent is right, execution too video-specific)
- Automated — reproducible pipeline

### What VISUAL_LANGUAGE.md (manual) does well
- **Hierarchical structure** with distinct sections
- **Animation styles as recipes**: Description + Use + Implementation + Variants per style
- **Generalized** — describes the visual language itself, not individual frames
- **Remotion implementation notes**: directly actionable component specs

### What both miss
- Neither produces a hierarchical asset taxonomy with categories → subtypes
- Neither has progress/status output during the long pipeline run

---

## 3. Proposed Changes

### 3.1 Output Structure Overhaul (HIGH IMPACT)

**Current:** Flat list of 20 asset types, all at same level.
**Proposed:** Hierarchical categories with open-ended subtypes discovered from the video:

```markdown
# VISUAL_STYLE_GUIDE.md

## 1. Asset Types

### B-Roll
  #### [subtype discovered from video]
  #### [subtype discovered from video]
  ...

### Archival Photos
  #### [subtype discovered from video]
  #### [subtype discovered from video]
  ...

### Graphics & Animation
  #### [subtype discovered from video]
  #### [subtype discovered from video]
  ...

### Text Elements
  #### [subtype discovered from video]
  #### [subtype discovered from video]
  ...

### Evidence & Documentation
  #### [subtype discovered from video]
  #### [subtype discovered from video]
  ...

## 2. Type Mapping (quick-reference table — keep from current)
```

Asset types are **not a fixed list**. The LLM freely discovers and labels subtypes from the video. The 5 categories provide grouping structure, but what appears within each category depends entirely on the source material.

Transition frames (black frames, color holds, film leader) are excluded — they are editing decisions, not asset types.

Remotion implementation notes are written to a separate `REMOTION_NOTES.md` file in the same output directory.

**Each asset subtype entry contains:**

| Variable | Purpose | Example |
|----------|---------|---------|
| **Description** | What it looks like visually | "Glowing white human cutout on pure black, overexposed/inverted with halo bloom" |
| **Use** | Narrative trigger — when to deploy | "People who are anonymous, unknown, or presented as archetypes" |
| **Implementation** | How to create it — background, elements, overlays, colors | "Source footage desaturated → levels crushed → outer glow added. Static hold." |
| **Variants** | Named sub-variants observed | "Power-dynamic (two figures, size contrast), Crowd silhouette, Solo figure" |
| **Stats** | Compact usage data | "19.6% · 32x · 7.4s avg" |
| **Examples** | 2-3 frame content descriptions | (kept from current) |

### 3.2 Categorization System for Asset Types (HIGH IMPACT)

**Problem:** Current output has 20 flat types, some near-duplicates. No grouping. Transitions treated as asset types.

**Proposed:** 5 broad categories (transitions excluded entirely):

| Category | Example subtypes (not fixed — discovered per video) |
|----------|-----------------------------------------------------|
| **B-Roll** | Archival Video, B-Roll Footage, ... |
| **Archival Photos** | Portrait, Location Shot, Historical Photo, ... |
| **Graphics & Animation** | Silhouette, Map Animation, Animated Graphic, Date Card, ... |
| **Text Elements** | Quote Card, Title Card, Text Overlay, Keyword Stinger, ... |
| **Evidence & Documentation** | Evidence Document, Screen Recording, ... |

The examples are illustrative — any subtype can emerge from analysis. The category list is the fixed structure; subtypes within are open-ended.

**Implementation:** Add a `category` field to the analysis prompt's output schema. The synthesis module groups by category first, then by scene_type within each category. Frames categorized as transitions are dropped.

### 3.3 Analysis Prompt Enhancements (MEDIUM IMPACT)

**Current prompt requests per frame:** scene_type, shotlist_type, asset_breakdown (background/main_element/overlays/text_elements), dominant_colors, content_description, narrative_trigger, confidence.

**Changes:**

| Field | Action | Rationale |
|-------|--------|-----------|
| `category` | **Add** — one of: `b_roll`, `archival_photos`, `graphics_animation`, `text_elements`, `evidence_documentation`, `transition` | Enables hierarchical grouping; transitions get filtered out |
| `variants` | **Add** — name any visual variant of this scene type if one is apparent | Populates the Variants field per asset type |
| `narrative_trigger` | **Refine wording** — emphasize generalized triggers, not video-specific descriptions | Current triggers are too tied to the source video |
| `asset_breakdown` | **Rename to `implementation`** — keep same sub-fields but frame it as "how to recreate this" | Better signals intent to the analyzing LLM |
| `scene_type` | **Remove fixed enum** — LLM labels freely, categories provide structure | Prevents artificial constraints on what types can be discovered |

**Token impact:** Minimal (~+20 tokens per frame for `category` + `variants`).

---

## 4. Pipeline / Dedup Investigation

### 4.1 Possible Scene Skipping (Dedup Too Aggressive?)

**Symptoms:** User suspects scenes are being dropped. 164 scenes detected → 119 unique frames (27% deduped).

**Investigation areas:**

1. **PHash threshold=6 may be too low** for this content style. The video uses many near-black frames, red holds, and similar-looking archival footage. A threshold of 6 means frames with very minor visual differences get merged.

2. **Near-black pre-grouping** (brightness < 25px, 92% of pixels) may be catching dark archival footage, not just true transitions.

3. **No visibility into what was deduped.** User can't tell which frames were dropped or why.

**Proposed fixes:**

| Fix | Effort | Impact |
|-----|--------|--------|
| **A. Add dedup report** — write `dedup_report.json` listing every group with member frames, representative selected, and reason (phash / near-black) | Low | High — user can audit |
| **B. Raise default threshold to 8** and make it a user-adjustable parameter | Low | Medium — fewer false merges |
| **C. Lower near-black brightness threshold to 15** (from 25) — catches only true black frames | Low | Medium — dark archival footage preserved |

### 4.2 Contact Sheet Quality

**Assessment:** Contact sheets are adequate. The bottleneck is the analysis prompt and synthesis structure, not image quality.

---

## 5. Progress Visualization

**Proposed:** Lightweight progress output at each stage:

```
[Stage 0/6] Acquiring video...
  Done: Mexico's Most Disturbing Cult (20:28)
[Stage 1/6] Detecting scenes...
  Done: 164 scenes detected (threshold: 3.0)
[Stage 2/6] Deduplicating frames...
  Done: 119 unique frames (45 removed: 42 near-black, 3 phash duplicates)
[Stage 3/6] Aligning transcript...
  Done: 892 subtitle cues aligned
[Stage 4/6] Generating contact sheets...
  Done: 14 contact sheets (9 frames each)
[Stage 5/6] Analyzing frames...
  Done: Batch 1/4 | Batch 2/4 | Batch 3/4 | Batch 4/4
  Merged: 119 frames (0 low-confidence removed)
[Stage 6/6] Synthesizing style guide...
  Done: VISUAL_STYLE_GUIDE.md (5 categories, N asset types)
```

**Implementation:** `print()` statements at key checkpoints. Token cost: ~200 tokens.

---

## 6. Implementation Priority

| # | Change | Effort | Impact | Dependencies |
|---|--------|--------|--------|--------------|
| 1 | Analysis prompt enhancements (§3.3) | Low | High | None |
| 2 | Dedup fixes — report + threshold (§4.1 A+B+C) | Low | High | None |
| 3 | Progress visualization (§5) | Low | Medium | None |
| 4 | Asset categorization system (§3.2) | Medium | Critical | §1 |
| 5 | Output structure overhaul + synthesis rewrite (§3.1) | High | Critical | §1, §4 |

**Execution order:**
- **Wave 1** (independent, parallel): #1 (prompt) + #2 (dedup) + #3 (progress)
- **Wave 2** (depends on Wave 1): #4 (categorization) + #5 (synthesis rewrite)

---

## 7. Test Plan

After implementation, re-run on the same Mexico cult video and verify:
1. Asset types are grouped under 5 categories (B-Roll, Archival Photos, Graphics & Animation, Text Elements, Evidence & Documentation)
2. Each asset subtype has: Description, Use, Implementation, Variants, Stats, Examples
3. Subtypes are discovered freely — not constrained to a fixed list
4. No transition types in output (black frames, color holds excluded)
5. Dedup report shows what was merged and why
6. Progress output appears during run
7. Frame count is equal or higher than current (dedup less aggressive)
8. Type Mapping table still present as quick-reference
9. REMOTION_NOTES.md generated as separate file
