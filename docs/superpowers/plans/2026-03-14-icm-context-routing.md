# ICM Context Routing Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adopt ICM's layered context routing — folder map, task routing table, stage contracts with checkpoints, and "docs over outputs" convention — so every current and future agent loads minimal, precise context.

**Architecture:** Add a folder map and "What to Load" table to CLAUDE.md (Layer 0-1), create CONTEXT.md stage contracts for each skill (Layer 2), and formalize checkpoints and quality audits as structured tables within those contracts. No code changes — all markdown.

**Tech Stack:** Markdown only. No code, no tests, no dependencies.

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `CLAUDE.md` | Add folder map, task routing table, "What to Load", conventions |
| Create | `.claude/skills/channel-assistant/CONTEXT.md` | Stage contract: Inputs/Process/Checkpoints/Outputs |
| Create | `.claude/skills/researcher/CONTEXT.md` | Stage contract: Inputs/Process/Checkpoints/Audit/Outputs |
| Create | `.claude/skills/visual-style-extractor/CONTEXT.md` | Stage contract: Inputs/Process/Outputs |

---

## Chunk 1: CLAUDE.md Enhancements

### Task 1: Add Folder Map to CLAUDE.md

**Files:**
- Modify: `CLAUDE.md:1-45`

- [ ] **Step 1: Add folder map after Project Overview section**

Insert after line 7 (after the project overview paragraph), before `## Context`:

```markdown
## Folder Map

```
Channel-automation V3/
├── CLAUDE.md                     # Project instructions (you are here)
├── Architecture.md               # Full pipeline spec (Phases 1-2)
├── context/                      # Persistent reference material (read-only)
│   ├── channel/
│   │   ├── channel.md            # Channel DNA: voice, tone, pillars, audience
│   │   ├── past_topics.md        # Previously covered topics (dedup safety)
│   │   └── writting_style_guide.md  # Narration style rules
│   ├── competitors/
│   │   ├── competitors.json      # Registered channel registry
│   │   └── analysis.md           # Stats, outliers, trends, topic clusters
│   ├── script-references/        # Full reference scripts (style extraction)
│   ├── topics/
│   │   └── topic_briefs.md       # Generated topic briefs
│   └── visual-references/        # Extracted visual style guides per video
│       └── [Video Name]/
│           └── VISUAL_STYLE_GUIDE.md
├── projects/                     # Per-video project directories
│   └── N. [Video Title]/
│       ├── metadata.md           # Topic brief, title variants, description
│       └── research/             # Research dossier outputs
│           ├── Research.md       # 9-section narrative dossier
│           ├── media_urls.md     # Visual media catalog
│           └── source_manifest.json
├── .claude/
│   ├── skills/                   # Agent skills (deterministic code + prompts)
│   │   ├── channel-assistant/    # Agent 1.1: Topics, competitors, project init
│   │   ├── researcher/           # Agent 1.2: Two-pass research pipeline
│   │   ├── visual-style-extractor/  # Frame analysis → visual patterns
│   │   └── crawl4ai-scraper/     # Web scraping utility
│   └── scratch/                  # Transient data (gitignored, ephemeral)
├── data/
│   └── channel_assistant.db      # SQLite: competitors & videos
├── tests/                        # pytest test suite
└── docs/                         # Plans, specs, documentation
```
```

- [ ] **Step 2: Verify the edit rendered correctly**

Read `CLAUDE.md` and confirm the folder map is present and properly formatted.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add folder map to CLAUDE.md (ICM Layer 0)"
```

---

### Task 2: Add Task Routing Table and "What to Load" to CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Replace the existing `## Context` section with a routing table**

Replace the current `## Context` section (lines 10-18, the `@Architecture.md` reference list) with:

