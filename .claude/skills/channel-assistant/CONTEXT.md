# Channel Assistant — Stage Contract

Select viable topics and initialize video projects for the dark mysteries channel.

## Inputs
| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Channel DNA | context/channel/channel.md | "Core Content Pillars", "Topic Selection Criteria" | Topic filtering rules |
| Past topics | context/channel/past_topics.md | Full file | Deduplication safety |
| Competitor data | context/competitors/analysis.md | Full file | Topic clusters, title patterns, outliers |
| Prompt | prompts/topic_generation.md | Full file | Scoring rubric |
| Prompt | prompts/trends_analysis.md | Full file | Content gap scoring |
| Prompt | prompts/project_init.md | Full file | Title/description generation |

## Process
1. [DETERMINISTIC] `scrape` — refresh competitor video data from YouTube
2. [DETERMINISTIC] `analyze` — compute stats, outliers, trend scan → write analysis.md
3. [HEURISTIC] Claude completes Topic Clusters + Title Patterns in analysis.md
4. [DETERMINISTIC] `topics` — load context for topic generation
5. [HEURISTIC] Claude generates 5 scored briefs → writes topic_briefs.md
6. [DISPLAY] Claude outputs formatted markdown cards in chat
7. User selects topic number
8. [HEURISTIC] Claude generates title variants + description
9. [DETERMINISTIC] `init_project()` → creates project directory + metadata.md

## Checkpoints
| After Step | Agent Presents | Human Decides |
|------------|---------------|---------------|
| Step 6 | 5 scored topic cards with briefs | Which topic to pursue (or regenerate) |
| Step 8 | 3-5 title variants + YouTube description | Final title for project init |

## Outputs
| Artifact | Location | Format |
|----------|----------|--------|
| Competitor analysis | context/competitors/analysis.md | Stats, outliers, clusters |
| Topic briefs | context/topics/topic_briefs.md | 5 scored briefs |
| Project metadata | projects/N. [Title]/metadata.md | Title variants, description, brief |
