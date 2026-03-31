# Asset Analyzer V2 — PE-Core CLIP Pipeline

## Semantic Video Analysis & Shotlist Matching for Claude Code

---

## 1. Problem & Context

### What failed (V1)

The V1 pipeline (PySceneDetect CPU + Claude Vision frame-by-frame) does not scale:
- PySceneDetect decodes every frame on CPU → overheating, 30+ min per long video
- Claude Vision requires sending thousands of individual JPEG frames → token-expensive, slow
- First run on 40 videos (22 hours): only completed 4 short cartoons after hours of work and millions of tokens

### What V2 solves

Replace PySceneDetect + Claude Vision with a single GPU model — Meta's PE-Core-L14-336 — that handles scene detection (embedding deltas), content matching (cosine similarity), and content classification (zero-shot taxonomy). All locally, zero cloud tokens for the heavy lifting. Claude is reserved for final review of top candidates via Sonnet (~13K tokens total).

The system manages two pools of indexed footage with different lifecycles: a persistent global library that grows across projects (via promotion from staging), and an ephemeral project index that gets cleaned up when the next project starts.

---

## 2. Why PE-Core-L14-336

| Model | Zero-Shot Classification | Text→Image Retrieval | Video Classification | VRAM |
|-------|--------------------------|---------------------|---------------------|------|
| OpenCLIP ViT-L-14 | 75.3% | 49.5 | ~55% | ~3.5 GB |
| SigLIP 2 L/16 | 83.1% | 55.3 | 65.3% | ~3.5 GB |
| **PE-Core-L14-336** | **83.5%** | **57.1** | **73.4%** | **~2.0 GB** |

PE wins on every metric. The video classification gap is massive (73.4 vs 65.3) because PE was finetuned on 22M synthetic video pairs. Less VRAM (~2 GB vs ~3.5 GB) leaves room for larger batches on 8 GB card. Reads text in images (documents, newspaper clippings, signs). Apache 2.0 licensed.

---

## 3. Architecture Overview

```
                    ┌─────────────────────┐
                    │    VIDEO FILES       │
                    │    staging/          │
                    └──────────┬──────────┘
                               │
                      ┌────────▼────────┐
                      │    INGEST        │  FFmpeg decode → 1fps frames
                      │    ingest.py     │  (NVDEC if available)
                      └────────┬────────┘  Frames stay in memory
                               │
                      ┌────────▼────────┐
                      │    EMBED         │  PE-Core-L14-336
                      │    embed.py      │  frame → 1024-dim vector
                      └────────┬────────┘  Writes to pool cache
                               │
               ┌───────────────┴───────────────┐
               │                               │
      ~/.broll-index/global/          ./.broll-index/
      (persistent library)            (project, ephemeral)
               │                               │
               └───────────┬───────────────────┘
                           │  merged at query time
                ┌──────────┤
                │          │
     ┌──────────▼───┐  ┌──▼──────────────┐
     │  SEARCH       │  │  DISCOVER        │
     │  search.py    │  │  discover.py     │
     │               │  │                  │
     │  Shotlist-     │  │  Auto-taxonomy   │
     │  driven match  │  │  from project    │
     │  + auto query  │  │  context +       │
     │  refinement    │  │  DBSCAN fallback │
     └──────┬────────┘  └──────┬───────────┘
            │                   │
     ┌──────▼───────────────────▼──┐
     │  CLAUDE REVIEW (Sonnet)      │
     │  Top candidates only         │
     │  Adaptive: 1 or 3 per shot   │
     └──────────────┬──────────────┘
                    │
            ┌───────▼───────┐
            │  EXTRACT       │
            │  export_clips  │
            │  + CATALOG     │
            └───────┬───────┘
                    │
            ┌───────▼───────┐
            │  EVALUATE      │  Compare selections vs
            │  evaluate.py   │  ground truth, suggest
            │                │  parameter adjustments
            └───────┬───────┘
                    │
            ┌───────▼───────┐
            │  PROMOTE       │  Move project clips
            │  promote.py    │  → global library
            └───────────────┘
```

