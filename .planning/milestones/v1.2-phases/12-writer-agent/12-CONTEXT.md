# Phase 12: Writer Agent - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Generate narrated chapter scripts from research dossiers using validated style context. The writer reads Research.md + STYLE_PROFILE.md + channel.md, applies the channel's voice rules, and produces a pure-narration Script.md in the project directory. CLI is a thin stdlib context-loader; Claude does all reasoning.

</domain>

<decisions>
## Implementation Decisions

### Arc Construction
- Writer derives chapter structure from Research.md content — timeline, hooks, key figures, and narrative tension points determine natural chapter breaks
- No predefined arc template required; Universal Voice Rules from STYLE_PROFILE.md apply to all topics regardless of arc shape
- Soft guardrail: 4-7 chapters per script (matches channel.md target of 4-7 acts)
- Per-chapter word count is not enforced — natural flow determines chapter length
- Open Ending Template from STYLE_PROFILE.md is applied when the topic qualifies (contested resolution, permanently incomplete record, moral weight in not-knowing)

### HOOK/QUOTE Consumption
- Writer selects a best subset of HOOKs from Research.md — the dossier is a buffet, not a checklist. Typically 2-4 hooks per script
- The strongest HOOK becomes the video's opening, following STYLE_PROFILE's 4-part hook formula: quote → compressed overview → optional misinformation flag → "This is the true story of…" closing formula. This formula is always followed.
- Remaining selected HOOKs anchor chapter entry points — they're the reason a new chapter begins
- QUOTEs appear verbatim as direct speech with inline attribution. The narrator introduces the speaker, the quote speaks, the narrator resumes. Example: 'As Nestor would later say: "When you are a bastard, it's like being born into a garbage can."'

### Script Output Format
- Script.md starts directly with Chapter 1 — no header, no metadata, no table of contents
- Each chapter is an H2 heading: `## N. Evocative Title` followed by continuous prose paragraphs
- No bullet points, sub-sections, stage directions, visual cues, or production notes within chapters
- Chapter titles use evocative register (what the chapter feels like) not descriptive (what happens in it) — per STYLE_PROFILE chapter naming rules
- Output location: `projects/N. [Title]/Script.md`

### Writer Invocation Workflow
- CLI subcommand: `python -m writer load "<topic>"` — resolves project directory, aggregates Research.md + STYLE_PROFILE.md + channel.md, prints to stdout
- Context package is fixed — all three files always included, no flags needed. Stays within 8,000-word budget.
- One-shot generation with no review gate — Claude generates full script and writes Script.md directly. Human reviews via git diff after the fact.
- Single generation prompt file (e.g., `prompts/generation.md`) contains all writer instructions. The prompt IS the agent's brain.
- No revision capability in Phase 12 — chapter-level iteration deferred to REFINE-01 (future requirement)

### Claude's Discretion
- Exact arc shape per topic (chronological, thematic, or hybrid) — derived from research content
- Which HOOKs and QUOTEs to select from the dossier
- Chapter count within the 4-7 range
- How to distribute word count across chapters
- Whether to apply the Truth-Seeking Coda (only when widespread misinformation exists about the subject)

</decisions>

<specifics>
## Specific Ideas

- The Duplessis Orphans topic is the validation target — institutional corruption, not a cult. The writer must build an original arc, not force Template A.
- The Duplessis dossier has 6 HOOKs and 5 QUOTEs — writer should select the most impactful subset, not try to use all of them
- For the opening hook: the "Child of Sin" QUOTE ("When you are a bastard, it's like being born into a garbage can") is a strong candidate for the opening quote slot
- The topic qualifies for the Open Ending Template — Church never apologized, survivors forced to waive claims, unanswered questions about bodies and experiments

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `context/channel/STYLE_PROFILE.md`: 5 Universal Voice Rules + Narrative Arc Templates + Transition Phrase Library + Open Ending Template + Hook Patterns + Chapter Naming Register — the writer's primary style guide
- `context/channel/channel.md`: Channel DNA (voice, tone, pillars, audience, output targets) — calibrates depth and register
- `.claude/skills/researcher/scripts/researcher/cli.py`: CLI pattern to follow — argparse, subcommands, resolve_output_dir, stdout printing
- `.claude/skills/researcher/scripts/researcher/writer.py`: Source aggregation pattern (load files → build markdown string → write)

### Established Patterns
- Skill structure: SKILL.md defines invocation, CONTEXT.md defines stage contract (see channel-assistant, researcher)
- CLI is thin context-loader: `python -m [skill] [subcommand] "[topic]"` — resolves project dir, reads files, prints to stdout
- PYTHONPATH set to skill scripts directory: `PYTHONPATH=.claude/skills/writer/scripts`
- Heuristic reasoning done by Claude after CLI prints context — no LLM calls in Python code

### Integration Points
- Input: `projects/N. [Title]/research/Research.md` (9-section dossier from researcher agent)
- Input: `context/channel/STYLE_PROFILE.md` (channel voice ruleset from style-extraction skill)
- Input: `context/channel/channel.md` (channel DNA)
- Output: `projects/N. [Title]/Script.md`
- CLAUDE.md routing table: needs "Script writing" row updated to point to writer skill

</code_context>

<deferred>
## Deferred Ideas

- REFINE-01: Iterate on specific chapters without regenerating the full script — future milestone
- REFINE-02: Adjust script length to hit target runtime (word count → minutes estimate) — future milestone
- REFINE-03: Multi-reference blending when multiple scripts exist in `context/script-references/` — future milestone
- Automated style drift detection between generated scripts and STYLE_PROFILE.md — future quality gate

</deferred>

---

*Phase: 12-writer-agent*
*Context gathered: 2026-03-15*
