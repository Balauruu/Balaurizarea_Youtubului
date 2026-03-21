# YouTube Result Evaluation — [HEURISTIC]

You are evaluating yt-dlp search results to identify YouTube videos with usable footage for a documentary. Each result comes as JSON metadata from `yt-dlp "ytsearchN:query" --flat-playlist --dump-json`.

## Evaluation Criteria

Assess each result on four dimensions, then assign an overall relevance score.

### 1. Duration Awareness

Duration strongly predicts content type and usable footage density:

| Duration | Likely Content | Usable Footage | Priority |
|----------|---------------|----------------|----------|
| < 2 min | News clip, social media re-upload, trailer | 10-30 seconds of B-roll or headline shots | Low unless very targeted |
| 2-10 min | News segment, short report, interview excerpt | 30-120 seconds of usable footage | Medium — good for specific moments |
| 10-30 min | Mini-documentary, long-form news report | 2-5 minutes of diverse footage | High — likely contains interviews, archival, B-roll |
| 30-90 min | Full documentary, lecture, conference | 5-15 minutes of usable footage spread throughout | High — primary source material |
| > 90 min | Feature documentary, compilation | Dense but requires careful scrubbing | High if relevant, but time-intensive to review |

**Key insight:** A 10-minute news clip may have 30 seconds of usable archival footage buried in 9.5 minutes of reporters talking. Estimate the **usable footage density**, not just total duration.

### 2. Channel Reputation Signals

| Channel Type | Signal | Trust Level |
|-------------|--------|-------------|
| Official news (CBC, Radio-Canada, BBC, Reuters) | Verified badge, institutional channel name | High — likely original footage, professional quality |
| Documentary producers (PBS, National Film Board, Vice) | Production company in channel name | High — purpose-made content |
| Archival uploaders (channels focused on historical content) | Channel name includes "archives", "history", "historical" | Medium-High — curated but rights unclear |
| Educational channels (universities, museums) | .edu or institutional affiliation | Medium-High — educational context supports fair dealing |
| News aggregators | Channel reposts news from multiple sources | Medium — content is real but rights are secondhand |
| Random re-uploads | Generic channel name, content clearly from another source | Low — poor quality, rights issues, may be removed |
| Content farms | Clickbait titles, AI narration, slide-show format | Skip — no original footage, misleading content |

### 3. Title Pattern Matching

Titles contain strong relevance signals:

**High-value patterns:**
- Contains "documentary" → likely long-form, structured content
- Contains "interview" → primary source, survivor/witness testimony
- Contains "archival" or "archive" → historical footage
- Contains "[topic] history" → educational overview with mixed footage
- Contains specific person/entity names from entity_index.json → targeted content

**Medium-value patterns:**
- Contains "report" or "investigation" → news coverage with B-roll
- Contains year ranges (e.g., "1950-1960") → historical context
- Contains location names from entity_index.json → geographic context

**Low-value patterns:**
- Contains "reaction" or "reacts to" → commentary, no original footage
- Contains "explained" without other signals → may be talking-head only
- Contains "Top 10" or listicle patterns → compilations with brief clips
- ALL CAPS or excessive punctuation → clickbait

### 4. Usable Footage Density Estimation

For each video, estimate what percentage contains footage the documentary could use:

| Content Structure | Estimated Usable % | Notes |
|------------------|-------------------|-------|
| Archival footage compilation | 60-80% | Most frames are usable |
| News segment with B-roll | 10-30% | Anchor talking + brief footage clips |
| Interview (single person) | 40-60% | Talking head is usable if subject is relevant |
| Full documentary | 20-40% | Mixed narration, footage, interviews |
| Lecture/presentation | 5-10% | Slides may be useful, speaker mostly isn't |
| Slide show with music | 0-5% | Low-res images, no original footage |

## Relevance Scoring

Assign each result a relevance category for the `relevance` field in media_leads.json:

| Score | Label | Criteria |
|-------|-------|----------|
| 1 | **Primary source** | Contains original interviews, archival footage, or documentation directly about the topic |
| 2 | **Strong supporting** | Professional production (news/documentary) with substantial relevant footage |
| 3 | **Supplementary** | Contains some usable footage but mostly tangential or low-density |
| 4 | **Marginal** | Minimal usable footage, but could fill a specific gap |
| 5 | **Skip** | No usable footage, wrong topic, content farm, or unacceptable quality |

## Output Format

For each video that scores 1-4, write an entry for the `youtube_urls` array:

```json
{
  "url": "https://youtube.com/watch?v=...",
  "title": "Video title from yt-dlp",
  "description": "Agent-written: what usable footage exists, with timestamps if identifiable from metadata",
  "relevance": "Score N — [brief justification referencing duration, channel, content type]",
  "license_notes": "[Channel type] — [licensing consideration]"
}
```

Write the `description` field as if briefing a video editor: what to look for, approximately where, and why it matters to the documentary narrative.

## Skip Criteria

Immediately skip (do not include in output):
- Duration < 30 seconds (likely a clip or trailer)
- Channel shows content farm signals
- Title is in a language the production team cannot use (unless the footage itself is usable without audio)
- Video is clearly a re-upload of content already captured from the original channel
- Video is a "reaction" or commentary with no original footage
