# Visual Style Extractor v4 — Decision Framework Redesign

> Date: 2026-03-10
> Status: SPEC + IMPLEMENTATION PLAN (approved for execution)

---

## 1. Problem Statement

The v3 output is a **frame analysis report disguised as a style guide**. It describes individual frames instead of documenting reusable visual building blocks.

**Current output (BAD — frame-specific):**
```
#### Silhouette Animation
- **Description:** Three human silhouette figures against a dark background with a warm
  glowing light source. The central figure is illuminated in bright golden-yellow...
- **Implementation:** Background: deep magenta/crimson solid color, dark background with
  dim red ambient glow, deep red with horizontal scanline texture; Main element: three
  human silhouette figures — one central figure in bright golden-yellow...
- **Examples:**
  | F005 | Three human silhouette figures against a dark background... |
  | F022 | A dark symbolic composition: multiple vertical lines or ropes... |
```

**Target output (GOOD — generalized building block):**
```
#### Silhouette Figure
> Shotlist type: `ai_generated`

**Visual:** Human figure(s) rendered as glowing silhouette cutouts against solid dark
background. High contrast, pure shape, no facial features.

**When to use:**
- Represent people whose identity is unknown, protected, or symbolic
- Depict power dynamics between individuals (size/position contrast)
- Visualize group scenes without specific faces

**When NOT to use:**
- When actual archival photos/footage of the person exist
- Back-to-back with another silhouette block

**Rules:**
- ALWAYS: Add subtle film grain — clean renders feel out of place in documentary
- NEVER: Show identifiable facial features
- CONSIDER: Warm gold tint for historical figures, cold white for modern subjects

**Production spec:**
- Background: Solid black or deep crimson
- Subject: Human silhouette (full body, high contrast)
- Treatment: Chromatic aberration edge glow, light film grain, optional scanlines
- Duration: 6-12s typical
- Text: None
- Colors: Black, white/warm gold, optional deep red accent

**Variations:**
- Solo figure: Single standing silhouette — for key individuals
- Power dynamic: Two figures with size contrast — authority vs. subject
- Crowd: Mass of small silhouettes — group/community scenes

**Weight:** Heavy (13%)
```

### Root causes

1. **Analysis prompt asks "describe this frame"** → produces frame-specific text
2. **Synthesis is Python-only** (`synthesize.py`) → can aggregate/count but CANNOT abstract. Taking 17 silhouette descriptions and writing "human figures as white cutouts on black" requires an LLM.
3. **`content_description` field** leaks frame specifics into Description and Examples

---

## 2. Architecture: Two-Pass Approach

**Pass 1 (existing, modified): Frame-level pattern extraction**
- Same pipeline: extract frames → contact sheets → parallel subagent analysis
- But the analysis prompt asks "what PATTERN is this?" not "describe this frame"
- Output: frame-level pattern data (internal only — never in final output)

**Pass 2 (NEW): LLM synthesis into building blocks**
- One LLM subagent reads ALL frame-level data and produces the final decision framework
- Replaces the Python-only `synthesize.py` markdown generation
- The LLM abstracts, merges, and generalizes

### Why two passes?
- Pass 1 must be parallel (subagents see images) — extracts raw pattern data
- Pass 2 must be holistic (one agent sees everything) — produces wisdom
- Pass 1 outputs data; Pass 2 outputs the decision framework

---

## 3. Pipeline Audit — What Stays, What Changes, What Goes

### Current stages

| Stage | Module | Function | v4 Verdict |
|-------|--------|----------|------------|
| 0 | `acquire.py` | Download video + subs via yt-dlp | **KEEP** — unchanged |
| 1 | `scene_detect.py` | PySceneDetect → keyframes | **KEEP** — unchanged |
| 2 | `dedup.py` | PHash + near-black dedup | **KEEP** — unchanged |
| 3 | `align.py` | Map transcript to frames | **KEEP** — narration context helps LLM understand narrative purpose of visual patterns |
| 4 | `contact_sheets.py` | 3x3 grids for LLM | **KEEP** — unchanged |
| 5 | LLM analysis (subagents) | Analyze contact sheets | **MODIFY** — new analysis prompt |
| 6 | `synthesize.py` | Python aggregation → markdown | **REPLACE** — LLM synthesis subagent |

