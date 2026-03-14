# Project Research Summary

**Project:** Channel Automation v1.2 — "The Writer"
**Domain:** Prompt-driven style extraction and automated script generation for documentary video pipeline
**Researched:** 2026-03-14
**Confidence:** HIGH

## Executive Summary

This milestone adds two skills to a working agentic pipeline (v1.1 ships Channel Assistant + Researcher): Skill 1.3 (Style Extraction) and Agent 1.3 (The Writer). Both are almost entirely [HEURISTIC] operations — Claude Code does the reasoning natively, and the only deterministic code required is a thin context-loader CLI that aggregates files and prints them to stdout. The recommended approach is to resist the pull toward NLP libraries, LLM SDKs, and complex templating in favor of prompt files and stdlib-only Python. Zero new pip dependencies are required.

The core insight from combined research: this is a prompt engineering problem, not a software engineering problem. STYLE_PROFILE.md is the key artifact — it must contain craft-oriented behavioral rules with verbatim examples from the reference script, not statistical summaries. The Writer's quality ceiling is determined by how precisely the synthesis prompt names the channel's deadpan-neutral voice patterns and how explicitly it instructs use of Research.md's HOOK/QUOTE callouts as narrative anchors. The build order is sequential and non-negotiable: style extraction must be validated before meaningful writer testing can begin.

The primary risk is misclassification — defaulting to deterministic code for tasks that are inherently heuristic. The Architecture.md HEURISTIC/DETERMINISTIC rule is the explicit guard against this. A secondary risk is context saturation: loading too many files into the Writer's generation context degrades output quality in the later chapters of the script. The research identifies a hard budget of 8,000 words of total context at generation time. Both risks are avoidable by strictly applying the classification rule before touching a keyboard.

---

## Key Findings

### Recommended Stack

The v1.0/v1.1 stack is unchanged and requires no re-evaluation. For v1.2 specifically, zero new third-party dependencies are needed. All deterministic work uses Python stdlib: `re` for sentence splitting, `collections.Counter` for word frequency, `statistics` for length distribution, `pathlib` for file operations, and `argparse` for the CLI. This is the correct outcome for a primarily heuristic milestone — the deterministic layer is intentionally thin by design.

**Core technologies:**
- `re` (stdlib): Sentence splitting and pattern detection for style metric computation — no third-party tokenizer needed for transcribed speech input
- `collections` (stdlib): Word frequency and vocabulary analysis via Counter — already idiomatic in the channel-assistant codebase
- `statistics` (stdlib): Sentence length distribution (mean, median, stdev) — anchors quantitative surface metrics in STYLE_PROFILE.md
- `pathlib` (stdlib): File discovery and project path resolution — already the project standard per CLAUDE.md
- `argparse` (stdlib): CLI argument parsing — same pattern as researcher and channel-assistant CLIs

