# Project Research Summary

**Project:** v1.3 Visual Orchestrator — Agent 1.4 (Shot List Generation)
**Domain:** Heuristic script-to-shot-list generation for archival documentary pipeline
**Researched:** 2026-03-15
**Confidence:** HIGH

## Executive Summary

The Visual Orchestrator (Agent 1.4) is a pure [HEURISTIC] skill that reads a finished `Script.md` and outputs `shotlist.json`. Research confirms this is the right classification: all reasoning is editorial judgment (what visual does this narrative beat need?), and the only deterministic work is resolving file paths and validating JSON schema. The correct template is the existing `style-extraction` skill — zero Python code, a single `generation.md` prompt, SKILL.md for invocation, and CONTEXT.md as the stage contract. No new dependencies are required; the entire stack is Python stdlib already present in the project.

The recommended approach is a single-pass, chapter-by-chapter generation where Claude reads Script.md and VISUAL_STYLE_GUIDE.md together and emits shot entries at narrative beat boundaries — not paragraph or sentence boundaries. The schema has evolved beyond Architecture.md's baseline: the actual generated Duplessis shotlist introduces `building_block`, `shotlist_type`, `building_block_variant`, `text_content`, and `suggested_sources` as fields that proved necessary in practice. This extended schema is the canonical target for the skill, not the Architecture.md baseline.

The primary risks are all prompt-design failures addressable before any generation attempt: production instruction creep in `visual_need`, under-specified visual needs that produce useless acquisition queries, wrong shot granularity in either direction, and JSON schema drift from narration quotes causing escaping failures. All have known mitigations that belong in `generation.md` as explicit fences with worked examples. A second risk category — shot ID instability across regenerations — is a pipeline design invariant (shotlist.json and manifest.json are atomically coupled; regeneration invalidates the manifest) that must be documented in CONTEXT.md, not handled in code.

---

## Key Findings

### Recommended Stack

No new dependencies for v1.3. The entire deterministic layer uses Python stdlib (`re`, `json`, `pathlib`, `argparse`). The skill follows the zero-code pattern of `style-extraction`: Claude performs all reasoning natively through Read/Write/Glob tools. There is no CLI to build, no PYTHONPATH to configure, no pip install step.

**Core technologies:**
- `re` (stdlib): Chapter boundary detection via `re.split()` on `## N.` headers — sufficient for Script.md's fixed format; no parsing library needed
- `json` (stdlib): Schema validation via manual `assert` checks on five required keys — no `jsonschema` library needed
- `pathlib` (stdlib): File discovery, already the project standard per CLAUDE.md
- Claude Code native tools: Glob for project path resolution, Read/Write for all file I/O — no CLI wrapping required

**Explicitly rejected:** `jsonschema` library (five flat keys do not justify 0.7MB install), spaCy/NLTK (script is clean prose, `re.split()` is sufficient), any LLM API wrapper (Architecture.md Rule 1 violation), Python context-loader CLI (Glob/Bash suffices for two-file resolution; style-extraction proves zero-code handles more complex workflows).

### Expected Features

**Must have (table stakes) — P1, required for Agent 2.1 to function at all:**
- Chapter mapping (`chapter` integer + `chapter_title` string) — Agent 2.1 groups acquisition by chapter; both fields required
- Sequential shot IDs in S001 format — referenced throughout Phase 2 manifest and gap analysis; never reset per chapter
- `visual_need` with era and location specificity — this is Agent 2.1's primary search query signal; must be concrete enough that two agents search the same source domain
- `building_block` matching VISUAL_STYLE_GUIDE names exactly — Agent 2.1 looks these up; invented names break the pipeline
- `shotlist_type` from the closed enum — routes acquisition: text_overlay shots are skipped, map/animation/vector flagged for Agents 2.2/2.3
- `narrative_context` as a concise paraphrase (max 50 words) — anchors acquisition to narration; must paraphrase, not transcribe
- `text_content` for text_overlay shots — verbatim text for editor-placed Quote Cards, Date Cards, Keyword Stingers
- `suggested_sources` as domain hints — archive.org, nfb.ca, wikimedia_commons; empty array for text_overlay
- `building_block_variant` — variant name from VISUAL_STYLE_GUIDE or null
- Every chapter covered — no narration chapter left without shot entries in Phase 2