### What's removed

| Artifact | Why |
|----------|-----|
| `analysis_results.json` | No longer saved to output dir. Batch results stay in `.claude/scratch/` during the run, then get fed to synthesis subagent and discarded. |
| `synthesize.py` → `generate_style_guide()` | Replaced by LLM synthesis. Keep `aggregate_by_category_and_type()` and `compute_proportions()` as data prep functions. |
| `pipeline.py` → `run_stage_6()` | Replaced by `prepare_synthesis_input()` — prepares data for the LLM subagent |
| `pipeline.py` → `merge_analysis_batches()` | Replaced by simpler `merge_batches()` that writes to scratch only |
| Frame Examples table in output | Gone entirely — zero frame references in final output |
| `content_description` field | Removed from analysis prompt |

### What's simplified

| Component | Before | After |
|-----------|--------|-------|
| `synthesize.py` | 424 lines — full markdown generation, Counter aggregation, template building | ~100 lines — `aggregate_by_category_and_type()`, `compute_proportions()`, `prepare_synthesis_input()` |
| `pipeline.py` | `run_stage_6()` calls `generate_style_guide()` | `prepare_synthesis_input()` writes a structured JSON for the LLM subagent |
| Stage 6 in SKILL.md | Python function call | Spawn one synthesis subagent with prompt + data |
| Intermediate files | `analysis_results.json` in output dir + scratch batches | Scratch batches only, cleaned up after synthesis |

---

## 4. New Analysis Prompt (Stage 5)

Replaces `prompts/analysis_prompt.txt`. The key shift: from "describe this frame" to "identify the visual pattern and write a recipe."

```
You are analyzing frames from a documentary video to identify reusable VISUAL PATTERNS.

Think of yourself as cataloging an editor's toolkit — each frame is an instance of a
visual tool. Your job is to identify WHICH tool is being used and document how to
recreate it from scratch.

For EACH frame in this contact sheet, output a JSON object:

1. **frame_id**: The frame label (e.g., "F001")

2. **confidence**: Rate 1-5 how clearly you can analyze this frame.

3. **pattern_name**: A short reusable label for the visual PATTERN this frame represents.
   Examples: "silhouette_figure", "location_map", "keyword_stinger", "archival_bw_footage",
   "date_card", "quote_card", "concept_diagram", "document_scan"

   CRITICAL: Use the SAME label for frames that use the SAME visual approach.
   If frame F005 shows a solo white silhouette on black and frame F022 shows three
   silhouettes on red — they are BOTH "silhouette_figure". The difference is a variant,
   not a different pattern.

   Think: "What tool from the editor's toolkit is being used here?"

4. **category**: One of:
   - `b_roll` — live-action or stock footage
   - `archival_photos` — still photographs
   - `graphics_animation` — motion graphics, silhouettes, maps, diagrams, animated elements
   - `text_elements` — quote cards, title cards, text overlays, stingers
   - `evidence_documentation` — documents, screen recordings, newspaper scans
   - `transition` — black frames, color holds, film leader (will be excluded from output)

5. **shotlist_type**: Closest shotlist mapping:
   [archival_photo | archival_video | news_clip | animation | ai_generated | map |
    text_overlay | document_scan]

6. **visual_recipe**: How to BUILD this pattern from scratch (not what this frame shows):
   - background: What goes behind everything (e.g., "solid black", "deep crimson with scanlines")
   - subject: The main visual element IN GENERAL (e.g., "human silhouette", "map outline", "text block")
   - treatment: Post-processing (e.g., "film grain, scanlines, chromatic aberration glow")
   - color_palette: 2-3 colors that define this PATTERN (e.g., "black, white, deep red")
   - text_style: If text is present: font character, position, color. Otherwise "none"

7. **narrative_function**: In what storytelling situation would ANY documentary use this
   visual tool? Write a GENERAL rule that applies beyond this specific video.
   GOOD: "Represent anonymous individuals whose identity is protected or symbolic"
   BAD: "Show the cult leader's followers gathering in the mountains"

8. **variant_name**: If this frame shows a sub-variant of the pattern, name it.
   E.g., for silhouette_figure: "solo", "crowd", "power_dynamic"
   If standard/default, write "default"

Output as a JSON array. If you cannot determine something, write "unclear" — do not guess.
```