**Two invocation modes:**
- **`search`** — Project mode. Loads shotlist, matches against both pools, refines weak queries automatically, Claude reviews top picks adaptively.
- **`discover`** — Exploratory mode on already-embedded footage. Auto-generates taxonomy from project context, clusters unmatched frames, presents for user review.

Both share `ingest.py` and `embed.py`. Embeddings are computed once and reused across modes, sessions, and projects.

---

## 4. Two-Pool Index Architecture

### Pool Definitions

**Global Library** (`~/.broll-index/global/`) — Persistent, ever-growing asset library. Populated exclusively via promotion from project staging footage. Footage that proves useful across projects lives here: atmospheric shots, cartoons, environment footage, generic institutional interiors. Survives project deletion. Compounds value over time.

**Project Index** (`./.broll-index/` inside the project directory) — Ephemeral footage specific to one production. All staging videos are embedded here first. When the next project starts, keepers are promoted to global and the project index is deleted.

### Cache Format (per pool)

Keyed by video file hash (SHA-256 of first 64KB + file size) so the same file is never re-embedded even if renamed or moved:

```
<pool-root>/
├── index.json                   # hash → metadata mapping
├── <hash>/
│   ├── embeddings.npy           # [N, 1024] float16
│   ├── timestamps.npy           # [N] float64 — second offset per frame
│   └── meta.json                # source path, duration, resolution, embed date,
│                                # file hash, original absolute path
```

Storage: ~330 KB per hour of footage. 22 hours = ~7.3 MB.

### Matching Across Pools

At query time, the matcher loads both indexes, concatenates embedding matrices, and runs cosine similarity against the merged set. Results are tagged with source pool.

### Pool Control Flags

```bash
# Embed staging videos into project pool (only valid target)
python scripts/embed.py --input-dir staging/ --pool project

# Search with pool filtering
python scripts/search.py --pool-only global        # ignore project footage
python scripts/search.py --pool-only project       # ignore global library
```

### Promotion Workflow

Promotion is the only entry point into the global library:

```bash
# Promote specific clips from project → global
python scripts/promote.py \
  --clips "exteriors.mp4:01:12-01:18" \
          "sunset.mp4"
```

Promoted clips copy their embeddings and metadata to the global index — no re-encoding needed.

### Global Library Health

```bash
python scripts/embed.py --pool global --health-check
```

Reports dead references (source files moved/deleted), index size, and frame count.

### Project Lifecycle

When a new project is initialized (via channel-assistant `init_project()`):

1. **Prompt to promote** — Review previous project's clips, select keepers for global library
2. **Promote** — `promote.py` saves selected clips + embeddings to global
3. **Cleanup** — Delete `./.broll-index/` (project index gone, global untouched)
4. Auto-generated project taxonomy is discarded (in-memory only, never persisted)

---

## 5. Auto-Taxonomy & Discovery Pipeline

### Taxonomy System

The skill uses two taxonomy tiers — neither requires manual creation.

**Global taxonomy** (`references/taxonomy_global.yaml`) — Ships with the skill. Derived from the channel's VISUAL_STYLE_GUIDE forms and variants. Covers all reusable video content categories. Grows over time as new patterns are discovered across projects.

```yaml
# references/taxonomy_global.yaml
atmospheric:
  atmospheric_institutional: "Institutional interior, ward, lobby, dim hallway"
  atmospheric_industrial: "Factory, machinery, smokestack, mechanical process"
  atmospheric_urban: "City texture, street, infrastructure, building at night"
  atmospheric_interior: "Generic indoor space, room, stairwell"

environment:
  environment_nature: "Forest, mountain, river, weather, landscape"
  environment_urban: "Cityscape, skyline, aerial city view"
  environment_rural: "Farmland, small town, open countryside"
  environment_water: "Ocean, lake, coastline, rain"

cartoon:
  cartoon_authority: "Authority figure, power dynamic, boss, ruler"
  cartoon_confinement: "Trap, cage, enclosure, locked room"
  cartoon_deception: "Trickery, disguise, hidden motive, con artist"
  cartoon_mechanical: "Machine, conveyor belt, labor, factory process"

archival_video:
  archival_news: "News broadcast, press footage, reporter on scene"
  archival_institutional: "Documentary footage of institution, hospital, school"

landscape:
  landscape_aerial: "Drone footage, aerial establishing shot, birds-eye view"
  landscape_rural: "Wide rural establishing shot, open field, countryside road"
  landscape_urban: "Wide urban establishing shot, city approach, downtown"

skip:
  talking_head: "Person speaking to camera, interview, talking head"
  title_graphic: "Title card, lower third, graphic overlay, channel logo"
  black_blank: "Black frame, blank screen, color bars, test pattern"
```