**Should have (differentiators) — P2, improves acquisition quality significantly:**
- Visual variety enforcement: at least 4 distinct `shotlist_type` values across the full shot list; review distribution after generation
- Establishing/orienting shot at the start of each chapter (geographic, temporal, or contextual before detail shots)
- Correct routing of abstract narration to `vector` or `animation` types — prevents phantom gaps in Agent 2.1 from searching for assets that do not exist
- Shot count calibrated to chapter word count: short chapters (~400 words) warrant 5-8 shots; long chapters (700+ words) warrant 12-18 shots

**Defer (v2+):**
- Two-pass generation (annotate beats separately, then assign types) — adds context overhead without quality improvement at this schema complexity level; consider only if single-pass produces inconsistent building block assignments
- Dedicated abstract narration prompt section — add after first real generation reveals which cases are problematic

### Architecture Approach

The Visual Orchestrator is a single-prompt skill following the `style-extraction` pattern. Three files in `.claude/skills/visual-orchestrator/`: CONTEXT.md (stage contract), SKILL.md (invocation workflow), and `prompts/generation.md` (all reasoning instructions). No `scripts/` directory. Build order: CONTEXT.md first (locks the contract), then `generation.md` (where reasoning complexity lives), then SKILL.md (human-facing entry point). Validate `generation.md` against the existing Duplessis Script V1.md before committing — the existing shotlist.json is the quality baseline.

**Major components:**
1. `CONTEXT.md` — inputs/outputs/process/checkpoints; defines the pipeline-reset invariant (shotlist.json and manifest.json are atomically coupled)
2. `prompts/generation.md` — shot granularity rules, extended schema definition, building block application from VISUAL_STYLE_GUIDE decision tree, text overlay handling, JSON constraints, worked examples showing correct specificity
3. `SKILL.md` — 3-step invocation: resolve project + identify guide, read inputs, generate and write shotlist.json

**Extended schema (canonical — from actual Duplessis shotlist.json, NOT the Architecture.md baseline):**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `project` | string | Yes (top-level) | From project directory name |
| `guide_source` | string | Yes (top-level) | Which VISUAL_STYLE_GUIDE was applied |
| `generated` | ISO 8601 | Yes (top-level) | Generation timestamp |
| `id` | string | Yes | S001 sequential across all chapters |
| `chapter` | integer | Yes | 0 for prologue, 1+ for numbered chapters |
| `chapter_title` | string | Yes | Verbatim from Script.md heading |
| `narrative_context` | string | Yes | 1-2 sentence paraphrase, max 50 words |
| `visual_need` | string | Yes | Free text, era/location specific, no production terms |
| `building_block` | string | Yes | Exact match from VISUAL_STYLE_GUIDE |
| `shotlist_type` | enum | Yes | archival_video, archival_photo, text_overlay, map, animation, vector |
| `building_block_variant` | string or null | Yes | Variant from guide or null |
| `text_content` | string or null | Yes | Verbatim text for text_overlay; null for media shots |
| `suggested_sources` | array | Yes | Domain hints; [] for text_overlay |

### Critical Pitfalls

1. **Production instruction creep in `visual_need`** — Claude's training on film shot lists pulls toward cinematographer language ("slow dolly into archival photo"). The generation prompt must include explicit prohibitions with side-by-side examples: "WRONG: slow dolly into archival photograph of compound. RIGHT: aerial or wide view of remote rural compound, 1970s." Paste Architecture.md's exclusion rule verbatim as a constraint header in the prompt.

2. **Under-specified visual needs** — "Historical imagery" or "relevant footage" produces nothing actionable for Agent 2.1. Rule: the description must be specific enough that two independent acquisition agents would search the same source domain. Include three worked examples in the prompt showing correct specificity: era, geography, subject, medium.

3. **Wrong shot granularity (both directions)** — Too many shots (sentence-level) produces 200+ entries that are unmanageable for Agent 2.1. Too few (one per chapter) produces gaps with no visual anchoring. Target 3-6 shots per chapter for the prompt instruction; the actual Duplessis shotlist shows 8-15 is realistic for 700-word chapters. Set both a minimum (2 per chapter) and a maximum (no single `narrative_context` spanning more than 450 words of narration).

4. **JSON schema drift from narration text** — Script narration contains survivor quotes with quotation marks and apostrophes that break JSON string escaping. Rule: `narrative_context` must paraphrase, not transcribe. "Do not add fields not shown in the schema." Include a self-validation step in CONTEXT.md: Claude reads back the generated JSON and verifies all required fields are present before writing the file.

