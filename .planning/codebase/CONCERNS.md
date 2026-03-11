# Codebase Concerns

**Analysis Date:** 2026-03-11

## Architecture & Design

**Incomplete Pipeline Implementation:**
- Issue: Only Phase 1 narrative agents (1.1, 1.2, 1.4) and visual style extractor are implemented; Phase 2 asset pipeline agents (2.1, 2.2, 2.3, 2.4) are not yet built
- Files: `Architecture.md` (lines 120-183), `.claude/skills/visual-style-extractor/`
- Impact: End-to-end workflow cannot run without implementing 4 major agents for media acquisition, generative visuals, animation, and asset management
- Fix approach: Create SKILL.md files for agents 2.1 through 2.4 following the v4 visual-style-extractor template; implement Asset Manager module to orchestrate outputs

**Undefined Pipeline State Management:**
- Issue: Architecture.md specifies "pipeline state will be managed via Claude Code invoking specific skills" but no formal state persistence mechanism is defined for tracking progress across multi-phase runs
- Files: `Architecture.md` (lines 1-4)
- Impact: If a skill fails mid-execution, there is no state file to resume from; intermediate results must be manually tracked
- Fix approach: Define a `pipeline_state.json` schema in `.planning/` documenting: phase, agent status, output locations, timestamps; update SKILL.md files to read/write this on entry/exit

**Competitor Tracking Infrastructure Missing:**
- Issue: Architecture.md line 58 states "Needs: A better way to keep track of competitors" but no competitor data structure or storage mechanism is defined
- Files: `context/competitors/competitors.md`, Architecture.md
- Impact: Agent 1.1 (Channel Assistant) cannot reliably filter topics against competitor coverage without structured competitor profiles
- Fix approach: Define a `competitor_profile_schema.json` with fields: channel_name, topics_covered (timestamped), upload_cadence, target_runtime; store as separate JSON files in `context/competitors/`

## Data Handling & Edge Cases

**Manifest Slicing Calculation is Error-Prone:**
- Issue: `.claude/skills/visual-style-extractor/SKILL.md` (line 70) requires manual calculation of start/end indices for manifest slices (e.g., 9 frames per sheet × batch size). If dedup ratio changes, calculations break silently
- Files: `SKILL.md` (lines 62-74), `synthesize.py` (lines 156-159)
- Impact: Subagents may receive incomplete or overlapping manifest data, causing frame analysis gaps; no validation that slices cover all frames exactly once
- Fix approach: Add `slice_manifest_batches(manifest_path, sheets_per_batch=3)` function to pipeline.py that auto-calculates indices and returns list of slice paths; validate coverage

**Timestamp Parsing Fragility in Align Module:**
- Issue: `align.py` line 9 manually parses MM:SS timestamps by string splitting, and line 32 uses float() without catching ValueError; if transcript has malformed timestamps, parsing silently fails and frames get no narration
- Files: `align.py` (lines 9-12, 32, 50)
- Impact: Frames with unparseable timestamps are assigned empty narration (""), reducing LLM context quality during Stage 5 analysis
- Fix approach: Wrap _timestamp_to_seconds() in try-except, log warnings for unparseable timestamps, provide fallback strategy (e.g., use median narration from adjacent frames)

**Scene Detection Thresholds Lack Validation:**
- Issue: `scene_detect.py` lines 71-76 print warnings if <10 or >200 scenes detected, but do not validate that `adaptive_threshold` parameter is within reasonable bounds (0.1-10.0 typical range)
- Files: `scene_detect.py` (lines 71-76), `pipeline.py` (line 166)
- Impact: User can pass invalid thresholds (e.g., -1.0, 100.0) without immediate feedback; pipeline proceeds with nonsensical outputs
- Fix approach: Add validation in PipelineConfig.__init__() to enforce 0.5 <= adaptive_threshold <= 10.0, raise ValueError with guidance

