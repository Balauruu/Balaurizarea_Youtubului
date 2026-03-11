# Trends Analysis Prompt

You have YouTube autocomplete suggestions, search results, and 30-day competitor video data
printed above by `cmd_trends()`. Perform three analyses and write the results.

---

## 1. Content Gap Detection (ANLZ-05)

Compare autocomplete suggestion breadth (more suggestions = higher demand signal) against
competitor coverage (how many of our tracked competitors have videos matching each keyword cluster).

For each gap:
- **Keyword/cluster**: The topic area
- **Demand signal**: Number of autocomplete suggestions (more = broader search interest)
- **Competitor coverage**: How many tracked competitors have published on this topic (0-2 = underserved)
- **Performance indicator**: If any competitor DID cover it, how did those videos perform vs their
  channel median? (use outlier data from analysis.md if available)
- **Composite score**: demand x opportunity. High demand + low coverage + strong performance when
  covered = highest score

Output as ranked list, highest composite score first.
Gap threshold: 0-2 competitors covering a topic = "underserved" (use your judgment based on total
competitor count).

---

## 2. Trending Topics (ANLZ-06)

From search results, identify topics with recent upload dates (look at published_text:
"X days ago", "X weeks ago"). Cross-reference with competitor video database to find which
results are from channels in our niche.

List the most timely/relevant topics, noting:
- Topic/title
- How many channels are covering it recently
- Estimated recency (from published_text)
- Relevance to our content pillars

---

## 3. Convergence Alerts (ANLZ-07)

From the 30-day competitor video list, identify topic clusters where 3+ different competitor
channels published videos within the 30-day window. Use the Topic Clusters from analysis.md
to define adjacency.

For each convergence:
- **Cluster**: The topic area
- **Channels involved**: Which competitors (3+ required)
- **Video titles**: The specific videos
- **Signal strength**: Is this cluster ALSO showing up in YouTube search trends?
  (cross-reference search results)
- **Framing**: Based on the data, frame as one of:
  - **Opportunity** — trending + underserved by us
  - **Saturation warning** — oversaturated + declining signals
  - **Neutral flag** — trending but unclear opportunity

---

## Output Format

After completing all three analyses, call `update_analysis_with_trends()` to write results
to `context/competitors/analysis.md`:

```python
from pathlib import Path
from channel_assistant.trend_scanner import update_analysis_with_trends

update_analysis_with_trends(
    analysis_path=Path("context/competitors/analysis.md"),
    trending_md="## Trending Topics\n\n...",
    gaps_md="## Content Gaps\n\n...",
    convergence_md="## Convergence Alerts\n\n...",
)
```

Then print to chat:

**Top 3 Content Gaps** (brief inline summary per gap):
- Keyword/cluster | demand signal | competitor coverage | composite score

**Convergence Alerts** (if any):
- Cluster | channels involved | framing (Opportunity / Saturation warning / Neutral flag)

**File updated:** `context/competitors/analysis.md`
