# Feature Landscape

**Domain:** YouTube Channel Assistant / Competitor Intelligence for Dark Mysteries Documentary Channel
**Researched:** 2026-03-11
**Confidence:** HIGH (well-understood problem space, clear commercial tool precedents)

## Context

This feature analysis is for Agent 1.1 (Channel Assistant) -- a CLI-only, Python-based, Claude Code-orchestrated tool that discovers competitors, scrapes metadata, analyzes content strategy, and generates scored topic briefs. The channel targets dark history, true crime, cults, and unsolved mysteries with 20-50 minute documentary deep dives.

Commercial tools (VidIQ, TubeBuddy, Subscribr) serve broad creator audiences. Our tool is narrower and more opinionated: it serves ONE channel in ONE niche with a specific editorial voice. This means we can skip generic features and go deep on what matters for documentary topic selection.

---

## Table Stakes

Features the tool MUST have or it provides no value over manual research.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Competitor channel registry** | Need a curated watchlist of 10-30 channels in the niche. Without this, there is nothing to analyze. | Low | Simple JSON file mapping channel name to YouTube channel ID/URL. Manual curation is fine -- auto-discovery is a differentiator, not table stakes. |
| **Video metadata scraping (yt-dlp)** | Titles, view counts, upload dates, descriptions, duration, tags. This is the raw data everything else depends on. | Medium | yt-dlp `--flat-playlist --dump-json` per channel. Rate limiting is real: ~50-100 extractions/hour per IP. Batch and cache. |
| **Local data cache with staleness tracking** | Cannot re-scrape 20 channels every run. Need a local store with timestamps so you only refresh stale data. | Medium | JSON files per channel in `context/competitors/data/`. Each file has `last_scraped` timestamp. Refresh policy: manual trigger or >7 days stale. |
| **Past topic deduplication** | Rejecting previously covered topics is explicitly in the Architecture spec. Without this, the tool suggests topics already made into videos. | Low | Check generated topics against `context/channel/past_topics.md`. Simple string/semantic matching via LLM reasoning. |
| **Topic brief generation (5 per run)** | The core output. Must follow the Topic Brief Schema (title, hook, timeline, complexity/obscurity/shock scores, runtime estimate). | Low | This is a [HEURISTIC] Claude Code prompt task, not code. The LLM reads competitor data + channel DNA + past topics and generates briefs. No code needed beyond data preparation. |
| **Scoring against channel criteria** | Topics must be scored on obscurity, complexity, shock factor, verifiability (channel DNA requires 3/4). Without scoring, briefs are just random suggestions. | Low | Part of the topic generation prompt. The LLM applies the 4-criteria filter from channel.md. [HEURISTIC] |
| **Project directory creation** | After user selects a topic, create `projects/N. [Title]/` with metadata file containing title variants and description. | Low | Simple filesystem operation. Sequential numbering based on existing directories. |
| **Basic channel stats display** | Video count, average views, upload frequency per tracked channel. Without this, the raw data is noise. | Low | Python aggregation over cached JSON. Formatted as tables in Claude Code chat. |

---

## Differentiators

Features that make this tool meaningfully better than just asking Claude "suggest 5 topics."

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Performance signal detection** | Identify which competitor videos significantly outperformed their channel average (views-per-day vs. channel median). These "outlier" videos reveal what the audience actually wants. Subscribr charges $19-79/mo for essentially this feature. | Medium | Calculate per-channel median views, flag videos at 2x+ median. Pure Python math on scraped data. |
| **Competitor topic clustering** | Group competitor videos by topic/theme to see what categories are oversaturated vs. underserved. Raw video lists are noise; clusters are signal. | Medium | [HEURISTIC] LLM reads all competitor video titles+descriptions and groups them into topic clusters. Output: which themes are overdone, which are fresh territory. |
| **Content gap detection** | Identify topics that have search demand but low/no coverage from competitors. This is the highest-value analytical feature. VidIQ and GapGens charge premium prices for this. | Medium | Compare competitor topic clusters against YouTube search autocomplete / Google Trends data. Surface topics competitors have NOT covered. Requires crawl4ai for search scraping. |
| **Title pattern analysis** | Extract winning title formulas from top-performing competitor videos. Documentary channels have specific patterns (question hooks, location anchors, time period framing, "The [Adjective] Case of..." etc.). | Low | [HEURISTIC] LLM analyzes top-performing titles and extracts patterns. Output: title templates/formulas specific to the dark mysteries niche. |
| **Trend awareness (YouTube search + autocomplete)** | Surface what people are currently searching for in the niche. Catches timely opportunities (new Netflix doc drops, anniversary of a cold case, etc.). | Medium | crawl4ai scrapes YouTube search results for niche keywords. Compare against recent competitor uploads. Flag trending searches with no recent coverage. |
| **Multiple title variants (3-5) per selected topic** | A/B thinking for titles is critical for CTR. VidIQ and TubeBuddy both emphasize title optimization as a key growth lever. | Low | [HEURISTIC] LLM generates title variants after topic selection. Varies hook type (question, statement, revelation) and keyword placement. |
| **Competitor selective refresh** | User says "refresh channel X" and only that channel re-scrapes. Avoids full-pipeline runs for targeted updates. | Low | Selective scraping by channel ID. Update only the specified channel's cache file. |
| **Cross-channel trend detection** | When 3+ competitors cover adjacent topics in the same timeframe, something is trending in the niche. Surface these convergences. | Medium | Cross-reference recent uploads (last 30 days) across all tracked channels. [HEURISTIC] LLM identifies thematic clusters in recent content. |
| **Upload cadence tracking** | Know when competitors publish and at what frequency. Spot gaps in the calendar. | Low | Date aggregation over cached data. Shows when the niche has less competition. |

