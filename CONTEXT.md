# Task Router

What's your task? Find it below, load the right files, skip the rest.

## Task Routing

| Task | Skill | Load These | Section/Scope | Skip These |
|------|-------|-----------|---------------|------------|
| **Topic ideation** | channel-assistant | `channel/channel.md`, `channel/past_topics.md`, `strategy/competitors/analysis.md` | channel.md: "Core Content Pillars", "Topic Selection Criteria". analysis.md: full file | `channel/voice/`, `channel/visuals/`, `projects/` — not relevant to topic selection |
| **Research a topic** | researcher | `channel/channel.md`, project's `metadata.md` | channel.md: "Core Content Pillars" only | `strategy/competitors/`, `channel/voice/`, `channel/visuals/` — research is topic-focused |
| **Extract channel voice** | style-extraction | `channel/scripts/*`, `channel/channel.md` | channel.md: full file (to avoid duplication) | `strategy/competitors/`, `projects/` — self-contained |
| **Write script** | writer | `channel/voice/WRITTING_STYLE_PROFILE.md`, `channel/scripts/`, `channel/channel.md`, project's `research/Research.md` | All full files | `strategy/competitors/`, `channel/visuals/` — writer needs voice + research, not strategy |
| **Create shot list** | visual-orchestrator | project's `script/Script.md`, `channel/visuals/VISUAL_STYLE_GUIDE.md`, `.claude/skills/visual-orchestrator/prompts/generation.md`, project's `visuals/media_leads.json` | All full files | `strategy/`, `channel/voice/`, `channel/scripts/` — director needs script + visual rules only |
| **Discover media** | media-scout | project's `research/entity_index.json`, project's `research/Research.md` | All full files | `strategy/`, `channel/` — entity-driven search |
| **Find b-roll** | visual-orchestrator | project's `visuals/shotlist.json` (`broll_themes` array), `channel/visuals/VISUAL_STYLE_GUIDE.md` | All full files (IA search is now part of Visual Orchestrator) | `strategy/`, `channel/voice/`, `channel/scripts/`, `research/` — uses themes, not narrative |
| **Analyze video assets** | asset-analyzer | project's `visuals/media_leads.json`, project's `visuals/shotlist.json`, staging videos | All full files | `strategy/`, `channel/` — asset analysis is video-focused |
| **Add/scrape competitors** | channel-assistant | `strategy/competitors/competitors.json` | Full file | Everything else |

## Cross-Phase Handoffs

Each skill produces output that feeds the next skill. The handoff is the file itself — edit it between phases and the next skill picks up your edits.

```
channel-assistant   → projects/N/metadata.md              → researcher reads it
researcher          → projects/N/research/                 → writer + media-scout read from here
writer              → projects/N/script/Script.md          → visual-orchestrator reads it
media-scout         → projects/N/visuals/media_leads.json  → visual-orchestrator uses for source decisions
visual-orchestrator → projects/N/visuals/shotlist.json     → asset-analyzer reads visual needs
media-scout         → D:/.../3. Assets/_staging/           → asset-analyzer processes staged videos
asset-analyzer      → projects/N/assets/ + global assets   → editor imports into DaVinci Resolve
asset-analyzer      → data/asset_catalog.db                → any skill can query the catalog
```

## Workspace Details

| Workspace | Purpose | CONTEXT.md |
|-----------|---------|------------|
| `strategy/` | Channel intel, competitor analysis, topic generation | `strategy/CONTEXT.md` |
| `channel/` | Channel identity: voice, style rules, visual guides, reference scripts | No CONTEXT.md |
| `projects/` | Per-video working directories (pipeline outputs) | No CONTEXT.md — each project is a data folder |
