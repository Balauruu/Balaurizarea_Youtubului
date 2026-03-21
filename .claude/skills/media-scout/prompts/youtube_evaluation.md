# YouTube Result Evaluation — [HEURISTIC]

Evaluate yt-dlp search results to identify YouTube videos with usable footage for a documentary. Each result comes as JSON metadata from `yt-dlp "ytsearchN:query" --flat-playlist --dump-json`.

## Scoring

Assign each result a relevance score:

| Score | Label | Criteria |
|-------|-------|----------|
| 1 | **Primary source** | Original interviews, archival footage, or documentation directly about the topic |
| 2 | **Strong supporting** | Professional production (news/documentary) with substantial relevant footage |
| 3 | **Supplementary** | Some usable footage but mostly tangential or low-density |
| 4 | **Marginal** | Minimal usable footage, but could fill a specific gap |

## Key Evaluation Signals

**Duration** — Videos under 2 min rarely have usable footage. 10-30 min mini-documentaries and news reports are the sweet spot. Long documentaries (30+ min) are high-value but time-intensive to review.

**Channel reputation** — Official news (CBC, BBC, Reuters), documentary producers (PBS, NFB, Vice), and archival/educational channels are high-trust. News aggregators are medium. Random re-uploads and content farms are low/skip.

**Title patterns** — "documentary", "interview", "archival", "[topic] history" are high-value. "reaction", "Top 10", ALL CAPS clickbait are low-value.

**Usable footage density** — Estimate what percentage of the video contains footage the documentary could actually use. A 10-minute news clip may have only 30 seconds of usable archival footage buried in anchor segments.

## Skip immediately

- Duration < 30 seconds
- Content farm signals (AI narration, slideshow format, clickbait)
- Re-uploads of content already captured from original channel
- Reaction/commentary videos with no original footage
- Unusable language (unless footage works without audio)

## Output

For each video scoring 1-4, write the `description` field as if briefing a video editor: what to look for, approximately where, and why it matters to the documentary.
