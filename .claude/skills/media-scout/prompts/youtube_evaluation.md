# YouTube Result Evaluation — [HEURISTIC]

Evaluate YouTube search results to identify videos with usable footage for a documentary. Each result has been discovered via crawl4ai and validated with `yt-dlp --dump-json`.

## Hard Filters — Discard Immediately

These filters are applied BEFORE scoring. If a video matches any of these, it is dropped from the output entirely:

| Filter | Rule | Why |
|--------|------|-----|
| **Duration** | < 30 seconds | Too short for usable footage |
| **View count** | < 1,000 views | Likely AI-generated, re-uploaded, or low-effort content. Exception: first-person accounts from verified personal channels of people directly involved in the events |
| **AI content signals** | Clickbait title patterns + new channel + very low views | AI-narrated slideshows are useless for a documentary |
| **Re-uploads** | Same content already captured from original channel | Duplicates waste slots |
| **Content farms** | Slideshow format, AI narration, no original footage | No usable material |
| **Reaction/commentary** | No original footage, just talking heads reacting | Nothing to extract |
| **Wrong topic** | Title shares keywords but video is about a different subject entirely | False positive from search |

### AI Content Detection

AI-generated documentary content has exploded on YouTube. It's useless for your purposes — you need real archival footage, real interviews, real locations. Red flags:

- **Channel with < 1K subscribers AND < 1K views on the video** — very likely AI
- **Sensationalist reformulation of the topic** — exaggerated, emotionally manipulative titles that no professional outlet would use (vs. factual titles from real producers)
- **Channel name signals** — generic dark/mystery branding like "Dreaded Documentary", "Suppressed Shadows", "Silent Century", "Dark Secrets Revealed" — these are AI content farm naming patterns
- **Language mismatch** — if the topic is primarily covered in a specific language/region, fluent English narration from an unknown channel is suspicious (real coverage comes from local media)
- **No visible original footage** — just stock images and AI voiceover

When in doubt, check: would a real journalist or documentary filmmaker publish this? If the answer is "probably not", discard it.

## Scoring

Assign each result that passes the hard filters a relevance score:

| Score | Label | Criteria |
|-------|-------|----------|
| 1 | **Primary source** | Original interviews, archival footage, or documentation **directly about the specific topic**. The video's main subject IS the documentary topic. Produced by a professional outlet (broadcaster, news org) or by the subjects themselves (survivor channels). |
| 2 | **Strong supporting** | Professional production with substantial relevant footage, BUT either: the video is about a broader topic that includes the documentary topic, OR it's from a smaller but legitimate channel. Also: verified first-person account channels regardless of view count. |
| 3 | **Supplementary** | Some usable footage but mostly tangential or low-density. Short news clips, tangentially related documentaries, exploration/urbex footage of related locations. |
| 4 | **Marginal** | Minimal usable footage, but could fill a specific gap. Very short clips, trailers, promotional material. |

### Scoring Discipline

**Score 1 is rare and precious.** In a typical run, only 3-7 videos should receive Score 1. If you're giving Score 1 to 15 videos, your threshold is too low.

Score 1 requires ALL of these:
- The video is **primarily about the documentary topic** (not just mentioning it)
- It contains **original footage** (not compiled from other sources)
- It's from a **credible producer** (broadcaster, investigative journalist, survivor, academic institution)
- It has **meaningful view count** (typically > 1K, though first-person account channels are exempt)

**Common mis-scoring to avoid:**
- A biography of a related figure is NOT a primary source about the events — it's Score 2 at best
- A long compilation from an unknown channel is NOT a primary source — it's likely a re-upload (Score 2-3)
- A conspiracy-adjacent channel covering the topic is NOT a primary source — it's Score 3
- A music/art performance about the topic is NOT a primary source — it's Score 3

## Key Evaluation Signals

**Duration** — Videos under 2 min rarely have usable footage. 10-30 min mini-documentaries and news reports are the sweet spot. Long documentaries (30+ min) are high-value but time-intensive to review.

**Channel reputation** — Official news networks, national broadcasters, and documentary producers are high-trust. Archival/educational channels are high-trust. News aggregators are medium. Random re-uploads and content farms are low/skip.

**Title patterns** — "documentary", "interview", "archival", "[topic] history" are high-value. "reaction", "Top 10", ALL CAPS clickbait, "How to Know..." are low-value.

**Usable footage density** — Estimate what percentage of the video contains footage the documentary could actually use. A 10-minute news clip may have only 30 seconds of usable archival footage buried in anchor segments.

## Output

For each video scoring 1-4, write the `description` field as if briefing a video editor: what to look for, approximately where, and why it matters to the documentary. Include specific details from the yt-dlp metadata (channel, duration, view_count) — do NOT write generic descriptions like "Long-form content about [topic]" or "Supporting footage about [topic]". Those are useless to the editor. Be specific about what footage the video contains.
