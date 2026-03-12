# Feature Research

**Domain:** Web Research Agent for Documentary Scriptwriting (Agent 1.2: The Researcher)
**Researched:** 2026-03-12
**Confidence:** HIGH (downstream consumer is known, schema is specified in Architecture.md, reference script exists)

## Context

Agent 1.2 operates inside a fixed pipeline. It reads a topic (from an existing `projects/N. [Title]/` directory created by Agent 1.1) and produces a `Research.md` dossier consumed directly by Agent 1.3 (The Writer). The Writer converts this dossier into a narrated 20-50 minute documentary script without any human filtering step in between.

This shapes every feature decision: the dossier is not for human browsing — it is for an LLM scriptwriter that needs structured, attributed, narrative-ready facts. Anything that wastes tokens or introduces ambiguity in the dossier directly degrades script quality.

The channel niche spans dark history, true crime, cults, institutional corruption, and unsolved disappearances. Sources range from court records and police reports to academic papers, newspaper archives, and wikis. The agent must handle all of these without niche-specific hardcoding.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features the agent must have or it provides no value over asking Claude to research from memory.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Manual topic input** | User must be able to invoke the agent with a topic name and have it pick up the correct project directory. | LOW | CLI: `topic` argument maps to `projects/N. [Title]/`. Agent reads `metadata.md` for working title and hook from Agent 1.1. |
| **Broad survey pass (Pass 1)** | Documentary research starts wide — identify the full landscape before diving deep. Without this, you miss key angles and secondary actors. | MEDIUM | crawl4ai scrapes Wikipedia, major news archives, relevant wiki-type sources. Produces a structured understanding of the topic: who, what, when, where, why. [DETERMINISTIC] scraping, [HEURISTIC] synthesis. |
| **Primary source deep-dive pass (Pass 2)** | Wikipedia and news articles are secondary sources. Scripts that cite only those feel thin. Court records, police reports, government documents, academic papers, and archived primary materials give the script authority and credibility. | HIGH | crawl4ai targets archive.org, loc.gov, archives.gov, court record databases, newspaper archives (Chronicling America, ProQuest-accessible free tiers). [DETERMINISTIC] scraping. |
| **Chronological timeline with sources** | The Writer needs events in date order with attribution. Without this, the script either invents a timeline or misorders events. Documentary scripts are structurally anchored to chronology. | MEDIUM | Each timeline entry: date, event description, source name, source URL. Gaps in the timeline must be labeled explicitly as gaps rather than silently omitted. |
| **Key figures section** | Named people are the backbone of documentary narrative. The Writer needs names, roles, relationships, and direct quotes. Anonymous "officials said" is useless for narration. | MEDIUM | Full names, roles/titles, relationship to the central event, at least one attributed quote per figure where available. Flag figures where only partial identification exists. |
| **Subject overview (500-word summary)** | The Writer needs a dense, factually-grounded overview before diving into the structured sections. This is the "establishing shot" of the dossier. | LOW | [HEURISTIC] Claude synthesizes scraped content into a 500-word summary anchored to documented facts. |
| **Source list with reliability ratings** | The Writer must know whether a fact came from a court record or a Reddit thread. Reliability shapes how confidently the narration can state something. | MEDIUM | Each source: name, URL, type (primary/secondary/tertiary), reliability rating (HIGH/MEDIUM/LOW), brief note on why. |
| **Contradictions section** | Conflicting accounts are documentary gold — they create narrative tension. Without surfacing contradictions, the Writer produces a falsely clean narrative. | MEDIUM | Pairs of conflicting claims with their respective sources. Not resolved — left as documented conflict for the Writer to use as narrative tension. |
| **Unanswered questions section** | Gaps that resist resolution are the best endings for documentaries. The Writer needs to know what can't be answered and why. | LOW | List of specific questions that research could not answer, with notation of what was tried. Ambiguity is a feature, not a bug. |
| **Output to project directory** | Research.md must land at `projects/N. [Title]/Research.md`. The Writer reads from a fixed path. | LOW | Deterministic file write. No path ambiguity. |

---

### Differentiators (Competitive Advantage)

