# Phase 11: Style Extraction Skill - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Extract channel voice from reference scripts in `context/script-references/` into a reusable `context/channel/STYLE_PROFILE.md` behavioral ruleset. The skill is HEURISTIC — zero Python code, implemented entirely as a SKILL.md prompt. It replaces the existing `writting_style_guide.md`.

</domain>

<decisions>
## Implementation Decisions

### Reference Script Processing
- Skill includes a "reconstruct" first pass — Claude cleans auto-captions into proper prose before extracting style patterns
- Cleaned version saved to `context/script-references/` alongside original (e.g., `[Title]_clean.md`)
- Skill should detect format — only reconstruct auto-captions, skip already-clean scripts
- Strip all bracket tags (`[Music]`, `[Applause]`) during reconstruction — pure narration text only

### Profile Structure
- Each voice rule follows: Rule definition → Do-this examples (verbatim from script) → Not-this counter-examples (generated)
- Include sentence rhythm analysis with examples — short/long patterns, paragraph cadence, emotional beat shifts
- STYLE_PROFILE.md replaces `writting_style_guide.md` entirely — single source of truth for voice and style
- Existing 6 rules from writting_style_guide.md get absorbed and expanded into the new profile
- Transition phrase library: 10-20 phrases, categorized by function (temporal, causal, contrast, escalation)

### Invocation & Workflow
- One-shot with review: Claude reads all scripts in `context/script-references/`, does reconstruct + extract passes, writes STYLE_PROFILE.md, presents summary for human review before committing
- Processes all scripts in the directory — no file path arguments needed
- Full overwrite on re-run — each invocation produces a fresh profile from all current scripts (previous version in git history)
- Auto-wire: after writing STYLE_PROFILE.md, skill updates CLAUDE.md routing table and removes/archives `writting_style_guide.md`

### Narrative Arc Templates
- Capture structure + pacing patterns: chapter count range, act progression (setup→escalation→resolution), pacing rules, chapter connections
- "Truth-Seeking Coda" captured as optional/conditional pattern — when topic has widespread misinformation, end with a chapter confronting it
- Dedicated "Open Ending Template" section with: when to use (unsolved cases), structure (present evidence → acknowledge unknowns → leave weight with audience), crafted examples in channel voice
- Hook pattern extracted: quote opening → compressed story overview → "this is the true story of…" formula — captured as reusable but flexible template

### Claude's Discretion
- Exact number and naming of voice rules (extracted from analysis, not predetermined)
- How to structure the format detection (auto-captions vs clean scripts)
- Internal organization of STYLE_PROFILE.md beyond the required sections
- How to handle edge cases in rhythm analysis

</decisions>

<specifics>
## Specific Ideas

- The reference script opens with a direct quote from a source ("it was the worst thing I've had to deal with in all my years") — this hook pattern is distinctive and should be captured
- Chapter titles use evocative naming ("Strangers in the Jungle", "Initial Control") rather than descriptive summaries — capture this register
- The "Truth: 2024" meta-commentary chapter is a signature element worth preserving as an optional pattern
- Counter-examples should show what generic/clickbait documentary narration sounds like (emotional inflation, intensifiers) to make the contrast with channel voice clear

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `context/channel/channel.md`: Channel DNA (voice, tone, pillars, audience) — STYLE_PROFILE.md complements but does not duplicate this
- `context/channel/writting_style_guide.md`: 6-rule placeholder — to be replaced by STYLE_PROFILE.md
- `context/script-references/Mexico's Most Disturbing Cult.md`: 496-line auto-caption export — the single current reference script

### Established Patterns
- Skill structure: SKILL.md defines invocation, CONTEXT.md defines stage contract (see channel-assistant, researcher, visual-style-extractor)
- Heuristic skills have no Python code — Claude does all reasoning (Architecture.md Rule 2)
- Context files live in `context/channel/` as channel-level artifacts

### Integration Points
- CLAUDE.md routing table: needs "Style extraction" row added, "Script writing" row updated to reference STYLE_PROFILE.md
- Phase 12 (Writer Agent): will load STYLE_PROFILE.md as primary style context
- `context/channel/`: STYLE_PROFILE.md joins channel.md and past_topics.md as persistent reference

</code_context>

<deferred>
## Deferred Ideas

- Multi-reference blending (REFINE-03) — future requirement, not Phase 11 scope
- Automated style drift detection between generated scripts and profile — future quality gate

</deferred>

---

*Phase: 11-style-extraction-skill*
*Context gathered: 2026-03-14*