**Project taxonomy** (auto-generated, never manually created) — At analysis time, Claude reads the project's shotlist + script + research and generates project-specific categories that supplement the global taxonomy. These capture content unique to the project that the global categories wouldn't match.

Example for a Duplessis Orphans project — Claude might generate:

```yaml
# Auto-generated, lives in memory during analysis only
project_specific:
  quebec_institutional: "Quebec orphanage exterior, Catholic institution, grey stone building"
  religious_ceremony: "Catholic mass, nuns in habit, church interior, crucifix"
  child_ward: "Children's dormitory, rows of beds, institutional childcare"
  government_hearing: "Quebec parliament, commission testimony, legislative chamber"
```

### Auto-Generation Flow

1. Claude reads `shotlist.json` — extracts all `search_query` fields from `curate` shots
2. Claude reads `script/Script.md` — identifies recurring visual subjects not covered by the global taxonomy
3. Claude generates 5-15 project-specific categories with CLIP-friendly descriptions (concrete, visual, no abstract language)
4. Claude writes the categories to `.claude/scratch/project_taxonomy.json` — `discover.py` reads this via `--taxonomy-project`. The file is disposable (scratch convention)

### Taxonomy Growth (Cross-Project Learning)

After each project's evaluation pass:

1. DBSCAN clusters frames that scored low against all categories (global + project)
2. Claude views 1 representative frame per unknown cluster, proposes a new category name and description
3. User approves/rejects
4. Approved categories are appended to `taxonomy_global.yaml` with a comment noting the source project and date

```yaml
# Added 2026-04-15 from "The Duplessis Orphans" project
  atmospheric_religious: "Church interior, chapel, stained glass, religious iconography"
```

Over time, the global taxonomy becomes increasingly complete for the channel's content patterns. After 5+ projects, most footage should classify into existing categories with fewer unknown clusters.

### Discovery Steps

**Step 1: Classify** — Each frame scored against all categories (global + project-specific). Primary category = highest score.

**Step 2: Filter** — Frames matching `skip` categories are dropped. Remaining frames are `asset_worthy`.

**Step 3: Cluster unknowns** — Frames where the best category score is below a confidence threshold get clustered via DBSCAN to find visual themes the taxonomy missed.

**Step 4: Present** — Claude presents category inventory (minutes per category) + unknown clusters with representative frames. User browses and selects what to extract.

---

## 6. Search Pipeline

### Step 1: Scene Boundaries from Embedding Deltas

Scene boundaries come for free from the CLIP embeddings — no separate model or PySceneDetect needed:

```python
# Cosine similarity between consecutive frames
deltas = 1.0 - cosine_similarity(embeddings[:-1], embeddings[1:])

# Auto-calibrate threshold per video: 90th percentile of deltas
threshold = np.percentile(deltas, 90)

# Peaks above threshold = scene cuts
boundaries = timestamps[np.where(deltas > threshold)]
```

At 1fps, boundaries are accurate to ±1 second. Clips get 2-second padding on both ends during extraction.

### Step 2: Shotlist Query Matching

Embed `search_query` text from the shotlist, score every frame across both pools against every query:

```python
scores = all_embeddings @ query_embeddings.T  # [N_frames, N_queries]
```

Group consecutive high-scoring frames into candidate segments using scene boundaries. Each candidate gets: `shot_id`, `start_sec`, `end_sec`, `peak_score`, `mean_score`, `best_frame_idx`, `pool` (global or project).

### Step 3: Automatic Query Refinement

For queries where `peak_score < 0.20`, Claude generates alternative phrasings without viewing any frames — Claude sees only score reports:

