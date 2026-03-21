# Reference Workspace

Stable factory files — configured once, used across every video project. These are Layer 3 (reference material) in the routing architecture.

## What's Here

| Folder | Contents | Used By |
|--------|----------|---------|
| `Architecture.md` | Pipeline architecture: infrastructure stack, parallelism model, Asset Library design, Vector Generation spec, source policy | On-demand reference for system design decisions |
| `voice/WRITTING_STYLE_PROFILE.md` | Channel voice behavioral ruleset (rules, arc templates, transitions) | writer skill |
| `scripts/*.md` | Full reference scripts from existing videos | style-extraction skill (source material) |
| `visuals/VISUAL_STYLE_GUIDE.md` | Visual building blocks, register definitions, equilibrium rules | visual-orchestrator, broll-curator |

## Routing

| Need | Go To |
|------|-------|
| Pipeline architecture, Asset Library, infrastructure | `Architecture.md` |
| Writing voice rules | `voice/WRITTING_STYLE_PROFILE.md` |
| Source material for style extraction | `scripts/` (all .md files) |
| Visual vocabulary and building blocks | `visuals/VISUAL_STYLE_GUIDE.md` |

## Key Principle

These are factory files, not product files. They define HOW to build — voice rules constrain writing style, visual guides constrain shot selection. They don't change per-project. If a future video reference produces a new visual style guide, it goes in `visuals/[Video Name]/VISUAL_STYLE_GUIDE.md`.
