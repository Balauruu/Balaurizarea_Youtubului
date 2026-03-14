---
phase: 12-writer-agent
plan: "01"
subsystem: writer-skill
tags: [writer, cli, prompts, skill-docs, tdd]
dependency_graph:
  requires: [context/channel/STYLE_PROFILE.md, projects/N/research/Research.md, context/channel/channel.md]
  provides: [.claude/skills/writer/, tests/test_writer/]
  affects: [pytest.ini, CLAUDE.md routing table]
tech_stack:
  added: []
  patterns: [argparse, pathlib, stdlib-only, TDD]
key_files:
  created:
    - .claude/skills/writer/scripts/writer/__init__.py
    - .claude/skills/writer/scripts/writer/__main__.py
    - .claude/skills/writer/scripts/writer/cli.py
    - .claude/skills/writer/prompts/generation.md
    - .claude/skills/writer/SKILL.md
    - .claude/skills/writer/CONTEXT.md
    - tests/test_writer/__init__.py
    - tests/test_writer/test_cli.py
  modified:
    - pytest.ini
decisions:
  - "Writer CLI is stdlib-only (argparse, pathlib, sys) — no third-party dependencies, no LLM calls"
  - "resolve_project_dir falls back to .claude/scratch/writer/{topic} when no project match found"
  - "pytest.ini updated to include .claude/skills/writer/scripts in pythonpath"
  - "generation.md prompt is self-contained — references Style Profile by name, not by content"
metrics:
  duration: "281 seconds (~5 minutes)"
  completed_date: "2026-03-15"
  tasks_completed: 2
  files_created: 9
  tests_added: 9
---

# Phase 12 Plan 01: Writer Skill — Summary

**One-liner:** Writer CLI context-loader with stdlib-only argparse pattern, plus 9-section generation prompt covering hook formula, HOOK/QUOTE rules, all 5 Universal Voice Rules, and Open Ending Template.

---

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create writer CLI and unit tests (TDD) | 6dd4cb1 | cli.py, __init__.py, __main__.py, test_cli.py |
| 2 | Create generation prompt and skill documentation | bd22bf3 | generation.md, SKILL.md, CONTEXT.md, pytest.ini |

---

## What Was Built

### Task 1: Writer CLI

`cli.py` implements a thin context aggregator (no LLM calls, stdlib only):

- `_get_project_root()` — walks up from `__file__` to `CLAUDE.md` (matches researcher pattern)
- `resolve_project_dir(root, topic)` — case-insensitive substring match on `projects/`, fallback to `.claude/scratch/writer/{topic}`
- `cmd_load(topic)` — reads Research.md, STYLE_PROFILE.md, channel.md; prints labeled sections plus output path and generation prompt path
- `main()` — argparse with `load` subcommand

**Usage:** `PYTHONPATH=.claude/skills/writer/scripts python -m writer load "Duplessis Orphans"`

9 unit tests written first (TDD RED → GREEN); all 9 pass.

### Task 2: Generation Prompt and Skill Docs

`generation.md` contains all 9 mandatory sections:

1. Role statement (writer for dark mysteries documentary channel)
2. Input contract (Research Dossier, Style Profile, Channel DNA)
3. Hook construction — 4-part formula always followed
4. HOOK/QUOTE selection rules — HOOKs are structural anchors, QUOTEs are verbatim speech
5. Chapter structure rules — derive from research, no predefined arc for non-cult topics
6. Universal Voice Rules 1–5 by name with one-line summaries
7. Output format constraints — starts with `## 1. [Chapter Title]`, no metadata
8. Open Ending Template — trigger condition + three-part structure + anti-patterns
9. Output instruction — write Script.md using Write tool, do not print to stdout

`SKILL.md` documents the 4-step invocation workflow.
`CONTEXT.md` defines the stage contract (inputs, process, checkpoints, outputs, deferred).

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added writer scripts path to pytest.ini**
- **Found during:** Task 2 verification (full `pytest -x --tb=short` run)
- **Issue:** `tests/test_writer/test_cli.py` imports `from writer.cli import ...` — the `writer` package was not in `pythonpath` for the default pytest invocation
- **Fix:** Added `.claude/skills/writer/scripts` to `pythonpath` in `pytest.ini`
- **Files modified:** `pytest.ini`
- **Commit:** bd22bf3

### Out-of-Scope Issues Noted

- `tests/test_researcher/test_integration.py::test_ddg_library_fallback` fails due to `duckduckgo_search` → `ddgs` package rename. Pre-existing issue, not caused by this plan. Logged here for awareness.

---

## Verification Results

```
PYTHONPATH=.claude/skills/writer/scripts pytest tests/test_writer/ -x --tb=short
9 passed in 0.06s

pytest -x --tb=short --ignore=tests/test_researcher/test_integration.py
249 passed, 7 warnings in 1.34s
```

All required files exist and pass automated checks.

---

## Self-Check: PASSED

Files verified:
- `.claude/skills/writer/scripts/writer/cli.py` — FOUND
- `.claude/skills/writer/prompts/generation.md` — FOUND
- `.claude/skills/writer/SKILL.md` — FOUND
- `.claude/skills/writer/CONTEXT.md` — FOUND
- `tests/test_writer/test_cli.py` — FOUND

Commits verified:
- `6dd4cb1` — feat(12-01): create writer CLI context loader with unit tests — FOUND
- `bd22bf3` — feat(12-01): add generation prompt, skill docs, and pytest path fix — FOUND