```
S014 (rubber_stamp_bureaucracy) — peak 0.14, no strong match

Claude generates alternatives:
  Alt 1: "cartoon character at desk with paperwork and stamp"
  Alt 2: "office worker processing documents in pile"
  Alt 3: "bureaucrat stamping papers at conveyor belt"
```

`search.py` re-embeds and re-scores with the new queries (instant — video embeddings are cached, only the text side changes). Up to 3 refinement iterations per weak query.

### Step 4: Adaptive Claude Review

Based on final scores after refinement:

| Score Range | Action | Candidates Sent |
|-------------|--------|-----------------|
| > 0.25 | High confidence | Top 1 per shot |
| 0.15 – 0.25 | Ambiguous | Top 3 per shot |
| < 0.15 | No match found | Skip — report to user |

Claude (Sonnet subagent) views candidate frames and writes segment metadata: description, mood, era, tags, scope, relevance. Rejects false positives.

**Token budget:** For a project with 10 b-roll shots: ~16 frames × 800 tokens = ~13K tokens via Sonnet.

**Note:** The 0.25/0.15 thresholds and 90th percentile scene boundary are starting values. The evaluation framework (Section 8) auto-calibrates these based on ground truth comparison.

---

## 7. Data Flow & Frame Handling

### No Frames on Disk

Frames do NOT hit disk en masse. `ingest.py` reads via ffmpeg pipe, `embed.py` embeds in memory, saves only embeddings. Only the candidate frames that reach Claude review get written temporarily to `.claude/scratch/frames/` — typically 1-3 per shotlist entry depending on score confidence, plus 1 per unknown cluster from discovery.

### Pipeline Data Flow

```
ingest.py:   video → ffmpeg pipe → raw frames in memory
embed.py:    raw frames → PE-Core → embeddings.npy + timestamps.npy (cached per pool)
search.py:   cached embeddings (both pools) + shotlist queries → candidates.json
discover.py: cached embeddings + auto-taxonomy → category inventory + clusters → discovery.json

Claude:      reads candidates.json or discovery.json
             extracts specific candidate frames to .claude/scratch/frames/
             Sonnet subagent views frames, writes analysis

export_clips.py: (existing, unchanged) extracts approved clips
catalog.py:      (existing, unchanged) catalogs in SQLite
evaluate.py:     compares selections vs ground truth, suggests parameter adjustments
promote.py:      moves project embeddings → global pool
```

---

## 8. Evaluation & Calibration Framework

### Purpose

Every project is a calibration opportunity. You manually mark which scenes you'd actually use, the system compares against its selections, and parameter adjustments are suggested automatically.

### Ground Truth Template

Before analysis, generate a template pre-populated with video filenames from staging:

```bash
python scripts/evaluate.py --generate-template --videos "staging/*.mp4" --output ground_truth.json
```

Produces:

```json
{
  "project": "The Duplessis Orphans",
  "videos": [
    {
      "file": "yt_9WCKpKRsb_A.mp4",
      "duration_sec": 2847,
      "segments": []
    }
  ]
}
```

You watch in DaVinci Resolve and fill in the segments you'd actually use:

```json
{
  "file": "yt_9WCKpKRsb_A.mp4",
  "duration_sec": 2847,
  "segments": [
    {"start_sec": 22.0, "end_sec": 35.5, "label": "institutional exterior"},
    {"start_sec": 120.0, "end_sec": 138.0, "label": "children in ward"}
  ]
}
```

### Evaluation Metrics

```bash
python scripts/evaluate.py \
  --ground-truth ground_truth.json \
  --predictions video_analysis.json \
  --output eval_report.json
```

For each ground-truth segment, check overlap against skill-selected segments using IoU (Intersection over Union):

- **Hit:** IoU ≥ 0.5 with any predicted segment
- **Miss:** No predicted segment overlaps at IoU ≥ 0.5
- **False positive:** Predicted segment with no ground-truth match

Output metrics:

