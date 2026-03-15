---
estimated_steps: 4
estimated_files: 3
---

# T02: Write tests and validate schema contract

**Slice:** S01 — Visual Orchestrator Skill
**Milestone:** M002

## Description

Write pytest tests for the visual orchestrator CLI and schema validator. Tests prove the shotlist.json contract that all downstream skills (S02-S05) depend on. Follow the writer test patterns exactly — tmp_path fixtures, capsys for stdout, mock `_get_project_root`.

## Steps

1. Create `tests/test_visual_orchestrator/__init__.py` and `test_cli.py` — test `resolve_project_dir` (substring match, case-insensitive, fallback to scratch, multiple match raises ValueError), test `cmd_load` stdout (prints Script content, VISUAL_STYLE_GUIDE content, channel.md content, shotlist.json output path, generation.md prompt path), test `cmd_load` with missing Script.md exits 1. Use tmp_path with fake project dirs, mock `_get_project_root`.
2. Create `test_schema.py` — build minimal valid shotlist fixture as pytest fixture. Test cases: valid fixture passes (empty error list), missing top-level key caught, missing shot field caught, invalid shotlist_type caught, invalid ID format caught (e.g. "shot1" instead of "S001"), text_overlay without text_content caught, non-text_overlay with non-null text_content caught, back-to-back glitch shots caught, >3 consecutive text_overlay shots caught, >3 consecutive Silhouette Figure shots caught. Each test modifies the valid fixture minimally to trigger exactly one error.
3. Run `pytest tests/test_visual_orchestrator/ -v` and fix any failures
4. Run full test suite `pytest tests/ -v` to ensure no regressions

## Must-Haves

- [ ] test_cli.py covers resolve_project_dir (4 cases: match, case-insensitive, fallback, ambiguous)
- [ ] test_cli.py covers cmd_load stdout content (5 checks: script, guide, channel, output path, prompt path)
- [ ] test_cli.py covers cmd_load missing input file error
- [ ] test_schema.py covers valid shotlist passes validation
- [ ] test_schema.py covers all error conditions (missing fields, invalid enum, bad ID, text_content rules, sequencing)
- [ ] All tests pass

## Verification

- `pytest tests/test_visual_orchestrator/ -v` — all tests pass, 0 failures
- `pytest tests/ -v` — full suite passes, no regressions from existing writer/researcher/channel-assistant tests

## Inputs

- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/cli.py` — module under test
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/schema.py` — module under test
- `tests/test_writer/test_cli.py` — test pattern reference
- S01-RESEARCH.md shotlist.json schema — field definitions for fixture construction

## Expected Output

- `tests/test_visual_orchestrator/__init__.py` — package init
- `tests/test_visual_orchestrator/test_cli.py` — CLI tests (≥9 test functions)
- `tests/test_visual_orchestrator/test_schema.py` — schema validator tests (≥10 test functions)

## Observability Impact

- **Test suite as contract probe:** `pytest tests/test_visual_orchestrator/ -v` exercises every schema validation path. A future agent can run this single command to verify the shotlist.json contract is intact after any schema.py or cli.py change.
- **Failure diagnostics:** Each test function name encodes the exact condition tested (e.g. `test_invalid_id_format`, `test_back_to_back_glitch`). pytest output on failure shows which contract clause broke.
- **No runtime signals added** — this task produces test artifacts only, no changes to production code or logging.
