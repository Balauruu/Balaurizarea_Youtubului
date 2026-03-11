# Testing Patterns

**Analysis Date:** 2026-03-11

## Test Framework

**Runner:**
- pytest (configured by convention, no explicit config file)
- Tests run via: `pytest` or `python -m pytest`

**Assertion Library:**
- pytest's built-in assertions (`assert`)
- Simple comparison-based assertions, no custom matchers

**Run Commands:**
```bash
pytest                           # Run all tests
pytest -xvs                      # Run with verbose output, stop on first failure
pytest .claude/skills/visual-style-extractor/scripts/visual_style_extractor/tests/
                                 # Run specific test suite
pytest tests/test_pipeline.py    # Run single test file
pytest -k "test_slice_manifest"  # Run tests matching pattern
```

**Coverage:**
- Not enforced — no pytest.ini or setup.cfg with coverage config
- No coverage measurement currently in place
- Run coverage with: `pytest --cov`

## Test File Organization

**Location:**
- Co-located in `tests/` subdirectory of module: `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/tests/`
- Test file naming: `test_*.py` convention

**Naming:**
- Module: `test_pipeline.py` — tests for `pipeline.py`
- Functions: `test_<function_name>` — each function or behavior gets a test
- Examples: `test_slice_manifest()`, `test_merge_analysis_batches()`, `test_prepare_synthesis_input()`

**Structure:**
```
.claude/skills/visual-style-extractor/scripts/
├── visual_style_extractor/
│   ├── acquire.py
│   ├── pipeline.py
│   ├── synthesize.py
│   └── tests/
│       ├── __init__.py
│       └── test_pipeline.py
```

## Test Structure

**Suite Organization:**
```python
def test_slice_manifest(tmp_path):
    """slice_manifest extracts frames by index range and writes to file."""
    # Setup
    manifest = { ... }
    manifest_path = tmp_path / "frames_manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    # Execute
    from visual_style_extractor.pipeline import slice_manifest
    out_path = tmp_path / "slice_0.json"
    result = slice_manifest(str(manifest_path), start_idx=0, end_idx=3, output_path=str(out_path))

    # Assert
    assert result == str(out_path)
    assert out_path.exists()
    with open(out_path) as f:
        sliced = json.load(f)
    assert len(sliced["frames"]) == 3
```

**Patterns:**
- Setup section: Create fixtures, establish test data
- Execute section: Call the function being tested
- Assert section: Verify results with specific, meaningful assertions
- File-based tests use `tmp_path` pytest fixture for isolated filesystems
- JSON data created inline for small datasets, used for input validation

**Setup/Teardown:**
- No explicit setup/teardown methods — use pytest fixtures (`tmp_path`, others passed as parameters)
- `tmp_path` fixture provides per-test isolated temporary directory
- Working directory changed only when necessary, restored after: `original_dir = os.getcwd(); os.chdir(...); ... os.chdir(original_dir)`

## Mocking

**Framework:** No external mocking library detected
- Tests use `tmp_path` fixture instead of mocking filesystem
- Actual file I/O tested (not mocked)
- Subprocess calls not mocked — real commands expected to exist

**Patterns:**
```python
# Example: test_run_stage_6_writes_synthesis_input
# Instead of mocking file write, use tmp_path
manifest_path = str(tmp_path / "manifest.json")
with open(manifest_path, "w") as f:
    json.dump(manifest, f)

# Change directory for test, restore after
original_dir = os.getcwd()
os.chdir(str(tmp_path))
try:
    result = run_stage_6(...)
    assert os.path.exists(result)
finally:
    os.chdir(original_dir)
```

**What to Mock:**
- Nothing is mocked — tests prefer real file I/O with temp directories
- External tools (yt-dlp, ffmpeg) are expected to be available
- No API calls are mocked

**What NOT to Mock:**
- Filesystem operations — test with actual files
- JSON serialization/deserialization
- Data structure transformations
- Confidence filtering logic

## Fixtures and Factories

**Test Data:**
- Inline JSON structures created per test for clarity
- Realistic data shapes used (matches actual manifest structure)
- Example from `test_merge_analysis_batches()`:
```python
batch_0 = [
    {"frame_id": "F001", "pattern_name": "title_card", "confidence": 5},
    {"frame_id": "F002", "pattern_name": "archival_photo", "confidence": 2},
]
batch_1 = [
    {"frame_id": "F003", "pattern_name": "news_clip", "confidence": 4},
]
```

