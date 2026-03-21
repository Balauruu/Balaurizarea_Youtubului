# Synthesis Prompt — Dossier Output

## When to Use This Prompt

Run this synthesis immediately after `cmd_write` completes and prints the synthesis_input.md path.
This is a [HEURISTIC] step — Claude reads the aggregated source content and produces two output files.

## Setup

1. Read the full synthesis_input.md file (path printed by cmd_write as "Synthesis input: ...")
2. Note the **Output directory:** line in the synthesis_input.md header — write both output files there
3. Note the **Topic:** line — use it as the document title in Research.md
4. Note any **Skipped / failed sources:** line — acknowledge those gaps; do not fabricate content for them

---

## Task

Read synthesis_input.md in full. Then produce two files in this exact order:

1. **Research.md** — the ~2,000-word narrative-first dossier (all 9 sections, strict order below)
2. **entity_index.json** — structured proper-noun index extracted from Research.md

Write both files to the output directory specified in the synthesis_input.md header.

---

## Research.md — Sections (strict order)

Research.md begins with a minimal header:

```
# [Topic Name]
*Research dossier — [Date YYYY-MM-DD]*
```

Then the 9 sections below, in this exact order. Do not reorder sections.

---

### Section 1 — Subject Overview

~500 words. Dense factual summary of who, what, when, where, and what happened.
No editorial framing. No adjectives that editorialize ("shocking", "disturbing", "remarkable").
Facts only. Write in the third person.

---

### Section 2 — Timeline

5–15 chronological entries covering the key events from earliest to latest.

Format each entry as:
```
- **[Date or Year]** -- [Event description, 1–2 sentences]. *Source: [domain]*
```

Example:
```
- **1974** -- The commune was established in a remote mountain valley outside Durango. *Source: en.wikipedia.org*
```

Include only events with source support. If a date range is the best available, use it (e.g., "1970–1972").

---

### Section 3 — Key Figures

3–8 figures central to the story. One block per figure.

Format:
```
**[Full Name]** -- [Role / Title]
[1–2 sentences on their relevance to the story.]
[If a direct quote from this person appears in Section 5, write: See QUOTE: [Label]]
```

Do not invent quotes. Only cross-reference quotes that appear in Section 5.

---

### Section 4 — Narrative Hooks

3–5 hooks. Each hook is a high-impact story beat the Writer can anchor a chapter around.

Format each hook as:
```
**HOOK: [Short Title]**
[1–2 sentences describing the story beat and why it is narratively significant.]
```

Example:
```
**HOOK: The Letter That Was Never Sent**
A handwritten letter found in the leader's belongings after the raid described plans to relocate followers to a remote jungle — weeks before the compound burned down. The letter was suppressed from the initial investigation.
```

Hooks must be grounded in source content. No speculation.

---

### Section 5 — Direct Quotes

3–8 quotes from primary or firsthand sources. Only include quotes with clear attribution.

Format each quote as:
```
**QUOTE: [Short Label]**
> "[Exact quoted text]"
-- [Speaker Name], [Role], [source domain or document title]
```

Example:
```
**QUOTE: The Leader's Admission**
> "We had to protect them from a world that would never understand what we had built here."
-- Ramón Castillo, cult leader, testimony to federal investigators (justice.gob.mx)
```

If a quote is paraphrased rather than verbatim, write *(paraphrased)* after the attribution.

---

### Section 6 — Contradictions

2–5 factual conflicts between sources. Name both sources. One block per conflict.

Format:
```
**[Short Label]**
[Source A domain] states [claim A]. [Source B domain] reports [claim B]. [1 sentence on significance of the conflict — which version has stronger sourcing, if determinable.]
```

Do not speculate on which is true if evidence is insufficient. Flag the conflict and move on.

---

### Section 7 — Unanswered Questions

3–7 open questions that create narrative tension. One sentence each.

Format as a simple numbered list:
```
1. [Question — phrased as a direct question]
2. [Question]
...
```

Examples:
- "Who authorized the destruction of the commune's financial records before the federal investigation began?"
- "What happened to the fifteen children who left the commune in the months before the raid?"

---

### Section 8 — Correcting the Record

2–4 entries where mainstream coverage diverges from primary source evidence.

