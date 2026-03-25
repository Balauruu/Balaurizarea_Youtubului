# Task Router

What's your task? Find it below, load the right files, skip the rest.

## Task Routing

| Task | Skill | Load These | Section/Scope | Skip These |
|------|-------|-----------|---------------|------------|
| **Topic ideation** | channel-assistant | `strategy/channel/channel.md`, `strategy/channel/past_topics.md`, `strategy/competitors/analysis.md` | channel.md: "Core Content Pillars", "Topic Selection Criteria". analysis.md: full file | `reference/`, `projects/` — not relevant to topic selection |
| **Research a topic** | researcher | `strategy/channel/channel.md`, project's `metadata.md` | channel.md: "Core Content Pillars" only | `strategy/competitors/`, `reference/` — research is topic-focused |
| **Extract channel voice** | style-extraction | `reference/scripts/*`, `strategy/channel/channel.md` | channel.md: full file (to avoid duplication) | `strategy/competitors/`, `projects/` — self-contained |
| **Write script** | writer | `reference/voice/WRITTING_STYLE_PROFILE.md`, `reference/scripts/`, `strategy/channel/channel.md`, project's `research/Research.md` | All full files | `strategy/competitors/`, `reference/visuals/` — writer needs voice + research, not strategy |
| **Create shot list** | visual-orchestrator | project's `Script.md`, `reference/visuals/VISUAL_STYLE_GUIDE.md`, `.claude/skills/visual-orchestrator/prompts/generation.md`, project's `research/media_leads.json` | All full files | `strategy/`, `reference/voice/`, `reference/scripts/` — director needs script + visual rules only |
| **Discover media** | media-scout | project's `research/entity_index.json`, project's `research/Research.md` | All full files | `strategy/`, `reference/` — entity-driven search |
| **Find b-roll** | broll-curator | project's `shotlist.json` (`broll_themes` array), `reference/visuals/VISUAL_STYLE_GUIDE.md` | VISUAL_STYLE_GUIDE: "B-Roll Theme Rules" section | `strategy/`, `reference/voice/`, `reference/scripts/`, `research/` — curator uses themes, not narrative |
| **Add/scrape competitors** | channel-assistant | `strategy/competitors/competitors.json` | Full file | Everything else |

## Cross-Phase Handoffs

Each skill produces output that feeds the next skill. The handoff is the file itself — edit it between phases and the next skill picks up your edits.

## Workspace Details

| Workspace | Purpose | CONTEXT.md |
|-----------|---------|------------|
| `strategy/` | Channel intel, competitor analysis, topic generation | `strategy/CONTEXT.md` |
| `reference/` | Stable factory files: voice rules, reference scripts, visual guides | `reference/CONTEXT.md` |
| `projects/` | Per-video working directories (pipeline outputs) | No CONTEXT.md — each project is a data folder |
