# Visual Style Extractor — Stage Contract

Extract visual patterns from a reference video into a reusable decision framework.

## Inputs
| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Video | YouTube URL or local video + transcript | Full file | Source material for analysis |
| Analysis prompt | prompts/analysis_prompt.txt | Full file | Frame-to-pattern analysis rules |
| Synthesis prompt | prompts/synthesis_prompt.txt | Full file | Pattern merging into building blocks |

## Process
1. [DETERMINISTIC] Stage 0: Acquire video + transcript (yt-dlp or local)
2. [DETERMINISTIC] Stage 1: Scene detection → keyframes + scenes.json
3. [DETERMINISTIC] Stage 2: Perceptual hash deduplication → deduplicated frames
4. [DETERMINISTIC] Stage 3: Transcript alignment → frames with narration context
5. [DETERMINISTIC] Stage 4: Contact sheet generation → 3×3 grids (1568×1568px)
6. [HEURISTIC] Stage 5: Parallel subagents analyze contact sheets → pattern JSON batches
7. [DETERMINISTIC] Merge analysis batches → merged_analysis.json
8. [HEURISTIC] Stage 6: Synthesis subagent → VISUAL_STYLE_GUIDE.md

## Checkpoints
| After Step | Agent Presents | Human Decides |
|------------|---------------|---------------|
| Step 5 (Stages 0-4) | Scene count, frame count, dedup ratio | Accept or adjust thresholds |
| Step 8 (Stage 6) | Building block count + path to guide | Review guide, re-run if needed |

## Outputs
| Artifact | Location | Format |
|----------|----------|--------|
| Visual style guide | context/visual-references/[Video]/VISUAL_STYLE_GUIDE.md | 10-15 building blocks |
| Frames manifest | context/visual-references/[Video]/frames_manifest.json | Frame metadata |
| Contact sheets | context/visual-references/[Video]/contact_sheets/ | 3×3 grid JPEGs |
| Dedup report | context/visual-references/[Video]/dedup_report.json | Merge decisions |