**Black Frame Detection Threshold is Hardcoded:**
- Issue: `dedup.py` line 17 defines black frame detection threshold (brightness < 15) and black_ratio (0.92) as constants with no user override
- Files: `dedup.py` (lines 15-31)
- Impact: Videos with intentionally dark opening scenes or night footage may be misclassified as transitions and deduplicated inappropriately; no way to tune without code changes
- Fix approach: Add `black_threshold` and `black_ratio` parameters to PipelineConfig and pass through to deduplicate_frames()

## Error Handling & Robustness

**Subprocess Error Messages Not Captured Clearly:**
- Issue: `acquire.py` line 71 raises RuntimeError with stderr, but if yt-dlp is not installed, subprocess.run raises FileNotFoundError before returncode check; error message unhelpful
- Files: `acquire.py` (lines 68-73)
- Impact: User sees "No such file or directory" instead of "yt-dlp is not installed"
- Fix approach: Wrap subprocess.run in try-except, catch FileNotFoundError separately with guidance: "yt-dlp not found. Install: pip install yt-dlp"

**File I/O Missing Encoding Specification:**
- Issue: Multiple modules open JSON files without specifying encoding (Python defaults to platform encoding on Windows)
- Files: `scene_detect.py` (line 94), `dedup.py` (line 184), multiple read operations
- Impact: On non-UTF-8 systems, files with Unicode characters (e.g., Cyrillic video titles) may fail to parse or write with encoding errors
- Fix approach: Add `encoding="utf-8"` to all open() calls; use pathlib.Path for path construction

**ImageMagick/Pillow Missing Graceful Fallback:**
- Issue: `contact_sheets.py` line 57 silently passes on FileNotFoundError or OSError, leaving white cells as placeholders without logging
- Files: `contact_sheets.py` (lines 53-58)
- Impact: If 5+ frames fail to load (corrupted, wrong path format), user doesn't know; analysis subagents receive sparse visual data
- Fix approach: Log each failure with frame_id and path; if >50% of batch fails to load, raise exception with frame list to investigate

**No Timeout on External Tool Calls:**
- Issue: `scene_detect.py` line 43 and `acquire.py` line 69 call subprocess.run() without timeout; if ffmpeg or yt-dlp hangs, script hangs indefinitely
- Files: `scene_detect.py` (line 43), `acquire.py` (line 69)
- Impact: Long videos or slow network conditions can cause indefinite blocking; no mechanism to cancel/retry
- Fix approach: Add `timeout=3600` (1hr) to subprocess.run() calls; implement retry logic with exponential backoff for network calls

## Test Coverage Gaps

**No Integration Tests for Full Pipeline:**
- Issue: `test_pipeline.py` tests individual helper functions (slice_manifest, merge_analysis_batches) but not end-to-end Stage 0-4 execution
- Files: `test_pipeline.py`
- Impact: Breaking changes to pipeline.py orchestration are not caught; real-world issues with file paths, directory structure not verified
- Fix approach: Add integration test that runs full pipeline on a small test video; verify all outputs (frames/, contact_sheets/, manifest, dedup_report) exist and contain expected data

**Scene Detection Untested:**
- Issue: No test for detect_scenes() or _extract_keyframes(); these are critical path but only covered by informal smoke testing
- Files: `scene_detect.py` (lines 19-98), `test_pipeline.py`
- Impact: Changes to adaptive_threshold logic or keyframe extraction timing can introduce subtle bugs
- Fix approach: Add test with synthetic small video or mock scenedetect library; verify frame count and timing accuracy

**Manifest Format Stability Not Tested:**
- Issue: No test verifies that manifest_schema (fields: frames, video_duration, total_scenes_detected, unique_frames_after_dedup) doesn't change; breaking changes to schema would break Stage 6 synthesis
- Files: `align.py` (lines 73-95), `synthesize.py` (lines 110-144)
- Impact: If manifest schema changes, Stage 6 synthesis fails silently on proportion calculations
- Fix approach: Add JSON schema file `.claude/skills/visual-style-extractor/schemas/manifest_schema.json`; validate in build_manifest() using jsonschema library

