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

These skills are already installed in Claude's skills directory:

- `yt-dlp` — Video/audio downloading from 1800+ sites
- `crawl4ai` — Web scraping
- `remotion` — Remotion animation best practices

## Coding Standards

- **Language:** All scripts must be written in Python. Do not use Node.js or JavaScript for scripting tasks.

## Other Notes

- I am editing in Davinci Resolve