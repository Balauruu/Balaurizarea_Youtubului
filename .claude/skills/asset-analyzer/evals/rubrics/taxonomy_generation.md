# Taxonomy Generation Quality Rubric

Score 1-5 based on how well Claude auto-generates project-specific taxonomy categories.

| Score | Criteria |
|---|---|
| 1 | Generic categories not tailored to project (could apply to any documentary) |
| 2 | Some project-specific categories but mixed with abstract ones ("emotional_weight") |
| 3 | All categories project-specific, but descriptions too vague for CLIP |
| 4 | Project-specific categories with concrete visual descriptions |
| 5 | Categories cover all visual themes in the script, no overlap with global taxonomy, all CLIP-friendly |

**What makes a category CLIP-friendly:**
- Describes physical, visible attributes (not emotions or concepts)
- Uses nouns and adjectives a human would use to describe a photograph
- Short (under 15 words)

**Example good:** "Quebec orphanage exterior, Catholic institution, grey stone building"
**Example bad:** "Institutional oppression and systemic neglect"
