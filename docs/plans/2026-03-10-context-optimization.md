# Visual Style Extractor — Context Optimization Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce the visual-style-extractor's context consumption by ~50-60%, primarily by eliminating inline data transfer between the coordinator and subagents.

**Architecture:** The coordinator (main agent running the skill) currently reads contact sheets, manifest slices, and the analysis prompt into its own context, then passes them to subagents as inline data. After analysis, subagent results return inline to the coordinator. This plan changes the flow so all large data moves through the filesystem — the coordinator only passes file paths to subagents, and subagents write results to files instead of returning them.

**Tech Stack:** Python (pipeline.py), SKILL.md (skill instructions)

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/pipeline.py` | Modify | Add `slice_manifest()` helper and `merge_analysis_batches()` helper |
| `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/tests/test_pipeline.py` | Modify | Add tests for new helpers |
| `.claude/skills/visual-style-extractor/SKILL.md` | Modify | Rewrite Stage 2 and Stage 3 instructions |

---

## Chunk 1: Pipeline Helpers

### Task 1: Manifest Slicing Helper

Extracts a subset of frames from `frames_manifest.json` for a given range of frame indices and writes it to a temporary file. This lets subagents read only the frames they need without the coordinator loading the full manifest into context.

**Files:**
- Modify: `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/pipeline.py`
- Modify: `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test**

```python
# In tests/test_pipeline.py — add this test

def test_slice_manifest(tmp_path):
    """slice_manifest extracts frames by index range and writes to file."""
    manifest = {
        "video_duration": 120.0,
        "total_scenes_detected": 18,
        "unique_frames_after_dedup": 9,
        "frames": [
            {"frame_id": i, "timestamp": i * 10.0, "narration": f"Text {i}",
             "scene_duration": 5.0, "represents_count": 1}
            for i in range(9)
        ],
    }
    manifest_path = tmp_path / "frames_manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    from visual_style_extractor.pipeline import slice_manifest

    out_path = tmp_path / "slice_0.json"
    result = slice_manifest(str(manifest_path), start_idx=0, end_idx=3, output_path=str(out_path))

    assert result == str(out_path)
    assert out_path.exists()

    with open(out_path) as f:
        sliced = json.load(f)

    assert len(sliced["frames"]) == 3
    assert sliced["frames"][0]["frame_id"] == 0
    assert sliced["frames"][2]["frame_id"] == 2
    # Metadata preserved
    assert sliced["video_duration"] == 120.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3" && PYTHONPATH=.claude/skills/visual-style-extractor/scripts python -m pytest .claude/skills/visual-style-extractor/scripts/visual_style_extractor/tests/test_pipeline.py::test_slice_manifest -v`
Expected: FAIL with `ImportError: cannot import name 'slice_manifest'`

- [ ] **Step 3: Implement slice_manifest**

Add to `pipeline.py` after the `_sanitize_dirname` function:

```python
def slice_manifest(
    manifest_path: str,
    start_idx: int,
    end_idx: int,
    output_path: str,
) -> str:
    """Extract a slice of frames from the manifest and write to a new file.

    Args:
        manifest_path: Path to the full frames_manifest.json.
        start_idx: Start frame index (inclusive).
        end_idx: End frame index (exclusive).
        output_path: Where to write the sliced manifest.

    Returns:
        The output_path.
    """
    with open(manifest_path) as f:
        manifest = json.load(f)

    sliced = {
        "video_duration": manifest["video_duration"],
        "total_scenes_detected": manifest["total_scenes_detected"],
        "unique_frames_after_dedup": manifest["unique_frames_after_dedup"],
        "frames": manifest["frames"][start_idx:end_idx],
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sliced, f, indent=2)

    return output_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3" && PYTHONPATH=.claude/skills/visual-style-extractor/scripts python -m pytest .claude/skills/visual-style-extractor/scripts/visual_style_extractor/tests/test_pipeline.py::test_slice_manifest -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd "D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3"
git add .claude/skills/visual-style-extractor/scripts/visual_style_extractor/pipeline.py .claude/skills/visual-style-extractor/scripts/visual_style_extractor/tests/test_pipeline.py
git commit -m "feat(visual-extractor): add slice_manifest helper for context-efficient subagent dispatch"
```

---

### Task 2: Batch Results Merger

Merges multiple per-subagent JSON result files into a single `analysis_results.json`, applying confidence gating.

**Files:**
- Modify: `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/pipeline.py`
- Modify: `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test**

```python
# In tests/test_pipeline.py — add this test