### Key differences from v3 prompt

| Field | v3 | v4 |
|-------|-----|-----|
| `content_description` | "Describe WHAT is depicted" | **REMOVED** |
| `scene_type` | Free label per frame | `pattern_name` — explicit instruction to REUSE labels |
| `implementation` | "background, main_element, overlays, text_elements" for THIS frame | `visual_recipe` — "how to BUILD this pattern from scratch" |
| `narrative_trigger` | "When would a documentary use this?" | `narrative_function` — stronger generalization, explicit good/bad examples |
| `dominant_colors` | Separate field, per-frame | Inside `visual_recipe.color_palette`, per-pattern |

---

## 5. New Synthesis Prompt (Stage 6)

New file: `prompts/synthesis_prompt.txt`. This is the prompt given to the synthesis subagent.

```
You are creating a VISUAL STYLE DECISION FRAMEWORK for documentary video production.

You will receive structured data about visual patterns extracted from a reference video.
Your job is to transform this raw data into a prescriptive toolkit of reusable
BUILDING BLOCKS that downstream production agents will follow.

## Instructions

1. MERGE patterns that share the same visual approach into BUILDING BLOCKS.
   - "Silhouette Figure" is ONE block even if there are 17 silhouette frames
   - Merge aggressively — if patterns differ in content but share the same visual
     technique, they are the SAME block
   - Target: 10-15 building blocks total. More than 15 = merge harder.

2. For each building block, write a GENERALIZED specification.
   Do NOT describe any specific frame. Write abstract recipes and general rules.

3. EXCLUDE from output:
   - References to specific people, places, events, or story details from the source video
   - Frame IDs or frame-specific descriptions
   - Transitions (black frames, color holds)

4. Use RELATIVE WEIGHTS for proportions:
   - Heavy: >10% of screen time
   - Medium: 3-10%
   - Light: 1-3%
   - Accent: <1%

5. After all building blocks, write:
   a. PACING & SEQUENCING RULES — derived from the video's patterns
   b. TYPE SELECTION DECISION TREE — IF/THEN rules mapping narrative triggers
      to building block selections

## Output Format

Use this exact markdown structure:

# Visual Style Decision Framework
> Source: {video_title} | Duration: {duration} | Generated: {date}

## Visual Toolkit

### [Category Name]

#### [Building Block Name]
> Shotlist type: `[type]`

**Visual:** [1-2 sentence abstract description — a recipe, not a frame description]

**When to use:**
- [General narrative trigger]

**When NOT to use:**
- [Anti-pattern that prevents overuse]

**Rules:**
- ALWAYS: [Non-negotiable production constraint]
- NEVER: [Hard constraint]
- CONSIDER: [Conditional guidance]

**Production spec:**
- Background: [what goes behind]
- Subject: [the main visual element]
- Treatment: [post-processing, overlays, effects]
- Duration: [Xs-Ys typical range]
- Text: [font style, position, color — or "none"]
- Colors: [2-3 defining colors]

**Variations:**
- [Name]: [How it differs + when to pick this variant]

**Weight:** [Heavy/Medium/Light/Accent] ([X%])

---

### [Next category...]

---

## Pacing & Sequencing Rules

- Shot duration by narrative mode
- Sequencing constraints (what should/shouldn't follow what)
- Transition patterns observed (cut vs. dissolve vs. fade)

## Type Selection Decision Tree

IF narration introduces a person → [building block]
IF narration introduces a location → [building block] OR [building block]
IF narration references a document → [building block]
IF narration builds tension → [building block]
IF transitioning between chapters → [building block]
[...additional rules]

## Quick Reference

| # | Category | Building Block | Shotlist Type | Weight |
|---|----------|---------------|---------------|--------|
```

