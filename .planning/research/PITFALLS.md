# Pitfalls Research

**Domain:** Script-to-Shot-List Generation — Heuristic Visual Orchestration (v1.3 "The Director")
**Researched:** 2026-03-15
**Confidence:** HIGH (based on direct analysis of Architecture.md, Script V1.md, existing pipeline contracts, and known failure modes of LLM-driven structured output generation)

---

## Critical Pitfalls

### Pitfall 1: Over-Specifying Shots (Production Instructions Creep)

**What goes wrong:**
The shotlist.json entries drift from "visual need" into production instructions. Shots acquire fields like `duration_seconds`, `camera_movement`, `color_grade`, `transition_type`, or `priority`. The `visual_need` field itself becomes prescriptive: "slow pan across black-and-white photograph of Maurice Duplessis at 24fps with film grain overlay" instead of "official portrait of political figure, 1940s-1950s." The downstream Media Acquisition agent (2.1) can't act on camera movement instructions — it sources media, not edit instructions. The editor (DaVinci Resolve) finds the shot list contradicts their editorial judgment on half the shots.

**Why it happens:**
Claude has extensive training on film production shot lists, which do include camera movement, timing, and transitions. When asked to generate a "shot list," the LLM draws on that training and produces cinematographer-style output. Without an explicit prohibition in the prompt, production instructions creep in naturally.

**How to avoid:**
The Visual Orchestrator prompt must contain a hard, explicit fence with examples of what does NOT belong:
- "Do not include: camera movement (pan, tilt, zoom), duration, timing, transitions, effects, color instructions, priority scores, or post-production notes."
- "The `visual_need` field describes WHAT the viewer needs to see — location, era, subject — not HOW the camera shows it."
- Provide a side-by-side: "WRONG: slow dolly into archival photograph of compound. RIGHT: aerial or wide view of remote rural compound, 1970s."

Architecture.md is explicit: "No duration, priority, effects, transitions, or post-production instructions — those are the editor's domain." This rule must be pasted verbatim into the generation prompt as a constraint header, not buried in prose.

**Warning signs:**
- Any shot entry contains keys beyond `id`, `chapter`, `narrative_context`, `visual_need`, `suggested_types`.
- `visual_need` strings contain camera terms: pan, tilt, dolly, push, pull, rack focus, dissolve.
- Shot entries include `duration`, `priority`, `mood`, `color`, or `effect` fields.

**Phase to address:** Phase 1 (Prompt Design — Hard Fences). Define the schema and field-level constraints in the prompt before any generation attempt. Test the prompt against a single chapter and verify no production terminology appears in any field.

---

### Pitfall 2: Under-Specifying Shots (Visual Need Too Vague to Act On)

**What goes wrong:**
The opposite failure from Pitfall 1. The Visual Orchestrator swings too abstract: `visual_need` becomes "something historical," "relevant imagery," or "footage of the time period." The narrative context is there, but the visual need provides no guidance for what Agent 2.1 should actually search for. The acquisition agent builds generic search queries, finds generic stock footage, and the gap between the script's specificity and the visual output is enormous. The editor receives 50 clips of "1940s people walking" with no connection to the actual story.

**Why it happens:**
When the generation prompt instructs the LLM to be "loose" and avoid over-specification, the LLM sometimes interprets "loose" as "vague." The concept of "narrative need, not production instruction" requires understanding the distinction — which is subtle enough that without examples, the LLM defaults to being unhelpfully abstract.

**How to avoid:**
The prompt must include examples showing the correct specificity level — not production detail, but specific enough that a human researcher could identify the right asset category:
- WRONG (too vague): "historical imagery from that era"
- RIGHT (correctly loose): "church-administered orphanage or residential institution interior, Quebec or Canada, 1940s-1950s"
- WRONG (too vague): "relevant footage"
- RIGHT (correctly loose): "government or legislative building, Quebec, mid-20th century — exterior or interior establishing shot"