## Performance & Scalability

**Contact Sheet Generation Memory Scaling:**
- Issue: `contact_sheets.py` line 44 creates full SHEET_SIZE (1568×1568) images in memory for each sheet; for 100+ frame videos, this loads many high-res PIL Images simultaneously
- Files: `contact_sheets.py` (lines 15-65)
- Impact: For 50+ frame videos, memory footprint grows linearly; on resource-constrained systems, could cause OOM
- Fix approach: Add stream-mode processing: load/resize frame image only when pasting (already done), but consider adding progress bar and memory check

**Frame Deduplication PHash Scaling:**
- Issue: `dedup.py` line 83 runs PHash.encode_images() on all frames at once; for 500+ frame videos, this becomes slow
- Files: `dedup.py` (lines 82-91)
- Impact: Stage 2 runtime becomes prohibitive for long videos; no batching or parallelization
- Fix approach: Consider batching: encode in chunks of 100 frames, then merge duplicate groups; low-priority unless user reports slowdown on 1h+ videos

**Manifest Lookup in Synthesize is O(n):**
- Issue: `synthesize.py` line 116 builds frame_lookup dict from manifest on every call; if called multiple times, this is redundant
- Files: `synthesize.py` (lines 110-144)
- Impact: Minor inefficiency in proportion calculation; negligible for typical ~50-frame videos
- Fix approach: Low priority; acceptable as-is

## Dependency Management

**External Tool Dependencies Not Documented:**
- Issue: Requirements for ffmpeg, yt-dlp, and scenedetect are not listed in `requirements.txt` or in a single place
- Files: `.claude/skills/visual-style-extractor/scripts/requirements.txt` (assumed to exist but not verified), SKILL.md (lines 12-22)
- Impact: User may install Python deps but forget system deps; pipeline fails at Stage 0 or Stage 1 with opaque error
- Fix approach: Create INSTALL.md documenting all system dependencies (ffmpeg, yt-dlp) with platform-specific install steps; verify SKILL.md prerequisites section is complete

**imagededup PHash Model Loading Unchecked:**
- Issue: `dedup.py` line 82 instantiates PHash() without checking if pre-trained models are cached; first run downloads ~50MB model
- Files: `dedup.py` (line 82)
- Impact: First-time users see long delay (minutes) without feedback; no progress indicator
- Fix approach: Add print() statement before PHash instantiation: "Loading PHash model (may take 1-2 min on first run)..."

## Known Limitations & Design Debt

**Synthesize Module Inference is Fragile:**
- Issue: `synthesize.py` line 77 infers category from pattern_name if no category field present (backward compatibility with v3); if pattern_name is misspelled or new, defaults to "graphics_animation"
- Files: `synthesize.py` (lines 77-84)
- Impact: Misclassified frames end up in wrong section of VISUAL_STYLE_GUIDE.md; inference fallback hides schema mismatches
- Fix approach: Log warnings when inferring category; add unit test that verifies all known pattern_names map correctly

**No Validation of Frame IDs Across Stages:**
- Issue: Frame IDs are assigned in dedup.py but their uniqueness and consistency through align → contact_sheets → manifest is not validated
- Files: `dedup.py` (line 129), `align.py` (line 62), `contact_sheets.py` (line 46)
- Impact: If Stage 2 and Stage 3 process frames out of order, manifest and contact sheets become misaligned; hard to debug
- Fix approach: Add assert in build_manifest() to verify frame_ids are sequential 1...N after dedup

**Transcript-Frame Alignment Assumes Temporal Coverage:**
- Issue: `align.py` line 66 assigns narration to first segment where `start <= frame_seconds < end`; if frame has no overlapping segment, narration is empty
- Files: `align.py` (lines 56-70)
- Impact: For transitions or silent sections, frames have no context; LLM analysis becomes harder
- Fix approach: Fall back to nearest neighboring segment's text if no overlap; log warnings for frames with >5s distance from nearest segment

