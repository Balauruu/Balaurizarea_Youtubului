---
phase: 14-generation-prompt
verified: 2026-03-15T00:00:00Z
status: gaps_found
score: 8/9 must-haves verified
gaps:
  - truth: "generation.md contains a building block vocabulary table with 23-28 entries (18 baseline + 5-10 additions)"
    status: partial
    reason: "User-approved deviation: vocabulary was deliberately consolidated from 25 to 10 non-overlapping blocks after human-verify checkpoint. The count deviation is intentional and user-approved. However, anti-pattern pair 5 (line 112) still references 'Concept Diagram' as the corrected building_block value — this block was removed during consolidation and does not exist in the vocabulary table. The valid block name is 'Diagram'. This is a dangling reference that will confuse any agent reading the prompt."
    artifacts:
      - path: ".claude/skills/visual-orchestrator/prompts/generation.md"
        issue: "Anti-pattern pair 5 RIGHT example uses 'building_block': 'Concept Diagram' — block does not exist in vocabulary table. Correct name is 'Diagram'."
    missing:
      - "Fix line 112: change 'Concept Diagram' to 'Diagram' in anti-pattern pair 5 RIGHT example"
human_verification:
  - test: "Walk through a chapter from Duplessis Script V1.md and apply generation.md rules manually"
    expected: "Output consistent with existing shotlist.json — same building block names, same type routing, similar granularity"
    why_human: "Requires reading a full script and existing shotlist, then evaluating whether the rules would produce equivalent output — cannot verify programmatically"
  - test: "Read building block vocabulary and verify coverage for channel topic range"
    expected: "10 consolidated blocks cover dark mysteries, true crime, unsolved cases, institutional scandals without routing ambiguity"
    why_human: "Requires editorial judgment about topical coverage — automated checks cannot assess whether vocabulary is complete for the content domain"
---

# Phase 14: Generation Prompt Verification Report

**Phase Goal:** Write the generation prompt that encodes all reasoning needed to turn a Script.md into a valid shotlist.json — schema, building block vocabulary, type routing, granularity rules, anti-patterns, and a worked example.
**Verified:** 2026-03-15
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | generation.md encodes chapter parsing rules including chapter 0 prologue handling | VERIFIED | Line 7: "Any unnumbered content before `## 1.` is the prologue." Line 73: Chapter 0 parsing rule with explicit Prologue assignment |
| 2 | generation.md defines the full 9-field shot schema with field-level rules | VERIFIED | Lines 13-41: Complete JSON example with all 9 fields plus field-by-field rules for each |
| 3 | generation.md contains a building block vocabulary table with 23-28 entries | PARTIAL | 10 entries present. User-approved consolidation (deliberate deviation from plan). However anti-pattern pair 5 uses a removed block name ("Concept Diagram") — dangling reference |
| 4 | generation.md has type routing rules mapping each building block to exactly one of 6 shotlist_type values | VERIFIED | Lines 75-88: Complete routing table with all 6 types; each of the 10 blocks appears in exactly one row |
| 5 | generation.md specifies narrative-beat-based shot boundaries with 450-word safety net | VERIFIED | Lines 62-64: "Primary trigger: narrative beat changes" and "approximately 450 words" safety net |
| 6 | generation.md requires establishing shots as first shot of each chapter | VERIFIED | Line 71: "Each chapter MUST begin with an establishing or orienting shot" with valid type examples |
| 7 | generation.md routes abstract narration to animation type, never archival | VERIFIED | Line 88: "Critical rule (SHOT-07): ... assign `animation`. Never assign `archival_photo` or `archival_video` to abstract content." |
| 8 | generation.md has 4-6 WRONG/RIGHT anti-pattern pairs for visual_need | VERIFIED | Lines 93-116: 6 WRONG/RIGHT pairs covering all planned cases |
| 9 | generation.md includes a synthetic worked example mapping narration to 2-3 shots | VERIFIED | Lines 126-173: Carol Marden synthetic case (not Duplessis) with 3 shots across 3 different shotlist_types |

