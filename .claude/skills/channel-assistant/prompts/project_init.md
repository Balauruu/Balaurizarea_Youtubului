# Project Init: Title Variants + Description

## Role

You are generating YouTube metadata for a dark mysteries documentary channel.
Tone: calm, clinical, journalistic. Let facts create unease — no superlatives, no
sensationalism, no cheap shock hooks.

## Input

You have two inputs loaded via `load_project_inputs(root, N)`:

1. **brief_markdown** — the selected topic brief (title, hook, timeline, scores)
2. **title_patterns** — the Title Patterns section from `strategy/competitors/analysis.md`,
   showing which patterns drive high-view outliers on competitor channels

## Title Variants (generate exactly 5)

Rules:
- Each variant must be 70 characters or fewer (hard channel constraint)
- Each variant must use a **different hook type** — draw hook types from the competitor
  title patterns data, not from a fixed list. Common types: question, statement,
  revelation, curiosity gap, number-led, name-led, date-anchored. Use what the data shows.
- One variant is marked RECOMMENDED with a brief note citing which competitor pattern
  it follows and why it fits this specific topic
- Tone stays neutral and clinical — avoid "SHOCKING", "INSANE", "You Won't Believe",
  or any superlative that the channel style rejects
- If title_patterns is empty (analysis.md absent), derive hook types from the brief
  itself and note that competitor data was unavailable

Evaluation order:
1. Does it fit within 70 characters?
2. Does it use the hook type correctly?
3. Does it match the channel's neutral voice?
4. Does it surface the obscurity/complexity that makes the topic compelling?

## Description (generate exactly 1)

Rules:
- 2-3 sentences — hook paragraph only
- No hashtags, no chapter list, no links, no "Subscribe"
- Marketing tone: slightly more engaging than the video's narration voice
  (descriptions serve YouTube search/discovery, not the viewer already watching)
- Must fit before YouTube's "Show more" fold (~200 characters visible)
- Ground it in the specific facts of this topic — no generic "In this video..."

## Output format

After generating, call `init_project()` with this exact structure:

```python
from channel_assistant.project_init import init_project
from pathlib import Path

root = Path(".")  # or _get_project_root() if running inside the skill

init_project(
    root=root,
    title="[title from the selected brief — verbatim]",
    hook="[hook from the selected brief — verbatim]",
    title_variants=[
        {"title": "...", "hook_type": "question", "recommended": False, "notes": ""},
        {"title": "...", "hook_type": "statement", "recommended": False, "notes": ""},
        {"title": "...", "hook_type": "revelation", "recommended": True, "notes": "Follows [pattern name] — [1-sentence reasoning]"},
        {"title": "...", "hook_type": "curiosity gap", "recommended": False, "notes": ""},
        {"title": "...", "hook_type": "...", "recommended": False, "notes": ""},
    ],
    description="[2-3 sentence hook paragraph, no hashtags]",
    brief_markdown="[raw markdown of the selected brief section from topic_briefs.md]",
)
```

## Anti-patterns

- Do NOT write code that calls an LLM API or imports anthropic/openai
- Do NOT create a new CLI subcommand for this step
- Do NOT modify topics.py
- Do NOT exceed 70 characters on any title variant — check length before finalising
- Do NOT mark more than one variant as RECOMMENDED
