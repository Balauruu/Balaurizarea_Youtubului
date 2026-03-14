# Researcher — Stage Contract

Build a factual foundation for a documentary topic through two-pass web research.

## Inputs
| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Project | projects/N. [Title]/metadata.md | "Topic Brief" section | Topic scope and angle |
| Channel DNA | context/channel/channel.md | "Core Content Pillars" | Depth and tone calibration |
| Prompt | prompts/survey_evaluation.md | Full file | Source evaluation rubric |
| Prompt | prompts/synthesis.md | Full file | 9-section dossier template |

## Process
1. [DETERMINISTIC] `survey "Topic"` — fetch Wikipedia + DuckDuckGo → `src_NNN.json`
2. [HEURISTIC] Evaluate sources using survey_evaluation.md → annotate `source_manifest.json`
3. [DETERMINISTIC] `deepen "Topic"` — fetch deep-dive URLs from manifest → `pass2_NNN.json`
4. [DETERMINISTIC] `write "Topic"` — aggregate all sources → `synthesis_input.md`
5. [HEURISTIC] Synthesize using synthesis.md → `Research.md` + `media_urls.md`

## Checkpoints
| After Step | Agent Presents | Human Decides |
|------------|---------------|---------------|
| Step 2 | Source verdict summary table | Proceed to deep dive, add/remove sources, or redirect |
| Step 5 | Research.md summary (sections + word count) | Accept, request revisions, or add missing sources |

## Audit (after Step 5, before writing final output)
| Check | Pass Condition |
|-------|---------------|
| Source diversity | ≥3 distinct source domains cited |
| Timeline populated | Timeline section has ≥5 dated entries |
| Contradictions addressed | Section 7 is non-empty OR explicitly states "no contradictions found" |
| Media inventory | ≥5 media URLs cataloged in media_urls.md |
| No fabrication | Every claim in Subject Overview traces to a source in Sections 4-5 |

## Outputs
| Artifact | Location | Format |
|----------|----------|--------|
| Research dossier | projects/N. [Title]/research/Research.md | 9-section markdown (~2000 words) |
| Media catalog | projects/N. [Title]/research/media_urls.md | URLs grouped by asset type |
| Source manifest | projects/N. [Title]/research/source_manifest.json | Verdicts + deep-dive URLs |