**Score:** 8/9 truths verified (Truth 3 is partial due to dangling "Concept Diagram" reference)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.claude/skills/visual-orchestrator/prompts/generation.md` | Complete generation prompt | VERIFIED | 182 lines; all required sections present; committed at `6271e84` |

**Artifact level checks:**

- Level 1 (Exists): File present at expected path
- Level 2 (Substantive): 182 lines; contains Schema, Building Blocks, Granularity Rules, Type Routing, Anti-Patterns, Worked Example, Output Format sections
- Level 3 (Wired): CONTEXT.md Process steps 1, 3, and Inputs table all explicitly reference `prompts/generation.md` by path

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `.claude/skills/visual-orchestrator/prompts/generation.md` | `.claude/skills/visual-orchestrator/CONTEXT.md` | CONTEXT.md Process step 1 and Inputs table reference prompts/generation.md | WIRED | CONTEXT.md line 10: "`.claude/skills/visual-orchestrator/prompts/generation.md` | Full file | Schema definition, granularity rules, building block vocabulary, anti-patterns". Lines 14 and 16 also reference it in Process steps. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| SHOT-01 | 14-01-PLAN.md | Skill parses Script.md chapter structure and generates shots grouped by chapter | SATISFIED | Lines 7, 73: `## N. Title` parsing rule and chapter 0 assignment rule |
| SHOT-02 | 14-01-PLAN.md | Shot boundaries follow narrative beats, not paragraphs or sentences | SATISFIED | Lines 62-63: "Primary trigger: narrative beat changes ... Never split at paragraph or sentence boundaries for their own sake." |
| SHOT-03 | 14-01-PLAN.md | Each shot has sequential ID, chapter number, narrative_context, visual_need, and suggested_types | SATISFIED | Lines 13-41: 9-field schema with globally sequential S001-S999 IDs, chapter field, and all required fields present |
| SHOT-04 | 14-01-PLAN.md | visual_need descriptions specific enough for acquisition queries (era + location + subject, no production terms) | SATISFIED | Lines 21, 36, 93-116: Field rules and 6 WRONG/RIGHT anti-pattern pairs for visual_need specifically |
| SHOT-05 | 14-01-PLAN.md | Visual variety enforced — mix of asset types across the shot list | SATISFIED | Lines 120: "No more than 2 consecutive shots may share the same `building_block`. Enforce variety across a chapter." |
| SHOT-06 | 14-01-PLAN.md | Each chapter begins with an establishing/orienting shot | SATISFIED | Lines 71-72: Establishing shot rule with MUST, lists valid types, states "Never begin a chapter with a detail shot." |
| SHOT-07 | 14-01-PLAN.md | Abstract narration with no visual record routes to vector/animation types, not archival | SATISFIED | Lines 84, 88: animation row in routing table and Critical rule with "Never assign archival_photo or archival_video to abstract content" |

All 7 SHOT requirements are addressed by specific sections in the prompt.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `prompts/generation.md` | 112 | Dangling vocabulary reference: `"building_block": "Concept Diagram"` used in anti-pattern pair 5 RIGHT example, but "Concept Diagram" was removed during consolidation. Valid block name is "Diagram". | Blocker | An agent reading this prompt sees a RIGHT example using a block name that does not appear in the vocabulary table — directly contradicts the rule "building_block MUST match a vocabulary entry exactly". Any agent following this example would produce an invalid shot. |

### Human Verification Required

#### 1. Duplessis Script Compatibility Check

**Test:** Open `projects/*/Script*.md` and apply generation.md rules to one chapter mentally (or via a test invocation), then compare output against the existing `shotlist.json`
**Expected:** Building block names match the 10-entry vocabulary, type assignments are consistent, granularity produces similar shot density
**Why human:** Requires reading a full script alongside the existing shotlist and making editorial comparisons — cannot verify with grep or structural checks

#### 2. Building Block Coverage for Channel Scope

**Test:** Read the 10-block vocabulary table and evaluate whether all channel topic types (dark mysteries, true crime, institutional scandals, historical mysteries, unsolved cases) have sufficient block options
**Expected:** No common visual moment type from the channel's content would require a block not in the vocabulary
**Why human:** Requires editorial judgment about domain coverage — automated checks cannot assess completeness for a content type

### Gaps Summary

One gap blocks full verification: anti-pattern pair 5's RIGHT example uses `"Concept Diagram"` as the `building_block` value (line 112), but this block was removed during the post-checkpoint consolidation. The vocabulary table has no entry named "Concept Diagram" — the surviving block is named "Diagram". This contradicts the Schema rule stating `building_block` must match a vocabulary entry exactly, and an agent following this example would emit invalid output.

The fix is a single-word change on line 112: `"Concept Diagram"` → `"Diagram"`.

The 23-28 block count deviation is NOT a gap — it is a user-approved deliberate decision documented in the SUMMARY. The consolidation to 10 blocks with rich variant fields is intentional and serves routing clarity.

---

_Verified: 2026-03-15_
_Verifier: Claude (gsd-verifier)_
