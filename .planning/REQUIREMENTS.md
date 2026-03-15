# Requirements: Channel Automation Pipeline

**Defined:** 2026-03-15
**Core Value:** Surface obscure, high-impact documentary topics backed by competitor data and deep web research — not guesswork.

## v1.3 Requirements

Requirements for Visual Orchestrator (Agent 1.4). Each maps to roadmap phases.

### Shot List Generation

- [ ] **SHOT-01**: Skill parses Script.md chapter structure (## N. Title) and generates shots grouped by chapter
- [ ] **SHOT-02**: Shot boundaries follow narrative beats (visual subject changes: era, location, figure, evidence type) — not paragraphs or sentences
- [ ] **SHOT-03**: Each shot has sequential ID (S001, S002...), chapter number, narrative_context, visual_need, and suggested_types
- [ ] **SHOT-04**: `visual_need` descriptions are specific enough for acquisition search queries (era + location + subject, no production terms)
- [ ] **SHOT-05**: Visual variety enforced — mix of asset types across the shot list, not repeated suggested_types
- [ ] **SHOT-06**: Each chapter begins with an establishing/orienting shot (geographic, temporal, or contextual)
- [ ] **SHOT-07**: Abstract narration with no visual record routes to vector/animation types, not archival

### Skill Infrastructure

- [x] **INFRA-01**: Pure [HEURISTIC] skill — SKILL.md + CONTEXT.md + prompts/generation.md, zero Python code
- [x] **INFRA-02**: CONTEXT.md documents pipeline-reset invariant (shotlist.json + manifest.json atomically coupled)
- [ ] **INFRA-03**: CLAUDE.md updated with visual-orchestrator task routing and context loading entries

## Future Requirements

### Enhanced Visual Orchestration

- **SHOT-08**: Two-pass generation (annotate beats first, then assign types) for improved consistency
- **SHOT-09**: VISUAL_STYLE_GUIDE.md integration for building block vocabulary and type decision tree
- **SHOT-10**: Shot density calibration based on chapter word count (short chapters: 5-8 shots, long: 12-18)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Shot duration/timing | Editor's domain — Architecture.md explicitly excludes |
| Camera angles/movement | Not an acquisition pipeline — no shoot, only source |
| Effects/transitions | Post-production decisions for DaVinci Resolve |
| Priority/importance scoring | Adds complexity without clear value — acquisition gets all shots |
| Python CLI or context-loader | Zero-code heuristic skill — Claude reads files directly |
| VISUAL_STYLE_GUIDE dependency | Baseline schema only — no style guide input for v1.3 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SHOT-01 | Phase 14 | Pending |
| SHOT-02 | Phase 14 | Pending |
| SHOT-03 | Phase 14 | Pending |
| SHOT-04 | Phase 14 | Pending |
| SHOT-05 | Phase 14 | Pending |
| SHOT-06 | Phase 14 | Pending |
| SHOT-07 | Phase 14 | Pending |
| INFRA-01 | Phase 13 | Complete |
| INFRA-02 | Phase 13 | Complete |
| INFRA-03 | Phase 15 | Pending |

**Coverage:**
- v1.3 requirements: 10 total
- Mapped to phases: 10
- Unmapped: 0

---
*Requirements defined: 2026-03-15*
*Last updated: 2026-03-15 after roadmap creation*