```markdown
## Context & Routing

### Task Routing

| Task | Skill | Entry Point |
|------|-------|-------------|
| Add/scrape/analyze competitors | channel-assistant | `cmd_add`, `cmd_scrape`, `cmd_analyze` |
| Generate topic ideas | channel-assistant | `cmd_topics` + Claude heuristic |
| Initialize video project | channel-assistant | `cmd_init_project` |
| Research a topic | researcher | `survey` → evaluate → `deepen` → `write` |
| Extract visual style | visual-style-extractor | 6-stage pipeline |
| Write script | *(not yet implemented)* | — |
| Create shot list | *(not yet implemented)* | — |

### What to Load

| Task | Load | Skip (and why) |
|------|------|----------------|
| Topic ideation | channel.md, past_topics.md, analysis.md, channel-assistant/CONTEXT.md | visual-references/, script-references/ — not relevant to topic selection |
| Research | channel.md, researcher/CONTEXT.md, projects/N/metadata.md | competitors/, visual-references/ — research is topic-focused |
| Style extraction | visual-style-extractor/CONTEXT.md, target video/URL | Everything else — self-contained pipeline |
| Script writing *(future)* | channel.md, writting_style_guide.md, script-references/, projects/N/research/Research.md | competitors/ — writer needs voice + research, not strategy |
| Visual planning *(future)* | visual-references/*/VISUAL_STYLE_GUIDE.md, projects/N/script.md | competitors/, channel.md — director needs visuals + script |

### Reference Files

- `Architecture.md` — Full pipeline specification (Phases 1-2)
- `context/channel/channel.md` — Channel DNA (voice, tone, pillars, audience)
- `context/channel/past_topics.md` — Past topics to avoid duplication
```

- [ ] **Step 2: Verify the edit**

Read `CLAUDE.md` and confirm the routing table replaced the old context list cleanly.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add task routing and What to Load tables (ICM Layer 1)"
```

---

### Task 3: Add Conventions Section to CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add conventions section before `## Coding Standards`**

Insert before the `## Coding Standards` section:

