# Requirements: Channel Assistant (Agent 1.1)

**Defined:** 2026-03-11
**Core Value:** Surface obscure, high-impact documentary topics backed by competitor data, not guesswork.

## v1 Requirements

### Data Foundation

- [x] **DATA-01**: User can define a competitor watchlist in a JSON config file with channel name, YouTube channel ID/URL, and notes
- [x] **DATA-02**: System scrapes video metadata (title, views, upload date, description, duration, tags) for all channels in the registry via yt-dlp
- [x] **DATA-03**: Scraped data is stored in a SQLite database with `channels` and `videos` tables, each record timestamped with `scraped_at`
- [x] **DATA-04**: Scraper uses rate limiting (jittered delays) and falls back to cached data on yt-dlp failure
- [x] **DATA-05**: User can view per-channel summary stats: total videos, average views, median views, upload frequency, most recent upload

### Analysis

- [x] **ANLZ-01**: System detects outlier videos per channel (views >= 2x channel median) and reports them with performance multiplier
- [x] **ANLZ-02**: System clusters competitor videos by topic/theme and reports saturation level per cluster
- [x] **ANLZ-03**: System extracts title patterns/formulas from top-performing competitor videos
- [x] **ANLZ-04**: System scores each generated topic on obscurity, complexity, shock factor, and verifiability using anchored rubrics with concrete criteria per score level
- [ ] **ANLZ-05**: System detects content gaps by comparing search demand (YouTube autocomplete via crawl4ai) against competitor topic coverage
- [ ] **ANLZ-06**: System surfaces trending topics by scraping YouTube search results for niche keywords sorted by recency
- [ ] **ANLZ-07**: System detects cross-channel trend convergence when 3+ competitors cover adjacent topics within a 30-day window

### Output

- [x] **OUTP-01**: System generates 5 scored topic briefs per run following the Topic Brief Schema (title, hook, timeline, complexity/obscurity/shock scores, estimated runtime)
- [x] **OUTP-02**: Generated topics are checked against `context/channel/past_topics.md` and duplicates/near-duplicates are rejected
- [ ] **OUTP-03**: User selects a topic from chat, and system creates `projects/N. [Video Title]/` with sequential numbering
- [ ] **OUTP-04**: System generates 3-5 YouTube title variants per selected topic, varying hook type (question, statement, revelation)
- [ ] **OUTP-05**: System generates 1 YouTube description per selected topic
- [ ] **OUTP-06**: Title variants and description are written to a `metadata.md` file in the project directory

## v2 Requirements

### Discovery & Maintenance

- **DISC-01**: Semi-automated competitor discovery via YouTube search (crawl4ai scrapes search results, user curates)
- **DISC-02**: Per-channel selective refresh (re-scrape only specified channels on demand)
- **DISC-03**: Upload cadence tracking per competitor (day-of-week distribution, monthly frequency)

### Social & External

- **SOCL-01**: Reddit niche monitoring for trending topics
- **SOCL-02**: Google Trends integration for topic validation

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time monitoring / notifications | Requires background service; tool runs on-demand in Claude Code |
| SEO keyword optimization / tag suggestions | Documentary content competes on topic selection, not keywords |
| Thumbnail analysis / A/B testing | Out of scope for topic selection; happens in DaVinci Resolve |
| Subscriber/view count prediction | Unreliable; outlier detection is more honest |
| Upload scheduling / calendar | Channel is quality-gated with no fixed schedule |
| Historical trend graphs / dashboards | Over-engineering; snapshot comparisons suffice |
| YouTube Data API v3 | yt-dlp covers same data without API key management |
| Comment sentiment analysis | View count and like ratio are sufficient performance signals |
| Web dashboard / GUI | Architecture mandates CLI-only, Claude Code orchestrated |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Complete (01-01) |
| DATA-02 | Phase 1 | Complete |
| DATA-03 | Phase 1 | Complete (01-01) |
| DATA-04 | Phase 1 | Complete |
| DATA-05 | Phase 2 | Complete |
| ANLZ-01 | Phase 2 | Complete |
| ANLZ-02 | Phase 2 | Complete |
| ANLZ-03 | Phase 2 | Complete |
| ANLZ-04 | Phase 3 | Complete |
| ANLZ-05 | Phase 5 | Pending |
| ANLZ-06 | Phase 5 | Pending |
| ANLZ-07 | Phase 5 | Pending |
| OUTP-01 | Phase 3 | Complete |
| OUTP-02 | Phase 3 | Complete |
| OUTP-03 | Phase 4 | Pending |
| OUTP-04 | Phase 4 | Pending |
| OUTP-05 | Phase 4 | Pending |
| OUTP-06 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0

---
*Requirements defined: 2026-03-11*
*Last updated: 2026-03-11 after roadmap creation*
