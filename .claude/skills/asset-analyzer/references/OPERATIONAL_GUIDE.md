# Operational Guide — Avoiding Known Failures

Read this before running the embedding or search pipeline. These patterns come from actual production failures and their root causes.

## Table of Contents

1. [FFmpeg Subprocess Safety](#ffmpeg-subprocess-safety)
2. [Embedding Performance](#embedding-performance)
3. [Monitoring Long Runs](#monitoring-long-runs)
4. [NVDEC Hardware Acceleration](#nvdec-hardware-acceleration)
5. [Pool Index Safety](#pool-index-safety)
6. [Memory Budget](#memory-budget)

---

## FFmpeg Subprocess Safety

### The Pipe Deadlock (Critical)

**Never** use `proc.stdout.read()` with `stderr=subprocess.PIPE`. This causes a deadlock when stderr fills its 64KB buffer — FFmpeg blocks writing stderr, Python blocks reading stdout, neither can proceed.

```python
# WRONG — deadlocks on videos with decode warnings
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
raw = proc.stdout.read()  # blocks forever

# CORRECT — drains both pipes concurrently
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
raw, stderr = proc.communicate()
```

This was the cause of the first embedding hang in the Duplessis project (stuck at 38% for 40+ minutes).

### Tolerating Partial Decode Errors

Some videos have corrupt H.264 NAL units. FFmpeg reports errors to stderr and exits non-zero, but still produces usable frames. Check frame count before raising:

```python
if proc.returncode != 0 and n_frames == 0:
    raise RuntimeError(...)
# If frames > 0, the decode was partially successful — use what we got
```

This was the cause of the second crash — `yt_FRM6njzI1zU.mp4` (1.4GB) had corrupt sections but produced valid frames.

### Always Set Timeouts

Add `timeout` to all `subprocess.run()` calls:
- Frame extraction: `timeout=300` (5 min per video)
- Clip export: `timeout=120` (2 min per clip)
- FFprobe: `timeout=30`

Without timeouts, a hung FFmpeg process blocks the entire pipeline indefinitely.

---

## Embedding Performance

### Expected Throughput (RTX 4070 8GB)

| Video Length | Frames at 1fps | Embed Time | Notes |
|-------------|----------------|------------|-------|
| < 5 min | < 300 | ~20s | Batch fits in single GPU pass |
| 5-30 min | 300-1800 | 20s-2min | Multiple batches, still fast |
| 30-60 min | 1800-3600 | 2-5 min | Frame extraction dominates |
| 1-2 hours | 3600-7200 | 5-10 min | Large raw frame buffer (2-4 GB RAM) |

Total for 40 videos / ~22h footage: **~33 minutes** (17 cached + 23 new).

### Why It Can Seem Stuck

1. **Frame extraction is the bottleneck, not GPU**: For a 1-hour video, FFmpeg must decode all ~108K source frames (at 30fps) to extract ~3600 frames (at 1fps). The GPU sits idle during decode.

2. **tqdm output buffering**: When running via background command, tqdm writes to stderr with carriage returns. The output file captures these as repeated lines. Progress appears frozen even when the process is active.

3. **Large videos spike RAM**: A 2-hour video at 1fps/336px produces ~7200 frames × 338KB = ~2.4GB of raw frame data, all held in memory. Combined with the model (~3.5GB VRAM + ~2GB RAM), total can reach 6-8GB.

### How to Monitor Real Progress

Don't rely on tqdm output. Instead check:

```bash
# Check if embedding files are being written
find "<project>/.broll-index/" -name "embeddings.npy" | wc -l

# Check GPU utilization (should spike during batch embed)
nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader

# Check process memory (growing = decoding frames, stable = embedding or stuck)
tasklist | grep python
```

If GPU utilization is 0% AND process memory is stable for >5 minutes, the process is likely stuck.

### Optimization: Skip Cached Videos

`embed.py` checks `pool_index.has(fhash)` before processing. On re-runs, cached videos return in <1ms. Only new/changed videos are processed.

---

## NVDEC Hardware Acceleration

### How It Works

When NVDEC is available, FFmpeg uses GPU-accelerated video decoding:
```
-hwaccel cuda -hwaccel_output_format cuda → hwdownload,format=nv12 → fps → scale → rgb24
```

This is ~2-3x faster than CPU decode for H.264/H.265 content.

### When It Fails

- **Unsupported codecs**: VP9, AV1 on older GPUs
- **10-bit content**: Some NVDEC implementations can't decode 10-bit H.264
- **Driver mismatch**: CUDA toolkit version vs. driver version

### Fallback Behavior

`_check_nvdec()` runs `ffmpeg -hwaccels` at startup. If "cuda" isn't in output, all videos decode on CPU. No per-video retry — if NVDEC fails on one video, the entire session falls back to CPU.

The current code does NOT retry with CPU if NVDEC fails mid-decode. A future improvement would add automatic CPU fallback per-video.

---

## Pool Index Safety

### Race Condition Risk

The pool index (`index.json`) has no file locking. If two processes write simultaneously, one's changes are lost. In practice this means:

- **Safe**: One `embed.py` process at a time
- **Unsafe**: Two terminal windows running embed on different video sets
- **Unsafe**: Running embed while search/discover reads the index

### Crash Recovery

If `embed.py` crashes between writing `.npy` files and updating `index.json`:
- Orphaned `.npy` files exist in `.broll-index/<hash>/`
- `index.json` doesn't reference them
- Re-running embed will recompute (wastes time but no data loss)

To detect orphans: compare directories in `.broll-index/` against keys in `index.json`.

### File Hash Stability

`file_hash()` uses SHA-256 of first 64KB + file size. This means:
- Moving a file doesn't change its hash (content-based)
- Appending to a file changes its hash (size changes)
- Modifying bytes beyond 64KB does NOT change the hash (unlikely but possible false positive)

---

## Memory Budget

### Per-Component RAM Usage

| Component | RAM | When |
|-----------|-----|------|
| PE-Core model (CPU mirror) | ~2 GB | After `load_model()` |
| Frame buffer (1h video at 1fps/336px) | ~1.2 GB | During `extract_frames()` |
| Frame buffer (2h video at 1fps/336px) | ~2.4 GB | During `extract_frames()` |
| Embeddings in pool (1000 videos) | ~1.5 GB | During `load_all_embeddings()` |
| Score matrix (75K frames × 10 queries) | ~3 MB | During `score_queries()` |

### Peak RAM During Embedding

`model + longest_video_frames + embedding_batch = ~3.5 + 2.4 + 0.5 = ~6.4 GB`

This is why the process showed 5.3GB RAM when decoding `yt_9XX8g0dirw8.mp4`.

### Peak RAM During Search

`model + all_pool_embeddings + score_matrix = ~2 + 1.5 + 0.003 = ~3.5 GB`

For the Duplessis project (40 videos, 75K frames), this was comfortable. A 500-video global pool would need ~10GB+.

### VRAM Budget (RTX 4070 8GB)

| Component | VRAM |
|-----------|------|
| Model weights | ~2 GB |
| Batch of 64 frames | ~1.5 GB |
| Text tokens | ~0.1 GB |
| PyTorch overhead | ~1 GB |
| **Total peak** | **~4.6 GB** |

Leaves ~3.4 GB headroom. Batch size 64 is safe. Could increase to 128 for faster throughput.