5. **Shot ID instability across regenerations** — Sequential IDs have no stable anchor to specific narrative moments. This is an intentional design trade-off documented as a pipeline invariant: shotlist.json and manifest.json are atomically coupled. Any Script.md change requires regenerating both from scratch. Document this in CONTEXT.md and SKILL.md explicitly — there is no merge operation, only full regeneration.

---

## Implications for Roadmap

The build is three deliverables in a clear dependency order, all achievable in a single milestone session validated against existing artifacts.

### Phase 1: Prompt Design (generation.md)

**Rationale:** The prompt is where all quality risk lives. Building and validating it first — against the existing Duplessis Script V1.md and shotlist.json — means reasoning constraints are tested before any skill infrastructure exists. This is the same order used for the Writer: write_script.md before cli.py.

**Delivers:** `prompts/generation.md` with: extended schema definition, shot granularity rules (with worked collapsing examples), explicit prohibitions on production terms with side-by-side examples, visual specificity calibration examples, full asset type taxonomy with usage triggers, chapter parsing instructions (prologue = chapter 0, verbatim title from heading), JSON escaping rules, self-validation step.

**Addresses features:** All P1 table-stakes features — chapter mapping, shot IDs, visual_need, building_block, shotlist_type, narrative_context, text_content, suggested_sources, building_block_variant.

**Avoids pitfalls:** 1 (production creep), 2 (vague visual needs), 3 (wrong granularity), 4 (JSON schema drift), 5 (visual monotony from prompt design side), 7 (verbatim narrative_context), 10 (chapter misread).

### Phase 2: Stage Contract (CONTEXT.md)

**Rationale:** The stage contract locks the pipeline invariant and provides the orchestrator routing reference. Must exist before SKILL.md so the invocation workflow has an authoritative document to reference.

**Delivers:** `CONTEXT.md` with: inputs table (Script.md, VISUAL_STYLE_GUIDE.md, prompts/generation.md), numbered process steps, checkpoint (human review via git diff after generation), outputs table (shotlist.json path), pipeline-reset invariant documented explicitly, deferred items (duration, priority, effects, transitions) listed.

**Avoids pitfalls:** 8 (shot ID instability — pipeline-reset invariant documented here), 9 (suggested_types as constraints — hint-not-constraint framing documented for Agent 2.1 handoff).

### Phase 3: Invocation Workflow (SKILL.md) + CLAUDE.md Update

**Rationale:** Written last because it references both the prompt file path and CONTEXT.md's defined inputs. Zero code means no integration risk. CLAUDE.md update registers the skill in routing so it is discoverable.

**Delivers:** `SKILL.md` with prerequisites, 3-step invocation workflow (resolve project + guide disambiguation, read inputs, generate and write), output path. CLAUDE.md task routing row added (`| Create shot list | visual-orchestrator | CONTEXT.md |`) and "What to Load" row added for visual planning.

**Implements:** Zero-code pure-heuristic skill pattern from style-extraction — no scripts/ directory, no CLI, no PYTHONPATH.

### Phase Ordering Rationale

- Prompt before contract: Testing generation.md against real artifacts (Duplessis Script V1.md + existing shotlist.json) reveals whether the schema definition and granularity rules are complete before the contract is locked.
- Contract before SKILL.md: Invocation steps reference the contract's defined inputs; writing SKILL.md without a locked CONTEXT.md creates documentation drift.
- Single session achievable: All three files are independent documents with no code imports or test suites. Each can be validated against existing project artifacts without new research.
- No Python phase: Architecture research confirms zero-code is the correct pattern. Adding a CLI is an explicitly documented anti-pattern in ARCHITECTURE.md — Glob/Bash performs project resolution directly.

### Research Flags

Phases with well-documented patterns (no additional research needed):
- **All phases:** The entire skill follows patterns already present in this codebase. `style-extraction` is the direct template. The Duplessis shotlist.json is a quality baseline. The Mexico Cult VISUAL_STYLE_GUIDE.md provides the type taxonomy. No external research required.

