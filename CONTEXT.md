# Task Router

What's your task? Find it below, load the right files, skip the rest.

## Task Routing

| Task | Skill | Load These | Section/Scope | Skip These |
|------|-------|-----------|---------------|------------|
| **Topic ideation** | channel-assistant | `channel/channel.md`, `channel/past_topics.md`, `strategy/competitors/analysis.md` | channel.md: "Core Content Pillars", "Topic Selection Criteria". analysis.md: full file | `channel/scripts/`, `projects/` — not relevant to topic selection |
| **Research a topic** | researcher | `channel/channel.md`, project's `metadata.md` | channel.md: "Core Content Pillars" only | `strategy/competitors/`, `channel/scripts/` — research is topic-focused |
| **Extract channel voice** | style-extraction | `channel/scripts/*`, `channel/channel.md` | channel.md: full file (to avoid duplication) | `strategy/competitors/`, `projects/` — self-contained |
| **Write script** | writer | `channel/voice/WRITTING_STYLE_PROFILE.md`, `channel/scripts/`, `channel/channel.md`, project's `research/Research.md` | All full files | `strategy/competitors/`, `channel/visuals/` — writer needs voice + research, not strategy |
| **Create shot list** | shot-planner | project's `Script.md`, `channel/visuals/VISUAL_STYLE_GUIDE.md`, project's `visuals/media_leads.json` | All full files | `strategy/`, `channel/voice/`, `channel/scripts/` — planner needs script + visual rules only |
| **Discover media** | media-scout | project's `research/entity_index.json`, project's `research/Research.md` | All full files | `strategy/`, `channel/` — entity-driven search |
| **Analyze assets** | asset-analyzer | project's `visuals/shotlist.json`, project's `visuals/media_leads.json`, project's `assets/staging/` | All full files | `strategy/`, `channel/` — analyzer uses shotlist + staged videos |
| **Add/scrape competitors** | channel-assistant | `strategy/competitors/competitors.json` | Full file | Everything else |

## Cross-Phase Handoffs

Each skill produces output that feeds the next skill. The handoff is the file itself — edit it between phases and the next skill picks up your edits.

## Workspace Details

| Workspace | Purpose | CONTEXT.md |
|-----------|---------|------------|
| `strategy/` | Channel intel, competitor analysis, topic generation | `strategy/CONTEXT.md` |
| `channel/` | Stable reference files: voice rules, reference scripts, visual guides | No CONTEXT.md — stable reference |
| `projects/` | Per-video working directories (pipeline outputs) | No CONTEXT.md — each project is a data folder |