Format:
```
**Mainstream account:** [What widely-reported sources claim]
**Primary source evidence:** [What official records, court documents, or firsthand accounts show]
**Source:** [domain or document title]
```

If no clear mainstream-vs-primary divergence exists in the sources, write:
"No significant mainstream-vs-primary divergences identified in available sources."

---

### Section 9 — Source Credibility

A compact table listing every source consulted.

Format:
```
| Source | Type | Corroborated By | Access Quality |
|--------|------|-----------------|----------------|
| en.wikipedia.org | wiki | archive.org, bbc.com | full |
| vault.fbi.gov | gov | justice.gob.mx | full |
| jstor.org/article/xyz | academic | — | partial |
```

**Type values:** gov, academic, journalism, wiki, primary
**Access Quality values:** full, partial, paywall

Do NOT include scalar scores (1–10 ratings). Use structured signals only.
List all sources from synthesis_input.md — including skipped/failed ones, marked as "failed" in Access Quality.

---

## Word Cap

Target: ~2,000 words of body text.

**Does NOT count toward the cap:**
- The Research.md header (topic + date)
- Section headings (lines starting with `###`)
- HOOK: labels and QUOTE: labels
- The Source Credibility table (all rows and headers)
- Timeline date prefixes and source attributions

**Does count toward the cap:**
- Subject Overview prose
- Timeline event descriptions
- Key Figures relevance sentences
- HOOK body text
- QUOTE text and attributions
- Contradictions body text
- Unanswered Questions sentences
- Correcting the Record entries

**Distill — do not summarize everything. Select the highest-value content.**
If sources contain 40,000 words, the dossier should still be ~2,000 words of curated content.
Prioritize: primary source evidence, firsthand accounts, contradiction signals, unique angles.
Deprioritize: generic biographical background, duplicate overviews, information already in Subject Overview.

---

## entity_index.json — Extraction Rules

After writing Research.md, read it back and extract every proper noun into a structured JSON index.

### Output Schema

```json
{
  "persons": [],
  "institutions": [],
  "locations": [],
  "events": [],
  "dates": []
}
```

### Category Definitions

- **persons** — Full names of individuals mentioned in Research.md. Use the most complete form of each name (e.g., "Maurice Duplessis" not "Duplessis"). Include titles only when they are part of how the person is identified (e.g., "Sister Mary of the Incarnation").
- **institutions** — Organizations, agencies, churches, governments, companies, and formal bodies (e.g., "Catholic Church", "Quebec Provincial Government", "Royal Commission on Aboriginal Peoples").
- **locations** — Cities, provinces, states, countries, and specific named places (e.g., "Montreal", "Quebec", "Mont Providence orphanage"). Use the most specific form available.
- **events** — Named historical events, incidents, investigations, or legal proceedings (e.g., "Duplessis Orphans Commission", "Operation Snow White"). Do not invent event names — only include events that are named as such in the text.
- **dates** — Specific dates (YYYY-MM-DD when available) or year ranges (e.g., "1940-1965") mentioned in the text. Extract from the Timeline section and any other dated references throughout Research.md.

### Rules

1. **Deduplicate** — Each value appears exactly once per array.
2. **Sort** — Alphabetically for persons, institutions, locations, events. Chronologically for dates.
3. **No fabrication** — Only extract proper nouns that appear in Research.md. Do not add entities from your own knowledge.
4. **Comprehensive** — Scan all 9 sections of Research.md. Do not stop at Section 1.
5. **JSON only** — The file must contain valid JSON and nothing else. No markdown, no comments, no wrapper text.

---

## Anti-Patterns

Do NOT include any of the following in Research.md or entity_index.json:

- **No recommended angles.** Do not write "This angle would work well for the intro" or similar.
- **No chapter suggestions.** Do not write "Chapter 1 could cover..." or similar.
- **No tone guidance.** Do not write "The Writer should emphasize..." or similar.
- **No fabrication.** If a source is empty or failed, skip it. Do not invent facts.
- **No editorializing adjectives.** Avoid: shocking, disturbing, haunting, chilling, remarkable, terrifying.
- **No speculation.** If evidence is insufficient to support a claim, flag it as unknown or disputed.
- **No scalar scores.** The Source Credibility table uses Type, Corroborated By, and Access Quality — no numbers.
