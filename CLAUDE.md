# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **agentic documentary video generation pipeline** for a YouTube channel focused on dark mysteries content. Claude Code itself is the orchestrator — it spawns sub-agents with skills to complete each phase. There is no application entry point; the pipeline is driven entirely through Claude Code skill invocations.


## Context

- @Architecture.md - Architecture spec
- @context/channel/channel.md -- Channel DNA: Voice, tone, style rules, audience profile
- @context/channel/past_topics.md -- Past topics to avoid duplication
- `context/competitors/` -- Competitor Data
- `context/script-references/` -- Full Successful Scripts
- `context/visual-references/` -- Visual References

## Keeping Context Current
- Update '

## Skills

- `yt-dlp` — Video/audio downloading from 1800+ sites
- `crawl4ai` — Web scraping
- `remotion` — Remotion animation best practices

## Context Engineering

### Scratch Pad
- When tool output exceeds ~1500 tokens, write it to `.claude/scratch/` with a descriptive filename
- Return only a 1-2 line summary in conversation context
- Read back specific sections with grep or line ranges when needed
- Sub-agents can read/write to `.claude/scratch/` for collaboration
- Files in `.claude/scratch/` are transient — not committed, can be deleted between sessions


## Coding Standards

- **Language:** All scripts must be written in Python. Do not use Node.js or JavaScript for scripting tasks.

## Other Notes

- I am editing in Davinci Resolve