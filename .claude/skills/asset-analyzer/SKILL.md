---
name: asset-analyzer
description: "Analyze and catalog video assets for documentary projects using PE-Core CLIP embeddings. Use when the user says 'analyze assets', 'analyze staging videos', 'discover footage', 'search footage for [topic]', 'find clips matching shotlist', 'evaluate asset selection', or any request to process downloaded video footage."
---

# Asset Analyzer V2

PE-Core CLIP embedding pipeline for video asset analysis. Embeds footage locally on GPU, matches against shotlist queries via cosine similarity, discovers content via auto-taxonomy, and evaluates selections against ground truth.

**Spec:** `docs/superpowers/specs/2026-03-31-asset-analyzer-v2-design.md`

## Modes

**Search mode** (default) — User references a project: "Analyze staging videos for Duplessis Orphans"
- Matches shotlist queries against embedded footage
- Searches both project and global pools
- Claude reviews top candidates adaptively (Sonnet subagent)

**Discovery mode** — "Discover what's in the Duplessis footage"
- Auto-generates project taxonomy from shotlist + script + research
- Classifies all frames against merged taxonomy (global + project)
- Clusters unknown frames via DBSCAN
- User browses and selects what to extract

**Evaluation mode** — "Evaluate asset selections for Duplessis"
- Compares skill selections against user-created ground truth
- Reports precision, recall, F1, boundary accuracy
- Suggests specific parameter adjustments

## Conda Environment

All scripts run via:
```
C:/Users/iorda/miniconda3/envs/perception-models/python.exe
```

## Search Workflow

### Step 1: Resolve context

1. Resolve project directory (case-insensitive substring match against `projects/`)
2. Read `visuals/download_manifest.json` — filter to video entries only (`.mp4`, `.webm`, `.mkv`)
3. Read `visuals/shotlist.json` — extract `search_query` fields from shots with `action: "curate"`

### Step 2: Embed staging videos

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/embed.py --input-dir "<project>/assets/staging" --pool project --project-dir "<project>"
```

Skips already-cached videos. First run ~15-20 min for 22h of footage, subsequent runs instant.

### Step 3: Build and run queries

Extract queries from shotlist — one per `curate` shot:
```json
[{"shot_id": "S006", "text": "Empty institutional corridor with dim lighting"}]
```

Write to `.claude/scratch/queries.json`, then:

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/search.py --queries .claude/scratch/queries.json --project-dir "<project>" --output .claude/scratch/candidates.json
```

### Step 4: Refine weak queries

Read `candidates.json`. For queries in `weak_queries` (peak < 0.20), generate 2-3 alternative phrasings with concrete visual descriptions. Re-run search with refined queries.

Up to 3 refinement iterations. No vision needed — Claude sees only score reports.

### Step 5: Adaptive Claude review

Extract candidate frames to `.claude/scratch/frames/`:

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/ingest.py --input "<video>" --output-dir .claude/scratch/frames --start <sec> --end <sec> --fps 1 --size 512
```

Send frames to Sonnet subagent (use `model: "sonnet"` in Agent tool):

| Score Range | Candidates Sent |
|-------------|-----------------|
| > 0.25 | Top 1 per shot |
| 0.15 – 0.25 | Top 3 per shot |
| < 0.15 | Skip — report to user |

Sonnet writes per-segment: description, mood, era, tags, scope, relevance.

### Step 6: Present for review

Present segment table:

| Video | Shot | Timestamps | Description | Score | Scope | Pool |
|-------|------|------------|-------------|-------|-------|------|

User approves/rejects, adjusts timestamps or scope.

### Step 7: Extract + Catalog

For each approved segment, use existing `export_clips.py`:

```bash
python .claude/skills/asset-analyzer/scripts/export_clips.py --input "<source>" --output "<dest>" --clips '[{"start": "<s>", "end": "<e>", "label": "<name>"}]'
```

Catalog in SQLite:
```python
from data.catalog import get_connection, insert_clip
conn = get_connection()
insert_clip(conn, path=clip_path, source_type="youtube", scope=scope,
            source_url=url, project=project_name, category=category,
            description=desc, mood=mood, era=era, tags=tags,
            duration_sec=duration)
```

**Output paths:**
- `scope: "project"` → `projects/N/assets/{category}/`
- `scope: "global"` → `D:/Youtube/D. Mysteries Channel/3. Assets/{category}/`

## Discovery Workflow

### Step 1: Embed (same as search, skips if cached)

### Step 2: Generate project taxonomy

Read `shotlist.json`, `script/Script.md`, and research docs. Generate 5-15 project-specific categories with CLIP-friendly descriptions. Write to `.claude/scratch/project_taxonomy.json`:

```json
{
  "project_specific": {
    "quebec_institutional": "Quebec orphanage exterior, Catholic institution, grey stone building",
    "religious_ceremony": "Catholic mass, nuns in habit, church interior, crucifix"
  }
}
```

### Step 3: Run discovery

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/discover.py --pool project --project-dir "<project>" --taxonomy-global .claude/skills/asset-analyzer/references/taxonomy_global.yaml --taxonomy-project .claude/scratch/project_taxonomy.json --output .claude/scratch/discovery.json
```

### Step 4: Present results

Show category inventory (minutes per category) + unknown clusters with representative frames.

For unknown clusters, extract 1 representative frame per cluster and view it (Sonnet subagent) to propose a name.

### Step 5: User selects what to extract

### Step 6: Extract + Catalog (same as search)

### Step 7: Taxonomy growth

If user approves unknown cluster names, append them to `references/taxonomy_global.yaml` with a date comment:

```yaml
# Added 2026-04-15 from "The Duplessis Orphans" project
  atmospheric_religious: "Church interior, chapel, stained glass, religious iconography"
```

## Evaluation Workflow

### Step 1: Generate ground truth template

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/evaluate.py --generate-template --videos "<project>/assets/staging/*.mp4" --project-name "<name>" --output "<project>/visuals/ground_truth.json"
```

Give template to user. They fill in segments in DaVinci Resolve.

### Step 2: Run evaluation

After user completes ground truth:

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe .claude/skills/asset-analyzer/scripts/evaluate.py --ground-truth "<project>/visuals/ground_truth.json" --predictions "<project>/visuals/video_analysis.json" --output "<project>/visuals/eval_report.json"
```

### Step 3: Review and apply calibration

Present metrics and calibration suggestions. Apply approved parameter changes for the next run.

## Project Lifecycle

When a new project is initialized (channel-assistant `init_project()`):

1. Check if `./.broll-index/` exists from a previous project
2. If yes: prompt user to promote keepers via `promote.py`
3. After promotion: delete `./.broll-index/`

## Checkpoints

| After | Agent Presents | Human Decides |
|-------|---------------|---------------|
| Step 2 (embed) | Embedding summary (videos, frames, time) | Continue |
| Step 4 (refine) | Weak queries + proposed alternatives | Approve alternatives |
| Step 6 (present) | Segment table with scores | Approve/reject segments |
| Step 7 (cleanup) | Extraction complete | Delete staging files or keep |

## Model Routing

- **Haiku:** Not used in V2 (CLIP handles triage locally)
- **Sonnet:** Claude review of candidate frames (Step 5)
- **Opus:** Orchestration only — query refinement, taxonomy generation, presentation