| Metric | Definition |
|---|---|
| **Precision** | hits / (hits + false positives) |
| **Recall** | hits / (hits + misses) |
| **F1** | harmonic mean of precision and recall |
| **Boundary accuracy** | mean timestamp offset between matched segment boundaries |

### Auto-Calibration

When recall is low (missing scenes), the report suggests:

| Symptom | Suggested adjustment |
|---|---|
| Missed soft cuts between similar scenes | Lower scene boundary percentile (90th → 85th) |
| Good scenes ranked below threshold | Lower score tier thresholds (0.25/0.15 → 0.22/0.12) |
| Relevant frames classified as skip | Review skip category descriptions — too broad? |
| Clusters contain mixed relevant/irrelevant | Tighten DBSCAN eps (0.3 → 0.25) |

When precision is low (too many false positives):

| Symptom | Suggested adjustment |
|---|---|
| Irrelevant scenes passing triage | Raise score tier thresholds |
| Skip categories missing common noise | Add new skip entries |
| Clusters too loose — mixing themes | Tighten DBSCAN eps, raise min_samples |

The report outputs specific parameter values to try, not just directions. Example:

```
Recall: 0.72 (target: 0.80+)
  → 4 misses caused by scene boundary threshold too aggressive
  → Suggestion: lower boundary percentile from 90 to 85
  → 2 misses caused by score threshold — relevant frames scored 0.13-0.14
  → Suggestion: lower ambiguous tier floor from 0.15 to 0.12

Precision: 0.88
  → 3 false positives in "atmospheric_urban" — footage was modern/clean
  → Suggestion: add "modern_clean" to skip categories or tighten atmospheric_urban description
```

### Calibration Persistence

Tuned parameters are saved per-project in `eval_report.json` and tracked across projects. After 3+ projects, the system can show parameter trends and suggest stable defaults to update in the skill config.

---

## 9. Scripts & CLI

### `scripts/ingest.py`

```bash
# Pipe raw RGB to stdout (for embed.py)
python scripts/ingest.py --input video.mp4 --fps 1 --size 336 --pipe

# Save frames to directory (for Claude review of specific frames)
python scripts/ingest.py --input video.mp4 --output-dir frames/ --fps 1 --size 336
```

- Uses `ffmpeg -hwaccel cuda` if NVDEC available, falls back to CPU
- `--size 336` matches PE-Core-L14 input resolution

### `scripts/embed.py`

```bash
# Embed staging videos into project pool
python scripts/embed.py --input-dir staging/ --pool project

# Force re-embed
python scripts/embed.py --input video.mp4 --pool project --force

# Health check on global library
python scripts/embed.py --pool global --health-check
```

- Calls `ingest.py` internally via pipe — frames never hit disk
- Batch size 64 (configurable via `--batch-size`)
- Progress bar via tqdm
- Skips videos already in cache (keyed by file hash)

### `scripts/search.py`

```bash
python scripts/search.py \
  --queries queries.json \
  --videos "staging/*.mp4" \
  --output candidates.json
```

- `queries.json` format: `[{"shot_id": "S006", "text": "Small character cast out..."}]`
- Also accepts markdown shotlist: `--shotlist shotlist.md`
- Computes scene boundaries from embedding deltas (auto-calibrated per video)
- Searches both pools by default, tags results with source
- Reports weak queries (peak < 0.20) for Claude refinement

### `scripts/discover.py`

```bash
# Discover project footage (uses auto-generated taxonomy + global)
python scripts/discover.py \
  --videos "staging/*.mp4" \
  --pool project \
  --taxonomy-global references/taxonomy_global.yaml \
  --taxonomy-project project_categories.json \
  --output discovery.json

# Discover/audit global library
python scripts/discover.py \
  --pool global \
  --output global_audit.json
```

- `--taxonomy-project` accepts the auto-generated categories from Claude (written to a temp JSON)
- When omitted for global pool, uses only global taxonomy
- DBSCAN params configurable: `--eps 0.3 --min-samples 3`

### `scripts/evaluate.py`

```bash
# Generate ground truth template from staging videos
python scripts/evaluate.py --generate-template \
  --videos "staging/*.mp4" \
  --output ground_truth.json

# Run evaluation
python scripts/evaluate.py \
  --ground-truth ground_truth.json \
  --predictions video_analysis.json \
  --output eval_report.json
```