**Explicitly rejected:** textstat (wrong signal — readability indices do not capture voice patterns), spaCy (50MB install for POS tagging that adds nothing on transcribed speech input), NLTK (heavy corpus downloads, no advantage over stdlib for this use case), LangChain/LlamaIndex (violates Architecture.md Rule 1 — zero LLM API wrappers), any LLM embedding library (style similarity is Claude's job, not cosine distance).

### Expected Features

The Writer milestone delivers two features. Style extraction is a one-time channel setup operation; script generation is a per-video production step. Both feed directly into the downstream Visual Orchestrator (Agent 1.4, future milestone), so the script output format must be stable.

**Must have (table stakes):**
- Style extraction prompt that produces STYLE_PROFILE.md with craft-oriented behavioral rules and verbatim examples — not statistics or readability scores
- STYLE_PROFILE.md stored in `context/channel/` as stable channel-level context (parallel to channel.md, not inside any project directory)
- Writer SKILL.md: numbered chapter structure, pure narration output, no stage directions or embedded production notes
- Factual anchoring: every claim in the script traceable to Research.md — Writer does not generate facts from training memory
- HOOK/QUOTE integration: Writer prompt explicitly instructs use of Research.md callouts as chapter entry points and narration anchors
- Script word count in target range: 3,000–7,000 words (20–50 min runtime per channel.md output targets)
- Channel tone enforcement: calm, journalistic, deadpan — achieved by loading STYLE_PROFILE.md + channel.md as generation context

**Should have (differentiators):**
- Transition phrase library extracted verbatim from reference script — prevents generic connective language ("furthermore", "notably") that breaks the deadpan register
- Pacing profile: slow historical build for first third, escalation to horror — qualitative instruction, not a hard word-count ratio
- Open-ending template derived from reference — prevents LLMs from artificially resolving ambiguity in unsolved cases (explicit style rule in writting_style_guide.md)
- Chapter title generation in the reference register: evocative short titles ("Strangers in the Jungle") rather than generic labels ("Background", "Chapter 1")
- Source authority woven into narration naturally ("court records from 1962 show...") without disrupting pacing
- STYLE_PROFILE.md distinguished into "Universal Voice Rules" vs. "Narrative Arc Templates by story type" — avoids cult-topic arc template overfitting to non-cult topics

**Defer (v2+):**
- Chapter outline approval checkpoint before full script generation — add reactively only if full scripts frequently need structural revision
- Multiple script variants for A/B testing — doubles review work, no feedback loop exists yet
- Style drift detection across generated scripts — needs more than one reference to establish a meaningful baseline
- TTS/voiceover generation — out of scope per Architecture.md; audio is handled in DaVinci Resolve

### Architecture Approach

Both new skills extend the established "CLI prints, Claude reasons" pattern used by all existing skills. The style-extraction skill has no Python code at all — two files only (SKILL.md + extract.md prompt). The writer skill adds a thin `cli.py` with a single `load` subcommand that aggregates Research.md + STYLE_PROFILE.md + channel.md and prints to stdout. Claude performs all generation natively from that context. No new architectural concepts are introduced — both skills are direct applications of patterns already proven in researcher and channel-assistant.

**Major components:**
1. `style-extraction/SKILL.md` + `prompts/extract.md` — One-time channel setup: reads reference scripts, writes STYLE_PROFILE.md. Pure heuristic, zero Python code written
2. `context/channel/STYLE_PROFILE.md` — Stable channel-level artifact: written once by style-extraction, read by every Writer invocation. Lives at the same tier as channel.md
3. `writer/scripts/writer/cli.py` — Thin context aggregator: resolves project path from topic string, reads three files, prints to stdout. Single `load` subcommand, identical pattern to researcher's CLI
4. `writer/prompts/write_script.md` — Script generation rules: chapter structure defined by narrative logic (not word count), voice constraints with verbatim examples, explicit Research.md reading instructions, output format specification
5. `projects/N. Title/script/Script.md` — Per-video terminal output: first-class production artifact (not scratch), feeds Agent 1.4 in the next milestone

**Build sequence (non-negotiable order):** style-extraction SKILL.md and extract.md prompt → validate STYLE_PROFILE.md output → writer prompts/write_script.md → writer cli.py → writer SKILL.md → end-to-end validation against Duplessis Orphans Research.md.

### Critical Pitfalls

1. **Style extraction implemented as NLP code instead of a prompt** — Any Python file created for style extraction is a classification error. STYLE_PROFILE.md must contain behavioral rules with examples ("sentences fragment mid-thought at revelation moments to force a beat") not statistics ("average sentence length: 14.2 words"). If the profile describes what the text IS rather than how it WORKS, discard and re-run with a corrected prompt.

2. **Script loses channel voice within the first chapter** — LLMs default to "competent documentary narrator" when given research + vague style instructions. Break the default with: verbatim reference script excerpts labeled with what they demonstrate, explicit prohibitions (no rhetorical questions, no "imagine if you will", no emotional signposting like "shockingly"), and the channel's specific deadpan device named and demonstrated. Validate the prompt against the Duplessis Orphans Research.md before considering the prompt finished.

3. **Research.md HOOK/QUOTE callouts ignored in script output** — Agent 1.2 embeds explicit narrative signal callouts in the dossier specifically for the Writer. The Writer's synthesis prompt must contain reading instructions: "The HOOK is the story's entry point — build the introduction around it, not buried in chapter 2." "QUOTE callouts anchor the chapter they appear in — they are not summary material." The handoff is a structured reading instruction, not a file path.

4. **Context saturation degrades second-half chapter quality** — Hard budget: 8,000 words of total input context at generation time. Curated package: Research.md + STYLE_PROFILE.md (relevant sections only) + reference script excerpt (intro + one chapter, not the full script) + channel.md executive summary (first 200 words). Do not load ResearchArchive.md, raw source files, or past_topics.md at generation time.

5. **LLM API wrapper introduced for quality evaluation or any other step** — Any `import anthropic` or `import openai` in writer skill scripts is an Architecture.md Rule 1 violation. Script quality evaluation is [HEURISTIC] — Claude reads the output and evaluates natively in the same session. No code evaluates script quality.

---

## Implications for Roadmap

Based on combined research, two phases cover the entire milestone. Both are tightly coupled by validation dependencies — Phase 1 must complete and produce a validated STYLE_PROFILE.md before Phase 2 has any meaningful tests to run.

### Phase 1: Style Extraction Skill

**Rationale:** STYLE_PROFILE.md is a prerequisite for meaningful Writer testing. Without it, writer output cannot be evaluated against the channel's voice — you have no anchor. This phase has zero code to write (pure heuristic), so it completes quickly and unblocks Phase 2 immediately. The sooner STYLE_PROFILE.md is committed to the repo, the sooner all downstream work has stable channel DNA to reference.

**Delivers:** `context/channel/STYLE_PROFILE.md` committed to the repository as stable channel-level context. Also delivers `.claude/skills/style-extraction/SKILL.md` and `prompts/extract.md`.

**Addresses (features):** STYLE_PROFILE.md with craft-oriented behavioral rules, transition phrase library, pacing profile, open-ending template, "Universal Voice Rules" vs. "Narrative Arc Templates" distinction (mitigates single-reference overfitting to cult topic type).

**Avoids:** Pitfall 1 (style extraction as NLP code — classify as HEURISTIC before any file is created), Pitfall 3 (single-reference profile forcing cult arc onto non-cult topics — design the profile format to accommodate multiple arc templates from the start), Pitfall 7 (STYLE_PROFILE.md drifting via in-place edits — set the versioning and regeneration policy before the first profile is written).

### Phase 2: Writer Agent

**Rationale:** Depends directly on Phase 1 output. The write_script.md prompt is written before the CLI because the prompt structure determines what context the CLI needs to load and print. Validated against the existing Duplessis Orphans Research.md as an integration test — this project has a completed dossier, so no new research work is required to run the first real end-to-end script generation.

**Delivers:** `writer/SKILL.md`, `writer/prompts/write_script.md`, `writer/scripts/writer/cli.py`, and `projects/1. The Duplessis Orphans.../script/Script.md` as the integration test output.

**Uses (stack):** stdlib only — `pathlib`, `argparse`. No new installs required.

**Implements (architecture):** "CLI prints, Claude reasons" pattern (established convention from researcher and channel-assistant). Project path resolution via directory matching — reuse researcher's pattern exactly, do not reimplement. Context aggregation: Research.md + STYLE_PROFILE.md + channel.md printed to stdout with clear section headers.

**Avoids:** Pitfall 2 (script loses channel voice — use verbatim examples and explicit prohibitions in write_script.md), Pitfall 4 (Research.md hooks lost in handoff — explicit reading instructions in synthesis prompt, not in a comment or readme), Pitfall 5 (LLM API wrapper for evaluation — evaluation is heuristic, no code), Pitfall 6 (formatting constraints override narrative logic — chapter breaks defined by narrative beats, not word count thresholds), Pitfall 8 (context saturation — enforce 8,000-word context budget before writing the generation prompt).

### Phase Ordering Rationale

- Style extraction must precede script generation because the Writer has no validated voice anchor without STYLE_PROFILE.md. Running Phase 2 before Phase 1 produces untestable output with no quality baseline.
- Within Phase 2, write_script.md must precede cli.py because the prompt defines the required context package, which determines what the CLI loads. Writing the CLI first produces a loader that may not serve the actual generation needs.
- SKILL.md for the writer is written last — after both prompt and CLI are validated — because SKILL.md references both and must accurately describe a tested, working workflow.
- End-to-end validation against the Duplessis Orphans project is the terminal step, not an optional check. It is the only meaningful integration test because it exercises the full pipeline on a real topic with a completed Research.md dossier.

### Research Flags

Phases with standard patterns (no deeper research needed during planning):
- **Phase 1 (Style Extraction):** No code, pure prompt design. Classification is HEURISTIC per Architecture.md Rule 2. No unknowns to research — the only variable is STYLE_PROFILE.md output quality, which is validated empirically by running the extraction and reviewing the result.
- **Phase 2 (Writer Agent):** CLI follows the researcher's established pattern exactly. The prompt engineering variables are fully documented by pitfalls research (8 specific failure modes with prevention strategies). No deeper technical research needed.

No phases require `/gsd:research-phase` during planning. Both phases are well-defined by direct codebase inspection and Architecture.md constraints. The only open question is whether the single reference script produces a STYLE_PROFILE.md that generalizes adequately to non-cult topic types — this is validated in Phase 1, not researched in advance.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Zero new dependencies — all stdlib. No version conflicts possible. Confirmed by direct codebase analysis of existing channel-assistant and researcher skills, both stdlib-only. |
| Features | HIGH | Derived from direct analysis of existing reference script, channel.md, writting_style_guide.md, Architecture.md spec, and the live Duplessis Orphans Research.md. Feature boundaries driven by the HEURISTIC/DETERMINISTIC rule, which is explicit and binding. No speculation involved. |
| Architecture | HIGH | Based on direct inspection of all existing skills. Both new skills extend established patterns without introducing new concepts. Build order is determined by validation dependencies, not preference. |
| Pitfalls | HIGH | Pitfalls derived from Architecture.md Rules 1 and 2 (binding constraints), direct analysis of the degraded reference script format, and documented LLM behavior patterns in long-context generation (RULER, InfiniteBench benchmarks). Prevention strategies map to specific, actionable prompt engineering decisions. |

**Overall confidence:** HIGH

### Gaps to Address

- **Single reference script limits STYLE_PROFILE.md coverage:** STYLE_PROFILE.md will be derived from one reference (`Mexico's Most Disturbing Cult.md`), which is a cult/group narrative — not all topic types on the channel. Mitigate by explicitly labeling profile sections as "universal voice rules" vs. "cult arc template (one reference only)." Add a second reference when a clean transcript becomes available for a non-cult topic (institutional corruption, disappearance, or dark web topic).
- **Auto-caption format degrades quantitative style metrics:** The reference script is a YouTube auto-caption export with no punctuation and arbitrary line breaks. Sentence boundary detection and length distribution will have lower signal quality than a properly punctuated transcript. The extraction prompt must work qualitatively — inferring rhythm from line groupings and narrative structure from chapter headers — rather than quantitatively. This is acknowledged and handled in the prompt design approach; it is not a blocker.
- **Script quality validation is manual at launch:** There is no automated way to verify a generated script matches the channel's voice. The validation step is human review of the Duplessis Orphans script against the reference. This is by design (heuristic task), but it means iteration speed depends on reviewer availability. Add a pacing audit heuristic (post-generation word count per chapter review) as a secondary check in v1.x after the first scripts are validated.

---

## Sources

### Primary (HIGH confidence)

- `.claude/skills/researcher/SKILL.md` and `cli.py` — established "CLI prints, Claude reasons" pattern that writer replicates directly
- `.claude/skills/channel-assistant/SKILL.md` and `project_init.py` — confirmed that scaffold already creates `script/` subdirectory; writer needs no directory creation logic
- `Architecture.md` — CRITICAL ARCHITECTURE RULES (binding project constraints): Rule 1 (zero LLM API wrappers), Rule 2 (HEURISTIC vs. DETERMINISTIC classification)
- `context/script-references/Mexico's Most Disturbing Cult.md` — confirmed reference script format (auto-caption, degraded), chapter structure, voice patterns, transition phrases
- `context/channel/channel.md` — channel DNA, tone rules, audience profile, output targets (3,000–7,000 words, 20–50 min)
- `context/channel/writting_style_guide.md` — six style rules: narration-only, chapters, pacing, sources, silence, open endings
- `projects/1. The Duplessis Orphans.../research/Research.md` — confirmed live dossier format, HOOK/QUOTE callout structure, word count
- `.planning/PROJECT.md` — v1.2 milestone definition, key decisions log

### Secondary (MEDIUM confidence)

- Programming Historian: Introduction to Stylometry with Python — validated TTR, sentence length, punctuation density as standard stylometric features for style analysis
- LLM long-context behavior (RULER, InfiniteBench benchmarks) — quality degradation in second half of long-form outputs under high input load; informed the 8,000-word context budget recommendation

### Tertiary (LOW confidence)

- LLM default to "competent but generic" documentary narrator mode — observed behavior pattern documented in multiple creative writing evaluation contexts; overridden by verbatim examples and explicit prohibitions rather than by abstract style descriptions

---
*Research completed: 2026-03-14*
*Ready for roadmap: yes*
