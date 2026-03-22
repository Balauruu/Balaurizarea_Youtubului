# Search Query Generation — [HEURISTIC]

Build web search queries to find visual media (photos, documents, screenshots) for a documentary. Your inputs are `entity_index.json` (structured proper nouns) and `Research.md` (narrative context).

## Strategy: Entity Cross-Products

Single-entity searches return obvious results. **Cross-product queries combine entities from different categories** to surface less-discovered media.

### Cross-product patterns

| Combination | Pattern |
|-------------|---------|
| Person + Institution | `"[person]" "[institution]" photo` |
| Person + Role/Title | `"[person]" [role] portrait` |
| Institution + Time Period | `"[institution]" [decade] photo` |
| Location + Event | `"[location]" "[event]" historical` |
| Event + Date | `"[event]" [year] photo OR document` |
| Institution + Location | `"[institution]" "[location]" photo` |

### Category-specific templates

- **Persons:** `"[full name]" portrait OR photo`, `"[full name]" interview OR testimony`
- **Institutions:** `"[institution]" building OR historical`, `"[institution]" [location] [decade]`
- **Locations:** `"[location]" historical photo [decade]`, `"[location]" aerial OR map`
- **Events:** `"[event]" [year] newspaper OR coverage`, `"[event]" protest OR hearing photo`

## Volume & Coverage

- **15-30 queries** per topic
- Prioritize cross-products over single-entity queries
- Cover at least 3 of 5 entity categories (persons, institutions, locations, events, dates)
- Include 2-3 screenshot-targeted queries (government reports, newspaper front pages)

## Output

Return a numbered query list grouped by strategy: cross-products first, category-specific second, screenshot-targeted last. Each query should be search-engine-ready.