The rule is: `visual_need` should be specific enough that two different acquisition agents would search the same source domain and retrieve similar asset types, without specifying the exact asset.

**Warning signs:**
- `visual_need` strings under 10 words that contain only generic terms ("historical imagery," "relevant footage," "period material").
- Multiple consecutive shots share identical or near-identical `visual_need` text.
- Agent 2.1 returns zero results for a shot because the search query built from `visual_need` returns nothing useful.

**Phase to address:** Phase 1 (Prompt Design — Specificity Calibration). Include three worked examples showing the correct level of specificity in the prompt. After the first test generation, review all `visual_need` strings for vagueness before moving to integration.

---

### Pitfall 3: Wrong Granularity — Too Many Shots (Noise)

**What goes wrong:**
The script is parsed at sentence or clause level. A 5,000-word script with 300 sentences produces 200+ shot entries. Most shots repeat the same visual need (the same location, the same era, the same subject) because the narration lingers on a topic across many sentences. Agent 2.1 builds 200 search queries, downloads 200 sets of results, and the manifest.json becomes unmanageable. The editor receives a shot list with no usable hierarchy — everything is equally weighted.

**Why it happens:**
LLMs are thorough by default. When asked to generate a shot for "each narrative moment," they parse every sentence as a moment. The script's prose is dense and continuous — it does not have natural breakpoints the LLM can use without explicit guidance on granularity.

**How to avoid:**
Define granularity rules explicitly in the prompt:
- "One shot entry per distinct visual setting, subject, or concept — not one per sentence."
- "If three consecutive narration sentences describe the same location and era, they share one shot entry."
- "Target: 3-6 shots per chapter. A 5-chapter script should produce 15-30 total shots."
- "Group related narration under a single `narrative_context` — include the 2-3 most representative sentences, not every sentence."

Provide an example of collapsing: show 4 sentences about the same topic mapped to 1 shot entry, with the `narrative_context` capturing the essence.

**Warning signs:**
- Total shot count exceeds 50 for a 5,000-word script.
- Multiple consecutive shot entries share the same `suggested_types` and nearly identical `visual_need`.
- Chapter shot counts exceed 10.

**Phase to address:** Phase 1 (Prompt Design — Granularity Rules). Set explicit target ranges in the prompt. After first test generation, count shots per chapter. If any chapter exceeds 8, the granularity rule is not working.

---

### Pitfall 4: Wrong Granularity — Too Few Shots (Gaps)

**What goes wrong:**
The script has 6 chapters but the shotlist.json has 8 shots total — roughly one per chapter section. The shots are broad: "footage of Quebec in the 1940s-1960s." Agent 2.1 can acquire assets, but has no way to match them to specific narrative moments. The manifest.json has 8 shot IDs for a 40-minute documentary. The editor receives a handful of assets with no contextual anchoring. The `gaps` section of the manifest is enormous because the shot entries are too coarse to evaluate gaps against.

**Why it happens:**
When the LLM consolidates aggressively (to avoid the "too many shots" pitfall), it over-collapses. A single `visual_need` ends up covering 800 words of narration across many distinct scenes. The prompt's instruction to be "loose" is interpreted as "minimal."

**How to avoid:**
Combine the upper-bound and lower-bound targets in the prompt: "Target 3-6 shots per chapter. Each shot should cover no more than 2-3 minutes of narration (approximately 300-450 words at documentary pacing). A shot entry that covers more than 500 words of narration is probably too coarse."

The lower bound is enforced by requiring each chapter to have at least 2 shots (intro and body minimum).

**Warning signs:**
- Total shot count under 15 for a 5-chapter script.
- Any single `narrative_context` field contains more than 5 sentences.
- Any chapter has fewer than 2 shot entries.

**Phase to address:** Phase 1 (Prompt Design — Granularity Rules). Same phase as Pitfall 3 — granularity rules address both extremes simultaneously.

---

### Pitfall 5: Visual Monotony — Repeated `suggested_types`