---

## 6. Detailed Implementation Plan

### File changes summary

| File | Action | Lines (est.) |
|------|--------|-------------|
| `prompts/analysis_prompt.txt` | **REWRITE** — new prompt from §4 | ~55 lines |
| `prompts/synthesis_prompt.txt` | **NEW** — synthesis prompt from §5 | ~85 lines |
| `synthesize.py` | **SIMPLIFY** — keep data prep, remove markdown generation | ~100 lines (from 424) |
| `pipeline.py` | **MODIFY** — replace `run_stage_6()` with `prepare_synthesis_input()`, simplify `merge_analysis_batches()` | ~180 lines |
| `SKILL.md` | **MODIFY** — Stage 6 becomes LLM subagent dispatch | ~140 lines |
| `tests/test_pipeline.py` | **UPDATE** — adjust for new function signatures | update existing |

### Step-by-step execution plan

#### Step 1: Rewrite `prompts/analysis_prompt.txt`
- Replace entire file with the v4 prompt from §4
- No other files depend on this — it's read by subagents at runtime

#### Step 2: Create `prompts/synthesis_prompt.txt`
- New file with the synthesis prompt from §5
- Read by the synthesis subagent at runtime

#### Step 3: Simplify `synthesize.py`

**Keep:**
- `CATEGORIES` dict and `CATEGORY_ORDER` list
- `_normalize_scene_type()` (update for `pattern_name` field)
- `_infer_category()`
- `aggregate_by_category_and_type()` (update to use `pattern_name` instead of `scene_type`)
- `compute_proportions()`

**Remove:**
- `_extract_field()`, `_collect_field_values()`, `_most_common()`
- `_format_scene_type_name()`, `_get_shotlist_type()`, `_collect_variants()`
- `_build_implementation_text()`, `_build_subtype_entry()`
- `generate_style_guide()` — the big markdown generator

**Add:**
- `prepare_synthesis_input(analysis_data, manifest, video_title, video_source) -> str`
  - Aggregates frame data by pattern_name within categories
  - Computes proportions using manifest
  - For each pattern: collects unique visual_recipe fields, all narrative_functions, all variants, proportion stats
  - Returns a structured text block that the synthesis LLM prompt will consume
  - This is the bridge between raw frame data and the synthesis prompt

#### Step 4: Simplify `pipeline.py`

**Modify `merge_analysis_batches()`:**
- Remove `output_path` parameter for analysis_results.json
- Return the merged data as a list instead of writing to output dir
- Or: write only to `.claude/scratch/merged_analysis.json` (transient)

**Replace `run_stage_6()` with `prepare_synthesis_input()`:**
- Calls `aggregate_by_category_and_type()` and `compute_proportions()`
- Calls new `synthesize.prepare_synthesis_input()`
- Writes result to `.claude/scratch/synthesis_input.txt`
- Returns the path

**Keep everything else unchanged:**
- `PipelineConfig`, `_sanitize_dirname()`, `slice_manifest()`
- `run_stages_0_to_4()` — completely unchanged

#### Step 5: Update `SKILL.md`

**Stage 5 (LLM Analysis)** — minor change:
- Subagent prompt references new analysis prompt (same file path, just new content)
- No structural changes to subagent dispatch

**Stage 6 (Synthesis)** — major change:
- Instead of calling `run_stage_6()` Python function:
  1. Call `prepare_synthesis_input()` to generate the structured data
  2. Spawn one synthesis subagent with this prompt:
     ```
     You are synthesizing a visual style decision framework.
     1. Read the synthesis prompt from: [SYNTHESIS_PROMPT_PATH]
     2. Read the synthesis input data from: .claude/scratch/synthesis_input.txt
     3. Follow the synthesis prompt instructions to produce the framework
     4. Write the final markdown to: [OUTPUT_DIR]/VISUAL_STYLE_GUIDE.md
     5. Return a 1-line summary
     ```

