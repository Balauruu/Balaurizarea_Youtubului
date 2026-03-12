# Pitfalls Research

**Domain:** Web Research Agent for Documentary Content Production (Agent 1.2 — The Researcher)
**Researched:** 2026-03-12
**Confidence:** HIGH (crawl4ai limitations verified via GitHub issues and official docs; hallucination risks documented by recent NeurIPS/GPTZero studies; source access challenges confirmed by major news publishers' 2025-2026 AI blocking actions)

---

## Critical Pitfalls

### Pitfall 1: LLM Fabricates Sources That Look Authoritative

**What goes wrong:**
The research agent synthesizes findings and produces plausible-sounding citations — court case numbers that don't exist, news articles with real outlets but fake titles, academic papers with believable authors. A GPT-4o study found 56% of AI-generated citations were fake or contained errors. A January 2026 GPTZero audit of NeurIPS 2025 papers found 100+ hallucinated references that passed human review. For documentary content, a single fabricated "primary source" that makes it into the script destroys credibility.

**Why it happens:**
LLMs generate text that satisfies the grammatical and semantic pattern of citations. They have training exposure to real sources, so they blend real outlet names, real author styles, and real topic domains into fabricated references that look valid. The synthesis step — where crawl4ai-fetched content is summarized — is the highest-risk moment because the LLM may confuse what it scraped vs. what it was trained on.

**How to avoid:**
- Enforce a strict separation between "scraped content" (URL + raw extract) and "synthesized claims" (LLM summary). Every claim in Research.md must trace back to a specific URL that was actually fetched.
- Never ask the LLM to generate citations. Instead, have it cite only URLs returned by crawl4ai fetch operations that succeeded (HTTP 200).
- The Research.md schema should include a `sources` section where each entry has: `url` (the actual URL fetched), `title` (from page metadata, not LLM-generated), `fetched_at` (timestamp), and `relevant_excerpt` (direct quote, not paraphrase).
- Build a verification step: after research completes, the user (or a verification subagent) can spot-check 3-5 URLs from the sources list. If links are dead or content does not match, the run is flagged.

**Warning signs:**
- Research.md contains citations with no URLs, only author/title/date.
- Sources section lists academic papers or court documents that the scraper would have had no way to access.
- Source URLs in Research.md return 404 or redirect to unrelated content.

**Phase to address:** Phase 1 (Research Schema Design). The schema must enforce URL provenance from day one. Adding it later requires rewriting the output format and re-testing all downstream consumers.

---

### Pitfall 2: crawl4ai Browser Context Contamination After Failures

**What goes wrong:**
After crawl4ai fails to scrape a page (timeout, bot detection, redirect loop), the internal browser context becomes contaminated — subsequent requests in the same session return empty results, "no results" pages, or stale cache. A documented GitHub issue (#501) shows this causing silent failures where the crawler returns a result object with no error but empty content. For a research agent running 20-40 URL fetches per topic, one mid-session failure can silently corrupt all subsequent fetches.

**Why it happens:**
Playwright's browser context preserves state (cookies, session storage, history) across requests in the same context. When a failed page leaves the context in an unexpected state (partial load, error page cached, security challenge unresolved), subsequent requests inherit that broken state.

**How to avoid:**
- Use a fresh browser context for each distinct source domain. Do not share a single context across archive.org, Wikipedia, and news sites in sequence.
- Implement explicit success verification: check that `result.markdown_v2.raw_markdown` (or equivalent field) has a minimum length before treating the fetch as successful. Empty or near-empty results are failures, not successes.
- After any fetch that returns less than 200 characters of content, reset the browser context before the next fetch.
- Use `async with AsyncWebCrawler() as crawler` context manager pattern — it guarantees cleanup on exit, even after exceptions.

**Warning signs:**
- Fetches returning empty content after a known-difficult site is scraped.
- Research.md sections covering late-in-the-run sources are conspicuously thin compared to early sources.
- crawl4ai returns `success: True` with `markdown: ""`.

**Phase to address:** Phase 1 (crawl4ai Integration Layer). Build the resilience wrapper before writing research logic. A fragile fetcher produces a fragile research agent regardless of how good the prompts are.

---

### Pitfall 3: Anti-Bot Detection Kills Primary Source Access

**What goes wrong:**
The most valuable sources for documentary research — news archive paywalls (NYT, Washington Post, Guardian), court record databases (PACER), government document repositories — are also the most aggressively protected. crawl4ai's success rate drops to 72% on anti-bot protected sites without proxy infrastructure. As of 2026, major publishers including the New York Times and Gannett are actively blocking AI crawlers and have added `archive.org_bot` to robots.txt, meaning even archive.org bypass strategies are now blocked. The agent confidently attempts 20 URLs, 8 fail silently, and the research dossier has structural gaps the scriptwriter cannot detect.

**Why it happens:**
Cloudflare, Akamai, PerimeterX, and DataDome detect headless browsers via TLS fingerprinting, canvas rendering signatures, timing analysis, and behavioral heuristics. AI crawlers are now a large enough problem that publishers are actively hardening defenses. The crawl4ai "undetected browser" mode reduces but does not eliminate detection, and adds resource overhead.

**How to avoid:**
- Tier sources by access reliability in the agent's source strategy. Tier 1 (reliably accessible without proxies): Wikipedia, archive.org for pre-2025 content, government `.gov` domains, HathiTrust, Internet Archive document collections, Wikisource. Tier 2 (try but expect failures): regional news sites, older news archives. Tier 3 (do not attempt, waste of time): NYT, Washington Post, Guardian, any Gannett property, PACER.
- Do not treat failed fetches as empty data — log them explicitly as `access_blocked` in the sources manifest and flag them for manual retrieval.
- For paywalled content: scrape the URL structure (headline, date, author, teaser) even if body is blocked. The metadata itself is useful context for the scriptwriter.
- robots.txt compliance: crawl4ai supports `check_robots_txt=True` — enable it. Scraping disallowed paths creates legal exposure, not just technical risk.

**Warning signs:**
- All high-quality sources (major newspapers, court records) show as failed fetches.
- Research dossier relies exclusively on Wikipedia and free blogs with no archival sources.
- crawl4ai returns HTTP 403 or CAPTCHA pages repeatedly on the same domain.

**Phase to address:** Phase 1 (Source Strategy and Tiering). Define the accessible source list before the first research run. Do not discover access limits mid-production.

---

### Pitfall 4: Two-Pass Design Collapses Into One Expensive Pass

**What goes wrong:**
The two-pass design (broad survey → deep dive) requires discipline. In practice, the broad survey pass tends to expand: "while we're here, let's go deep on this promising URL." The deep dive pass then restarts with unstructured scope. The result is one expensive, unfocused pass that scrapes 60 URLs randomly without the prioritization a true two-pass structure provides. Research quality degrades because depth and breadth are pursued simultaneously.

**Why it happens:**
The temptation is natural — if Pass 1 finds a promising primary source, why not extract everything from it now? But Pass 1's job is mapping the territory, not inhabiting it. Mixing the passes loses the strategic advantage: the ability to make informed decisions about where to invest deep-dive effort after seeing the full landscape.

**How to avoid:**
- Define hard constraints per pass enforced in code, not just in prompts. Pass 1: maximum 2 URLs per source type, no full-document downloads, output is a structured source manifest with relevance scores and not a draft Research.md. Pass 2: operates exclusively on the source manifest from Pass 1, maximum 15 deep-fetch operations, each fetch justified by a specific schema field it fills.
- Pass 1 output must be a machine-readable intermediate artifact (JSON source manifest), not a prose summary. Prose output from Pass 1 means Pass 2 context is wasted re-processing language instead of fetching new data.
- The user should be able to review and edit the Pass 1 source manifest before Pass 2 begins. This catches scope issues early and adds a human-in-the-loop quality gate.

**Warning signs:**
- Pass 1 takes longer than 10 minutes (it is doing Pass 2's work).
- The source manifest from Pass 1 already contains full article content rather than URLs and relevance scores.
- Pass 2 cannot execute because context is already full from Pass 1's output.

**Phase to address:** Phase 1 (Research Architecture Design). The two-pass boundary must be a hard architectural constraint, not a soft guideline in a prompt. Define the intermediate artifact schema before writing any research logic.

---

### Pitfall 5: Automated Credibility Scoring Produces False Confidence

**What goes wrong:**
The research agent assigns credibility scores to sources (1-10, or low/medium/high). Scores give the scriptwriter false confidence — a source rated 8/10 gets used without independent verification. But credibility scoring by domain name alone is broken: a credible outlet like Reuters can publish one bad article; a low-rated fringe site can publish a documented fact that mainstream outlets missed (which is often the case for the channel's obscure topics). Research shows that labeling every article from a low-rated domain as false is "as reliable as flipping a coin."

**Why it happens:**
Automated credibility scoring typically reduces to domain reputation heuristics (`.gov` is reliable, personal blogs are not). This ignores article-level quality, recency, corroboration, and most importantly, the topic domain — where "credibility" of mainstream outlets for obscure historical events is often low because they simply did not cover the event.

**How to avoid:**
- Do not use binary or scalar credibility scores. Use a structured credibility signal instead:
  - `corroborated_by`: list of other sources that report the same claim
  - `source_type`: primary (document, court record, direct account) / secondary (journalism, analysis) / tertiary (wiki, aggregator)
  - `recency`: date of publication
  - `access_quality`: full_text / excerpt_only / blocked (so the scriptwriter knows how much was actually read)
- Flag claims that appear in only one source as `single_source` — the scriptwriter should treat these as unverified.
- Never assign a single credibility number. Numbers create unwarranted precision in what is fundamentally a qualitative judgment.

**Warning signs:**
- Research.md has a `credibility: 8` field next to every source with no explanation.
- Scriptwriter treats all highly-scored sources as verified facts without questioning.
- The scoring rubric rewards domain prestige (NYT = 9) rather than content quality.

**Phase to address:** Phase 1 (Research Schema Design). Define the credibility signal structure in the schema before writing the research prompts.

---

### Pitfall 6: Research.md Overloads the Scriptwriter's Context Window

**What goes wrong:**
The research agent produces a thorough 8,000-word Research.md with every source, every quote, every contradicting account, and every piece of discovered media. The scriptwriter agent then receives this as context — but 8,000 words of research consumes the bulk of a useful context window before any script-writing work begins. The scriptwriter either truncates the research (losing critical details), or produces a script that reads like a Wikipedia article (because it is trying to incorporate everything).

**Why it happens:**
Research agents optimize for completeness. The researcher's job is to not miss things. But downstream consumers need curation, not completeness. These are opposite optimization targets that are rarely reconciled in the schema design.

**How to avoid:**
- Split Research.md into two files: `Research.md` (scriptwriter-facing, curated) and `ResearchArchive.md` (complete, for reference).
- Research.md scriptwriter version: maximum 2,000 words covering the narrative spine (timeline, key figures, best quotes, contradictions, unanswered questions). Everything that does not directly serve the narrative goes to archive.
- ResearchArchive.md: full source list, all fetched content excerpts, media URLs, credibility signals. Used by scriptwriter only when drafting specific sections that need source verification.
- Alternatively: structure Research.md with a mandatory 500-word executive summary at the top, and full detail in collapsible sub-sections. The scriptwriter reads the summary first and expands only what they need.

**Warning signs:**
- Research.md exceeds 5,000 words.
- The scriptwriter's output is a listicle of facts rather than a narrative.
- Script lacks the "hook" quality of the channel's reference scripts despite rich research.

**Phase to address:** Phase 1 (Output Schema Design). Define the Research.md word budget and structure before the first research run. Retrofitting a schema after the agent is producing output is painful.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Single crawl4ai browser context for all fetches | Simpler code, fewer setup calls | Silent failures contaminate subsequent fetches (Pitfall 2) | Never |
| Source credibility as a 1-10 scalar | Simple to generate and read | False precision, drives bad decisions (Pitfall 5) | Never |
| Research.md as one monolithic file | Simple output | Overloads scriptwriter context (Pitfall 6) | MVP only, split before v1 ships |
| Skip robots.txt check for speed | Fewer HTTP calls per run | Legal exposure, IP bans on high-value research domains | Never |
| Hardcoding "reliable" domains list | Avoids credibility logic complexity | Domain reputation != article quality | MVP only, replace with structured credibility signals |
| Fetching entire pages vs. targeted CSS selectors | Works for all page structures | 11% noise ratio wastes context tokens, hurts extraction quality | Only for pages with no identifiable content structure |
| Storing all research in a single pass | Simpler orchestration | Loses the strategic advantage of the two-pass design (Pitfall 4) | Never — two passes is the architectural rationale |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| crawl4ai on Windows 11 | Skipping `crawl4ai-setup` after pip install; Playwright browsers not found | Always run `crawl4ai-setup` post-install, run `crawl4ai-doctor` to verify; set `PLAYWRIGHT_BROWSERS_PATH` if custom install dir |
| crawl4ai async context | Using `await crawler.arun()` without async context manager | Always use `async with AsyncWebCrawler() as crawler:` — guarantees browser cleanup on exceptions |
| crawl4ai + Git Bash on Windows | Paths with spaces in the project directory cause subprocess failures | Quote all paths; use `pathlib.Path` for path construction; avoid spaces in crawl4ai temp file paths |
| Research.md → Scriptwriter handoff | Passing the full Research.md file path with no structure signal | Pass a structured context block: `## Research Summary\n[summary]\n\n## Key Sources\n[top 5 sources]\n\n## Full Research\n[path to file]` |
| Source URL provenance | LLM paraphrases a URL rather than returning the crawled URL | Fetch URLs must be passed into the research prompt, never generated by the LLM |
| crawl4ai markdown extraction | `result.markdown` vs `result.markdown_v2.raw_markdown` — API changed between versions | Pin crawl4ai version, test output field names explicitly, do not assume field stability |
| Two-pass intermediate artifact | Storing Pass 1 output as prose in the conversation context | Write Pass 1 output to a JSON file in the project directory; Pass 2 reads the file — keeps context clean |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Scraping 40+ URLs sequentially with no rate limiting | 429 errors, IP blocks mid-research run | Enforce minimum 5-10 second jittered delay between fetches; hard cap of 30 fetches per run | First run on a new topic with many sources |
| Loading all fetched content into a single LLM call | Context window exceeded; LLM truncates silently | Process sources in batches; write extracted facts to scratch files between batches | At ~15 full-page fetches worth of markdown |
| No caching of successful fetches | Same URLs refetched on every research run iteration | Cache fetched content keyed by URL + date; skip re-fetch if cached within 24 hours | On any topic that requires iteration or correction |
| Browser instances not closed between topics | Memory grows monotonically; system slows after 2-3 topics | Use `async with` pattern; explicitly close crawler between topic runs | After 3+ consecutive research runs without restart |
| Parsing raw crawl4ai markdown output directly | Brittle code breaks when crawl4ai updates markdown format | Write a content extractor abstraction that normalizes crawl4ai output; update one place when API changes | Every crawl4ai minor version update |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Logging full scraped content to files | Scraped pages may contain PII (victim names, personal details in court records) | Log only URLs and fetch status, not content; content stays in memory and scratch files only |
| No robots.txt compliance | Legal exposure from scraping disallowed paths; ethical violation | Enable `check_robots_txt=True` in crawl4ai config; never override for "important" sources |
| Passing raw scraped content directly to prompts without sanitization | Prompt injection: a malicious web page could contain instructions that hijack the research agent's behavior | Sanitize scraped content before adding to prompts: strip content between `<script>` tags, limit extraction to visible text content only |
| Storing API keys or credentials in research scripts | Credential exposure in version control | No credentials needed for this agent's scope — all sources are public. If credentials are ever added, use environment variables only |

---

## "Looks Done But Isn't" Checklist

- [ ] **Source provenance:** Research.md contains citations — verify each has a real crawled URL, not an LLM-generated reference. Spot-check 3 URLs manually.
- [ ] **Pass 1 / Pass 2 boundary:** Both passes complete — verify Pass 1 produced a machine-readable source manifest, not prose. Verify Pass 2 operated exclusively on that manifest.
- [ ] **Failed fetch handling:** Research completes successfully — check the fetch log for silently-failed URLs. If >30% of attempted fetches failed, research has structural gaps.
- [ ] **Content extraction quality:** crawl4ai returned results — verify extracted markdown has meaningful content (>500 chars per source) and not boilerplate navigation/footer text.
- [ ] **Schema completeness:** Research.md looks complete — verify it contains all required schema fields: `timeline`, `key_figures`, `contradictions`, `unanswered_questions`, `source_reliability`. Missing sections mean the scriptwriter gets an incomplete dossier.
- [ ] **Windows path handling:** Research runs on dev machine — verify the output path `projects/N. [Video Title]/Research.md` handles the space in the title correctly on Windows without path truncation.
- [ ] **Context hygiene:** Research agent completes — verify fetch content was written to `.claude/scratch/`, not held in conversation context. Re-running should not OOM.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Hallucinated citations discovered post-research | MEDIUM | Delete Research.md; re-run with stricter URL-provenance enforcement; add spot-check step to workflow |
| Browser context contamination mid-run | LOW | Restart crawl4ai with fresh context; re-run from the failed URL onward using the source manifest checkpoint |
| 60%+ of sources blocked by anti-bot | HIGH | Switch to Tier 1 sources only; add manual research step to the workflow for Tier 2-3 sources; document which sources require human access |
| Research.md too long for scriptwriter | LOW | Split into Research.md (curated) + ResearchArchive.md (full); update scriptwriter context to load only curated version |
| Two passes collapsed, research unfocused | MEDIUM | Define strict Pass 1 URL cap in code; add intermediate review step between passes; re-run with hard constraints |
| crawl4ai version update breaks field names | LOW | Pin version in requirements.txt; run extraction tests after any update before using in production |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Hallucinated citations (Pitfall 1) | Phase 1: Schema Design | Each source in Research.md has a verified crawled URL |
| Browser context contamination (Pitfall 2) | Phase 1: crawl4ai Integration | Run 20+ sequential fetches, verify no silent failures after any error |
| Anti-bot access failures (Pitfall 3) | Phase 1: Source Strategy | Source tier list defined; failed fetches logged explicitly as `access_blocked` |
| Two-pass collapse (Pitfall 4) | Phase 1: Architecture Design | Pass 1 produces JSON source manifest; Pass 2 reads it; neither pass can be skipped |
| False credibility scoring (Pitfall 5) | Phase 1: Schema Design | No scalar credibility scores exist in Research.md; structured signals used instead |
| Context window overload (Pitfall 6) | Phase 1: Output Schema | Research.md has defined word budget; scriptwriter-facing version is separate from archive |
| Windows path issues | Phase 1: Integration Testing | Research run completes successfully with a project title containing spaces |
| Prompt injection via scraped content | Phase 1: crawl4ai Integration | Sanitization layer verified; test with a page containing adversarial instructions |

---

## Sources

- [Crawl4AI GitHub Issue #501: Browser context contamination after failed scrapes](https://github.com/unclecode/crawl4ai/issues/501)
- [Crawl4AI GitHub Issue #1256: Memory leak on repeated requests](https://github.com/unclecode/crawl4ai/issues/1256)
- [Crawl4AI GitHub Issue #1379: Browser closed during pagination with managed browser](https://github.com/unclecode/crawl4ai/issues/1379)
- [Crawl4AI Documentation: Anti-Bot and Fallback](https://docs.crawl4ai.com/advanced/anti-bot-and-fallback/)
- [Crawl4AI Documentation: Undetected Browser](https://docs.crawl4ai.com/advanced/undetected-browser/)
- [Morphllm: AI Web Scraping 2026 — 89.7% success rate, 72% on anti-bot sites](https://www.morphllm.com/ai-web-scraping)
- [Nieman Journalism Lab: News publishers limit Internet Archive access due to AI scraping (2026)](https://www.niemanlab.org/2026/01/news-publishers-limit-internet-archive-access-due-to-ai-scraping-concerns/)
- [Techdirt: News Publishers Are Now Blocking The Internet Archive (2026)](https://www.techdirt.com/2026/02/13/news-publishers-are-now-blocking-the-internet-archive-and-we-may-all-regret-it/)
- [GPTZero: 100 hallucinated citations found in NeurIPS 2025 accepted papers](https://gptzero.me/news/neurips/)
- [StudyFinds: GPT-4o fabricated 56% of citations in mental health literature review](https://studyfinds.org/chatgpts-hallucination-problem-fabricated-references/)
- [Historica: AI Hallucinations and the Risks to Historical Research Integrity](https://www.historica.org/blog/ai-fictions-historiography-misinformation)
- [PMC: Source credibility assessment — domain-level scoring as unreliable as coin flip](https://revistas.unir.net/index.php/ijimai/article/download/856/915)
- [arxiv: Deep Research Agents — Systematic Examination (2025)](https://arxiv.org/html/2506.18096v1)
- [Medium: Can LLMs really do web research? Failure modes in search, page selection, extraction](https://medium.com/@prxshetty/can-llms-really-do-web-research-and-why-your-agent-still-gets-stuck-d74598b44e45)
- [EFF: Keeping the Web Up Under the Weight of AI Crawlers (2025)](https://www.eff.org/deeplinks/2025/06/keeping-web-under-weight-ai-crawlers)
- [ScrapingBee: Crawl4AI Hands-on Guide](https://www.scrapingbee.com/blog/crawl4ai/)

---

*Pitfalls research for: Web Research Agent (Agent 1.2) — documentary video production pipeline*
*Researched: 2026-03-12*