Features that make the dossier meaningfully better than what an LLM produces from training data alone.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Source chain tracing** | The reference script (Mexico's Most Disturbing Cult) traces facts through multiple layers: a news report cites a court document which cites a police report. Flat "source lists" miss this. A chain trace shows the Writer where authority actually originates. | HIGH | For each key claim, trace: assertion → source → that source's basis. Particularly important for contradicted or contested facts. [HEURISTIC] Claude reads scraped content and explicitly traces attribution chains. |
| **Direct quote extraction** | The reference script uses direct quotes from historical figures to punctuate narration ("in 1961 he said..."). These must come from primary sources, not paraphrase. Unquoted facts are narrated; quoted facts become memorable moments. | MEDIUM | Explicitly extract verbatim quotes with full attribution (speaker, date, context, source). Separate section or inline callout. |
| **Narrative hooks identification** | The Writer needs to know which facts are most dramatically potent — what the audience does not expect, where the story pivots, what the "reveal" is. The raw research does not surface these; a heuristic pass does. | MEDIUM | [HEURISTIC] After research synthesis, Claude identifies 3-5 narrative hooks: "the detail that changes everything," "the fact most people get wrong," "the unanswered question that haunts the case." These are explicitly labeled for the Writer. |
| **Media inventory (separate file)** | The Director (Agent 1.4) and Media Acquisition agent (Agent 2.1) need URLs for available images, video, audio. Keeping this in Research.md bloats the dossier for the Writer. Separate file keeps both consumers happy. | LOW | Output as `media_inventory.md` in the project directory, separate from `Research.md`. Contains URLs, media type, subject described, licensing notes. |
| **Wikipedia "Errors vs. Other Sources" check** | For this channel's niche, the reference script explicitly notes "the internet has been telling the story incorrectly since the turn of the century." Wikipedia is often the corrupted source. Flagging where Wikipedia contradicts primary sources is high-value. | MEDIUM | Compare Wikipedia's account against primary/academic sources. Flag divergences explicitly as "Wikipedia states X; primary source states Y." These become narrative moments: "you may have read..." |
| **Scope estimation for runtime** | The Writer must produce a 20-50 minute script (3,000-7,000 words, 4-7 acts). If the research is too thin for 20 minutes, the Writer will pad. If too rich for 50, it will miss critical material. Knowing depth upfront shapes script structure. | LOW | [HEURISTIC] After research, Claude estimates: "This topic has sufficient material for approximately X-Y minutes based on timeline depth, source density, and sub-narrative count." |
| **Cross-reference with past topics** | The agent should flag if any researched material overlaps significantly with a topic the channel has already covered. Prevents the Writer from producing a script that retreads ground. | LOW | Reads `context/channel/past_topics.md` (already exists from v1.0). Flags thematic overlap. Does not block — just informs. |

---

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Automated scraping of paywalled sources** | Academic papers, newspaper archives, court records often sit behind paywalls. "Get everything" sounds like it means paywalls too. | CFAA and equivalents. Also: login bypass adds brittle auth logic, account risks, and legal liability. Not worth it. | Scrape freely accessible portions (abstracts, previews, snippets). Flag paywalled sources explicitly so the user can manually retrieve if needed. |
| **Real-time fact verification against every claim** | "Check every fact" sounds like quality control. | Every claim verification multiplies crawl4ai calls by 5-10x, dramatically increasing runtime and rate-limit risk for marginal gain. The source rating system already conveys confidence. | Rate sources HIGH/MEDIUM/LOW. Flag low-confidence claims in the dossier. Batch verification is the user's job if they choose to do it. |
| **Automated interview subject identification and contact** | "Find me someone to interview" sounds useful. | Scraping personal contact info is a different legal and ethical domain. The agent cannot conduct interviews. This is fundamentally out of scope. | List named sources and their institutional affiliations in the key figures section. User finds contact info manually if needed. |
| **Multi-language research by default** | International topics often have better primary sources in local languages (Spanish-language sources for Mexico cases, German for WWII topics, etc.). | Translation-on-scrape multiplies complexity significantly. crawl4ai returns raw HTML; translation requires an LLM call per page. Also: multi-language output creates consistency problems for the dossier. | Scrape English-language sources first. If key sources are only in another language, flag them with the URL and language tag so the user can manually translate and inject. |
| **Storing research in SQLite database** | "What if we want to retrieve old research?" | Research.md is already a persistent file in the project directory. A parallel database adds complexity without enabling queries that the file system cannot already handle. Re-running research on an existing topic is rare enough that a file is sufficient. | File-based persistence. One Research.md per project directory. If the user wants to update research, they re-run the agent and the file is overwritten (with the previous version accessible via git history). |
| **Sentiment analysis on sources** | "Know whether sources are biased" | NLP sentiment of scraped text is a weak proxy for source bias. Source type (primary court record vs. tabloid article) and source rating (HIGH/MEDIUM/LOW) provide more honest and actionable signal. | Reliability ratings with brief justification (e.g., "LOW — single tabloid source, no corroboration") replace sentiment analysis. |
| **Auto-generated chapter outline** | "Give the Writer a chapter structure" | Imposing chapter structure in the Research phase constrains the Writer's narrative choices before they've engaged with the material. The Writer should derive structure from the material, not receive a pre-baked outline. | Narrative hooks section gives the Writer potent turning points without mandating structure. The Writer applies the style guide and reference scripts to determine act structure. |

---

## Feature Dependencies

```
Manual Topic Input (reads project dir from Agent 1.1)
    |
    v
Pass 1: Broad Survey Scrape [DETERMINISTIC]
    |
    +---> Subject Overview (500-word synthesis) [HEURISTIC]
    |
    +---> Preliminary Timeline
    |
    +---> Key Figures (initial pass)
    |
    v
Pass 2: Primary Source Deep-Dive [DETERMINISTIC]
    |
    +---> Timeline refinement (dates, corrections, gaps)
    |
    +---> Source chain tracing [HEURISTIC]
    |
    +---> Direct quote extraction
    |
    +---> Contradictions identification [HEURISTIC]
    |
    +---> Wikipedia error check [HEURISTIC]
    |
    v
Synthesis Pass [HEURISTIC]
    |
    +---> Narrative hooks identification
    |
    +---> Scope estimation
    |
    +---> Unanswered questions section
    |
    +---> Source list with reliability ratings
    |
    v
Output
    |
    +---> Research.md → projects/N. [Title]/Research.md
    |
    +---> media_inventory.md → projects/N. [Title]/media_inventory.md
```

**Cross-reference with past topics** can run in parallel with synthesis — it reads a local file, not a remote source.

**Media inventory** is separated from Research.md to serve two consumers without bloating either output.

### Dependency Notes

- **Pass 2 requires Pass 1:** The broad survey identifies which primary sources exist and are worth targeting. Targeting primary sources without a subject understanding wastes crawl4ai calls on irrelevant archives.
- **Source chain tracing requires both passes:** Chains can only be traced once both secondary and primary sources have been scraped and compared.
- **Narrative hooks require synthesis:** Cannot identify what is surprising or pivotal without a full picture of the facts.
- **Scope estimation requires synthesis:** Cannot assess depth until all sections are assembled.

---

## MVP Definition

### Launch With (v1)

Minimum viable dossier that a scriptwriter can actually use.

- [x] Manual topic input — without this, the agent cannot run
- [x] Pass 1: Broad survey (Wikipedia, news archives, general web) — without this, no baseline knowledge
- [x] Pass 2: Primary source dive (archive.org, loc.gov, government sources) — without this, the dossier is thin and purely secondary
- [x] Chronological timeline with source attribution per entry — critical for script structure
- [x] Key figures section with roles, relationships, quotes — backbone of narration
- [x] Subject overview (500-word synthesis) — establishing context for the Writer
- [x] Contradictions section — narrative tension material
- [x] Unanswered questions section — potential endings and hooks
- [x] Source list with reliability ratings — lets the Writer calibrate confidence in each claim
- [x] Output to `projects/N. [Title]/Research.md` — required for pipeline continuity

### Add After Validation (v1.x)

Features to add once the base dossier proves useful to the Writer.

- [ ] Source chain tracing — add when Writer feedback indicates sourcing is too flat
- [ ] Direct quote extraction as separate labeled section — add when Writer asks for quote callouts
- [ ] Narrative hooks identification — add when Writer feedback shows difficulty identifying dramatic turning points
- [ ] Media inventory as separate file — add when Agent 1.4 (Director) is built and needs the data
- [ ] Wikipedia error check — add when a video is produced and the "correcting the record" angle proves valuable

### Future Consideration (v2+)

- [ ] Scope estimation — defer until enough Research.md outputs exist to calibrate the heuristic
- [ ] Cross-reference with past topics — low risk without it; add when the backlog grows large enough that overlap becomes a real concern

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Manual topic input | HIGH | LOW | P1 |
| Pass 1: Broad survey scrape | HIGH | MEDIUM | P1 |
| Pass 2: Primary source dive | HIGH | HIGH | P1 |
| Chronological timeline + sources | HIGH | MEDIUM | P1 |
| Key figures + quotes | HIGH | MEDIUM | P1 |
| Subject overview | HIGH | LOW | P1 |
| Contradictions section | HIGH | LOW | P1 |
| Unanswered questions | MEDIUM | LOW | P1 |
| Source list + reliability ratings | HIGH | MEDIUM | P1 |
| Output to project dir | HIGH | LOW | P1 |
| Source chain tracing | HIGH | HIGH | P2 |
| Direct quote extraction | MEDIUM | LOW | P2 |
| Narrative hooks identification | HIGH | MEDIUM | P2 |
| Media inventory (separate file) | MEDIUM | LOW | P2 |
| Wikipedia error check | MEDIUM | MEDIUM | P2 |
| Scope estimation | LOW | LOW | P3 |
| Cross-reference with past topics | LOW | LOW | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## What the Scriptwriter Actually Needs

Analysis of the reference script ("Mexico's Most Disturbing Cult") reveals what the downstream Writer requires. These are not aspirational — they are structural requirements derived from how the channel's scripts are actually written.

| Script Pattern | Research Dossier Requirement |
|----------------|-------------------------------|
| Events narrated in strict chronological order with precise dates | Timeline with dated entries and sources per entry |
| Named actors with full names, not "the suspect" or "a local official" | Key figures: full names, roles, relationships |
| Transition via factual pivots, not opinion ("this would prove to be the beginning of...") | Contradictions and unanswered questions sections to generate clean factual pivots |
| Correcting mainstream misconceptions ("the internet has been telling the story incorrectly") | Wikipedia error check; primary source prioritization |
| Quotes from historical figures to anchor scenes | Direct quote extraction with full attribution |
| Pacing shift from exposition to tension requires knowing where the inflection point is | Narrative hooks identification |
| Script word count 3,000-7,000 words across 4-7 acts | Scope estimation |
| Source credibility communicated implicitly ("court records show...") | Source reliability ratings inform how Writer frames each assertion |

---

## Niche-Specific Considerations

This agent must handle multiple documentary sub-niches without hardcoding. Each has distinct primary source types:

| Sub-Niche | Primary Source Types | Key Free Archives |
|-----------|---------------------|-------------------|
| Dark history / historical crimes | Court records, police reports, newspaper archives, inquest records | archive.org, Chronicling America (loc.gov), national archives |
| Cults / psychological control | FBI files (FOIA releases), survivor testimonies, court transcripts | vault.fbi.gov, archive.org, PACER (limited free access) |
| Unsolved disappearances | Missing persons reports, coroner reports, local news archives | NamUs (national missing persons), local newspaper archives |
| Institutional corruption | Government reports, whistleblower documents, congressional records | archives.gov, govinfo.gov, ProPublica Documented |
| Dark web / digital crimes | Court indictments, DOJ press releases, cybersecurity research papers | justice.gov, pacer.gov (indictments), academic preprints |

The agent must generate appropriate Pass 2 source targets based on the topic's sub-niche, not use a fixed source list. Sub-niche is [HEURISTIC] — Claude infers it from the topic title and Pass 1 findings.

---

## Sources

- Architecture.md — Research Dossier Schema (ground truth for output fields)
- `context/script references/Mexico's Most Disturbing Cult.md` — Reference script analysis for scriptwriter requirements
- [Research Methodologies for Documentaries (Fiveable)](https://fiveable.me/documentary-production/unit-4/research-methodologies-documentaries/study-guide/P6YntwxZNeRvOXor)
- [Ken Burns on Documentary Research (MasterClass)](https://www.masterclass.com/articles/learn-about-documentary-filmmaking-with-tips-and-advice-from-ken-burns)
- [How to Write a Documentary Script (Celtx)](https://blog.celtx.com/how-to-write-a-documentary-script/)
- [Crawl4AI Documentation (v0.8.x)](https://docs.crawl4ai.com/)
- [Web scraping for research: Legal considerations (SAGE Journals, 2025)](https://journals.sagepub.com/doi/10.1177/20539517251381686)
- [Web Scraping for Investigative Journalism (ICIJ)](https://www.icij.org/inside-icij/2018/09/web-scraping-how-to-harvest-data-for-untold-stories/)

---
*Feature research for: Agent 1.2 — The Researcher (documentary web research agent)*
*Researched: 2026-03-12*