**What goes wrong:**
Every shot entry lists `["archival_photo", "archival_video"]` as `suggested_types`. The suggestion provides no differentiation signal for the acquisition agent. The shot list fails its visual variety function — all 30 shots converge on the same two asset types, and the final video cuts between static photos and archival clips with no visual texture variation. Documents, vectors, animations, and broll are never suggested, so Agent 2.1 never looks for them, and Agent 2.2/2.3 never gets meaningful input.

**Why it happens:**
`archival_photo` and `archival_video` are the "safe" documentary asset types — they are always plausible. The LLM defaults to them unless forced to consider other options. Without explicit prompting to consider the full asset type vocabulary, the suggestion field becomes a formality rather than a meaningful signal.

**How to avoid:**
The prompt must:
1. List all valid asset types with their definitions: `archival_video`, `archival_photo`, `broll`, `documents`, `vectors`, `animations`.
2. Provide examples of when non-obvious types apply: newspaper clippings and court records → `documents`; maps or organizational charts → `animations`; subjects with no photographic record → `vectors`.
3. Include a distribution expectation: "A well-varied shot list should include at least 4 different asset types across all shots. If your list uses only archival_photo and archival_video, review it."
4. Add prompting for `documents` specifically — dark history content is rich with government reports, court filings, newspaper front pages, and official memos that are visually compelling and publicly available.

**Warning signs:**
- More than 70% of shot entries list identical `suggested_types`.
- `documents`, `vectors`, or `animations` appear in zero shot entries for a script with government records, court proceedings, or abstract concepts.
- `broll` appears in zero entries for a script with location or atmosphere needs.

**Phase to address:** Phase 1 (Prompt Design — Asset Type Distribution). Include the full asset type taxonomy in the prompt with usage examples. After first generation, count the distribution of suggested types. If any valid type appears in 0 entries, add a targeted example to the prompt.

---

### Pitfall 6: LLM-Generated JSON Is Malformed or Schema-Incomplete

**What goes wrong:**
The Visual Orchestrator generates JSON with structural problems: trailing commas, unescaped quotes in `narrative_context` strings (the narration often contains actual quotes from testimony), missing closing brackets, inconsistent field naming (`suggested_type` vs. `suggested_types`), or extra fields not in the schema. Agent 2.1 attempts to read shotlist.json and fails with a JSON parse error, halting the pipeline. Worse, the JSON is valid but structurally wrong — an array where an object is expected, or string values where arrays are required for `suggested_types`.

**Why it happens:**
The `narrative_context` field pulls directly from script narration, which contains survivor testimony with quotation marks and apostrophes. These characters break JSON string escaping. LLMs sometimes produce well-formed JSON structurally but introduce character escaping errors when field values contain rich text. Additionally, LLMs sometimes invent additional "helpful" fields (`urgency`, `mood`, `source_era`) that do not belong in the schema.

**How to avoid:**
1. The schema must be defined in the prompt as a JSON example with annotated field types — not described in prose.
2. Add an explicit rule: "narrative_context is a plain string — do not include quotation marks from the script inside this field. Paraphrase or describe what the narrator says; do not transcribe it verbatim."
3. Add: "Do not add fields not shown in the schema. The schema is final."
4. Since this is a [HEURISTIC] skill (no Python code), include a validation step in the CONTEXT.md: after generating shotlist.json, Claude reads it back and verifies all required fields are present and no extra fields exist before writing the file.
5. Instruct Claude to validate the JSON by mentally parsing it before writing — "Review the output. Are all strings properly closed? Are all arrays properly terminated? Does each shot object have exactly the four required fields?"

**Warning signs:**
- Python `json.loads()` raises `JSONDecodeError` on the output file.
- Any shot entry contains fields not in the schema (`urgency`, `mood`, `era`, `color`, `priority`).
- `suggested_types` is a string instead of an array in any entry.
- Agent 2.1 fails with a KeyError or TypeError when accessing shot fields.

