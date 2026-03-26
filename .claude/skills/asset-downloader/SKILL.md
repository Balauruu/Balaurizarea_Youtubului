---
name: asset-downloader
description: "Download video files for documentary projects from YouTube and archive.org. Reads media_leads.json (YouTube URLs from media-scout) and shotlist.json (archive.org broll_leads from shot-planner), downloads all videos to staging, and writes download_manifest.json as handoff for asset-analyzer. Triggers on: 'download assets', 'download videos', 'fetch footage', 'download for [topic]', or any request to download video assets for a project."
---

# Asset Downloader

Download all video assets for a documentary project. Reads upstream URL sources, downloads to staging, writes a manifest for asset-analyzer.

**Classification:** [DETERMINISTIC] — Python script handles all logic.

## Inputs

- `projects/N. [Title]/visuals/media_leads.json` → `youtube_urls[]` entries (URL, title, duration_sec, score)
- `projects/N. [Title]/visuals/shotlist.json` → `curate` shots with `broll_leads[]` (archive.org URLs)

## Outputs

- Videos → `projects/N. [Title]/assets/staging/`
- Manifest → `projects/N. [Title]/visuals/download_manifest.json`

## Workflow

### Step 1 — Resolve Project

Topic is a case-insensitive substring match against `projects/` directory names. Multiple matches → list all and ask. No match → error.

Verify both input files exist:
- `visuals/media_leads.json` — required (from media-scout)
- `visuals/shotlist.json` — optional (if missing, only YouTube leads are downloaded)

### Step 2 — Run Download Script

```bash
python .claude/skills/asset-downloader/scripts/download.py \
  --project "projects/N. [Title]"
```

To skip 24fps re-encoding (keep original frame rate):
```bash
python .claude/skills/asset-downloader/scripts/download.py \
  --project "projects/N. [Title]" --no-reencode
```

The script:
1. Reads both input files
2. Collects all video URLs (YouTube from media_leads, archive.org from shotlist broll_leads)
3. Deduplicates by URL
4. Downloads to `assets/staging/` with site-specific rate limiting
5. Re-encodes videos above 24fps to 24fps (default behavior — fits the channel's cinematic aesthetic and reduces frames for downstream analysis)
6. Writes `visuals/download_manifest.json`
7. Prints summary to stdout

### Step 3 — Present Results

Read the script's stdout summary. Present to the user:

| Source | Attempted | Completed | Failed | Skipped | Total Size |
|--------|-----------|-----------|--------|---------|------------|

For failures, show the URL and error reason. Offer to retry failed downloads by re-running the script (it skips already-completed entries).

## Download Manifest Schema

```json
{
  "project": "The Duplessis Orphans",
  "downloaded_at": "2026-03-26T14:30:00Z",
  "total_size_mb": 4230,
  "videos": [
    {
      "id": "DL-001",
      "source": "youtube",
      "source_url": "https://youtube.com/watch?v=...",
      "title": "CBC Documentary: Les Enfants de Duplessis",
      "duration_sec": 2847,
      "score": 1,
      "file_size_mb": 385,
      "local_path": "assets/staging/yt_dQw4w9WgXcQ.mp4",
      "status": "completed",
      "shot_refs": [],
      "context": "Primary source documentary from CBC archives, interviews with survivors"
    },
    {
      "id": "DL-002",
      "source": "internet_archive",
      "source_url": "https://archive.org/details/the_cobweb_hotel",
      "title": "The Cobweb Hotel (1936)",
      "duration_sec": 420,
      "score": null,
      "file_size_mb": 95,
      "local_path": "assets/staging/ia_cobweb-hotel.mp4",
      "status": "completed",
      "shot_refs": ["S004", "S017"],
      "context": "Metaphor for institutional trap — spider-innkeeper concealing predatory intent"
    }
  ]
}
```

**Fields:**
- `source`: `"youtube"` or `"internet_archive"`
- `score`: from media-scout scoring (null for archive.org)
- `shot_refs`: shotlist entry IDs this video serves (empty for YouTube leads)
- `context`: why this video matters — from media_leads description or broll_leads match_reasoning
- `status`: `"completed"`, `"failed"`, or `"skipped"`

## 24fps Re-encoding (Default)

By default, videos with frame rates above 24fps are re-encoded to 24fps after download. This:
- Fits the channel's cinematic documentary aesthetic
- Reduces frames for downstream analysis (asset-analyzer processes fewer frames)
- Produces smaller files on disk

The re-encode uses `ffmpeg -r 24 -c:v libx264 -crf 23 -preset fast -c:a copy`. If re-encoding fails, the original file is kept.

The manifest records both `original_fps` and `fps` (the actual FPS of the staged file) so asset-analyzer knows what it's working with.

To disable: pass `--no-reencode` to the script, or when invoking the skill say "download at original fps" / "skip re-encoding".

## Resume Logic

The script is idempotent. If `download_manifest.json` already exists, it loads it and skips entries with `status: "completed"` whose files still exist on disk. Re-running after a failure picks up where it left off.

## Rate Limiting

Site-specific — critical to avoid blocks:

- **YouTube:** `--sleep-interval 3 --max-sleep-interval 8 --sleep-requests 1.5`. Batches of 10 with 15s pause between batches. On 429 error, stop immediately and mark remaining as failed.
- **Archive.org:** 2-second delay between requests. Generally permissive.

## Volume Cap

200GB total per run. Tracks cumulative file size. When approaching the cap, remaining entries are logged as `status: "skipped"` with reason.

## Dependencies

- `yt-dlp` — YouTube and archive.org video download
- `ffmpeg` — post-download validation (ffprobe)
- `requests` — archive.org metadata API + direct HTTP download
