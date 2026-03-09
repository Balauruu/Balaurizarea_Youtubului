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
        - Subagents:
            - Competitor subagent :
                1. Searches for competitors in my niche, analyzes topic selection, title selection. Retrives useful information for my channel. 
                2. Evaluates competitor data
                3. Retrieves useful information for my channel. 
    - **Logic:** Filters for obscurity, complexity and shock factor. Rejects previously covered topics to maintain novelty.
    - **Output:** A list of topics, each with 50-100 word brief estimated runtime. User will choose from chat window the topic
    
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
    - @context/competitors.md -- Competitor Data
    ```
    
- Needs: A better way to keep track of competitors.
- **Agent 1.2: Deep Research (The Researcher)**
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
    - ***Function:***  Parses the script to map visual continuity and determine the necessary media for every scene. This aligns with the industry standard of programmatic shot-listing.
    - **Output: s**hotlist.json + needed_assets.json
    
    ```jsx
    ## Shot List Entry
    - **chapter**: Which script chapter
    - **timestamp_range**: Start-end in script (by word count or narration time)
    - **visual_type**: [archival_photo | archival_video | news_clip | animation | ai_generated | map | text_overlay | document_scan]
    - **description**: What should be shown
    - **source_hint**: Suggested search query or asset reference
    - **duration_seconds**: How long this visual holds
    - **transition**: [cut | fade | dissolve | zoom]
    - **motion**: [ken_burns_in | ken_burns_out | pan_left | static]
    ```
    

---

### Phase 2: Asset Pipeline

This phase translates the text script into individual, tangible media assets.

- Module 2.0: Asset Management System

example:

```jsx
{
  "assets": [
    {
      "id": "001",
      "type": "audio_narration",
      "chapter": "intro",
      "file": "001_Audio_Intro.wav",
      "status": "ready"
    },
    {
      "id": "002",
      "type": "visual_archival",
      "chapter": "intro",
      "file": "001_Visual_HistoricalPhoto.jpg",
      "source_url": "https://...",
    }
  ]
}
```

- **Agent 2.1: Media Acquisition**
    - **Function:** Sources historical and contextual media.
    - Triggers scrapper to execute targeted web searches historical media, documents, and news clippings and more TBD, such as: official voice recordings, old-cartoon B-roll, old footage b-roll in general that fits the visual.
    - **Output:** Downloaded assets.
    - **Quality Target:** https://www.opus.pro/agent (for research only, not use in my stack.)
- **Agent 2.2: Generative Visual Engine**
    - **Main Function:** Fills visual gaps where media is unavailable.
        - Subagents: Be able to generate prompts for different (style/assets) in parallel
            - realistic: B-roll Footage
            - vector: Assets for Remotion
    - **Output:** Text-based prompts optimized for image generation (ComfyUI).
    - **Context:**
        
        ```jsx
        - `context/Styles/` -- Style formats for different visual prompts.
        ```
        
- **Agent 2.3: Animation Agent (Remotion)**
    - **Logic:** Runs independently to generate isolated visual components, mainly animation.
        1. Shot list specifies which animations are needed (maps, timelines, text reveals, data visualizations)
        2. A `remotion-templates/` folder contains reusable React components for each animation type
        3. The agent generates a `compositions.json` that parameterizes each template
        4. Remotion renders via CLI: `npx remotion render --props compositions.json`
    - **Output:** `.mp4` or `.mov` files.
    - **Animations Quality Target:** https://hera.video/ (for research only, not use in my stack)
    - **Context:**
    
    ```jsx
    Assets Folder
    + Remotion global skill
    ```
    
- **Agent 2.4: Asset Manager**
    - **Logic:** Gathers all generated audio, scraped media, and Remotion animations. Renames files sequentially based on their appearance order (e.g., `001_Audio_Intro.wav`, `001_Visual_MapAnim.mp4`, `002_Audio_Main.wav`, `002_Visual_Prompt_Cult.txt`).
    - **Output:** The final target. A consolidated, sequentially ordered local folder.

---

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