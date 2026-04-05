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

## Reference Files

| File | When to Read |
|------|-------------|
| `references/OPERATIONAL_GUIDE.md` | Before running embed.py — covers subprocess safety, monitoring, performance expectations, memory budget |
| `references/KNOWN_ISSUES.md` | When debugging failures or planning improvements — prioritized backlog with file:line references |
| `references/SCORING_GUIDE.md` | When interpreting search results — score ranges, content type effects, query refinement tips |
| `references/PE_CORE_USAGE.md` | When modifying model loading or encoding — API reference for PE-Core-L14-336 |
| `references/taxonomy_global.yaml` | Discovery mode — global category definitions for frame classification |

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

**Pre-filter: blank/empty frame detection.** After extracting candidate frames, check if frames are near-blank (mostly a single color — e.g., black, white, or solid fill). If >50% of extracted frames for a segment are near-blank, auto-reject the segment without sending to Sonnet. This saves vision calls on title cards, fade-outs, and leader footage.

Send remaining frames to Sonnet subagent (use `model: "sonnet"` in Agent tool):

| Score Range | Candidates Sent |
|-------------|-----------------|
| > 0.25 | Top 1 per shot |
| 0.15 – 0.25 | Top 3 per shot |
| < 0.15 | Skip — report to user |

Sonnet writes per-segment: description, mood, era, tags, scope, relevance.

**Auto-reject and refinement.** If Sonnet gives a candidate `relevance <= 2` or `recommendation: "reject"`, do NOT include it in the review file. Instead:
1. Generate 2-3 alternative search queries with different visual descriptions for that shot
2. Re-run search.py with the alternative queries
3. Extract and review the new candidates through the same pipeline
4. Repeat up to 3 refinement rounds per shot
5. If after 3 rounds no candidate achieves `relevance >= 3`, report the gap to the user with the best attempt and why it was insufficient

Only segments with `relevance >= 3` and `recommendation: "keep"` or `"maybe"` proceed to the review file.

### Step 6: Present for review

**Always display timestamps in H:MM:SS or M:SS format** (use `start_ts`/`end_ts` fields from candidates.json, never raw seconds).

Assign each recommendation a unique `rec_id` in sequential format: `R001`, `R002`, etc. Only segments that passed the Step 5 filters (relevance >= 3, recommendation "keep" or "maybe") appear here.

Present results in conversation AND generate `<project>/visuals/asset_review.json` for the user to edit:

```json
{
  "segments": [
    {
      "rec_id": "R001",
      "shot_id": "S006",
      "shot_description": "Children born to unmarried women were classified as illegitimate...",
      "video": "ia_EducationForDeathTheMakingOfTheNazi.mp4",
      "start_ts": "6:43",
      "end_ts": "6:45",
      "score": 0.217,
      "sonnet_description": "1940s animated child in dunce cap...",
      "relevance": 5,
      "recommendation": "keep",
      "decision": "",
      "adjusted_start": "",
      "adjusted_end": "",
      "user_comment": ""
    }
  ]
}
```

User fills in:
- `decision`: `"approve"`, `"reject"`, or leave empty (= approve recommendation)
- `adjusted_start` / `adjusted_end`: If different from proposed timestamps, write new values in `M:SS` or `H:MM:SS` format
- `user_comment`: Optional free-text feedback on the recommendation

Include the **shot description** from `shotlist.json` (`narrative_context` field) so the user can instantly see what the shot is for.

Present a summary table in conversation:

| Rec | Shot | Shot Description | Video | Timestamps | Sonnet Description | Score | Rec |
|-----|------|-----------------|-------|------------|-------------------|-------|-----|

Tell the user: "Edit `visuals/asset_review.json` — fill `decision`, `adjusted_start`/`adjusted_end`, and optionally `user_comment` fields, then tell me to proceed."

### Step 6b: Process review file

Read `<project>/visuals/asset_review.json`. For each segment:
- If `decision` is `"reject"`: skip
- If `decision` is `"approve"` or empty with recommendation `"keep"`: extract
- If `adjusted_start` or `adjusted_end` is set: use those timestamps instead of the proposed ones

Parse user timestamps: accept `M:SS`, `H:MM:SS`, or raw seconds.

### Step 6c: Process calibration data

After processing the review file, compare each segment's user decisions against the original recommendations. For any segment where the user's input differs from the recommendation, log to `<project>/visuals/calibration_log.json`:

```json
{
  "entries": [
    {
      "rec_id": "R001",
      "shot_id": "S006",
      "video": "...",
      "proposed_start": "6:43",
      "proposed_end": "6:45",
      "adjusted_start": "",
      "adjusted_end": "",
      "recommendation": "keep",
      "decision": "keep",
      "user_comment": "a more appropriate shot could've been found",
      "delta_type": "comment_only"
    },
    {
      "rec_id": "R004",
      "shot_id": "S017",
      "video": "ia_Wastageo1947.mp4",
      "proposed_start": "6:38",
      "proposed_end": "6:50",
      "adjusted_start": "6:45",
      "adjusted_end": "7:00",
      "recommendation": "keep",
      "decision": "keep",
      "user_comment": "perfect recommendation",
      "delta_type": "timestamp_adjusted"
    }
  ]
}
```

**Delta types:**
- `timestamp_adjusted` — user changed `adjusted_start` or `adjusted_end` from proposed values
- `recommendation_overridden` — user's `decision` contradicts the `recommendation` (e.g., recommendation was "keep" but decision is "reject", or vice versa)
- `comment_only` — user left a `user_comment` but did not change timestamps or override the recommendation

**Timestamp offset tracking.** When `delta_type` is `timestamp_adjusted`, calculate the offset in seconds between proposed and adjusted timestamps (for both start and end). Track whether the user typically widens segments (adjusted range > proposed range) or narrows them (adjusted range < proposed range). This data can later inform segment boundary detection thresholds in search.py.

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