```markdown
## Conventions

### Docs Over Outputs
Reference docs (`prompts/`, `context/`) are authoritative sources of truth. Previous project outputs (`projects/*/research/`) are artifacts, NOT templates. Agents never read other projects' outputs to learn patterns — they use prompt files and context files.

### Stage Contracts
Every skill has a `CONTEXT.md` that defines its Inputs, Process, Checkpoints, and Outputs. When invoking a skill as an agent, load `CONTEXT.md` for routing — load `SKILL.md` only when the user needs usage help.

### Canonical Sources
Every piece of information has ONE home. Other files point to it — they don't duplicate it. Channel voice rules live in `context/channel/channel.md`, not repeated in prompts or skill docs.
```

- [ ] **Step 2: Also update the Skills section**

Replace the current `## Skills` section (which lists yt-dlp, crawl4ai, remotion) with one that includes the pipeline skills:

```markdown
## Skills

### Pipeline Skills
| Skill | Agent | Purpose |
|-------|-------|---------|
| `channel-assistant` | 1.1 | Competitor intel, topic ideation, project init |
| `researcher` | 1.2 | Two-pass web research → narrative dossier |
| `visual-style-extractor` | — | Reference video → visual pattern toolkit |

### Utility Skills
| Skill | Purpose |
|-------|---------|
| `crawl4ai-scraper` | Web scraping (used by researcher) |
| `yt-dlp` | Video/audio downloading |
| `remotion` | Animation best practices (future) |
```

- [ ] **Step 3: Clean up the broken "Keeping Context Current" section**

The current line 20-21 reads `## Keeping Context Current\n- Update '` — this is truncated/broken. Remove it entirely (it's an incomplete fragment).

- [ ] **Step 4: Verify all edits**

Read full `CLAUDE.md` and verify: folder map, routing tables, conventions, skills table, no broken sections.

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add conventions, update skills table, clean up CLAUDE.md"
```

---

## Chunk 2: Skill CONTEXT.md Contracts

### Task 4: Create channel-assistant CONTEXT.md

**Files:**
- Create: `.claude/skills/channel-assistant/CONTEXT.md`

- [ ] **Step 1: Write the stage contract**

```markdown
# Channel Assistant — Stage Contract

Select viable topics and initialize video projects for the dark mysteries channel.

## Inputs
| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Channel DNA | context/channel/channel.md | "Core Content Pillars", "Topic Selection Criteria" | Topic filtering rules |
| Past topics | context/channel/past_topics.md | Full file | Deduplication safety |
| Competitor data | context/competitors/analysis.md | Full file | Topic clusters, title patterns, outliers |
| Prompt | prompts/topic_generation.md | Full file | Scoring rubric |
| Prompt | prompts/trends_analysis.md | Full file | Content gap scoring |
| Prompt | prompts/project_init.md | Full file | Title/description generation |

## Process
1. [DETERMINISTIC] `scrape` — refresh competitor video data from YouTube
2. [DETERMINISTIC] `analyze` — compute stats, outliers, trend scan → write analysis.md
3. [HEURISTIC] Claude completes Topic Clusters + Title Patterns in analysis.md
4. [DETERMINISTIC] `topics` — load context for topic generation
5. [HEURISTIC] Claude generates 5 scored briefs → writes topic_briefs.md
6. [DISPLAY] Claude outputs formatted markdown cards in chat
7. User selects topic number
8. [HEURISTIC] Claude generates title variants + description
9. [DETERMINISTIC] `init_project()` → creates project directory + metadata.md

## Checkpoints
| After Step | Agent Presents | Human Decides |
|------------|---------------|---------------|
| Step 6 | 5 scored topic cards with briefs | Which topic to pursue (or regenerate) |
| Step 8 | 3-5 title variants + YouTube description | Final title for project init |

## Outputs
| Artifact | Location | Format |
|----------|----------|--------|
| Competitor analysis | context/competitors/analysis.md | Stats, outliers, clusters |
| Topic briefs | context/topics/topic_briefs.md | 5 scored briefs |
| Project metadata | projects/N. [Title]/metadata.md | Title variants, description, brief |
```

- [ ] **Step 2: Verify file was created**

Read `.claude/skills/channel-assistant/CONTEXT.md` and confirm format matches ICM stage contract pattern.

- [ ] **Step 3: Commit**

```bash
git add ".claude/skills/channel-assistant/CONTEXT.md"
git commit -m "docs: add channel-assistant stage contract (ICM Layer 2)"
```

---

### Task 5: Create researcher CONTEXT.md

**Files:**
- Create: `.claude/skills/researcher/CONTEXT.md`

- [ ] **Step 1: Write the stage contract with audit**

```markdown
# Researcher — Stage Contract

Build a factual foundation for a documentary topic through two-pass web research.

## Inputs
| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Project | projects/N. [Title]/metadata.md | "Topic Brief" section | Topic scope and angle |
| Channel DNA | context/channel/channel.md | "Core Content Pillars" | Depth and tone calibration |
| Prompt | prompts/survey_evaluation.md | Full file | Source evaluation rubric |
| Prompt | prompts/synthesis.md | Full file | 9-section dossier template |

## Process
1. [DETERMINISTIC] `survey "Topic"` — fetch Wikipedia + DuckDuckGo → `src_NNN.json`
2. [HEURISTIC] Evaluate sources using survey_evaluation.md → annotate `source_manifest.json`
3. [DETERMINISTIC] `deepen "Topic"` — fetch deep-dive URLs from manifest → `pass2_NNN.json`
4. [DETERMINISTIC] `write "Topic"` — aggregate all sources → `synthesis_input.md`
5. [HEURISTIC] Synthesize using synthesis.md → `Research.md` + `media_urls.md`

## Checkpoints
| After Step | Agent Presents | Human Decides |
|------------|---------------|---------------|
| Step 2 | Source verdict summary table | Proceed to deep dive, add/remove sources, or redirect |
| Step 5 | Research.md summary (sections + word count) | Accept, request revisions, or add missing sources |

## Audit (after Step 5, before writing final output)
| Check | Pass Condition |
|-------|---------------|
| Source diversity | ≥3 distinct source domains cited |
| Timeline populated | Timeline section has ≥5 dated entries |
| Contradictions addressed | Section 7 is non-empty OR explicitly states "no contradictions found" |
| Media inventory | ≥5 media URLs cataloged in media_urls.md |
| No fabrication | Every claim in Subject Overview traces to a source in Sections 4-5 |

## Outputs
| Artifact | Location | Format |
|----------|----------|--------|
| Research dossier | projects/N. [Title]/research/Research.md | 9-section markdown (~2000 words) |
| Media catalog | projects/N. [Title]/research/media_urls.md | URLs grouped by asset type |
| Source manifest | projects/N. [Title]/research/source_manifest.json | Verdicts + deep-dive URLs |
```

- [ ] **Step 2: Verify file**

Read `.claude/skills/researcher/CONTEXT.md` and confirm it matches ICM stage contract format.

- [ ] **Step 3: Commit**

```bash
git add ".claude/skills/researcher/CONTEXT.md"
git commit -m "docs: add researcher stage contract with audit (ICM Layer 2)"
```

---

### Task 6: Create visual-style-extractor CONTEXT.md

**Files:**
- Create: `.claude/skills/visual-style-extractor/CONTEXT.md`

- [ ] **Step 1: Write the stage contract**

```markdown
# Visual Style Extractor — Stage Contract

Extract visual patterns from a reference video into a reusable decision framework.

## Inputs
| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Video | YouTube URL or local video + transcript | Full file | Source material for analysis |
| Analysis prompt | prompts/analysis_prompt.txt | Full file | Frame-to-pattern analysis rules |
| Synthesis prompt | prompts/synthesis_prompt.txt | Full file | Pattern merging into building blocks |

## Process
1. [DETERMINISTIC] Stage 0: Acquire video + transcript (yt-dlp or local)
2. [DETERMINISTIC] Stage 1: Scene detection → keyframes + scenes.json
3. [DETERMINISTIC] Stage 2: Perceptual hash deduplication → deduplicated frames
4. [DETERMINISTIC] Stage 3: Transcript alignment → frames with narration context
5. [DETERMINISTIC] Stage 4: Contact sheet generation → 3×3 grids (1568×1568px)
6. [HEURISTIC] Stage 5: Parallel subagents analyze contact sheets → pattern JSON batches
7. [DETERMINISTIC] Merge analysis batches → merged_analysis.json
8. [HEURISTIC] Stage 6: Synthesis subagent → VISUAL_STYLE_GUIDE.md

## Checkpoints
| After Step | Agent Presents | Human Decides |
|------------|---------------|---------------|
| Step 5 (Stages 0-4) | Scene count, frame count, dedup ratio | Accept or adjust thresholds |
| Step 8 (Stage 6) | Building block count + path to guide | Review guide, re-run if needed |

## Outputs
| Artifact | Location | Format |
|----------|----------|--------|
| Visual style guide | context/visual-references/[Video]/VISUAL_STYLE_GUIDE.md | 10-15 building blocks |
| Frames manifest | context/visual-references/[Video]/frames_manifest.json | Frame metadata |
| Contact sheets | context/visual-references/[Video]/contact_sheets/ | 3×3 grid JPEGs |
| Dedup report | context/visual-references/[Video]/dedup_report.json | Merge decisions |
```

- [ ] **Step 2: Verify file**

Read `.claude/skills/visual-style-extractor/CONTEXT.md` and confirm format.

- [ ] **Step 3: Commit**

```bash
git add ".claude/skills/visual-style-extractor/CONTEXT.md"
git commit -m "docs: add visual-style-extractor stage contract (ICM Layer 2)"
```

---

## Chunk 3: Final Verification

### Task 7: Full Verification Pass

- [ ] **Step 1: Verify all 4 files are consistent**

Read each file and verify:
- `CLAUDE.md` folder map matches actual directory structure
- `CLAUDE.md` routing table references the correct skill names
- Each CONTEXT.md Inputs table references files that exist
- Each CONTEXT.md Outputs table matches the folder map in CLAUDE.md
- No duplication between CLAUDE.md and CONTEXT.md files (canonical sources principle)

- [ ] **Step 2: Verify CLAUDE.md is under ~120 lines**

Count lines in CLAUDE.md. Target: ≤120 lines. If over, trim redundant content. The routing table + folder map should replace verbose descriptions, not add to them.

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -A
git commit -m "docs: fix consistency issues from verification pass"
```

- [ ] **Step 4: Push**

```bash
git push
```
