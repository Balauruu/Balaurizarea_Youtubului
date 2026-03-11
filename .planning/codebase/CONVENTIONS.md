# Coding Conventions

**Analysis Date:** 2026-03-11

## Language & Environment

**Language:** Python only (per CLAUDE.md project mandate)

**Python Version:** Implied 3.10+ (union type syntax `|` used throughout)

**UTF-8 Encoding:** All files

**Line Endings:** LF (`\n`) — enforced via `.gitattributes` for Git

## Naming Patterns

### Files

- **Lowercase with underscores:** `scene_detect.py`, `acquire.py`, `dedup.py`, `align.py`, `contact_sheets.py`, `synthesize.py`, `pipeline.py`
- **Stage-based naming:** Files named after their stage function (Stage 0 = acquire, Stage 1 = scene_detect, etc.)
- **Module names are descriptive:** `scraper.py` (web scraping), `pipeline.py` (orchestrator)

### Functions

- **snake_case:** `detect_scenes()`, `deduplicate_frames()`, `parse_transcript()`, `align_frames()`, `generate_contact_sheets()`
- **Private functions:** Prefixed with underscore: `_is_near_black()`, `_format_timestamp()`, `_extract_keyframes()`, `_run_detection()`, `_normalize_pattern_name()`, `_infer_category()`
- **Verb-based names:** Action verbs for operations: `validate_local_input()`, `download_from_youtube()`, `build_manifest()`
- **Query-like names for checks:** `find_video_file()`, `find_transcript_file()`

### Variables

- **snake_case throughout:** `video_path`, `output_dir`, `manifest_path`, `contact_sheet_paths`, `frame_seconds`
- **Dictionary keys use snake_case:** `frame_id`, `scene_number`, `keyframe_path`, `represents_count`, `narration`
- **Avoid single-letter vars except in loops:** Use `output_dir` not `od`; acceptable: `for i, frame in enumerate(frames):` or `for fname in filenames:`
- **Boolean variable names:** Properties use `is_` prefix: `is_youtube` (property), functions use `_is_near_black()`
- **Collections are plural:** `scenes`, `frames`, `results`, `groups`, `segments`, `keyframe_paths`, `black_filenames`

### Types & Classes

- **PascalCase for classes:** `PipelineConfig`, `SceneInfo`
- **All constants UPPERCASE:** `VIDEO_EXTENSIONS`, `SHEET_SIZE`, `COLS`, `PADDING`, `CATEGORIES`, `CATEGORY_ORDER`, `PATTERN_TO_CATEGORY`
- **Type hints with union syntax:** `str | None`, `list[dict]`, `dict[str, list]`

## Code Organization

### Import Order

1. Standard library: `os`, `json`, `subprocess`, `re`, `shutil`, `glob`, `asyncio`
2. Third-party: `PIL`, `numpy`, `scenedetect`, `webvtt`, `pysrt`, `imagededup`, `crawl4ai`, `dataclasses`
3. Local/relative: `from visual_style_extractor.acquire import ...`

**Example from `pipeline.py`:**
```python
import os
import re
import json
import shutil
from dataclasses import dataclass

from visual_style_extractor.acquire import validate_local_input, download_from_youtube
from visual_style_extractor.scene_detect import detect_scenes
```

**No wildcard imports** (`from module import *`)

**No import aliases** unless absolutely necessary

### Constants

- Defined at module top, after imports
- ALL_CAPS with underscores: `VIDEO_EXTENSIONS`, `SHEET_SIZE`, `COLS`, `ROWS`, `PADDING`, `JPEG_QUALITY`
- Grouped logically:
  ```python
  # File discovery
  VIDEO_EXTENSIONS = (".mp4", ".webm", ".mkv", ".avi", ".mov")
  TRANSCRIPT_EXTENSIONS = (".vtt", ".srt", ".txt")

  # Contact sheet layout
  SHEET_SIZE = 1568
  COLS = 3
  ROWS = 3
  PADDING = 4
  ```

### Dataclasses

**Pattern:** Used for configuration and structured results

```python
@dataclass
class PipelineConfig:
    source: str
    output_dir: str | None = None
    adaptive_threshold: float = 3.0
    min_scene_len: int = 15

@dataclass
class SceneInfo:
    scene_number: int
    start_time: float  # seconds
    end_time: float    # seconds
    duration: float    # seconds
    keyframe_path: str
```

- All fields typed
- Default values explicit and semantic
- No frozen/slots flags yet

## Function Signatures

### Pattern

```python
def function_name(
    required_param: Type,
    optional_param: Type | None = None,
    config_param: int = 8,
) -> ReturnType:
    """One-line description of function purpose.

    Optional longer description explaining algorithm or special behavior.

    Args:
        required_param: What it is and why.
        optional_param: What it is, when to use, when optional.
        config_param: Default value and what it controls.

    Returns:
        What is returned and its structure.
    """
```

### Type Hints

**Mandatory** on all parameters and returns:
- `def detect_scenes(video_path: str, output_dir: str, adaptive_threshold: float = 3.0, min_scene_len: int = 15) -> list[SceneInfo]:`
- `def parse_transcript(transcript_path: str) -> list[dict]:`
- `def generate_contact_sheets(frames: list[dict], output_dir: str) -> list[str]:`
- `-> tuple[int, int]` for multiple returns
- `-> dict[str, dict[str, list]]` for nested structures

### Parameters

- **Required first, optional with defaults after**
- **Defaults are semantic:** `adaptive_threshold: float = 3.0` (meaningful value, not arbitrary)
- **No *args or **kwargs** — explicit parameters preferred
- **Optional params use None:** `output_dir: str | None = None` instead of empty string