- Template pre-populates video filenames and durations
- IoU threshold configurable: `--iou-threshold 0.5`
- Outputs precision, recall, F1, boundary accuracy, and parameter adjustment suggestions

### `scripts/promote.py`

```bash
# Promote specific clips from project → global
python scripts/promote.py \
  --clips "exteriors.mp4:01:12-01:18" \
          "sunset.mp4"
```

Copies embeddings and metadata to global index — no re-encoding needed.

### Existing scripts (unchanged)

- `export_clips.py` — clip extraction via ffmpeg
- `catalog.py` — SQLite CRUD for `data/asset_catalog.db`

---

## 10. SKILL.md Integration

### Search Workflow (Project Mode)

1. **Resolve context** — Load `visuals/download_manifest.json` (filter to video entries only: `.mp4`, `.webm`, `.mkv`) + `visuals/shotlist.json`
2. **Embed** — `embed.py --input-dir staging/ --pool project` (skips cached videos)
3. **Build queries** — Claude extracts `search_query` fields from shotlist for shots with `action: "curate"`
4. **Search** — `search.py` against both pools (instant)
5. **Refine** — Claude generates alternatives for weak queries, re-runs search (instant, no vision)
6. **Review** — Extract top candidate frames to scratch, Sonnet reviews adaptively
7. **Present** — Segment table for user approval
8. **Extract + Catalog** — `export_clips.py` + `catalog.py`

### Discovery Workflow (Separate Invocation)

1. **Embed** — Same cache, skips if already done
2. **Generate project taxonomy** — Claude reads shotlist + script + research, produces project-specific categories
3. **Discover** — `discover.py` with merged taxonomy (instant on cached embeddings)
4. **Present** — Category inventory + unknown clusters with representative frames
5. **User selects** — Which clusters/categories to extract
6. **Extract + Catalog** — Same scripts
7. **Taxonomy growth** — Approved unknown clusters become new global taxonomy entries

### Project Lifecycle

1. **New project starts** (via channel-assistant `init_project()`) → prompt to promote keepers from previous project's index
2. **Promote** — `promote.py` saves selected clips + embeddings to global library
3. **Cleanup** — Delete `./.broll-index/` (project index gone, global untouched)
4. Previous project's auto-generated taxonomy is discarded (in-memory only, never persisted)

---

## 11. Hardware & Environment

### Target Machine

| Component | Spec |
|-----------|------|
| GPU | NVIDIA RTX 4070 (Ada Lovelace) |
| VRAM | 8 GB GDDR6X |
| NVDEC | 8th gen — H.264, H.265, VP9, AV1 |
| CPU | 16 cores |
| OS | Windows 11 |

### Conda Environment: `perception-models`

```bash
C:/Users/iorda/miniconda3/Scripts/conda.exe create -n perception-models python=3.12 -y
conda activate perception-models

# PyTorch + CUDA 12.4
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 xformers \
  --index-url https://download.pytorch.org/whl/cu124

# PE-Core (source install)
git clone https://github.com/facebookresearch/perception_models.git \
  C:\Users\iorda\repos\perception_models
pip install -e C:\Users\iorda\repos\perception_models

# Search/discovery/evaluation dependencies
pip install scikit-learn tqdm pillow numpy
```

**Disk:** ~5.2 GB (PyTorch + CUDA + xformers + PE + model weights)

**FFmpeg:** Existing install. NVDEC optional — `ingest.py` falls back to CPU decode if unavailable.

### Script Python Path

All scripts reference the conda env Python directly:
```python
PE_PYTHON = "C:/Users/iorda/miniconda3/envs/perception-models/python.exe"
```

---

## 12. Performance

### First Run (40 videos, 22 hours)

| Step | Time | GPU VRAM | Tokens |
|------|------|----------|--------|
| Model load | ~5s | ~2 GB | 0 |
| Embed all videos | ~15-20 min | ~3.5 GB peak | 0 |
| Search (10 queries, both pools) | <2s | 0 (CPU) | 0 |
| Query refinement (3 iterations) | <5s | 0 (CPU) | 0 |
| Frame extract for review | <10s | 0 | 0 |
| Sonnet review | ~2-3 min | 0 | ~13K |
| **Total** | **~20 min** | | **~13K tokens** |

