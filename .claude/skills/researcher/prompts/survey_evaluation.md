# Survey Evaluation — Pass 1

## When to Use This Prompt

Run this evaluation immediately after `cmd_survey` completes. Claude reads all
src_NNN.json files listed in source_manifest.json and annotates the manifest with
evaluation results. This is the [HEURISTIC] step — no code runs.

## Setup

Source files are in the output directory printed by cmd_survey as "Output directory: ..."
Manifest: {output_dir}/source_manifest.json

For each source, read the corresponding src_NNN.json file listed in the manifest.
Evaluate based on the full "content" field — not just the manifest metadata.

## Evaluation Criteria (in priority order)

### 1. Primary Source Potential (highest priority)

Does this source reference or link to primary documents?
Look for: court records, government reports (.gov URLs), archive.org documents,
official inquiries, Freedom of Information Act releases, academic peer-reviewed papers.

Extract these URLs into deep_dive_urls — they become the Phase 9 (cmd_deepen) fetch targets.

### 2. Unique Perspective

Does this source offer angles absent from the Wikipedia entry? Prioritize:

- **Local journalism first**: Regional and local outlets often contain details that national
  outlets sanitize or miss entirely. Names, dates, locations, eyewitness quotes.
- **Firsthand accounts**: Survivor testimony, participant statements, personal narratives.
- **Academic analysis**: Peer-reviewed treatment, historiographical context.
- **Reddit community discussions**: Alternative framings, community knowledge, links to
  obscure sources the mainstream coverage ignores.

### 3. Contradiction Signals

Does this source contradict another source you have already read?
Note the specific factual conflict (dates, figures, event sequences, attributed quotes).
These contradictions become the DOSS-02 contradictions section in the final Research.md.

## Output Instructions

For each source entry in source_manifest.json, add three fields:

**evaluation_notes** (string)
1-3 sentences. What did you find? Why is it useful or not?
If a contradiction is detected, name both conflicting sources and the disputed fact.

**deep_dive_urls** (array of strings)
URLs extracted from the source content that warrant a targeted fetch in Pass 2.
Include only: primary document URLs, government archives, academic papers,
or highly relevant secondary sources not yet in the source list.
Use an empty array if none found.

**verdict** (string) — "recommended" or "skip"
- recommended: source has primary source links, unique perspective, contradiction signals,
  or local journalism value not in Wikipedia
- skip: generic overview that duplicates Wikipedia with no unique URLs or angles

## After Annotating

1. Write the annotated manifest back to source_manifest.json (overwrite in place)
2. Print a verdict summary table:

   #   Source                        Verdict        Notes
   --  ----------------------------  -------------  -------------------------------
   1   en.wikipedia.org              recommended    FBI vault docs referenced
   2   bbc.com                       skip           Generic overview, no unique URLs
   ...

3. Say: "Proceed to Pass 2 (cmd_deepen)?"
