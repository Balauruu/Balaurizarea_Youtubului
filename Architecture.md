*description:*  Automated documentary video generation pipeline, optimized for generating narrative-driven video content. This pipeline is executed by a CLI-based coding agent (Claude Code.). The agent itself is the orchestrator.

The pipeline state will be managed via Claude Code invoking specific skills. Module 1.1 (Channel Assistant) should be a Claude Code skill/agent that outputs a markdown dossier, which is then read by the next skill/agent.

*Do not write wrapper code for LLM APIs. LLM reasoning is provided natively by the runtime environment (being run in claude code).* 

# CRITICAL ARCHITECTURE RULES

1. **ZERO LLM API WRAPPERS:** Never write code that initializes LLM SDKs (`@anthropic-ai/sdk`, `openai`, etc.). All reasoning and orchestration is handled natively by Claude Code. LLM API Wrappers can be used only if are part of an essential tool for my workflow.
2. **SEPARATION OF CONCERNS:** PROMPT VS. CODE
Before executing any task, explicitly classify it as:
- [HEURISTIC]: Requires logic, narrative design, or evaluation. Solved via Claude Code skills and prompt files. No code written.
- [DETERMINISTIC]: Requires structured data manipulation, scraping, or media rendering. Solved via code.

## Requirements:

- Must be an agentic framework with specific agents created along with their skills and tool calls.
- Must be context-engineered

## Pipeline:

- **Scraper: Crawl4ai**
- Database/Knowledge System/Context-engineering - Filesystem

### Phase 1: Narrative Engineering

This phase manages the intellectual rigor of the documentary. It requires three distinct agent personas.

- **Agent 1.1: Channel Assistant (Strategy & Ideation)**
    - **Main Function:** Select viable topics, for future videos.
    - **Logic:** Filters for obscurity, complexity and shock factor. Rejects previously covered topics to maintain novelty.
    - Other Functions: Write the metadata, for the video: title, description. (this should also be done after analyzing competitors)
        - Subagents:
            - Competitor subagent :
                1. Searches for competitors in my niche, analyzes topic selection, title selection. Retrives useful information for my channel. 
                2. Evaluates competitor data
                3. Retrieves useful information for my channel. 
    - **Output:** A list of topics, each with 50-100 word brief estimated runtime. User will choose from chat window the topic after which a file with the name of the topic selected will be created in projects with the following format “1. [Video Title]”. In the created directory a .md file with the metadata will also be created.
    
    ```
    ## Topic Brief Schema
    - **title**: Working title (max 80 chars, YouTube-optimized)
    - **hook**: The core mystery in 1 sentence
    - **timeline**: Key events in chronological order (3-8 entries)
    - **complexity_score**: 1-10 (how layered is the story)
    - **obscurity_score**: 1-10 (how little-known)
    - **shock_factor**: 1-10 (emotional impact potential)
    - **estimated_runtime**: minutes 
    ```
    
    - **Context:**
    
    ```
    - @context/Channel.md -- Channel DNA
    - @context/channel/past_topics.md -- Past topics to avoid duplication
    ```
    
- Needs: A better way to keep track of competitors.
- **Agent 1.2: The Researcher**
    - **Function:** Executes comprehensive web scraping to build a factual foundation.
    - **Logic:** Uses a scrapper to scrape sources and write an in depth research about the subject.
    - **Output:** Research.md file that can be used for script writting
    
    ```jsx
    ## Research Dossier Schema
    - **subject_overview**: 500-word summary
    - **timeline**: Detailed chronological events with sources
    - **key_figures**: People involved, roles, quotes
    - **primary_sources**: Official documents, court records, interviews
    - **secondary_sources**: News articles, books, documentaries
    - **media_inventory**: URLs of available images, videos, audio recordings
    - **contradictions**: Conflicting accounts across sources
    - **unanswered_questions**: Gaps that create narrative tension
    - **source_reliability**: Credibility rating per source
    ```
    
    - **Context:**
    
    ```jsx
    - `context/Script References/` -- Full Successful Scripts
    ```
    
- **Skill 1.3: style_extraction**

**Improvement:** Create a `style_extraction` skill that:

1. Reads the reference script
2. Extracts: sentence length distribution, vocabulary register, transition phrases, chapter structure pattern, narrative pacing (exposition vs. tension ratio)
3. Outputs a `STYLE_PROFILE.md` that the Writer skill loads as context
4. This is a one-time [HEURISTIC] operation, not per-run
- **Agent 1.3: The Writer**
    - **Function:** Converts the research dossier into a narrated video script.
    - **Logic:** Enforces a structure and style extracted from the script reference.  Must have a style_guide.MD
    - **Output:** A clean text file containing numbered chapters and pure narration text.
    - **Context:**
    
    ```jsx
    - `context/Script References/` -- Full Successful Scripts
    ```
    
- **Agent 1.4: Visual Orchestrator (The Director)**
    - ***Function:***  Parses the script to map visual continuity and determine the necessary media for every scene. Outputs a loose shot list of narrative needs — not strict asset types.
    - **Output:** `shotlist.json`

    ```json
    {
      "shots": [
        {
          "id": "S001",
          "chapter": "intro",
          "narrative_context": "Narrator describes the remote mountain commune in 1970s Mexico",
          "visual_need": "Remote rural settlement, mountainous terrain, 1970s feel",
          "suggested_types": ["archival_video", "archival_photo", "broll"]
        }
      ]
    }
    ```

    **Shot Entry Fields:**
    - **id**: Unique shot identifier (S001, S002, ...)
    - **chapter**: Script chapter this shot belongs to
    - **narrative_context**: What the narrator is saying during this shot
    - **visual_need**: Free-text description of what visual is needed (intentionally loose)
    - **suggested_types**: Hints, not constraints — acquisition agent can use any type that fits

    **Design Principles:**
    - No duration, priority, effects, transitions, or post-production instructions — those are the editor's domain
    - `needed_assets.json` is no longer a separate output — the manifest serves this role
    