### Subsequent Runs (cached)

| Step | Time |
|------|------|
| Search with new queries | <2s |
| Discovery | <10s |
| Re-run with different shotlist | <5s |

### vs V1

| Metric | V1 (PySceneDetect + Claude Vision) | V2 (PE-Core CLIP) |
|--------|-------------------------------------|---------------------|
| Scene detection | Hours, CPU overheating | Free from embeddings |
| Content matching | 3.3M+ tokens (never finished) | 15-20 min local, 0 tokens |
| Claude review | Thousands of frames | ~13K tokens |
| Re-query cost | Start from scratch | Instant |
| Total first run | Did not complete | ~20 minutes |
| Total re-run | Same as first | Seconds |

---

## 13. Known Limitations

1. **No temporal understanding.** Embeds individual frames. Cannot distinguish "spider slowly wrapping fly over 8 seconds" from a still. Mitigation: scene boundary grouping + Claude review adds narrative context.

2. **Abstract concepts score poorly.** "Bureaucratic menace" won't match. Mitigation: automatic query refinement rephrases to concrete visual descriptions.

3. **No audio.** French narration invisible. Same limitation as V1.

4. **1fps boundary precision.** Scene cuts accurate to ±1 second. Mitigation: 2-second padding on extraction.

5. **Threshold calibration.** Score thresholds (0.25/0.15) and scene boundary percentile (90th) are starting values. The evaluation framework auto-calibrates these per project. Cartoon footage may score lower than live-action — use relative ranking, not absolute scores.

6. **Global library index grows unbounded.** Mitigation: `--health-check` reports size and dead references.

---

## 14. Upstream Changes Required

The following files need updates to support V2:

**`channel/visuals/VISUAL_STYLE_GUIDE.md`:**
- Add `broll_environment` as a new form under "Curated B-Roll Forms" with variants: `nature`, `urban`, `rural`, `water`
- Update `broll_atmospheric` variants from `institutional_corridor, industrial, nature, urban_decay` to `institutional, industrial, urban, interior`

**`.claude/skills/shot-planner/SKILL.md`:**
- Add `broll_environment` to the Form Values table as a valid `curate` form
- Update `broll_atmospheric` variant examples to match

---

## 15. Success Criteria

1. **22 hours of footage indexed in under 25 minutes** on the RTX 4070
2. **Total Claude token cost under 15K** per project
3. **Recall ≥ 0.80** against ground truth on the Duplessis test set
4. **Precision ≥ 0.75** — few enough false positives that review isn't tedious
5. **Re-running with a new shotlist takes seconds** (cached embeddings)
6. **Auto-generated project taxonomy** covers ≥ 90% of project-specific footage without manual category creation
7. **Global taxonomy grows** — after 3+ projects, unknown clusters decrease per project
8. **Project cleanup is gated by new project init** — no orphaned indexes

---

## 16. Skill Directory Structure

```
.claude/skills/asset-analyzer/
├── SKILL.md                    # Skill definition and workflow
├── scripts/
│   ├── ingest.py               # FFmpeg decode → frames in memory
│   ├── embed.py                # PE-Core embedding + pool-aware caching
│   ├── search.py               # Shotlist matching + query refinement
│   ├── discover.py             # Auto-taxonomy + DBSCAN clustering
│   ├── evaluate.py             # Ground truth comparison + auto-calibration
│   ├── promote.py              # Project → global library promotion
│   ├── export_clips.py         # (existing) clip extraction
│   └── catalog.py              # (existing) SQLite CRUD
├── references/
│   ├── PE_CORE_USAGE.md        # Model loading and inference guide
│   ├── SCORING_GUIDE.md        # How to interpret similarity scores
│   └── taxonomy_global.yaml    # Channel-derived global taxonomy (grows over time)
└── eval/
    └── ground_truth.json       # Per-project ground truth (gitignored, user-created)
```