**Stage presentation** — update "Present Results" to match new output format

#### Step 6: Update tests
- Update `test_pipeline.py` for new function signatures
- Add test for `prepare_synthesis_input()` output structure
- Remove tests for `generate_style_guide()` (deleted)

---

## 7. What Does NOT Change

Explicitly listing unchanged components to reduce implementation risk:

- `acquire.py` — zero changes
- `scene_detect.py` — zero changes
- `dedup.py` — zero changes
- `align.py` — zero changes
- `contact_sheets.py` — zero changes
- Contact sheet format (1568x1568, 3x3, 4px padding) — unchanged
- Parallel subagent dispatch model — unchanged
- 5 category system — unchanged
- `frames_manifest.json` — unchanged
- `scenes.json` — unchanged
- `dedup_report.json` — unchanged
- Stages 0-4 Python pipeline — unchanged

---

## 8. Quality Considerations

### Frame-by-frame analysis preserved

The user wants maximum quality even at the cost of analyzing frame-by-frame. The current approach already does this — each frame in a contact sheet is analyzed individually, producing one JSON object per frame. The contact sheet format is an optimization for passing images (9 frames in one image read vs. 9 separate reads) but the analysis granularity is per-frame. This is preserved.

### Transcript context helps generalization

Stage 3 (transcript alignment) is kept because narration context helps the LLM understand WHY a visual choice was made. "This map appears when the narration mentions a new city" → generalizes to "maps are used when introducing locations." Without narration context, the LLM would only see visuals and miss the narrative function.

### LLM synthesis vs Python aggregation

The new synthesis subagent is the most impactful change. It can:
- Merge 17 silhouette frames into 1 building block with an abstract description
- Generate "When NOT to use" anti-patterns (Python can't infer these)
- Write ALWAYS/NEVER/CONSIDER rules based on pattern observation
- Build a decision tree mapping narrative triggers to visual types
- Generalize away from video-specific content

### Cost: one additional LLM call

The synthesis subagent adds ~10K input tokens (aggregated data) + ~3K output tokens. This is minor compared to the 4 analysis subagents processing contact sheets. Total pipeline cost increase: ~5%.

---

## 9. Expected Output Structure

The final `VISUAL_STYLE_GUIDE.md` will contain:

1. **Visual Toolkit** — 10-15 building blocks organized under 5 categories, each with:
   - Visual (abstract recipe)
   - When to use (general narrative triggers)
   - When NOT to use (anti-patterns)
   - Rules (ALWAYS/NEVER/CONSIDER)
   - Production spec (background, subject, treatment, duration, text, colors)
   - Variations (named sub-variants with descriptions)
   - Weight (relative: Heavy/Medium/Light/Accent + percentage)

2. **Pacing & Sequencing Rules** — shot duration ranges, sequencing constraints, transition patterns

3. **Type Selection Decision Tree** — IF/THEN rules mapping narrative situations to building blocks

4. **Quick Reference** — table mapping building blocks to shotlist types and weights

### Expected metrics

| Metric | v3 | v4 |
|--------|-----|-----|
| Output length | ~400 lines | ~150-200 lines |
| Building blocks | 30+ subtypes | 10-15 blocks |
| Frame references in output | Yes (Examples table) | Zero |
| Video-specific content | Descriptions, implementations | Only proportions |
| "When NOT to use" | Absent | Every block |
| Decision tree | Absent | Present |
| Pacing rules | Absent | Present |
| LLM synthesis calls | 0 | 1 subagent |

---

## 10. Execution Order

All steps are sequential (each depends on the previous):

1. Rewrite `analysis_prompt.txt`
2. Create `synthesis_prompt.txt`
3. Simplify `synthesize.py`
4. Update `pipeline.py`
5. Update `SKILL.md`
6. Update tests
7. Integration test with a YouTube URL
