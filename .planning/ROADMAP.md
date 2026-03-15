# Roadmap: Channel Automation Pipeline

## Milestones

- ✅ **v1.0 Channel Assistant** — Phases 1-6 (shipped 2026-03-11)
- ✅ **v1.1 The Researcher** — Phases 7-10 (shipped 2026-03-14)
- ✅ **v1.2 The Writer** — Phases 11-12 (shipped 2026-03-15)
- 🚧 **v1.3 The Director** — Phases 13-15 (in progress)

## Phases

<details>
<summary>✅ v1.0 Channel Assistant (Phases 1-6) — SHIPPED 2026-03-11</summary>

- [x] Phase 1: Scraping Infrastructure + Data Model (2/2 plans) — completed 2026-03-11
- [x] Phase 2: Query Layer + Competitor Analysis (3/3 plans) — completed 2026-03-11
- [x] Phase 3: Topic Generation + Scoring (2/2 plans) — completed 2026-03-11
- [x] Phase 4: Project Initialization + Metadata (2/2 plans) — completed 2026-03-11
- [x] Phase 5: Trend Scanning + Content Gaps (2/2 plans) — completed 2026-03-11
- [x] Phase 6: Tech Debt Cleanup + OUTP-02 Wiring (1/1 plan) — completed 2026-03-11

</details>

<details>
<summary>✅ v1.1 The Researcher (Phases 7-10) — SHIPPED 2026-03-14</summary>

- [x] Phase 7: Scraping Foundation (2/2 plans) — completed 2026-03-12
- [x] Phase 8: Survey Pass (2/2 plans) — completed 2026-03-14
- [x] Phase 9: Deep-Dive Pass (1/1 plan) — completed 2026-03-14
- [x] Phase 10: Dossier Output (3/3 plans) — completed 2026-03-14

</details>

<details>
<summary>✅ v1.2 The Writer (Phases 11-12) — SHIPPED 2026-03-15</summary>

- [x] Phase 11: Style Extraction Skill (2/2 plans) — completed 2026-03-14
- [x] Phase 12: Writer Agent (2/2 plans) — completed 2026-03-15

</details>

### 🚧 v1.3 The Director (In Progress)

**Milestone Goal:** Build the Visual Orchestrator skill that parses finished scripts into structured shot lists, bridging narrative engineering (Phase 1) to the asset pipeline (Phase 2).

- [ ] **Phase 13: Stage Contract** — CONTEXT.md with pipeline-reset invariant and stage boundaries
- [ ] **Phase 14: Generation Prompt** — generation.md with full schema, granularity rules, and anti-patterns
- [ ] **Phase 15: Skill Entry Point** — SKILL.md invocation workflow and CLAUDE.md routing update

## Phase Details

### Phase 13: Stage Contract
**Goal**: The Visual Orchestrator skill's contract is locked — inputs, outputs, process, and the pipeline-reset invariant are documented so the skill can be invoked without ambiguity.
**Depends on**: Phase 12 (Writer Agent ships Script.md as input)
**Requirements**: INFRA-01, INFRA-02
**Success Criteria** (what must be TRUE):
  1. CONTEXT.md exists at `.claude/skills/visual-orchestrator/CONTEXT.md` and defines the skill as a pure [HEURISTIC] skill with zero Python code
  2. CONTEXT.md documents inputs (Script.md, VISUAL_STYLE_GUIDE.md, prompts/generation.md), numbered process steps, and outputs (shotlist.json path)
  3. CONTEXT.md explicitly documents the pipeline-reset invariant: shotlist.json and manifest.json are atomically coupled; any Script.md change requires full regeneration of both
  4. CONTEXT.md lists deferred items (shot duration, timing, camera movement, effects, transitions) so future contributors know what is out of scope by design
**Plans**: 1 plan

Plans:
- [ ] 13-01-PLAN.md — Write CONTEXT.md for visual-orchestrator skill

