# Strategy Workspace

Channel intelligence, competitor analysis, and topic ideation. This is where new video projects originate.

## What's Here

| Folder | Contents | Updated By |
|--------|----------|------------|
| `channel/channel.md` | Channel DNA — voice, tone, pillars, audience | Manual (rare) |
| `channel/past_topics.md` | Previously covered topics | channel-assistant (auto-appended on project init) |
| `competitors/competitors.json` | Registered channel registry | channel-assistant `add` command |
| `competitors/analysis.md` | Stats, outliers, trends, topic clusters | channel-assistant `analyze` command + Claude heuristic |
| `topics/topic_briefs.md` | Generated topic briefs | channel-assistant `topics` command + Claude heuristic |

## When to Load

| Task | Load | Skip |
|------|------|------|
| Topic ideation | `channel/channel.md` (pillars + criteria), `channel/past_topics.md`, `competitors/analysis.md` | Nothing in this workspace |
| Competitor refresh | `competitors/competitors.json` only | `channel/`, `topics/` |
| Project init | `topics/topic_briefs.md`, `competitors/analysis.md` (title patterns) | `channel/channel.md` (already consumed during topic gen) |

## Anti-Patterns

- Do NOT read other projects' outputs for topic inspiration — use `competitors/analysis.md` and channel DNA
- Do NOT duplicate channel.md content into analysis.md — point to it
- Do NOT load `reference/` files during strategy work — voice and visuals aren't relevant here
