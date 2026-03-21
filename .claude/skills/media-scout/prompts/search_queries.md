# Search Query Generation — [HEURISTIC]

You are building web search queries to find visual media (photos, documents, screenshots) for a documentary. Your input is `entity_index.json` (structured proper nouns) and `Research.md` (narrative context).

## Strategy: Entity Cross-Products

Single-entity searches ("Duplessis Orphans photo") return obvious results everyone has seen. **Cross-product queries combine entities from different categories** to surface oblique, less-discovered media.

### Cross-product combinations

Build queries by pairing entities across categories:

| Combination | Pattern | Example |
|-------------|---------|---------|
| Person + Institution | `"[person]" "[institution]"` | `"Maurice Duplessis" "Union Nationale"` |
| Person + Role/Title | `"[person]" [role] photo` | `"Daniel Jacoby" ombudsman Quebec` |
| Institution + Time Period | `"[institution]" [decade] photo` | `"Mont Providence" 1950s orphanage photo` |
| Location + Event | `"[location]" "[event]"` | `"Baie-Saint-Paul" psychiatric institution historical` |
| Event + Date | `"[event]" [year]` | `"Quebec orphan commission" 1999 apology` |
| Institution + Location | `"[institution]" "[location]"` | `"Grey Nuns" Montreal orphanage` |

### Worked example — Duplessis Orphans entity_index.json

Given:
- **persons:** Maurice Duplessis, Daniel Jacoby, Lucien Bouchard, Hervé Bertrand...
- **institutions:** Catholic Church, Grey Nuns of Montreal, Union Nationale, Law Commission of Canada...
- **locations:** Montreal, Baie-Saint-Paul, Mount Providence orphanage, Huberdeau...
- **events:** Bedard Commission, Federal-Provincial Conference on Orphanages...
- **dates:** 1940, 1954, 1999...

Generate queries like:
1. `"Mount Providence orphanage" children 1950s photo`
2. `"Grey Nuns of Montreal" orphanage historical`
3. `"Maurice Duplessis" premier Quebec portrait`
4. `"Duplessis Orphans" protest 1999` (event + date cross-product)
5. `"Baie-Saint-Paul" psychiatric institution 1950s`
6. `"Hervé Bertrand" Duplessis orphan survivor`
7. `"Lucien Bouchard" apology orphans 1999`
8. `Quebec orphanage "Catholic Church" historical photo`
9. `"Bedard Commission" 1962 psychiatric report`
10. `"Law Commission of Canada" institutional child abuse report`

## Category-Specific Query Templates

### Persons
- `"[full name]" portrait OR photo OR mugshot`
- `"[full name]" [known role or title]`
- `"[full name]" interview OR testimony` (for survivors/witnesses)

### Institutions
- `"[institution name]" building OR exterior OR historical`
- `"[institution name]" [location] photo`
- `"[institution name]" [decade] conditions OR report`

### Locations
- `"[location]" historical photo [decade]`
- `"[location]" aerial OR map [time period]`
- `"[location]" [associated institution] photo`

### Events
- `"[event name]" [year] photo OR document`
- `"[event name]" newspaper OR coverage`
- `"[event name]" protest OR ceremony OR hearing`

### Dates/Periods
- Use date ranges to narrow results: `[topic] [year1]..[year2]`
- Combine with events: `[event] [year] photo`

## Screenshot Guidance

**Take screenshots of document-like pages:**
- Newspaper articles with distinctive layouts or headlines
- Government reports, commission findings, official documents
- Wikipedia sections with well-structured timelines or info boxes
- Court documents, legal filings with visible headers

**Do NOT screenshot pages where embedded images are the real asset:**
- Encyclopedia articles with inline photos → extract the image URLs instead
- Photo galleries → extract individual image URLs
- News articles where the header photo is the valuable content → extract the image

**Rule of thumb:** If the *page layout itself* conveys information (a newspaper front page, a government letterhead, a timeline), screenshot it. If the page is just a container for images, extract the images.

## License Signal Heuristics

Do not fabricate license information. Note the signal and let the human review:

| Source Type | Signal | Note |
|-------------|--------|------|
| Government sites (.gc.ca, .gouv.qc.ca) | Likely public domain (Crown copyright / PD-Canada) | Verify on the specific page |
| News sites (cbc.ca, radio-canada.ca) | Fair dealing review needed | News reporting context may support fair dealing |
| Wikimedia Commons | Check individual file page | Each file has its own license — do not assume |
| Academic/research sites | Varies — check page footer | Often CC-BY or restricted |
| Personal blogs, memorial sites | Unknown — flag for review | May contain rights-holder content |
| Social media | Skip entirely | Rights unclear, quality low |

## Query Volume

- Aim for **15-30 queries** per topic
- Prioritize cross-product queries over single-entity queries
- Cover at least 3 of the 5 entity categories
- Include at least 2-3 screenshot-targeted queries (government reports, newspaper articles)

## Output

Return the query list as a simple numbered list. Each query should be a search-engine-ready string. Group by strategy (cross-products first, then category-specific, then screenshot-targeted).
