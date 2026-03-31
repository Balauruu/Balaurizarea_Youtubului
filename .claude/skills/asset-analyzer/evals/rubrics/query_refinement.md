# Query Refinement Quality Rubric

Score 1-5 based on how well Claude rephrases abstract queries into CLIP-friendly visual descriptions.

| Score | Criteria |
|---|---|
| 1 | Refined query is still abstract or synonymous with original |
| 2 | Slightly more concrete but still not CLIP-friendly (uses emotional/conceptual language) |
| 3 | Concrete visual description, single attempt, no variation |
| 4 | Multiple concrete alternatives, varied visual angles |
| 5 | Alternatives span different visual interpretations, all CLIP-friendly, progressive refinement |

**Red flags (automatic -1):**
- Refined query uses cinematographer language ("slow dolly", "shallow depth of field")
- Refined query is longer than 20 words (CLIP works best with short descriptions)
- All alternatives are synonymous (no actual variation)