---

## Anti-Features

Features that seem useful but add complexity without proportional value for a solo documentary creator. Deliberately do NOT build these.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Real-time monitoring / notifications** | "Alert me when a competitor uploads about my planned topic" | Requires a background service, scheduling, and persistent state. Massive complexity for a tool that runs on-demand in Claude Code. Solo creator does not need real-time alerts. | Run the tool before starting a new video. Check competitor recent uploads as part of that run. |
| **SEO keyword optimization / tag suggestions** | VidIQ and TubeBuddy make this their core feature. Seems essential. | For documentary content, SEO is secondary to topic selection. A 30-min documentary on an obscure cult does not compete on keywords -- it competes on being the only/best coverage. Over-optimizing tags wastes time that should go into research depth. | Generate 3-5 title variants (covers the SEO angle). Skip tag optimization entirely. |
| **Thumbnail analysis / A/B testing** | VidIQ tracks competitor thumbnail changes and their impact on views. | Requires image analysis infrastructure, screenshot capture of YouTube pages, and before/after tracking. Way outside scope for a topic selection tool. | Thumbnail decisions happen in post-production (DaVinci Resolve), not during topic selection. |
| **Social media cross-platform analysis** | "Also check Reddit, Twitter/X for trending topics" | Each platform requires different scraping logic, authentication, rate limiting. Multiplies complexity 3-4x for marginal signal. Reddit true crime communities are useful but can be manually browsed. | Keep YouTube-only for v1. Add Reddit as a separate optional data source later if warranted. |
| **Subscriber/view count prediction** | "Predict how many views this topic will get" | Prediction models for YouTube performance are notoriously unreliable. Even VidIQ's predictions are rough estimates. Building one from scratch is pointless. | Use competitor outlier detection instead -- "topics like this got 3x average views" is more honest than "this will get 50K views." |
| **Upload scheduling / calendar** | "Plan my content calendar" | This channel is quality-gated with no fixed schedule. A calendar creates pressure to publish on schedule rather than when the video is ready. Also out of scope per PROJECT.md. | Keep a simple backlog of approved topics in a queue file. |
| **Historical trend graphs / dashboards** | "Show me competitor growth over time" | Requires persistent time-series data, charting libraries, and regular data collection. Over-engineering for a tool that runs episodically. | Snapshot comparisons are sufficient. "Channel X uploaded 4 videos this month, averaging 200K views" is more actionable than a growth chart. |
| **YouTube Data API v3 integration** | "Use the official API for better data" | Requires API key management, quota tracking (10,000 units/day default), and OAuth for some endpoints. yt-dlp already extracts the same metadata without API quotas. Adds credential management overhead. | yt-dlp + crawl4ai cover all needed data without API keys. Revisit only if rate limiting becomes a real blocker. |
| **Full automated competitor discovery** | "Automatically find ALL competitors in my niche" | The niche (dark mysteries documentaries) has maybe 30-50 relevant channels. Manual curation produces a better watchlist than algorithmic discovery, which will include irrelevant channels (true crime podcasts, news channels, etc.). | Semi-automated: search YouTube for niche keywords, present results, user confirms which to track. |
| **SQLite database** | "Need queryability and visualization" | For 20-30 channels with ~100-500 videos each, JSON files are perfectly adequate. SQLite adds a dependency and migration concerns without enabling queries that JSON + Python cannot handle at this scale. | JSON files per channel. Python scripts for any aggregation/filtering needed. Revisit at 100+ tracked channels (unlikely). |
| **Comment sentiment analysis** | "Analyze what viewers are saying about competitor videos" | Adds NLP complexity, requires scraping comments (separate yt-dlp call per video), massive data volume. | View count and like ratio are sufficient performance signals for topic selection. |
| **Web dashboard / GUI** | "Visualize data in a browser" | Architecture says CLI-only, Claude Code orchestrated. A GUI adds a whole second project. | Formatted tables in Claude Code chat. Export to CSV/markdown if the user wants to explore data externally. |

