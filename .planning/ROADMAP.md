# Roadmap: Channel Automation Pipeline

## Milestones

- ✅ **v1.0 Channel Assistant** — Phases 1-6 (shipped 2026-03-11)
- ✅ **v1.1 The Researcher** — Phases 7-10 (shipped 2026-03-14)
- 🔄 **v1.2 The Writer** — Phases 11-12 (active)

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

### v1.2 The Writer (Phases 11-12)

- [x] **Phase 11: Style Extraction Skill** - Extract channel voice from reference scripts into reusable STYLE_PROFILE.md (completed 2026-03-14)
- [ ] **Phase 12: Writer Agent** - Generate narrated chapter scripts from research dossiers using validated style context

## Phase Details

### Phase 11: Style Extraction Skill
**Goal**: Channel voice is captured as a reusable behavioral ruleset — not statistics — that any future Writer invocation can load as stable context
**Depends on**: Nothing (no code dependency; reference scripts already exist in `context/script-references/`)
**Requirements**: STYLE-01, STYLE-02, STYLE-03, STYLE-04, STYLE-05
**Success Criteria** (what must be TRUE):
  1. Running the style-extraction skill against the reference script produces `context/channel/STYLE_PROFILE.md` with named voice rules illustrated by verbatim examples from the reference
  2. STYLE_PROFILE.md contains a "Universal Voice Rules" section separable from a topic-specific "Narrative Arc Templates" section — so non-cult topics are not forced into the cult story arc
  3. STYLE_PROFILE.md includes a transition phrase library drawn verbatim from the reference script — generic connective language ("furthermore", "notably") is not present in a generated test passage that uses only the profile as style guidance
  4. STYLE_PROFILE.md includes an open-ending template that prevents artificial resolution of unsolved cases
  5. The skill is invocable via SKILL.md with no Python code — classification is HEURISTIC; zero Python files exist in the style-extraction skill directory
**Plans:** 2/2 plans complete
Plans:
- [ ] 11-01-PLAN.md — Create style-extraction skill infrastructure (SKILL.md, CONTEXT.md, extraction prompt)
- [ ] 11-02-PLAN.md — Invoke skill to produce STYLE_PROFILE.md, human review, wire into project

### Phase 12: Writer Agent
**Goal**: A completed, narrated video script exists in the project directory — written in the channel's voice, anchored to Research.md sources, with no hallucinated facts or production notes
**Depends on**: Phase 11 (STYLE_PROFILE.md must be committed and validated before meaningful script quality can be evaluated)
**Requirements**: SCRIPT-01, SCRIPT-02, SCRIPT-03, SCRIPT-04, SCRIPT-05, SCRIPT-06, SCRIPT-07
**Success Criteria** (what must be TRUE):
  1. Running `python -m writer load "<topic>"` aggregates Research.md + STYLE_PROFILE.md + channel.md and prints them to stdout — Claude then generates the script in the same session with no additional file loading required
  2. The generated Duplessis Orphans script contains numbered chapters with titles in the reference register (evocative, not generic) and pure narration text — no stage directions, visual cues, or production notes anywhere in the output
  3. Every factual claim in the script can be traced to a specific section of Research.md — no fact appears that is not present in the dossier
  4. Research.md HOOK and QUOTE callouts appear as chapter entry points or narration anchors in the generated script — they are not ignored or buried mid-chapter
  5. The generated script reaches 3,000-7,000 words and maintains the channel's calm, deadpan tone throughout — it does not shift to an emotionally heightened register in later chapters
**Plans:** 1/2 plans executed
Plans:
- [ ] 12-01-PLAN.md — Build writer skill (CLI, generation prompt, tests, skill docs)
- [ ] 12-02-PLAN.md — End-to-end validation (generate Duplessis Orphans script, human review, wire CLAUDE.md)

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
| 12. Writer Agent | 1/2 | In Progress|  | - |
