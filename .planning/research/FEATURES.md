# Feature Research

**Domain:** Style extraction and automated script generation for documentary narrative content
**Researched:** 2026-03-14
**Confidence:** HIGH (domain derived from existing reference scripts, channel DNA, and Architecture.md spec — not speculation)

---

## Context: What Already Exists

This milestone adds two features to a working pipeline (v1.1 shipped):

- Agent 1.1 (Channel Assistant) — topic briefs, competitor intel, project init
- Agent 1.2 (The Researcher) — two-pass web research → `Research.md` dossier with HOOK/QUOTE callouts
- `context/script-references/Mexico's Most Disturbing Cult.md` — one reference script (auto-captioned transcript, fragmented format)
- `context/channel/channel.md` — channel DNA (tone, voice, audience, output targets)
- `context/channel/writting_style_guide.md` — six style rules (narration-only, chapters, pacing, sources)

The two new features:

- **Skill 1.3: Style Extraction** — one-time heuristic that reads reference scripts, writes `STYLE_PROFILE.md`
- **Agent 1.3: The Writer** — per-video agent that reads `Research.md` + `STYLE_PROFILE.md` + channel DNA → numbered chapter script

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features the pipeline must have or the output is unusable / requires heavy manual correction.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Chapter structure with numbered acts | Reference script shows chapters 1–N with evocative titles; channel DNA mandates numbered acts | LOW | Style extraction must identify chapter boundaries in reference; Writer must output same format |
| Pure narration output — no stage directions, no host commentary | Style rule #2: "Script is narration only." Producer cannot hand this to a voiceover artist if production notes are embedded | LOW | Enforced via prompt output format spec; the existing SKILL.md pattern handles this |
| Factual fidelity anchored to Research.md | Style rule #4: "Every claim must be sourced. Speculation labeled as such." Hallucinated facts undermine the channel's authority positioning | MEDIUM | Writer prompt must anchor to dossier content; Research.md already provides per-claim attribution |
| Channel tone: calm, journalistic, deadpan | Channel DNA defines this as the core voice. Deviation breaks brand consistency across every video | MEDIUM | Achieved via STYLE_PROFILE.md + channel.md loaded as context in Writer prompt |
| Script word count in target range | 3,000–7,000 words, 20–50 min runtime (channel.md output targets). Too short = thin content; too long = padding | MEDIUM | Writer prompt must state target; may need a review pass if first draft is significantly short or long |
| STYLE_PROFILE.md captures actionable patterns | "Calm tone" is not actionable. Must capture sentence rhythm, transition phrases, pacing structure, vocabulary register | MEDIUM | Reference script is a YouTube auto-caption transcript (no punctuation, arbitrary line breaks). Extraction prompt must work with this degraded format — see Implementation Notes |
| STYLE_PROFILE.md as standalone readable artifact | Writer loads it as context on every video; it must be human-readable for manual review and editing | LOW | Plain markdown; stored in `context/` — not embedded in code |

### Differentiators (Competitive Advantage)

