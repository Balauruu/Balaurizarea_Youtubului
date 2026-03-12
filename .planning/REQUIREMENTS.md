# Requirements: Channel Automation Pipeline

**Defined:** 2026-03-12
**Core Value:** Surface obscure, high-impact documentary topics backed by competitor data, not guesswork.

## v1.1 Requirements

Requirements for Agent 1.2 — The Researcher. Each maps to roadmap phases.

### Scraping Infrastructure

- [ ] **SCRP-01**: Agent can scrape web pages using crawl4ai with domain-isolated browser contexts
- [ ] **SCRP-02**: Agent retries failed fetches and validates minimum content length (>200 chars) per response
- [ ] **SCRP-03**: Agent categorizes sources into access tiers (reliable / attempt / do-not-attempt) before scraping

### Research Pipeline

- [ ] **RSRCH-01**: Agent accepts a manual topic input and locates the corresponding project directory
- [ ] **RSRCH-02**: Pass 1 scrapes 10-15 broad sources (Wikipedia, DuckDuckGo, news archives) and outputs a JSON source manifest
- [ ] **RSRCH-03**: Pass 2 reads the source manifest and fetches 5-10 targeted primary sources (archive.org, .gov, academic)
- [ ] **RSRCH-04**: Scraped content is stored in `.claude/scratch/researcher/` — never held in conversation context

### Dossier Output

- [ ] **DOSS-01**: Agent produces a Research.md with subject overview (~500 words), chronological timeline, and key figures (names, roles, quotes)
- [ ] **DOSS-02**: Research.md includes a contradictions section identifying conflicting accounts across sources
- [ ] **DOSS-03**: Research.md includes unanswered questions that create narrative tension
- [ ] **DOSS-04**: Research.md uses structured credibility signals (source_type, corroborated_by, access_quality) — no scalar scores
- [ ] **DOSS-05**: Research.md is capped at ~2,000 words of curated scriptwriter-facing content
- [ ] **DOSS-06**: Agent extracts direct quotes as labeled callouts for scene anchoring
- [ ] **DOSS-07**: Agent identifies 3-5 narrative hooks (high-impact story beats) explicitly labeled for the Writer
- [ ] **DOSS-08**: Agent flags where mainstream coverage contradicts primary sources (correcting-the-record opportunities)
- [ ] **DOSS-09**: Agent writes Research.md to `projects/N. [Title]/research/`

### Media Catalog

- [ ] **MEDIA-01**: Agent produces a separate `media_urls.md` cataloging media URLs found during research
- [ ] **MEDIA-02**: media_urls.md includes URL, description, and source type — kept separate from Research.md

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Research Depth

- **DEPTH-01**: Agent estimates minutes-of-material from research volume
- **DEPTH-02**: Agent cross-references topics against past_topics.md to flag overlap

### Scraping Enhancements

- **SCRP-04**: trafilatura fallback for noisy crawl4ai output
- **SCRP-05**: archive.org API client integration (internetarchive library)
- **SCRP-06**: Source chain tracing through multiple attribution layers

## Out of Scope

| Feature | Reason |
|---------|--------|
| LLM API wrappers for reasoning | Architecture.md Rule 1 — all reasoning is native Claude Code |
| PDF extraction (PyMuPDF/OCR) | Add reactively when first PDFs encountered |
| Paid source access (PACER, newspaper archives) | Free sources only per Architecture.md source policy |
| Real-time research updates | Agent runs on demand, not as background service |
| Automatic topic selection | Manual input only — user chooses what to research |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SCRP-01 | Phase 7 | Pending |
| SCRP-02 | Phase 7 | Pending |
| SCRP-03 | Phase 7 | Pending |
| RSRCH-01 | Phase 7 | Pending |
| RSRCH-02 | Phase 8 | Pending |
| RSRCH-04 | Phase 8 | Pending |
| RSRCH-03 | Phase 9 | Pending |
| DOSS-01 | Phase 10 | Pending |
| DOSS-02 | Phase 10 | Pending |
| DOSS-03 | Phase 10 | Pending |
| DOSS-04 | Phase 10 | Pending |
| DOSS-05 | Phase 10 | Pending |
| DOSS-06 | Phase 10 | Pending |
| DOSS-07 | Phase 10 | Pending |
| DOSS-08 | Phase 10 | Pending |
| DOSS-09 | Phase 10 | Pending |
| MEDIA-01 | Phase 10 | Pending |
| MEDIA-02 | Phase 10 | Pending |

**Coverage:**
- v1.1 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-12*
*Last updated: 2026-03-12 — traceability mapped to Phases 7-10*