**Contact Sheets Discard Frame Metadata:**
- Issue: `contact_sheets.py` intentionally generates sheets with no labels (line 19 docstring); metadata only in manifest JSON
- Files: `contact_sheets.py` (lines 15-25)
- Impact: Subagents must cross-reference images with manifest for every frame; if manifest gets corrupted, images are useless
- Fix approach: Consider adding optional `--with_labels` flag to contact_sheets.py to include frame_id + timestamp as small text overlay; useful for debugging

## Security & Data Handling

**No Input Validation on URLs:**
- Issue: `acquire.py` line 53 passes user URL directly to yt-dlp without validation
- Files: `acquire.py` (lines 53-86)
- Impact: User could pass command-injection payloads; unlikely but possible if used in automated pipeline
- Fix approach: Validate URL format with urllib.parse.urlparse(); reject non-http(s) schemes

**Temporary Download Directory Cleanup:**
- Issue: `pipeline.py` line 141 uses os.rmdir() after moving temp files; if any files remain, rmdir fails silently and temp directory persists
- Files: `pipeline.py` (lines 134-141)
- Impact: Over many runs, `context/visual-references/_download_temp/` accumulates; low risk but poor cleanup
- Fix approach: Use shutil.rmtree() instead of os.rmdir() to ensure removal; add check and log warning if cleanup fails

**No Logging of Processing Decisions:**
- Issue: Dedup algorithm (phash vs. near_black grouping) is deterministic but not logged in detail; only summary written to dedup_report.json
- Files: `dedup.py` (lines 93-110)
- Impact: If user disputes which frames were merged, no audit trail of matching scores or confidence
- Fix approach: Enhance dedup_report.json to include phash distance scores for each duplicate pair

## Testing Strategy Gaps

**Synthesis Subagent Prompt Not Tested:**
- Issue: `synthesize_prompt.txt` is loaded and passed to subagent, but never validated for format or completeness
- Files: `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/prompts/synthesis_prompt.txt` (assumed)
- Impact: If prompt file is corrupted or missing, Stage 6 fails silently; subagent receives malformed instructions
- Fix approach: Add test that reads synthesis_prompt.txt, validates it contains required sections: "INPUT", "TASK", "OUTPUT_FORMAT", "RULES"

**Analysis Subagent Prompt Version Mismatch Risk:**
- Issue: Analysis prompt template referenced in Stage 5 may diverge from what v4 subagents expect if prompt evolves
- Files: `pipeline.py` (line 199), `.claude/skills/visual-style-extractor/scripts/visual_style_extractor/prompts/analysis_prompt.txt` (assumed)
- Impact: If prompt is updated without updating test expectations, batch analysis results schema changes, causing merge_analysis_batches() to fail
- Fix approach: Add version field to analysis_prompt.txt header; validate in merge_analysis_batches() that all batches match expected version

## Architecture-Level Concerns

**Skill Dispatch Lacks Retry Logic:**
- Issue: SKILL.md (line 77) dispatches subagents in parallel without retry mechanism; if one subagent fails, pipeline halts
- Files: `SKILL.md` (lines 77-91)
- Impact: Transient failures (network, LLM rate limit) cause entire run to fail; no graceful degradation
- Fix approach: Implement retry helper in skill main script: retry subagent dispatch up to 2 times on failure; log which batches failed; optionally continue with partial results

**No Dry-Run Mode:**
- Issue: Pipeline always creates output files and directory structure; no way to validate config without committing state
- Files: `pipeline.py` (lines 114-256)
- Impact: User must delete outputs if they made a mistake in config; no safe way to test threshold changes
- Fix approach: Add `PipelineConfig.dry_run: bool = False` flag; skip file writes in dry-run mode, print what would be created

---

*Concerns audit: 2026-03-11*