---

## Feature Dependencies

```
Competitor Channel Registry
    |
    v
Video Metadata Scraping (yt-dlp)
    |
    v
Local Data Cache (JSON per channel)
    |
    +---> Basic Channel Stats Display
    |
    +---> Performance Signal Detection (needs view counts + channel medians)
    |
    +---> Competitor Topic Clustering (needs titles + descriptions)
    |         |
    |         v
    |     Content Gap Detection (needs clusters + search data from crawl4ai)
    |
    +---> Title Pattern Analysis (needs top-performing video titles)
    |
    +---> Upload Cadence Tracking (needs upload dates)
    |
    +---> Cross-Channel Trend Detection (needs recent uploads across channels)
    |
    v
Topic Brief Generation (reads all analysis outputs + channel DNA + past topics)
    |
    v
Past Topic Deduplication (filters briefs against past_topics.md)
    |
    v
User Selection (interactive in Claude Code chat)
    |
    v
Project Directory Creation + Title Variants + Description
```

**Trend Awareness** is independent of the competitor pipeline -- it scrapes YouTube search directly and can run in parallel with competitor analysis.

**Competitor Discovery** is a setup-time feature, not a per-run feature. It feeds the channel registry.

---

## MVP Definition

Build in this order. Each layer adds value independently.

### Layer 1: Data Foundation (must ship first)
1. **Competitor channel registry** -- JSON config file with 10-15 seed channels
2. **Video metadata scraping** -- yt-dlp batch scrape with JSON output
3. **Local data cache** -- per-channel JSON files with staleness tracking
4. **Basic channel stats** -- video count, avg views, upload frequency

### Layer 2: Analysis (makes the data useful)
5. **Performance signal detection** -- flag outlier videos per channel
6. **Competitor topic clustering** -- group videos by theme
7. **Title pattern analysis** -- extract winning title formulas

### Layer 3: Output (the actual product)
8. **Topic brief generation** -- 5 scored briefs per run, using channel DNA criteria
9. **Past topic deduplication** -- filter against covered topics
10. **Project directory creation** -- `projects/N. Title/` with metadata
11. **Multiple title variants** -- 3-5 per selected topic

### Layer 4: Advanced (defer until core is validated)
12. **Content gap detection** -- search demand vs. coverage analysis
13. **Trend awareness** -- YouTube search/autocomplete scraping
14. **Cross-channel trend detection** -- convergence analysis
15. **Upload cadence tracking** -- timing intelligence
16. **Competitor selective refresh** -- per-channel re-scrape

**Rationale:** Layers 1-3 can ship together as the initial version. Without Layer 1, nothing works. Without Layer 2, the topic generation is just "Claude guessing" without data backing. Layer 3 is the user-facing output. Layer 4 adds sophistication but is not required for the tool to be useful on day one.

---

## Feature Prioritization Matrix

| Feature | Impact | Effort | Priority | Category |
|---------|--------|--------|----------|----------|
| Competitor registry | HIGH | LOW | P0 | Table Stakes |
| Metadata scraping | HIGH | MEDIUM | P0 | Table Stakes |
| Data cache + staleness | HIGH | MEDIUM | P0 | Table Stakes |
| Basic channel stats | MEDIUM | LOW | P0 | Table Stakes |
| Topic brief generation | HIGH | LOW | P0 | Table Stakes |
| Scoring against criteria | HIGH | LOW | P0 | Table Stakes |
| Past topic dedup | MEDIUM | LOW | P0 | Table Stakes |
| Project dir creation | MEDIUM | LOW | P0 | Table Stakes |
| Performance signal detection | HIGH | MEDIUM | P1 | Differentiator |
| Topic clustering | HIGH | MEDIUM | P1 | Differentiator |
| Title pattern analysis | MEDIUM | LOW | P1 | Differentiator |
| Title variants | MEDIUM | LOW | P1 | Differentiator |
| Content gap detection | HIGH | MEDIUM | P2 | Differentiator |
| Trend awareness | MEDIUM | MEDIUM | P2 | Differentiator |
| Cross-channel trends | MEDIUM | MEDIUM | P2 | Differentiator |
| Upload cadence | LOW | LOW | P2 | Differentiator |
| Competitor selective refresh | LOW | LOW | P3 | Differentiator |

---

## Competitor Feature Analysis

What commercial tools offer vs. what this channel actually needs:

