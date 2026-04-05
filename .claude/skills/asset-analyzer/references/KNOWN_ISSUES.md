# Known Issues & Improvement Backlog

Tracked issues from production runs and code audit. Prioritized by impact.

## Critical — Fix Before Next Large Run

### 1. Pool loads all embeddings into RAM
- **File**: `pool.py:110-132` (`load_all_embeddings()`)
- **Impact**: OOM on pools > ~500 videos. Current project (40 videos, 75K frames) uses ~1.5 GB. A 500-video global pool would need ~10GB+.
- **Fix**: Implement memory-mapped numpy arrays or per-video lazy loading. Score queries against one video at a time, merge top-K results.
- **Workaround**: Use `--pool-only project` to avoid loading global pool.

### 2. Pool index has no file locking
- **File**: `pool.py:46-95` (`_load`, `_save`, `put`)
- **Impact**: Concurrent writes corrupt `index.json`. Lost entries, silent data loss.
- **Fix**: Add `msvcrt.locking()` (Windows) around read-modify-write cycle. Or atomic write pattern: write to temp file, rename.
- **Workaround**: Only run one embed process at a time.

### 3. Large frame buffers held entirely in RAM
- **File**: `ingest.py:53-54` (`extract_frames`)
- **Impact**: A 2-hour video at 1fps/336px = 2.4GB raw frames in memory. Combined with model = 6-8GB total.
- **Fix**: Stream frames to disk, or process in chunks (decode N seconds → embed → discard → next N seconds).
- **Workaround**: Process videos under 90 minutes. For longer videos, split with ffmpeg first.

## High — Should Fix

### 4. No NaN/INF validation in scoring
- **File**: `search.py:61-68` (`score_queries`)
- **Impact**: Corrupted embeddings propagate silently. All scores become NaN, no candidates returned.
- **Fix**: Add `assert np.all(np.isfinite(query_emb))` before scoring, and check frame embeddings on load.

### 5. NVDEC failure has no per-video retry
- **File**: `ingest.py:38-40`
- **Impact**: If NVDEC fails on a specific codec mid-run, that video gets 0 frames. No CPU fallback attempted.
- **Fix**: Catch FFmpeg error, retry without hwaccel args for that video only.

### 6. No timeout on subprocess calls
- **Files**: `ingest.py:101`, `evaluate.py:129`, `export_clips.py:43`
- **Impact**: Hung FFmpeg blocks the pipeline forever.
- **Fix**: Add `timeout=300` to all `subprocess.run()` calls.

### 7. Query embeddings not cached across refinement rounds
- **File**: `search.py:221`
- **Impact**: Same queries re-encoded on GPU each search run. 3 refinement iterations = 3x wasted GPU time.
- **Fix**: Cache query embeddings by text hash in scratch directory.

## Medium — Quality of Life

### 8. No progress reporting inside embed_video()
- **File**: `embed.py:80-84`
- **Impact**: For a 2-hour video, user sees no progress for 5-10 minutes during frame extraction + batch embedding.
- **Fix**: Add tqdm for batch processing within `embed_frames()`, or periodic status prints.

### 9. Hardcoded paths and magic numbers
- **Files**: `embed.py:19,25,29`, `ingest.py:46`
- **Impact**: Scripts aren't portable. Break on different machines.
- **Fix**: Read from environment variables or a config.json. Fall back to defaults.

### 10. health_check() doesn't verify .npy integrity
- **File**: `pool.py:147-162`
- **Impact**: Corrupted embeddings discovered only at search time.
- **Fix**: Load and verify shape/dtype of each .npy during health check. Optional CRC in meta.json.

### 11. Tests in scripts/ directory
- **Impact**: Test files deployed with production code. Could be accidentally executed.
- **Fix**: Move test_*.py to a separate tests/ directory.

## Low — Nice to Have

### 12. No structured logging
- **Impact**: Debugging relies on print() output. No timestamps, levels, or log files.
- **Fix**: Replace print() with `logging` module. Add timestamps and log level control.

### 13. Inconsistent path handling (str vs Path)
- **Impact**: Code style inconsistency. Minor maintenance burden.
- **Fix**: Standardize on pathlib.Path across all scripts.

### 14. promote.py substring matching too loose
- **File**: `promote.py:62-67`
- **Impact**: Ambiguous clip names could match wrong pool entries.
- **Fix**: Require exact basename match or prompt for disambiguation.

### 15. Float16 precision not validated at scale
- **File**: `pool.py:81`
- **Impact**: Cosine similarity error ~0.001 per query. Cumulative effect over many searches unknown.
- **Fix**: Run precision benchmark: compare float16 vs float32 recall@10 on real data.