**Phase to address:** Phase 1 (Prompt Design — JSON Schema Enforcement) AND Phase 2 (Integration — Validation Step). The prompt prevents schema drift; the CONTEXT.md validation step catches it before the file is committed.

---

### Pitfall 7: Narrative Context Transcribes the Script Instead of Summarizing It

**What goes wrong:**
The `narrative_context` field becomes a verbatim copy of 300+ words of script narration. The shotlist.json file size balloons. More critically, the field is supposed to help the acquisition agent understand what the narrator is saying during this shot — but a 300-word verbatim block does not communicate the visual need any more efficiently than 20 words would. Agent 2.1 cannot build a meaningful search query from a dense narration excerpt. The field's signal-to-noise ratio is low.

**Why it happens:**
The LLM has access to the full script and finds it easier to copy relevant text than to synthesize. Without a word limit or a synthesis instruction, verbatim reproduction is the path of least resistance.

**How to avoid:**
Define the purpose and limit of `narrative_context` explicitly:
- "narrative_context is a 1-2 sentence synthesis of what the narrator is communicating during this shot — not a transcription."
- "Maximum 50 words. Paraphrase, do not quote directly."
- Example: WRONG: "[200 words of narration about the 1962 Bedard Report]". RIGHT: "Narrator describes the 1962 Bedard Report finding that one-third of Quebec's psychiatric patients were misclassified for fiscal reasons."

**Warning signs:**
- Any `narrative_context` value exceeds 100 words.
- `narrative_context` strings contain quotation marks (sign of verbatim transcription).
- The shotlist.json file size is disproportionately large relative to shot count.

**Phase to address:** Phase 1 (Prompt Design — Field Definitions). Include explicit word limits and synthesis instruction in the field definition.

---

### Pitfall 8: Shot IDs Are Not Stable Across Regenerations

**What goes wrong:**
The script is revised (the user edits Script.md manually or the Writer re-generates). The Visual Orchestrator re-runs. New shot IDs are generated differently — S001 now maps to a different shot than the previous run. Meanwhile, manifest.json from a partial Agent 2.1 run still references the old S001-S030 range. The shot mappings in manifest.json become wrong. The `gaps` section references non-existent shot IDs. The pipeline is in an inconsistent state.

**Why it happens:**
Shot IDs are generated sequentially by the LLM, starting from S001. If the chapter structure changes or shots are added/removed, all subsequent IDs shift. There is no stable anchor that links a shot ID to a specific narrative moment across runs.

**How to avoid:**
Document this as an explicit design constraint in the CONTEXT.md and SKILL.md:
- "shotlist.json is regenerated from scratch when Script.md changes. Any existing manifest.json is invalidated and must be discarded."
- "Do not attempt to patch or merge shot lists. Full regeneration is the only safe operation."
- Add a clear operational note: "If Agent 2.1 has already run against a shot list, do not regenerate the shot list without also discarding the manifest and re-running acquisition."

This is a pipeline reset design, not a merge design. The CONTEXT.md should make this explicit so the user does not attempt to reconcile two runs.

**Warning signs:**
- A manifest.json exists with shot references that do not match the current shotlist.json.
- User attempts to "update" shotlist.json by editing individual entries after Agent 2.1 has run.
- Chapter count in script differs from chapter names in shotlist.json.

**Phase to address:** Phase 2 (CONTEXT.md — Pipeline Invariants). Define the invariant: shotlist.json and manifest.json are atomically coupled. Changing one invalidates the other.

---

### Pitfall 9: `suggested_types` Treated as Constraints by Agent 2.1

**What goes wrong:**
Agent 2.1 reads `suggested_types: ["archival_photo"]` and acquires only archival photos for that shot, discarding an archival video clip it found that would work perfectly. The suggestions become a filter rather than a hint. The shot list's "loose" design intent is violated at the consumer level. The result is unnecessary gaps in the manifest where good assets existed but were excluded.

