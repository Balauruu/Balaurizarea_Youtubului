# IA Search Query Generation — [HEURISTIC]

Translate a single `broll_theme` object into effective Internet Archive Advanced Search queries.

## Input

A single broll_theme object from `shotlist.json`:

```json
{
  "id": "T1",
  "concept": "Institutional confinement",
  "mood": "oppressive, cold, bureaucratic",
  "search_direction": "Institutional interiors, dormitories, long corridors, regimented environments",
  "cartoon_angle": "Characters trapped, confined spaces, authority figures looming"
}
```

## Curated IA Collection List

These are verified, active collections the agent should target. The agent cannot discover collections dynamically — use only from this list:

| Collection ID | Contents | Best For |
|--------------|----------|----------|
| `prelinger` | Prelinger Archives — industrial, educational, institutional films (1920s-1980s) | Atmospheric footage: factories, schools, hospitals, public health, institutional life |
| `19201928publicdomainanimation` | 1920s public domain animation | Early cartoon footage matching `cartoon_angle` themes |
| `classic_cartoons` | Classic cartoon collection (various decades) | Broader cartoon/animation matching |
| `stock_footage` | Stock footage collection (public domain) | General atmospheric b-roll — cityscapes, nature, industry |
| `newsandpublicaffairs` | News and public affairs footage | Documentary-style footage, press conferences, public events |
| `feature_films` | Feature films (public domain) | Dramatic footage, establishing shots, atmospheric sequences |

## Query Construction Rules

### Filters (always include)
- **`mediatype:(movies)`** — restricts results to video content. Always include this filter.
- **`collection:(name)`** — targets a specific collection from the list above. Vary collection across queries for diversity.

### Keyword Strategy
- **Derive from `search_direction`** — break compound descriptions into individual search terms. "Institutional interiors, dormitories, long corridors" → `institutional`, `dormitory`, `corridor`, `factory`.
- **For cartoon themes** — use keywords from `cartoon_angle` plus animation/cartoon collections (`19201928publicdomainanimation`, `classic_cartoons`).
- **For atmospheric themes** — use keywords from `search_direction` plus `prelinger` and `stock_footage` collections.
- **Use OR for keyword variants** — `(institutional OR factory OR dormitory)` catches more results than requiring all terms.
- **Use the `subject:` field** — IA items have subject tags. `subject:(corridor OR industrial)` searches these tags specifically.

### Critical: Metadata-Only Search
IA search indexes item **titles, descriptions, and subjects** — NOT video frame content. Query for what items are *about*, not what they visually contain. A film titled "Industrial Safety" is findable; a random shot of a corridor inside that film is not.

### Conceptual Matching
The match is **metaphorical, not literal**. The theme's mood and concept drive the search, not the documentary's specific subject.

- "Institutional confinement" → search for factory footage, dormitory footage, military barracks — NOT "orphanage"
- "Bureaucratic control" → search for office films, government training films, filing systems — NOT the specific government agency in the documentary
- "Isolation" → search for empty landscapes, single figures, institutional solitude — NOT the specific person being discussed

### Query Count
Build **2-4 queries per theme**, varying:
- Collection (try at least 2 different collections per theme)
- Keywords (alternate between `search_direction`-derived and `cartoon_angle`-derived terms)
- Search field (`title/description` default vs. `subject:` field)

## Example

Given theme:
```json
{
  "id": "T1",
  "concept": "Institutional confinement",
  "mood": "oppressive, cold, bureaucratic",
  "search_direction": "Institutional interiors, dormitories, long corridors, regimented environments",
  "cartoon_angle": "Characters trapped, confined spaces, authority figures looming"
}
```

Generate queries:
```
mediatype:(movies) AND collection:(prelinger) AND (institutional OR factory OR dormitory)
mediatype:(movies) AND collection:(prelinger) AND subject:(corridor OR industrial OR regimented)
mediatype:(movies) AND collection:(classic_cartoons) AND (trapped OR confined OR authority)
mediatype:(movies) AND collection:(stock_footage) AND (institution OR corridor OR barracks)
```

## Output

Return all generated queries as a list. The calling process will execute each query via `ia.search_items(query)` and collect results.