Features that make this pipeline produce better scripts than a generic "write a documentary script about X" prompt.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Hook and quote integration from Research.md | Research.md already contains `HOOK:` and `QUOTE:` callouts placed by Agent 1.2 specifically for the Writer. Consuming these directly = narrative tension for free | LOW | Writer prompt must explicitly instruct: use HOOK/QUOTE callouts as chapter openers and narration anchors. High ROI, zero extra work |
| Transition phrase library extracted from reference | Reference script uses specific connective phrases ("this proved to be", "in the spring of", "it was upon this track that"). Capturing these preserves voice consistency; generic transitions ("furthermore", "notably") break the deadpan register | LOW | Simple verbatim extraction during style analysis. High signal, low effort |
| Pacing profile: exposition vs. tension escalation | Reference script spends 2–3 chapters in slow historical setup before escalating to horror. Encoding this pattern as a qualitative instruction ("build slowly for the first third, then escalate") prevents flat pacing in generated scripts | MEDIUM | Word count per chapter in reference gives a rough baseline; qualitative instruction in STYLE_PROFILE.md is more durable than a hard ratio |
| Open-ending pattern explicitly encoded | Style rule #6: if a mystery is unsolved, present evidence and leave the weight with the audience. Without explicit instruction, LLMs tend to artificially resolve ambiguity | LOW | STYLE_PROFILE.md includes an open-ending template derived from reference; prompt constraint reinforces it |
| Chapter title generation in reference register | Reference uses evocative short titles ("Strangers in the Jungle", "Initial Control"). These titles carry narrative weight. Writer generates titles in same register, not generic "Background" or "Chapter 1" | LOW | Example titles from reference provide direct model for Writer |
| Source authority woven into narration | Dossier provides per-claim attribution. Weaving these into narration naturally ("court records from 1962 show...") elevates perceived credibility without disrupting pacing | MEDIUM | Prompt instruction + example from reference of how factual authority is conveyed (stated with conviction, not always explicitly cited) |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Multiple script variants (A/B versions) | Seems useful for optimization | Doubles review work; pipeline converges on one topic per video; no feedback loop exists yet to evaluate which variant performs better | One authoritative script per run; manual iteration if revision is needed |
| Inline production notes in script text | Directors want visual cues alongside narration | Breaks the "pure narration" rule (style rule #2); confuses voiceover source with direction; Agent 1.4 (Visual Orchestrator) reads the finished script and generates the shotlist — that is where visual cues live | Clean narration only; Agent 1.4 handles visual interpretation |
| Style extraction re-run every video | "Fresher style" sounds like quality | Style extraction is explicitly one-time per Architecture.md Skill 1.3 spec; re-running on the same reference adds cost with no benefit | Re-run only when new reference scripts are added to `context/script-references/` |
| Automated fact-checking pass after writing | Catching hallucinations sounds essential | The dossier-anchored approach already mitigates hallucination risk; a fact-checking pass requires another scraping/LLM pass, adds latency, and the checking LLM faces the same hallucination risk as the writing LLM | Anchor Writer to Research.md; human review catches errors that matter for publication |
| Auto-generated chapter outline for Writer approval before full script | Adds a review checkpoint | Adds a round-trip that may not be needed; the Writer derives structure from the material using STYLE_PROFILE.md guidance; impose this only if full scripts frequently need structural revision | Ship full scripts first; add outline approval step reactively if structural issues emerge |
| TTS / voice-over generation | Natural next step after script | Out of scope per Architecture.md; no TTS tool in stack; audio is handled in DaVinci Resolve by the editor | Stop at script text; TTS is a Phase 3+ concern |
| Style extraction from multiple reference scripts averaged | More data sounds better | The existing reference is already an auto-caption transcript (degraded format); averaging multiple degraded transcripts produces more noise, not better signal | Use one clean style profile; add more references only when clean transcripts are available |
| LLM API wrapper for Writer reasoning | Seems like the "right" way to call Claude programmatically | Architecture.md Rule 1: zero LLM API wrappers. All reasoning handled natively by Claude Code runtime | SKILL.md pattern — Claude Code is the runtime; no SDK code written |

---

## Feature Dependencies

```
[context/script-references/*.md]
    └──required by──> [Style Extraction (Skill 1.3)]  [HEURISTIC — one-time]
                          └──produces──> [context/STYLE_PROFILE.md]
                                             └──required by──> [The Writer (Agent 1.3)]

[projects/N. Title/research/Research.md]   (output of Agent 1.2)
    └──required by──> [The Writer (Agent 1.3)]

[context/channel/channel.md]
    └──required by──> [The Writer (Agent 1.3)]
    └──required by──> [Style Extraction (Skill 1.3)]   (tone validation context)

[context/channel/writting_style_guide.md]
    └──required by──> [The Writer (Agent 1.3)]

[The Writer (Agent 1.3)]
    └──produces──> [projects/N. Title/script.md]
                       └──feeds──> [Agent 1.4: Visual Orchestrator]  (future milestone)
```

### Dependency Notes

- **Style Extraction requires reference scripts:** One reference exists (`Mexico's Most Disturbing Cult.md`). Sufficient to produce an initial STYLE_PROFILE.md. The auto-caption format is degraded — see Implementation Notes.
- **Writer requires STYLE_PROFILE.md:** Without it, Writer falls back to generic documentary voice, losing the channel's deadpan-neutral register. Hard dependency.
- **Writer requires Research.md:** Script cannot be generated without a completed research dossier. Sequential dependency — research must complete before writing begins.
- **STYLE_PROFILE.md is a reusable artifact:** Lives in `context/`, shared across all future videos. Not regenerated per video.
- **Agent 1.4 is downstream:** The Writer's script is consumed by the Visual Orchestrator (not yet built). The script output format must be stable for that future handoff.

---

## MVP Definition

### Launch With (v1.2)

Minimum needed to produce a usable script from a research dossier.

- [ ] **Style extraction prompt** — reads reference script(s), outputs `STYLE_PROFILE.md` with: sentence rhythm description, chapter structure pattern, transition phrases (verbatim list), pacing notes (build rate), tone markers, open-ending instruction. [HEURISTIC — no code needed]
- [ ] **STYLE_PROFILE.md stored in `context/`** — loaded by Writer on every run; human-readable for manual adjustment
- [ ] **Writer SKILL.md** — defines the four context files to load, output format (numbered chapters, word count target, file path), and the generation prompt
- [ ] **Script format spec** — chapter numbers and evocative titles, pure narration, no production notes, 3,000–7,000 word target
- [ ] **HOOK/QUOTE integration instruction** — Writer prompt explicitly instructs use of Research.md callouts as narrative anchors

### Add After Validation (v1.x)

Add once a first script has been reviewed and gaps identified.

- [ ] **Pacing audit heuristic** — after Writer produces script, a secondary review step checks word count per chapter and flags disproportionate chapters. Trigger: first scripts show consistently unbalanced acts.
- [ ] **Transition phrase enforcement** — if early scripts drift from channel voice, promote the transition phrase list from STYLE_PROFILE.md to a hard constraint section in the Writer prompt
- [ ] **Second reference script** — when a clean (non-auto-captioned) transcript is available, re-run style extraction and expand STYLE_PROFILE.md with merged patterns
- [ ] **Writer CLI pre-check** — thin Python script that verifies `Research.md` exists before invoking Writer, prints clear error if missing. [DETERMINISTIC — low priority, prevents confusing failures]

### Future Consideration (v2+)

Defer until core is validated.

- [ ] **Chapter outline approval checkpoint** — generate outline first, get user approval, then write full narration. Add only if full scripts frequently need structural revision.
- [ ] **Style drift detection** — compare script output against STYLE_PROFILE.md metrics. Needs multiple reference scripts to establish meaningful baselines.
- [ ] **Script versioning** — keep draft history in `projects/N. Title/drafts/`. Worthwhile once multiple videos shipped and iteration patterns emerge.

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Style extraction prompt → STYLE_PROFILE.md | HIGH | LOW (pure heuristic) | P1 |
| Writer SKILL.md: chapter structure + pure narration | HIGH | LOW (prompt + format spec) | P1 |
| Writer: factual anchoring to Research.md | HIGH | MEDIUM (prompt engineering) | P1 |
| Writer: HOOK/QUOTE integration from dossier | HIGH | LOW (prompt instruction) | P1 |
| Writer: channel tone via STYLE_PROFILE.md | HIGH | LOW (context loading) | P1 |
| Writer: chapter title generation | MEDIUM | LOW | P1 |
| STYLE_PROFILE.md: transition phrase library | MEDIUM | LOW | P2 |
| STYLE_PROFILE.md: pacing notes | MEDIUM | MEDIUM | P2 |
| STYLE_PROFILE.md: open-ending template | MEDIUM | LOW | P2 |
| Pacing audit heuristic (post-generation) | LOW | MEDIUM | P3 |
| Chapter outline approval checkpoint | LOW | LOW | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Implementation Notes

### Reference Script Format Problem

The only existing reference script (`Mexico's Most Disturbing Cult.md`) is a YouTube auto-caption transcript. It has:
- No sentence-ending punctuation
- Arbitrary line breaks mid-sentence
- `[Music]` / `[Applause]` markers interspersed
- Chapter headers embedded mid-file (`1. Strangers in the Jungle`, `2. Initial Control`)

**Consequence for style extraction:** Cannot use punctuation-based sentence boundary detection or quantitative rhythm analysis. The extraction prompt must instead:
1. Identify chapter boundaries from numbered headers
2. Read line groupings to infer sentence rhythm qualitatively
3. Extract transition phrases and connective language verbatim
4. Characterize pacing as qualitative instruction ("slow historical build for chapters 1–2, escalate in chapters 3–4") not a numeric ratio

This is a prompt engineering constraint, not a blocker. The extraction is still achievable from this format. A clean transcript (properly punctuated) would yield higher-confidence style patterns.

### STYLE_PROFILE.md Scope

The profile should contain only what the Writer can act on. Avoid abstract descriptions. Include:
- 5–8 example transition phrases extracted verbatim from the reference script
- Chapter structure pattern: how many chapters, approximate distribution of content across acts
- Pacing instruction: when to build slowly, when to escalate, when to let a fact land without commentary
- Vocabulary register: word classes to favor (precise historical nouns, active past-tense verbs) and avoid (rhetorical questions, superlatives, first-person)
- Open-ending template: how the reference script ends unresolved cases, with example
- What the voice does NOT do: no "smash that subscribe button", no "join us as we explore", no "shockingly", no rhetorical questions to the audience

### Writer Skill Architecture

Per Architecture.md Rule 2, the Writer is [HEURISTIC] — Claude Code does the reasoning. The skill is a SKILL.md that:
1. Instructs Claude to load the four context files (STYLE_PROFILE.md, Research.md, channel.md, writting_style_guide.md)
2. Defines the output format (numbered chapters with titles, word count target, file path)
3. Provides the generation prompt

No Python code needed for the core writing step. A thin CLI pre-check (deterministic) can be added later to verify Research.md exists before invoking, but that is not MVP.

---

## Sources

- `context/script-references/Mexico's Most Disturbing Cult.md` — analyzed directly: chapter format, voice patterns, transition phrases, pacing, open-ending treatment
- `context/channel/channel.md` — channel DNA, tone rules, audience profile, output targets
- `context/channel/writting_style_guide.md` — six style rules (narration-only, chapters, pacing, sources, silence, open endings)
- `Architecture.md` — Skill 1.3 and Agent 1.3 spec, HEURISTIC/DETERMINISTIC classification rule, zero-LLM-wrapper rule
- `.planning/PROJECT.md` — v1.2 milestone definition, existing features, constraints
- `.claude/skills/researcher/SKILL.md` — Research.md dossier format (Writer's primary input); confirmed HOOK/QUOTE callout structure
- `projects/1. The Duplessis Orphans.../research/Research.md` — live example of dossier output, confirmed section structure and callout pattern

---
*Feature research for: Skill 1.3 (Style Extraction) and Agent 1.3 (The Writer)*
*Researched: 2026-03-14*