def test_merge_analysis_batches(tmp_path):
    """merge_analysis_batches combines batch files and applies confidence gating."""
    batch_0 = [
        {"frame_id": "F001", "scene_type": "title_card", "confidence": 5},
        {"frame_id": "F002", "scene_type": "archival_photo", "confidence": 2},
    ]
    batch_1 = [
        {"frame_id": "F003", "scene_type": "news_clip", "confidence": 4},
    ]

    (tmp_path / "batch_0.json").write_text(json.dumps(batch_0))
    (tmp_path / "batch_1.json").write_text(json.dumps(batch_1))

    from visual_style_extractor.pipeline import merge_analysis_batches

    output_path = tmp_path / "analysis_results.json"
    kept, removed = merge_analysis_batches(
        batch_paths=[str(tmp_path / "batch_0.json"), str(tmp_path / "batch_1.json")],
        output_path=str(output_path),
        min_confidence=3,
    )

    assert kept == 2  # F001 (5) and F003 (4)
    assert removed == 1  # F002 (2)

    with open(output_path) as f:
        results = json.load(f)
    assert len(results) == 2
    assert results[0]["frame_id"] == "F001"
    assert results[1]["frame_id"] == "F003"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3" && PYTHONPATH=.claude/skills/visual-style-extractor/scripts python -m pytest .claude/skills/visual-style-extractor/scripts/visual_style_extractor/tests/test_pipeline.py::test_merge_analysis_batches -v`
Expected: FAIL with `ImportError: cannot import name 'merge_analysis_batches'`

- [ ] **Step 3: Implement merge_analysis_batches**

Add to `pipeline.py` after `slice_manifest`:

```python
def merge_analysis_batches(
    batch_paths: list[str],
    output_path: str,
    min_confidence: int = 3,
) -> tuple[int, int]:
    """Merge per-subagent batch result files into a single analysis_results.json.

    Args:
        batch_paths: List of paths to JSON files, each containing a JSON array.
        output_path: Where to write the merged results.
        min_confidence: Minimum confidence score to keep a frame entry.

    Returns:
        Tuple of (kept_count, removed_count).
    """
    all_frames = []
    for path in sorted(batch_paths):
        with open(path) as f:
            batch = json.load(f)
        if isinstance(batch, list):
            all_frames.extend(batch)

    kept = [f for f in all_frames if f.get("confidence", 0) >= min_confidence]
    removed_count = len(all_frames) - len(kept)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(kept, f, indent=2)

    return len(kept), removed_count
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3" && PYTHONPATH=.claude/skills/visual-style-extractor/scripts python -m pytest .claude/skills/visual-style-extractor/scripts/visual_style_extractor/tests/test_pipeline.py::test_merge_analysis_batches -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd "D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3"
git add .claude/skills/visual-style-extractor/scripts/visual_style_extractor/pipeline.py .claude/skills/visual-style-extractor/scripts/visual_style_extractor/tests/test_pipeline.py
git commit -m "feat(visual-extractor): add merge_analysis_batches helper with confidence gating"
```

---

## Chunk 2: SKILL.md Rewrite

### Task 3: Rewrite Stage 2 — Pipeline Output to Scratch

Change the instructions so `run_stages_0_to_4` output goes to `.claude/scratch/` instead of staying in the coordinator's context.

**Files:**
- Modify: `.claude/skills/visual-style-extractor/SKILL.md`

- [ ] **Step 1: Replace Stage 2 instructions**

Replace the current `### 2. Run Stages 0–4 (Automated Python)` section with:

```markdown
### 2. Run Stages 0–4 (Automated Python)

```bash
PYTHONPATH=.claude/skills/visual-style-extractor/scripts python -c "
from visual_style_extractor.pipeline import run_stages_0_to_4, PipelineConfig
import json

config = PipelineConfig(source='USER_INPUT_HERE')
result = run_stages_0_to_4(config)

# Write result to scratch pad — do NOT keep in context
with open('.claude/scratch/pipeline_result.json', 'w') as f:
    json.dump(result, f, indent=2)
print('Pipeline result saved to .claude/scratch/pipeline_result.json')
print(f'Output dir: {result[\"output_dir\"]}')
print(f'Contact sheets: {len(result[\"contact_sheet_paths\"])}')
print(f'Video title: {result[\"video_title\"]}')
```​

Read back only the fields you need from `.claude/scratch/pipeline_result.json` using grep or targeted reads. You need: `output_dir`, `contact_sheet_paths` (count and paths), `manifest_path`, `video_title`, `video_source`, `prompt_path`.

**Output directory:** For YouTube URLs, a subfolder named after the video title is created under `context/visual-references/`. For local input, the source directory is used as-is.

If scene count warnings appear, ask the user if they want to re-run with adjusted threshold.
```

- [ ] **Step 2: Commit**

```bash
cd "D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3"
git add .claude/skills/visual-style-extractor/SKILL.md
git commit -m "refactor(visual-extractor): Stage 2 output goes to scratch pad"
```

