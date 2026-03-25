---
name: researcher
description: "Research pipeline for documentary video topics. Use this skill when the user wants to research a topic, gather sources, build a research dossier, or prepare factual foundations for a documentary script. Triggers on: 'research [topic]', 'gather sources', 'build dossier', 'deep dive into [topic]', or any request to investigate a subject for the channel."
---

# Researcher Skill

Three-pass research pipeline that scrapes web sources and produces a factual dossier for documentary scripts.

## Setup

crawl4ai is installed in a dedicated venv at `C:/Users/iorda/venvs/crawl4ai`. Also needs `ddgs`:

```bash
C:/Users/iorda/venvs/crawl4ai/Scripts/pip install ddgs
```

## Invocation

```bash
PYTHONPATH=.claude/skills/researcher/scripts C:/Users/iorda/venvs/crawl4ai/Scripts/python -m researcher survey "Topic"
PYTHONPATH=.claude/skills/researcher/scripts C:/Users/iorda/venvs/crawl4ai/Scripts/python -m researcher deepen "Topic"
PYTHONPATH=.claude/skills/researcher/scripts C:/Users/iorda/venvs/crawl4ai/Scripts/python -m researcher write "Topic"
```

---

## Workflow

### Pass 1 — Survey

1. Run `researcher survey "Topic"` — fetches Wikipedia + up to 12 DuckDuckGo results, saves each as `src_NNN.json` in the project's `research/` directory.
2. **[HEURISTIC] Evaluate sources** — read the prompt at `@.claude/skills/researcher/prompts/survey_evaluation.md`, then read each `src_NNN.json` and annotate `source_manifest.json` with `evaluation_notes`, `deep_dive_urls`, and `verdict` ("recommended" or "skip").
3. Print verdict summary table. Ask: "Proceed to Pass 2?"

### Pass 2 — Deep Dive

1. Verify `source_manifest.json` has `verdict` and `deep_dive_urls` on all sources.
2. Run `researcher deepen "Topic"` — fetches URLs from recommended sources, saves as `pass2_NNN.json`. Budget: max 15 total files across both passes.

### Pass 3 — Write Dossier

1. Run `researcher write "Topic"` — aggregates all source files into `synthesis_input.md`.
2. **[HEURISTIC] Synthesize** — read `synthesis_input.md` and `@.claude/skills/researcher/prompts/synthesis.md`, then produce:
   - `Research.md` (~2,000 words, 9-section narrative dossier)
   - `entity_index.json` (proper-noun index: persons, institutions, locations, events, dates)
   Both written to the project's `research/` directory.

---

## Tier System

| Tier | Behavior | Retries | Examples |
|------|----------|---------|---------|
| 1 | Authoritative — full retry | 3 | archive.org, loc.gov, en.wikipedia.org |
| 2 | General / unknown — attempt once | 1 | bbc.com, reuters.com, unknown domains |
| 3 | Social — skip entirely | 0 | facebook.com, x.com, instagram.com |

Unknown domains default to Tier 2.

---

## Checkpoints

| After Step | Agent Presents | Human Decides |
|------------|---------------|---------------|
| Pass 1, Step 2 | Source verdict summary table | Proceed to deep dive, add/remove sources, or redirect |
| Pass 3, Step 2 | Research.md summary (sections + word count) | Accept, request revisions, or add missing sources |

## Audit (after Pass 3, before writing final output)

| Check | Pass Condition |
|-------|---------------|
| Source diversity | ≥3 distinct source domains cited |
| Timeline populated | Timeline section has ≥5 dated entries |
| Contradictions addressed | Section 7 is non-empty OR explicitly states "no contradictions found" |
| Entity coverage | All 5 entity categories populated in entity_index.json (persons, institutions, locations, events, dates) |
| No fabrication | Every claim in Subject Overview traces to a source in Sections 4-5 |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Research dossier | `projects/N. [Title]/research/Research.md` | 9-section markdown (~2000 words) |
| Entity index | `projects/N. [Title]/research/entity_index.json` | Proper-noun index (persons, institutions, locations, events, dates) |
| Source manifest | `projects/N. [Title]/research/source_manifest.json` | Verdicts + deep-dive URLs |

If no matching project exists in `projects/`, output falls back to `.claude/scratch/researcher/`.