| Feature Area | VidIQ ($7.50-49/mo) | TubeBuddy ($3.49-28/mo) | Subscribr ($19-79/mo) | Our Tool Needs? |
|-------------|-------|-----------|-----------|-------------------|
| Keyword research | Full suite, search volume, competition scores, rising keywords | Full suite, tag explorer, keyword rankings | AI keyword generator | NO -- documentary topics are not keyword-driven |
| Competitor tracking | Channel comparison, growth graphs, video velocity (views/hour) | Competitor scorecard, tag comparison | Outlier video detection across thousands of channels | YES -- simplified. Channel stats + outlier videos only |
| Thumbnail analysis | Track thumbnail changes + impact on performance | Thumbnail A/B testing | No | NO -- out of scope for topic selection |
| Title optimization | AI title suggestions, title change tracking | Title scoring | Title generator | PARTIAL -- title variants generation only |
| SEO scoring | Video SEO score overlay on every YouTube page | Search rankings per tag | No | NO -- over-engineering for documentary content |
| Content gap analysis | Limited, paid tier only | No | Research assistant for finding underserved angles | YES -- highest unique value feature |
| Topic ideation | AI-powered suggestions based on channel niche | Keyword-based suggestions | 10 ideas with angles, hooks, and thumbnail concepts | YES -- our core output, tuned to channel DNA and 4-criteria scoring |
| Script writing | No | No | Full AI scriptwriting workflow | NO -- separate agent (Agent 1.3) handles this |
| Data ownership | Cloud-only, SaaS dependency | Cloud-only, SaaS dependency | Cloud-only | YES -- all data local in JSON files, no vendor lock-in |

**Key insight:** Commercial tools optimize for breadth (serve all creators). Our tool optimizes for depth in ONE niche. We skip 70% of what VidIQ offers and go deeper on the 30% that matters: competitor intelligence, content gaps, and scored topic generation aligned to a specific editorial voice.

---

## Niche-Specific Features (Dark Mysteries Documentary)

Features unique to this channel's niche that generic tools would never offer:

| Feature | Why It Matters | Implementation |
|---------|---------------|----------------|
| **Obscurity scoring** | The channel's edge is covering topics nobody else has. Generic tools optimize for popular topics -- we need the opposite. | Cross-reference topic against competitor coverage count. Fewer competitors covering it = higher obscurity score. |
| **Source verifiability assessment** | Channel DNA requires verifiable sources. Topics based only on Reddit threads or urban legends fail the quality bar. | Part of the topic brief prompt: require the LLM to assess source availability (court records, news archives, books, official documents). |
| **Runtime estimation (20-50 min target)** | A topic too thin for 20 minutes or too sprawling for 50 needs flagging before research begins. | LLM estimates based on timeline complexity and available source material depth. |
| **Content pillar alignment** | Topics must map to one of 5 pillars (historical crimes, cults, disappearances, corruption, dark web). Random true crime does not fit the channel identity. | Classify each brief against the 5 pillars. Ensure balanced coverage over time by checking past_topics.md pillar distribution. |
| **Shock factor calibration** | The channel needs genuine shock, not sensationalism. "This is disturbing because of the facts" not "this is disturbing because we made it sound scary." | Part of scoring prompt. LLM evaluates whether shock comes from documented facts or from presentation framing. Reject sensationalism-dependent topics. |

---

## Sources

- [VidIQ Features - Competitors Tool](https://vidiq.com/features/competitors/)
- [VidIQ Features - Keyword Tools](https://vidiq.com/features/keyword-tools/)
- [TubeBuddy - YouTube Competitor Analysis Tool](https://www.tubebuddy.com/tools/youtube-competitor-analysis-tool)
- [VidIQ vs TubeBuddy Comparison (2026)](https://linodash.com/vidiq-vs-tubebuddy/)
- [VidIQ vs TubeBuddy (thumbnailtest.com, 2026)](https://thumbnailtest.com/guides/vidiq-vs-tubebuddy/)
- [Subscribr - AI Script Writer & Video Idea Generator](https://subscribr.ai/)
- [Content Gap Analysis for YouTube (Subscribr)](https://subscribr.ai/p/youtube-content-gap-analysis)
- [GapGens - YouTube Content Gap Analysis](https://www.gapgens.com/)
- [How to Analyze YouTube Competitors at Scale (ScraperAPI)](https://www.scraperapi.com/blog/analyze-youtube-competitors/)
- [yt-dlp YouTube Data Adventure (nv1t)](https://nv1t.github.io/blog/scraping-by-my-youtube-data-adventure/)
- [AI YouTube Trend Finder (n8n workflow)](https://n8n.io/workflows/2606-ai-youtube-trend-finder-based-on-niche/)
- [Best YouTube Competitor Analysis Tools 2025 (OutlierKit)](https://outlierkit.com/blog/best-youtube-competitor-analysis-tools-free-and-paid)
- [YouTube Niche Analyzer (TubeLab)](https://tubelab.net/niche-analyzer)
