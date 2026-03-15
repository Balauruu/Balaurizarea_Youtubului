# S01: Visual Orchestrator Skill — UAT

**Milestone:** M002
**Written:** 2026-03-15

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: The skill is a context-loader CLI + schema validator — no live runtime, no server, no UI. All behavior is verified through CLI output inspection and pytest assertions.

## Preconditions

- Python 3.10+ installed
- Working directory is `Channel-automation V3/` repo root
- `projects/1. The Duplessis Orphans/Script.md` exists (from M001)
- `context/visual-references/` contains at least one `VISUAL_STYLE_GUIDE.md`
- `context/channel/channel.md` exists

## Smoke Test

Run `PYTHONPATH=.claude/skills/visual-orchestrator/scripts python -m visual_orchestrator load "Duplessis Orphans"` — should exit 0 and print labeled sections for Script, Visual Style Guide, and Channel DNA.

## Test Cases

### 1. CLI loads all three context sources

1. Run `PYTHONPATH=.claude/skills/visual-orchestrator/scripts python -m visual_orchestrator load "Duplessis Orphans"`
2. Inspect stdout output
3. **Expected:** Output contains three labeled sections:
   - `═══ SCRIPT ═══` followed by Script.md content
   - `═══ VISUAL STYLE GUIDE ═══` followed by VISUAL_STYLE_GUIDE.md content
   - `═══ CHANNEL DNA ═══` followed by channel.md content

### 2. CLI prints output path and generation prompt path

1. Run `PYTHONPATH=.claude/skills/visual-orchestrator/scripts python -m visual_orchestrator load "Duplessis Orphans"`
2. Inspect stdout for path lines
3. **Expected:** Output contains:
   - `Output path:` followed by a path ending in `shotlist.json`
   - `Generation prompt:` followed by a path ending in `generation.md`

### 3. CLI exits 1 on missing Script.md

1. Create a project directory with no Script.md: `mkdir -p projects/99.\ Test\ Project`
2. Run `PYTHONPATH=.claude/skills/visual-orchestrator/scripts python -m visual_orchestrator load "Test Project"`
3. **Expected:** Exit code 1, stderr contains the missing file path

### 4. CLI --guide flag selects specific guide

1. Run `PYTHONPATH=.claude/skills/visual-orchestrator/scripts python -m visual_orchestrator load "Duplessis Orphans" --guide "Mexico"`
2. **Expected:** Output loads the guide from `context/visual-references/Mexico's Most Disturbing Cult/VISUAL_STYLE_GUIDE.md`

### 5. Schema validates a correct shotlist

1. Create a JSON file with valid shotlist structure:
   ```json
   {
     "metadata": {"project": "test", "total_shots": 2, "generated_from": "test"},
     "shots": [
       {"id": "S001", "chapter": 1, "narrative_context": "intro", "visual_need": "establishing shot", "building_block": "Archival Footage", "shotlist_type": "archival_video", "suggested_sources": ["archive.org"]},
       {"id": "S002", "chapter": 1, "narrative_context": "text", "visual_need": "quote", "building_block": "Quote Card", "shotlist_type": "text_overlay", "suggested_sources": [], "text_content": "A quote here"}
     ]
   }
   ```
2. Place it as `projects/1. The Duplessis Orphans/shotlist.json`
3. Run `PYTHONPATH=.claude/skills/visual-orchestrator/scripts python -m visual_orchestrator validate "Duplessis Orphans"`
4. **Expected:** Exit code 0, no errors printed

### 6. Schema rejects invalid shotlist_type

1. Modify shotlist.json so one shot has `"shotlist_type": "podcast_audio"`
2. Run validate
3. **Expected:** Exit code 1, error message includes the shot ID and lists valid types

### 7. Schema enforces text_content on text_overlay

1. Create shotlist with a text_overlay shot missing `text_content`
2. Run validate
3. **Expected:** Exit code 1, error mentions the shot ID and missing text_content

### 8. Schema rejects text_content on non-overlay shots

1. Create shotlist with an archival_video shot that has `"text_content": "some text"`
2. Run validate
3. **Expected:** Exit code 1, error mentions text_content should not be present on non-text_overlay types

### 9. Schema enforces sequencing — no back-to-back glitch

1. Create shotlist with two consecutive shots both using glitch building blocks (e.g., "Static Noise")
2. Run validate
3. **Expected:** Exit code 1, error identifies the consecutive shot IDs as back-to-back glitch elements

### 10. Schema enforces sequencing — max 3 consecutive text_overlay

1. Create shotlist with 4 consecutive text_overlay shots
2. Run validate
3. **Expected:** Exit code 1, error identifies >3 consecutive text_overlay violations

## Edge Cases

### Empty shots array

1. Create shotlist with `"shots": []`
2. Run validate
3. **Expected:** Exit code 0 (empty is valid — no constraint violations possible)

### Non-sequential IDs

1. Create shotlist with shots S001, S003 (skipping S002)
2. Run validate
3. **Expected:** Exit code 1, error identifies non-sequential IDs

### Ambiguous project name resolution

1. If two project directories contain the same substring
2. Run `load` with the ambiguous substring
3. **Expected:** Exit code 1, error explains the ambiguity

## Failure Signals

- CLI exits with non-zero when it should succeed → check file paths exist
- Schema validation passes when it should fail → check `schema.py` constraint logic
- pytest tests fail → run `pytest tests/test_visual_orchestrator/ -v` for per-test diagnostics
- Windows encoding errors on load → `_ensure_utf8_stdout()` may not be triggering

## Requirements Proved By This UAT

- R001 — Script-to-shotlist mapping: CLI loads Script.md + VISUAL_STYLE_GUIDE, generation prompt encodes decision tree, schema validates output
- R002 — Text overlay entries: Schema enforces text_content field on text_overlay type, rejects it on other types

## Not Proven By This UAT

- Quality of Claude-generated shotlist.json content (assessed during S06 integration)
- Behavior with multiple different VISUAL_STYLE_GUIDEs (only one guide exists currently)
- Downstream consumption of shotlist.json by S02-S05 skills (proven in those slices)

## Notes for Tester

- The `load` command is a context aggregator — it doesn't generate the shotlist. Claude reads the output and uses the generation prompt to create shotlist.json.
- For validation tests (cases 5-10), you'll need to manually create shotlist.json files in the project directory. The validate command reads from `projects/N/shotlist.json`.
- The pre-existing `test_ddg_links_extraction` failure in the researcher test suite is unrelated — it's a crawl4ai API change.