**Location:**
- Test data defined inside each test function (no shared fixtures file)
- Pytest's `tmp_path` fixture used for all file-based tests
- No factory classes or builder patterns (data is simple enough for direct creation)

## Coverage

**Requirements:** No coverage targets enforced
- No `pytest.ini` or `setup.cfg` with coverage settings
- No CI enforcement of coverage thresholds
- Coverage is optional and informational

**View Coverage:**
```bash
pytest --cov=visual_style_extractor --cov-report=html
pytest --cov=visual_style_extractor --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Functions tested in isolation with controlled inputs
- Each function behavior covered: success path, error paths, boundary conditions
- Examples: `test_slice_manifest()`, `test_aggregate_supports_v3_scene_type_field()`, `test_aggregate_infers_category_from_pattern_name()`
- Scope: Single function call with assertions on return value and side effects (file writes)

**Integration Tests:**
- Tests verify interaction between pipeline stages
- `test_run_stage_6_writes_synthesis_input()` tests the full `run_stage_6()` flow including file I/O
- Manifest files loaded, processed, and written to verify stage outputs
- Multi-function chains tested together (manifest loading → synthesis prep → file writing)

**E2E Tests:**
- Not implemented — pipeline orchestration tested manually via Claude Code skills
- Full end-to-end testing would require running entire pipeline with real video input

## Common Patterns

**Async Testing:**
- Not used — codebase is synchronous except for `crawl4ai` scraper (async usage in `scraper.py`, not tested)

**Error Testing:**
```python
# Pattern: Test exception conditions
def test_validate_local_input_raises_on_missing_video(tmp_path):
    # Would create a directory with transcript but no video
    # Expect FileNotFoundError with specific message
    pass
```

**Boundary Testing:**
```python
# Pattern: Test edge cases and limits
def test_aggregate_excludes_transitions():
    """Transitions are fully excluded from aggregation."""
    frames = [
        {"frame_id": "F001", "category": "transition", "pattern_name": "black_transition", "confidence": 5},
        {"frame_id": "F003", "category": "b_roll", "pattern_name": "archival_video", "confidence": 5},
    ]
    result = aggregate_by_category_and_type(frames)
    assert "_transition" not in result
```

**Data Transformation Testing:**
```python
# Pattern: Verify correct output format and structure
def test_prepare_synthesis_input():
    """prepare_synthesis_input produces structured text with pattern data."""
    result = prepare_synthesis_input(analysis_results, manifest, "Test Video", "test_source")

    # Verify string output
    assert isinstance(result, str)
    # Verify metadata included
    assert "VIDEO_TITLE: Test Video" in result
    # Verify categories present
    assert "=== CATEGORY: B-Roll" in result
    # Verify pattern data included
    assert "--- PATTERN: archival_bw_footage ---" in result
    # Verify exclusions work
    assert "black_transition" not in result
```

## Test Execution

**Running tests:**
- No setup.py or requirements-test.txt — dependencies specified in project root (not yet analyzed)
- pytest expected to be installed in same environment as source dependencies
- Tests import directly: `from visual_style_extractor.pipeline import slice_manifest`
- `PYTHONPATH` may need to include `.claude/skills/visual-style-extractor/scripts` for discovery

**Current coverage (observed from test file):**
- `pipeline.py`: 3 tests covering `slice_manifest()`, `merge_analysis_batches()`, `run_stage_6()`
- `synthesize.py`: 6 tests covering aggregation, synthesis, and v3/v4 compatibility
- Other modules (acquire, scene_detect, align, dedup, contact_sheets): No tests present

**Gaps:**
- No tests for `acquire.py` (download_from_youtube, validate_local_input)
- No tests for `scene_detect.py` (detect_scenes, _run_detection, _extract_keyframes)
- No tests for `align.py` (parse_transcript, align_frames)
- No tests for `dedup.py` (deduplicate_frames, _is_near_black)
- No tests for `contact_sheets.py` (generate_contact_sheets)
- No error condition tests (malformed inputs, missing files, external tool failures)

---

*Testing analysis: 2026-03-11*