---

### Task 4: Rewrite Stage 3 — Filesystem-Based Subagent Dispatch

This is the biggest change. Replace the current "read everything into context, pass to subagent, collect results inline" pattern with a filesystem-based approach.

**Files:**
- Modify: `.claude/skills/visual-style-extractor/SKILL.md`

- [ ] **Step 1: Replace Stage 3 instructions**

Replace the current `### 3. Run Stage 5: LLM Analysis (Subagents)` section with:

```markdown
### 3. Run Stage 5: LLM Analysis (Subagents)

**Preparation — generate manifest slices for each batch:**

Group contact sheets into batches of 3-4 sheets each. For each batch, generate a manifest slice:

```bash
PYTHONPATH=.claude/skills/visual-style-extractor/scripts python -c "
from visual_style_extractor.pipeline import slice_manifest
# Repeat for each batch — adjust start/end indices (9 frames per sheet)
slice_manifest('MANIFEST_PATH', start_idx=0, end_idx=27, output_path='.claude/scratch/manifest_slice_0.json')
slice_manifest('MANIFEST_PATH', start_idx=27, end_idx=54, output_path='.claude/scratch/manifest_slice_1.json')
# ... etc
print('Manifest slices ready')
"
```​

**Dispatch subagents in parallel.** For each batch, spawn one subagent (Agent tool, type: general-purpose) with this prompt:

> You are analyzing documentary video frames to extract visual style information.
>
> 1. Read the analysis prompt from: `PROMPT_PATH`
> 2. Read the manifest slice from: `.claude/scratch/manifest_slice_N.json`
> 3. For each contact sheet in your batch, read the image using the Read tool:
>    - `CONTACT_SHEET_PATH_1`
>    - `CONTACT_SHEET_PATH_2`
>    - `CONTACT_SHEET_PATH_3`
> 4. Analyze every frame following the prompt instructions
> 5. Write your JSON array result to: `.claude/scratch/analysis_batch_N.json`
> 6. Return only a 1-line summary: "Analyzed X frames, wrote to .claude/scratch/analysis_batch_N.json"

Do NOT pass the prompt text, manifest data, or image contents in the subagent prompt. The subagent reads everything from files itself.

**After all subagents complete — merge results:**

```bash
PYTHONPATH=.claude/skills/visual-style-extractor/scripts python -c "
from visual_style_extractor.pipeline import merge_analysis_batches
import glob

batch_paths = sorted(glob.glob('.claude/scratch/analysis_batch_*.json'))
kept, removed = merge_analysis_batches(batch_paths, 'OUTPUT_DIR/analysis_results.json')
print(f'Merged {kept} frames ({removed} removed for low confidence)')
"
```​

If `removed > 0`, tell the user how many low-confidence frames were dropped.
```

- [ ] **Step 2: Verify the full SKILL.md reads coherently**

Read the complete SKILL.md and check that Stages 1-5 flow logically with the new instructions.

- [ ] **Step 3: Commit**

```bash
cd "D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3"
git add .claude/skills/visual-style-extractor/SKILL.md
git commit -m "refactor(visual-extractor): Stage 5 uses filesystem-based subagent dispatch

Subagents read prompt, manifest, and images from files instead of
receiving them inline. Results written to scratch/ and merged via
Python helper. Reduces coordinator context consumption ~50-60%."
```

---

### Task 5: Run All Tests

- [ ] **Step 1: Run full test suite**

Run: `cd "D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3" && PYTHONPATH=.claude/skills/visual-style-extractor/scripts python -m pytest .claude/skills/visual-style-extractor/scripts/visual_style_extractor/tests/ -v`
Expected: All tests PASS

- [ ] **Step 2: Push**

```bash
cd "D:/Youtube/D. Mysteries Channel/1.2 Agents/Channel-automation V3"
git push
```

---

## Context Flow — Before vs After

### Before (current)
```
Coordinator reads: prompt (400 tok) + manifest slice (500 tok) + contact sheet (1500 tok) × per batch
Coordinator passes all data inline to subagent prompt
Subagent returns: full JSON array (~800 tok) × per batch
All returns accumulate in coordinator context
Total coordinator context for 15 sheets: ~25,000-35,000 tokens
```

### After (this plan)
```
Coordinator runs: Python one-liners to write slices to scratch/
Coordinator passes: file paths only (~50 tok per subagent prompt)
Subagent returns: 1-line summary (~20 tok) × per batch
Coordinator runs: Python merger, gets 1-line count
Total coordinator context for 15 sheets: ~2,000-3,000 tokens
```

**Estimated reduction: ~90% of Stage 5 coordinator context**