**Why it happens:**
The `suggested_types` field name reads as prescriptive. If Agent 2.1's prompt doesn't explicitly frame the field as a non-binding hint, it reasons: "the shot list says archival_photo, so I should acquire archival photos for this shot."

**How to avoid:**
This is an Agent 2.1 design concern, but Agent 1.4 can prevent it by making the intent explicit in the shot list itself:
- In the shotlist.json file, include a top-level `"schema_notes"` object (or document-level comment via the generation prompt) that states: `"suggested_types: non-binding hints — acquisition agent may use any asset type that satisfies the narrative need."`
- Architecture.md already states: "Hints, not constraints — acquisition agent can use any type that fits." This phrasing should appear in the CONTEXT.md for Agent 2.1 when it is built.
- The shotlist.json field name `suggested_types` is deliberately named with "suggested" to signal non-binding intent — the prompt for Agent 1.4 should explain this reasoning so the naming choice is documented.

**Warning signs:**
- Agent 2.1 reports zero results for a shot despite the source domains having relevant material (because it searched only one asset type).
- Manifest.json has no cross-type asset mappings (every shot mapped to exactly one asset type).
- Gap analysis finds gaps for shots where broll or documents would have worked but only photos were searched.

**Phase to address:** Phase 2 (Agent 2.1 Design — Hint Interpretation). Explicitly address the hint-not-constraint interpretation in Agent 2.1's CONTEXT.md. Also addressed by the field naming convention established in Agent 1.4.

---

### Pitfall 10: Script Chapter Structure Is Misread (No Chapter Markers)

**What goes wrong:**
Script.md uses `## 1. Chapter Title` markdown headers to mark chapter boundaries. The Visual Orchestrator generates a shotlist.json that doesn't respect chapter boundaries — shots from the introduction appear mixed with shots from chapter 3, or the chapter field values are inconsistent strings ("intro," "1," "Chapter 1," "1. The Arithmetic of Abandonment"). Agent 2.1 cannot use the chapter field for any ordering or grouping because it isn't normalized.

**Why it happens:**
The LLM reads the script as flowing prose. Chapter headers are visible but the LLM must be explicitly instructed to use them as structural anchors, not just headings. Without that instruction, chapter attribution is approximate and the naming convention is inconsistent.

**How to avoid:**
The generation prompt must include:
- "Script.md uses `## N. Chapter Title` headers to mark chapter boundaries. Each shot's `chapter` field must use the exact chapter title as it appears in the header, verbatim."
- "Example: if the header is `## 1. The Arithmetic of Abandonment`, the chapter field value is `1. The Arithmetic of Abandonment`."
- "All shots that fall between the start of a chapter header and the next chapter header belong to that chapter."

This creates a normalized, predictable chapter field that Agent 2.1 and the Asset Manager (2.4) can use for ordering.

**Warning signs:**
- Different shot entries for the same chapter use different `chapter` field strings.
- Shots from the script introduction appear with `chapter: "intro"` but the script header reads `## 1. [Title]`.
- Chapter values are bare numbers ("1", "2") rather than full chapter titles.

