---
name: asset-downloader
description: "Download video files for documentary projects from YouTube and archive.org. Reads media_leads.json (YouTube URLs from media-scout) and shotlist.json (archive.org broll_leads from shot-planner), downloads all videos to staging, and writes download_manifest.json as handoff for asset-analyzer. Triggers on: 'download assets', 'download videos', 'fetch footage', 'download for [topic]', or any request to download video assets for a project."
---

# Asset Downloader

Download all video assets for a documentary project. Reads upstream URL sources, downloads to staging, writes a manifest for asset-analyzer.

**Classification:** [DETERMINISTIC] — Python script handles all logic.

## Inputs

- `projects/N. [Title]/visuals/media_leads.json` → `youtube_urls[]` (URL, title, duration_sec, score)
- `projects/N. [Title]/visuals/shotlist.json` → `curate` shots with `broll_leads[]` (archive.org URLs)

## Outputs

- Videos → `projects/N. [Title]/assets/staging/`
- Manifest → `projects/N. [Title]/visuals/download_manifest.json`

## Workflow

### Step 1 — Resolve Project

Topic is a case-insensitive substring match against `projects/` directory names. Multiple matches → list all and ask. No match → error.

Verify `visuals/media_leads.json` exists (required). `visuals/shotlist.json` is optional — if missing, only YouTube leads download.

### Step 2 — Run Download Script

```bash
python .claude/skills/asset-downloader/scripts/download.py \
  --project "projects/N. [Title]"
```

Options:
- `--no-reencode` — Skip 24fps re-encoding (keep original frame rate)
- `--cookies-from-browser brave` — Force specific browser for YouTube auth
- `--no-cookies` — Disable authentication entirely

The script downloads YouTube sequentially (with rate limiting and anti-bot detection) and archive.org in parallel (5 workers), running both concurrently. Videos above 24fps are re-encoded to 24fps by default. Only score-1 YouTube videos include audio; all others are video-only.

### Step 3 — Present Results

Read stdout summary. Present:

| Source | Attempted | Completed | Failed | Skipped | Total Size |
|--------|-----------|-----------|--------|---------|------------|

For failures, show URL and error. Offer to retry (script skips already-completed entries).

## Notes

- **Audio:** Only tier-1 YouTube videos (score=1) download with audio. All other YouTube and all archive.org downloads are video-only.
- **Re-encoding:** Videos above 24fps are re-encoded to 24fps by default (cinematic aesthetic + fewer frames for analysis). Pass `--no-reencode` to skip.
- **Authentication:** Auto-detects Brave cookies for YouTube. On bot detection, remaining YouTube downloads stop immediately; archive.org continues unaffected.
- **Resume:** Idempotent — re-running skips completed entries whose files still exist.

## Dependencies

- `yt-dlp` — video download (both sources)
- `ffmpeg` — validation (ffprobe) and 24fps re-encoding