---

### Phase 2: Asset Pipeline

This phase translates the shot list into tangible media assets. Agents run sequentially, each triggered manually by the user.

**Architecture:** Sequential pipeline. Each agent reads/writes a shared `manifest.json` at `projects/[Video Title]/assets/manifest.json`.

**Source Policy:** All footage and media must be free (public domain, CC0, or Creative Commons). No paid or subscription sources.

**Tools:** Crawl4ai for web scraping, yt-dlp for video downloads.

```
Agent 1.4 writes shotlist.json
    |
Agent 2.1 (Media Acquisition) — bulk scrape + gap analysis
    |
Agent 2.2 (Vector Generation) — ComfyUI prompts for gaps
    |
Agent 2.3 (Remotion Animations) — motion graphics [details deferred]
    |
Agent 2.4 (Asset Manager) — number, consolidate, final manifest
```

- **Agent 2.1: Media Acquisition**
    - **Function:** Two-pass design. Sources all relevant media for the topic.
    - **Input:** Reads only `shotlist.json` (not the script — Agent 1.4 already distilled the script into shot needs).
    - **Pass 1 — Bulk Acquisition:**
        - Reads shotlist.json to understand the topic (era, location, key figures, events)
        - Builds search queries from the topic context
        - Scrapes free/public domain sources for everything relevant
        - Downloads into type folders, unnumbered, with descriptive filenames
        - Writes each asset as an entry in `manifest.json`
    - **Pass 2 — Gap Analysis [HEURISTIC]:**
        - Matches acquired assets to shot list entries
        - Updates manifest.json with shot mappings
        - Outputs unmatched shots into the `gaps` section for downstream agents
    - **Output:** Downloaded assets in type folders + manifest.json with mappings and gaps
    - **Source Domains:**
        - Tier 1: archive.org, loc.gov, archives.gov, commons.wikimedia.org
        - Tier 2: publicdomainreview.org, images.nasa.gov, nps.gov, pdimagearchive.org, nationalarchives.gov.uk
        - Tier 3 (screenshots): en.wikipedia.org, britannica.com, news sites
        - Old cartoons: archive.org/details/19201928publicdomainanimation, publicdomainreview.org, LOC National Film Registry PD list, Wikimedia Commons animated shorts category
        - YouTube (via yt-dlp) for CC-licensed and public domain footage
    - **Rules:** Verify soundtracks on old cartoons are also PD (video may be PD but added music may not)
- **Agent 2.2: Vector Generation (ComfyUI)**
    - **Function:** Generates vector assets for shots that couldn’t be filled by acquisition.
    - **Logic:** Reads `gaps` section of manifest.json. [HEURISTIC] Generates ComfyUI prompts optimized for Z-image turbo. Updates manifest and marks gaps as filled.
    - **Scope:** Vector/figure generation only. Realistic AI-generated b-roll is out of scope — gaps requiring realistic imagery remain unfilled for the editor to address manually.
    - **Output:** Vector images in `assets/vectors/`, manifest.json updated.
- **Agent 2.3: Animation Agent (Remotion)**
    - **Function:** Renders motion graphics (maps, silhouettes, diagrams, other animations).
    - **Logic:** Details deferred to later design session.
    - **Interface:** Reads shotlist.json, can use vectors from Agent 2.2, outputs to `assets/animations/`, updates manifest.json.
    - **Output:** `.mp4` or `.mov` files.
- **Agent 2.4: Asset Manager**
    - **Function:** Final consolidation and sequential numbering.
    - **Logic:** Reads manifest.json. Assigns sequential prefixes based on order of appearance in shotlist.json (e.g., `001_compound_aerial.mp4`). Assets mapped to multiple shots get the number of their first appearance. Moves unmatched assets to `_pool/`. Sets remaining gaps to `unfilled`.
    - **Output:** Numbered assets in type folders + final manifest.json.

---

### Assets:

**Scraping:**

- archival_video
- archival_photo
- **Evidence & Documentation (these are all screenshotted, or pictures)**
    - **Wiki/Encyclopedia Text Block**
    - **Newspaper Clipping**
    - **Document Scan**
    - **Digital Screen Capture**

**Animations (remotion):**

- silhouettes animation
- map animations

**Text elements: (I will do myself)**

- Quote Card
- Testimony Card
- Date Card
- Keyword Stinger

**Davinci Resolve: (these I will search for myself)**

- BG’s
- Overlays
- Effects

### Resources:

Crawl4AI:
https://github.com/unclecode/crawl4ai

https://github.com/sadiuysal/crawl4ai-mcp-server

Context-Engineering:
https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering

### Useful skills:

- Use when creating the agents

skill-creator: "D:\AI\Agents\anthropic-skills\skills\skill-creator\[SKILL.md](http://skill.md/)"

crawl4ai: "D:\AI\Agents\crawl4ai”

all skills from Agent-Skills-for-Context-Engineering: "D:\AI\Agents\Agent-Skills-for-Context-Engineering”