**Phase to address:** Phase 1 (Prompt Design — Script Parsing Instructions). The chapter parsing rule must be in the prompt. After first generation, verify all chapter field values match the exact chapter headers in the source script.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skipping JSON validation step in CONTEXT.md | Faster skill design | Malformed shotlist.json halts Agent 2.1 on first run | Never — add the validation step before first use |
| Generating shot IDs without a stable anchor | Simple sequential IDs, easy to read | Any script edit invalidates manifest.json; no safe merge path | Acceptable as a design choice if the pipeline-reset invariant is clearly documented |
| Using only archival_photo and archival_video as suggested types | Safe, always sourced | Visual monotony; Agent 2.2 and 2.3 receive no meaningful input; vectors and animations underused | Never — the full asset type taxonomy must be used |
| Verbatim narrative_context from script | No synthesis work needed | Shotlist.json bloats; Agent 2.1 cannot build useful search queries from dense narration blocks | Never — synthesis is the value the orchestrator adds |
| One shot per chapter (coarse granularity) | Minimal shot list, fast to generate | Manifest.json cannot distinguish visual needs within a chapter; gap analysis is useless at this coarseness | Never for production; acceptable as a smoke-test to verify JSON structure only |
| Including production instructions in visual_need | Satisfies the LLM's training on film shot lists | Editor and acquisition agent cannot use the output; output is for a different pipeline | Never |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Agent 1.4 → Agent 2.1 (shot list consumption) | Agent 2.1 treats `suggested_types` as a required filter | Agent 2.1 prompt must frame `suggested_types` as a non-binding hint; any asset type satisfying the narrative need is valid |
| Agent 1.4 → Agent 2.1 (narrative_context as search input) | Agent 2.1 uses full `narrative_context` verbatim as a search query | Agent 2.1 must extract search terms from `narrative_context`; long verbatim strings produce bad queries |
| Agent 1.4 → Agent 2.4 (shot ordering) | Asset Manager uses shot IDs assuming stable ordering across regenerations | Ordering only applies within a single shotlist.json version; any regeneration invalidates the ordering |
| Script.md → shotlist.json (chapter attribution) | Chapter field uses inconsistent naming conventions | Chapter field must match exact `## N. Chapter Title` headers from Script.md verbatim |
| shotlist.json → manifest.json (pipeline coupling) | User edits shotlist.json after manifest.json is created | These artifacts are atomically coupled — editing one invalidates the other; full regeneration is the only safe operation |
| documents asset type | Acquisition agent never receives `documents` suggestions because orchestrator defaults to photo/video | Visual Orchestrator prompt must explicitly include examples showing when `documents` applies (court filings, newspaper front pages, government reports) |

---

## "Looks Done But Isn't" Checklist

