# Score Interpretation Guide

## Cosine Similarity Ranges

CLIP-family models (including PE-Core) produce cosine similarities in roughly [-1, 1], but in practice text-image scores cluster in [0.05, 0.40].

| Score | Meaning | Action |
|-------|---------|--------|
| > 0.30 | Strong match | Use directly |
| 0.25 - 0.30 | Good match | Top 1 candidate per shot |
| 0.15 - 0.25 | Ambiguous | Send top 3 to Claude review |
| < 0.15 | Weak/no match | Skip, or trigger query refinement |

## Content Type Effects

- **Live-action footage** tends to score higher (0.20-0.35 for good matches)
- **Cartoon/animated content** scores lower across the board (~0.15-0.28)
- **Abstract concepts** ("bureaucratic menace") score very low - rephrase to concrete visuals

## Query Refinement

When peak score < 0.20, the query is likely too abstract. Claude rephrases without viewing frames:
- Bad: "The psychological weight of institutional confinement"
- Good: "Empty corridor with rows of closed doors in dim lighting"

## Threshold Calibration

Starting thresholds (0.25/0.15) and boundary percentile (90th) are adjusted via the evaluation framework. After running `evaluate.py`, follow the calibration suggestions to tune for your footage mix.