### Phase 14: Generation Prompt
**Goal**: The generation prompt encodes all reasoning needed to turn a Script.md into a valid shotlist.json — schema definition, granularity rules, type routing, and anti-patterns — so Claude can generate correctly on first invocation.
**Depends on**: Phase 13
**Requirements**: SHOT-01, SHOT-02, SHOT-03, SHOT-04, SHOT-05, SHOT-06, SHOT-07
**Success Criteria** (what must be TRUE):
  1. generation.md produces shots grouped by chapter (## N. Title parsing), with chapter 0 for prologues and sequential IDs (S001, S002...) never resetting per chapter
  2. Shot boundaries follow narrative beat changes (era, location, figure, evidence type), not paragraph or sentence boundaries — each chapter has a minimum of 2 shots and no single narrative_context spans more than 450 words of narration
  3. Each shot entry contains all required fields: id, chapter, chapter_title, narrative_context (max 50-word paraphrase, not transcription), visual_need, building_block, shotlist_type, building_block_variant, text_content, and suggested_sources
  4. visual_need descriptions are specific enough for acquisition search queries: era + geography + subject with no cinematographer language ("slow dolly", "close-up") — the generation prompt includes explicit side-by-side WRONG/RIGHT examples
  5. Abstract narration with no visual record routes to vector or animation shotlist_type values, not archival — each chapter begins with an establishing/orienting shot before detail shots
**Plans**: TBD

Plans:
- [ ] 14-01: Write prompts/generation.md for visual-orchestrator skill

### Phase 15: Skill Entry Point
**Goal**: The skill is discoverable and invocable — SKILL.md provides a 3-step invocation workflow and CLAUDE.md routes visual planning tasks to the skill.
**Depends on**: Phase 14
**Requirements**: INFRA-03
**Success Criteria** (what must be TRUE):
  1. SKILL.md exists at `.claude/skills/visual-orchestrator/SKILL.md` with 3-step invocation: (1) resolve project directory and identify/disambiguate VISUAL_STYLE_GUIDE, (2) read Script.md and guide, (3) generate and write shotlist.json
  2. SKILL.md explicitly handles the case where multiple VISUAL_STYLE_GUIDE.md files exist in context/visual-references/ — asks user which to apply rather than guessing
  3. CLAUDE.md task routing table includes a "Create shot list" row pointing to visual-orchestrator and CONTEXT.md; "What to Load" table includes a visual planning row specifying visual-references/ and the project script as inputs
**Plans**: TBD

Plans:
- [ ] 15-01: Write SKILL.md and update CLAUDE.md routing

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Scraping Infrastructure + Data Model | v1.0 | 2/2 | Complete | 2026-03-11 |
| 2. Query Layer + Competitor Analysis | v1.0 | 3/3 | Complete | 2026-03-11 |
| 3. Topic Generation + Scoring | v1.0 | 2/2 | Complete | 2026-03-11 |
| 4. Project Initialization + Metadata | v1.0 | 2/2 | Complete | 2026-03-11 |
| 5. Trend Scanning + Content Gaps | v1.0 | 2/2 | Complete | 2026-03-11 |
| 6. Tech Debt Cleanup + OUTP-02 Wiring | v1.0 | 1/1 | Complete | 2026-03-11 |
| 7. Scraping Foundation | v1.1 | 2/2 | Complete | 2026-03-12 |
| 8. Survey Pass (Pass 1) | v1.1 | 2/2 | Complete | 2026-03-14 |
| 9. Deep-Dive Pass (Pass 2) | v1.1 | 1/1 | Complete | 2026-03-14 |
| 10. Dossier Output | v1.1 | 3/3 | Complete | 2026-03-14 |
| 11. Style Extraction Skill | v1.2 | 2/2 | Complete | 2026-03-14 |
| 12. Writer Agent | v1.2 | 2/2 | Complete | 2026-03-15 |
| 13. Stage Contract | v1.3 | 0/1 | Not started | - |
| 14. Generation Prompt | v1.3 | 0/1 | Not started | - |
| 15. Skill Entry Point | v1.3 | 0/1 | Not started | - |
