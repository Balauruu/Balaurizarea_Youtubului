---
phase: 11
slug: style-extraction-skill
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual review — HEURISTIC classification, no automated tests |
| **Config file** | None — heuristic skill |
| **Quick run command** | Invoke skill, inspect STYLE_PROFILE.md output sections |
| **Full suite command** | Run style-extraction skill end-to-end, review all 4 mandatory sections |
| **Estimated runtime** | ~5 minutes (LLM extraction + human review) |

---

## Sampling Rate

- **After every task commit:** Inspect STYLE_PROFILE.md sections after writing
- **After every plan wave:** Full manual review — read STYLE_PROFILE.md end-to-end, verify all 4 mandatory sections present and populated
- **Before `/gsd:verify-work`:** STYLE_PROFILE.md reviewed and approved by human
- **Max feedback latency:** ~120 seconds (LLM call time)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | STYLE-01 | manual | Inspect `context/channel/STYLE_PROFILE.md` — count named rules, verify verbatim quotes | ❌ W0 | ⬜ pending |
| 11-01-02 | 01 | 1 | STYLE-02 | manual | Inspect `## Narrative Arc Templates` — verify chapter range, arc structure, applicability labels | ❌ W0 | ⬜ pending |
| 11-01-03 | 01 | 1 | STYLE-03 | manual | Inspect rhythm subsection — verify short/long pattern with actual script quotes | ❌ W0 | ⬜ pending |
| 11-01-04 | 01 | 1 | STYLE-04 | manual | Confirm Universal and Narrative Arc are distinct H2 sections; Universal has no cult-specific content | ❌ W0 | ⬜ pending |
| 11-01-05 | 01 | 1 | STYLE-05 | manual | `ls context/channel/STYLE_PROFILE.md` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `context/channel/STYLE_PROFILE.md` — created by this phase
- [ ] `.claude/skills/style-extraction/SKILL.md` — invocation instructions
- [ ] `.claude/skills/style-extraction/CONTEXT.md` — stage contract
- [ ] `.claude/skills/style-extraction/prompts/extraction.md` — extraction prompt

*All artifacts are created during execution — no pre-existing test infrastructure needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Named voice rules with verbatim examples | STYLE-01 | LLM output quality requires human judgment | Read Universal Voice Rules section, verify each rule has do/don't format with script quotes |
| Arc templates separable from universal rules | STYLE-04 | Structural separation requires semantic understanding | Confirm Universal section has no cult-specific language; confirm Arc section carries applicability labels |
| Transition phrases are channel-authentic | STYLE-03 | Authenticity requires human judgment | Cross-reference transition phrases with reference script; verify no generic connectives |
| Open ending template prevents false resolution | STYLE-01 | Narrative judgment | Review open ending template; verify it signals continuation not closure |

---

## Validation Sign-Off

- [ ] All tasks have manual verification steps documented
- [ ] Sampling continuity: manual review after each wave
- [ ] Wave 0 covers all MISSING references
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter
- [ ] STYLE_PROFILE.md approved by human before Phase 12

**Approval:** pending