Validation checkpoint (not a research gap, but a required implementation step):
- **After Phase 1:** Run `generation.md` against Duplessis Script V1.md and compare output to the existing shotlist.json. If building block distribution or shot density diverges significantly from the baseline, revise granularity rules before proceeding to Phase 2.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Zero new dependencies confirmed by Architecture.md Rule 1 and direct inspection of all existing skill directories; style-extraction proves the zero-code pattern works for more complex workflows |
| Features | HIGH | Extended schema derived from the actual Duplessis shotlist.json artifact (60+ shots); Architecture.md defines the baseline and Phase 2 consumer contracts |
| Architecture | HIGH | Direct codebase inspection of style-extraction (the template), writer (the prompt-before-CLI build order), visual-style-extractor (two-pass — confirmed NOT to apply here); build order from actual file dependencies |
| Pitfalls | HIGH | Derived from Architecture.md binding constraints ("No duration, priority, effects"), actual Script V1.md content (quotes/apostrophes confirmed in narration), and documented LLM structured-output failure patterns (schema drift, production instruction training bias) |

**Overall confidence:** HIGH

### Gaps to Address

- **Shot density calibration:** PITFALLS research recommends 3-6 shots per chapter as the prompt target, but the actual Duplessis shotlist shows 8-15 per chapter is realistic for 700-word chapters. The prompt should express density as word-count proportional rather than a flat range. Resolve by counting shots-per-chapter in the Duplessis baseline during Phase 1 validation.

- **Multiple VISUAL_STYLE_GUIDE disambiguation:** SKILL.md Step 1 must handle the case where multiple guides exist in `context/visual-references/`. Current recommendation: ask the user which to apply. This is correct but must be written as an explicit conditional in SKILL.md to avoid ambiguous behavior at invocation time.

- **Schema naming mismatch (suggested_types vs. suggested_sources):** Architecture.md baseline uses `suggested_types`; the actual Duplessis shotlist uses `suggested_sources` + `shotlist_type` as separate fields serving distinct purposes. The generation.md prompt and SKILL.md must reference the extended schema exclusively — any reference to the Architecture.md baseline schema risks regenerating with the wrong field names, breaking Agent 2.1.

---

## Sources

### Primary (HIGH confidence)

- `Architecture.md` — Agent 1.4 spec, Phase 2 pipeline design, asset type taxonomy, CRITICAL ARCHITECTURE RULES (Rule 1: no LLM wrappers; Rule 2: HEURISTIC/DETERMINISTIC classification)
- `projects/1. The Duplessis Orphans.../shotlist.json` — canonical extended schema from actual generation (60+ shots); quality and density baseline
- `projects/1. The Duplessis Orphans.../Script V1.md` — actual Script.md format, chapter structure (`## N. Title`), narration density, survivor testimony (confirms quote/apostrophe escaping risk)
- `.claude/skills/style-extraction/` (SKILL.md, CONTEXT.md, prompts/extraction.md) — direct zero-code template for the Visual Orchestrator's skill structure
- `.claude/skills/writer/` (SKILL.md, CONTEXT.md, prompts/generation.md) — prompt structure reference and prompt-before-CLI build order
- `context/visual-references/Mexico's Most Disturbing Cult/VISUAL_STYLE_GUIDE.md` — type taxonomy and building block vocabulary source
- `.planning/PROJECT.md` — v1.3 milestone requirements and [HEURISTIC] classification

### Secondary (MEDIUM confidence)

- [Desktop Documentaries — How To Create A Shot List For Your Documentary](https://www.desktop-documentaries.com/create-a-shot-list.html) — professional documentary shot list conventions (narrative anchor, visual subject, media type, sequence position)
- [StudioBinder — How to Create a Documentary Shot List](https://www.studiobinder.com/blog/documentary-shot-list-template/) — confirmed what shot lists do NOT contain (camera angles, timing, transitions, music, color)
- [Fiveable — Pacing and Rhythm in Narrative Documentary Production](https://fiveable.me/narrative-documentary-production/unit-6/pacing-rhythm/study-guide/wA0rkICSeb7KoDNi) — archival documentary pacing: 1 shot every 4-12 seconds, beat-based not paragraph-based
- [Fiveable — Narrative Structure in Documentary Editing](https://fiveable.me/documentary-production/unit-12/narrative-structure-documentary-editing/study-guide/ImaHZdcuYc8nDo5i) — beat definition for archival narration documentary context

### Tertiary (inference from known patterns)

- LLM structured-output failure modes — JSON escaping errors from rich text field values, schema field drift ("helpful" extra fields), production instruction training bias when prompted for "shot list" without explicit schema constraints; all documented behaviors that directly inform the pitfall prevention strategies

---
*Research completed: 2026-03-15*
*Ready for roadmap: yes*
