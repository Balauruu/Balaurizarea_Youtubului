---
estimated_steps: 4
estimated_files: 4
---

# T03: Add pytest suite for animation CLI and manifest merge

**Slice:** S04 — Remotion Animation Skill
**Milestone:** M002

## Description

Mocked test suite for the animation CLI. Mirrors graphics-generator test patterns: `resolve_project_dir` resolution tests, `cmd_load` stdout content assertions, `cmd_render` with patched `subprocess.run`, and manifest merge contract tests. All tests mock the subprocess boundary — no real Remotion installation required. Also updates `pytest.ini` to add animation scripts to pythonpath.

## Steps

1. Add `.claude/skills/animation/scripts` to `pytest.ini` pythonpath.
2. Create `tests/test_animation/test_cli.py` — test `resolve_project_dir` (single match, multiple match ValueError, scratch fallback), test `cmd_load` (prints MAP_SHOTS section with only map-type shots, skips non-map shots), test `cmd_render` with `unittest.mock.patch("subprocess.run")` (verifies subprocess called with correct args including cwd, writes output file, merges manifest), test error paths (missing shotlist exits with error, no map shots prints message, subprocess failure captured).
3. Create `tests/test_animation/test_manifest.py` — test `_merge_manifest` (new assets appended with correct fields, gaps updated from pending_generation to filled, idempotent re-merge doesn't duplicate, atomic write creates parent dirs), test `_empty_manifest` returns correct skeleton.
4. Run full test suite, verify ≥15 tests pass.

## Must-Haves

- [ ] pytest.ini updated with animation scripts pythonpath
- [ ] resolve_project_dir tests: single match, multi match error, scratch fallback
- [ ] cmd_load tests: map shots filtered, sections labeled in stdout
- [ ] cmd_render tests: subprocess.run mocked, correct args verified, manifest merged
- [ ] Error path tests: missing shotlist, no map shots, subprocess failure
- [ ] Manifest merge tests: assets appended, gaps updated, idempotent, atomic write

## Observability Impact

- **Test diagnostics:** `pytest tests/test_animation/ -v` surfaces pass/fail per test with descriptive names. Failures include assertion diffs showing expected vs actual manifest structure, stdout content, and subprocess call args.
- **Future agent inspection:** Run `pytest tests/test_animation/ -v --tb=short` to quickly verify animation CLI contract hasn't regressed after changes. Test names map 1:1 to CLI behaviors (resolve_project_dir, cmd_load filtering, cmd_render subprocess, manifest merge).
- **Failure visibility:** Mocked subprocess tests verify error paths (missing shotlist, no map shots, subprocess failure) — if these tests fail, the error-handling contract has broken.

## Verification

- `pytest tests/test_animation/ -v` — all tests pass (≥15)
- `pytest tests/ -v` — no regressions in existing test suites

## Inputs

- T02 output — `animation.cli` module with cmd_load, cmd_render, cmd_status, resolve_project_dir, _merge_manifest
- `tests/test_graphics_generator/test_cli.py` — Test pattern reference
- `tests/test_graphics_generator/test_manifest.py` — Manifest merge test reference

## Expected Output

- `tests/test_animation/__init__.py` — Test package init
- `tests/test_animation/test_cli.py` — CLI tests with mocked subprocess (~10 tests)
- `tests/test_animation/test_manifest.py` — Manifest merge tests (~6 tests)
- `pytest.ini` — Updated pythonpath