- [ ] **No production instructions in any field:** Review 5 random shot entries. Verify `visual_need` contains no camera movement, timing, effect, or transition language. Verify no extra fields beyond the four schema fields exist.
- [ ] **Correct granularity:** Count total shots and divide by chapter count. Average should be 3-6 shots per chapter. No chapter should have fewer than 2 or more than 8 shots.
- [ ] **Visual type diversity:** Count unique values in all `suggested_types` arrays. At least 4 distinct types should appear across the full shot list. `documents` should appear if the script references any official records, reports, or publications.
- [ ] **JSON is valid:** Load shotlist.json with `python -c "import json; json.load(open('shotlist.json'))"`. Any parse error is a blocker before Agent 2.1 runs.
- [ ] **Schema compliance:** Verify every shot entry has exactly four fields: `id`, `chapter`, `narrative_context`, `visual_need`, `suggested_types`. No additional fields. No missing fields.
- [ ] **Chapter names are exact:** Compare all unique `chapter` values in shotlist.json against the exact chapter headers in Script.md. They must match verbatim.
- [ ] **narrative_context is synthesized, not transcribed:** Verify no `narrative_context` value exceeds 80 words. Verify no `narrative_context` value contains quotation marks (sign of verbatim script copy).
- [ ] **suggested_types are arrays:** Verify `suggested_types` is a JSON array (not a string) in every shot entry.
- [ ] **Shot count is in range:** A 5,000-word, 5-chapter script should produce 15-30 shots. Outside this range, review granularity before passing to Agent 2.1.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Production instructions in shot list | LOW | Revise prompt with explicit prohibitions and examples; regenerate full shot list |
| Under-specified visual needs | LOW | Add specificity examples to prompt; regenerate full shot list |
| Wrong granularity (too many shots) | LOW | Add target ranges and collapsing examples to prompt; regenerate |
| Wrong granularity (too few shots) | LOW | Add minimum-per-chapter rule to prompt; regenerate |
| Visual monotony (only 2 asset types) | LOW | Add asset type taxonomy with usage examples to prompt; regenerate |
| Malformed JSON | LOW | Identify escaping issue (usually unescaped quotes in narrative_context); fix prompt to instruct paraphrase not transcription; regenerate |
| Shot IDs out of sync with manifest.json | MEDIUM | Discard manifest.json; re-run Agent 2.1 against the updated shotlist.json from scratch |
| Inconsistent chapter field values | LOW | Regenerate with explicit chapter naming instruction; or manually correct chapter fields if only 2-3 are wrong |
| Agent 2.1 treating suggested_types as constraints | LOW | Update Agent 2.1 CONTEXT.md to restate hint-not-constraint intent; re-run acquisition for affected shots |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Production instructions creep (Pitfall 1) | Phase 1: Prompt Design — Hard Fences | Review 5 random shot entries; zero production terms in any field |
| Visual need too vague (Pitfall 2) | Phase 1: Prompt Design — Specificity Calibration | Two independent searches from each `visual_need` string should return the same source domain |
| Too many shots — noise (Pitfall 3) | Phase 1: Prompt Design — Granularity Rules | Chapter shot count average is 3-6; no chapter exceeds 8 |
| Too few shots — gaps (Pitfall 4) | Phase 1: Prompt Design — Granularity Rules | No chapter has fewer than 2 shots; no `narrative_context` covers more than 450 words of narration |
| Visual monotony (Pitfall 5) | Phase 1: Prompt Design — Asset Type Distribution | At least 4 distinct types across shot list; `documents` present if script references records |
| Malformed JSON (Pitfall 6) | Phase 1: Prompt Design — Schema Enforcement AND Phase 2: CONTEXT.md Validation Step | `json.load()` succeeds; all required fields present in every entry |
| Verbatim narrative_context (Pitfall 7) | Phase 1: Prompt Design — Field Definitions | No `narrative_context` exceeds 80 words; no quotation marks in the field |
| Unstable shot IDs across regenerations (Pitfall 8) | Phase 2: CONTEXT.md — Pipeline Invariants | Pipeline-reset invariant documented; no merge operation defined |
| suggested_types as constraints (Pitfall 9) | Phase 2: Agent 2.1 Design — Hint Interpretation | Agent 2.1 CONTEXT.md states hint-not-constraint explicitly |
| Script chapter misread (Pitfall 10) | Phase 1: Prompt Design — Script Parsing Instructions | All `chapter` field values match exact headers from Script.md |

---

## Sources

- Direct analysis: `Architecture.md` — Agent 1.4 schema definition, design principles ("No duration, priority, effects, transitions"), `suggested_types` field intent ("hints, not constraints"), asset type taxonomy
- Direct analysis: `projects/1. The Duplessis Orphans.../Script V1.md` — actual script structure, chapter headers, narration density, survivor testimony (shows rich quoted text that will cause JSON escaping issues)
- Direct analysis: `Architecture.md` Phase 2 — Agent 2.1 input contract ("reads only shotlist.json"), gap analysis mechanism, manifest schema
- Direct analysis: `.planning/PROJECT.md` — v1.3 milestone goal, [HEURISTIC] classification, zero Python code constraint
- Known pattern: LLM default to cinematographer-style shot lists when prompted for "shot list" without explicit schema constraints — training data contains extensive film production templates
- Known pattern: JSON escaping failures in LLM-generated structured output when field values contain rich text (quotation marks, apostrophes) — documented behavior in structured output benchmarks
- Known pattern: Schema field drift (LLM adding "helpful" extra fields) — documented in JSON-mode evaluations; occurs without explicit "no extra fields" instruction
- Known pattern: LLM interpretation of "loose" as "vague" in generation prompts without worked examples showing the correct specificity level

---

*Pitfalls research for: Script-to-Shot-List Generation — Heuristic Visual Orchestration (v1.3 "The Director")*
*Researched: 2026-03-15*