### Return Values

- **Always typed:** `-> str:`, `-> dict:`, `-> list[SceneInfo]:`
- **Meaningful return types:** avoid `-> None` unless function is truly side-effect only
- **Tuples for multiple values:** `(kept_count, removed_count)` returns as `tuple[int, int]`
- **Dicts for structured results:** `{"video_path": "...", "transcript_path": "..."}` returns as `dict[str, str]`
- **Lists for sequences:** `list[dict]`, `list[str]`, `list[SceneInfo]`

## Function Design

### Docstrings

**Module-level (at file top):**
```python
"""Stage 1: Scene Detection using PySceneDetect AdaptiveDetector."""
```

**Function-level (required):**
```python
def detect_scenes(
    video_path: str,
    output_dir: str,
    adaptive_threshold: float = 3.0,
    min_scene_len: int = 15,
) -> list[SceneInfo]:
    """Detect scenes in a video and extract keyframes.

    Args:
        video_path: Path to video file.
        output_dir: Directory to write frames/ and scenes.json.
        adaptive_threshold: PySceneDetect sensitivity (lower = more scenes).
        min_scene_len: Minimum scene length in frames.

    Returns:
        List of SceneInfo objects.
    """
```

### Scope & Complexity

- **Single responsibility:** Each function does one thing well
- **Median length:** 20-40 lines
- **Large functions decomposed:** `run_stages_0_to_4()` breaks into stage calls rather than inlining
- **Helper functions extracted:** `_is_near_black()`, `_format_timestamp()` are private helpers

### Parameter Design

- **No global state:** All configuration passed explicitly or via dataclass
- **Type hints on all args:** No type ambiguity
- **Sensible defaults:** `max_distance_threshold: int = 8`, `min_confidence: int = 3`
- **Configuration objects over many params:** Use `config: PipelineConfig` not 5 individual threshold args

## Error Handling

### Pattern: Explicit Exceptions

```python
# FileNotFoundError — use for missing files/directories
if not video_path:
    raise FileNotFoundError(
        f"No video file found in {directory}. "
        f"Expected one of: {', '.join(VIDEO_EXTENSIONS)}"
    )

# RuntimeError — for external tool failures
if result.returncode != 0:
    raise RuntimeError(
        f"yt-dlp failed (exit {result.returncode}):\n{result.stderr}"
    )

# ValueError — for invalid input/state
if not isinstance(batch, list):
    raise ValueError("Expected JSON array in batch file")
```

### Guidelines

- **Raise explicitly, not silently**
- **Error messages include context:** What was expected? What was found?
- **Use named exception types** (not generic `Exception`)
- **Subprocess auto-raise:** Use `subprocess.run(..., check=True)` to raise on non-zero exit
- **Catch specific exceptions:** `except (FileNotFoundError, OSError):` not bare `except:`
- **Try/finally for cleanup:** `try: ... finally: os.chdir(original_dir)`

## Logging & Output

**Framework:** `print()` only (no logging library)

### Patterns

**Progress messages:**
```python
print(f"\n[Stage 1/6] Detecting scenes...")
print(f"  Done: {len(scenes)} scenes detected (threshold: {config.adaptive_threshold})")
```

**File operations:**
```python
print(f"Manifest saved to {output_path} ({len(frames)} frames)")
print(f"Saved contact sheet: {sheet_path} ({len(batch)} frames)")
```

**Warnings:**
```python
print(f"  WARNING: Only {scene_count} scenes detected. Consider lowering threshold.")
print(f"  WARNING: Dedup removed >90% of frames. Video may be too uniform.")
```

**Indentation:** Use 2 spaces for sub-operations

### Verbosity

- **One message per major operation**
- **Summary counts at completion**
- **No per-item logging** (would be too noisy for 100+ frames)

## Comments

### When to Comment

**DO comment:**
- Non-obvious algorithm choices: "Near-black frames are pre-grouped before hashing to prevent duplicates that PHash misses"
- Threshold explanations: `threshold: 15 — catches only true black frames, not dark footage`
- Workarounds for tool limitations: "Handle HH:MM:SS.mmm or MM:SS.mmm formats"
- Complex data transformations: "Build filename -> SceneInfo lookup before operating on it"

**DON'T comment:**
- Self-evident code: `for fname in scene_by_filename:` needs no comment
- Type hints already explain: `is_youtube: bool` is clear
- Good function names speak for themselves: `deduplicate_frames()` is obvious

### Comment Style

```python
# Capitalize first letter for full sentences
# Use descriptive comments that explain "why", not "what"

# Example: Good comment
# Near-black frames (transitions, fades) are pre-grouped before hashing
# to prevent duplicates that PHash misses due to noise variation.
detected = phasher.find_duplicates(...)
```

## Conventions for New Code

### Writing Functions

1. Use **snake_case** for name
2. Add **type hints** to all parameters and return
3. Write **docstring** with Args/Returns
4. Use **imperative/descriptive** names
5. Place **private helpers** (`_*`) before public functions
6. **Raise exceptions explicitly**; never silently fail

### Writing Modules

1. Add **module docstring** at top explaining pipeline stage
2. Import in order: stdlib → third-party → local
3. Define **constants** (all caps) at top
4. Define **dataclasses** next
5. Define **private helpers** (`_*`) before public functions
6. Define **public functions** last

### Writing New Tests

See TESTING.md for test patterns (pytest, fixtures, assertions)

---

*Convention analysis: 2026-03-11*
