# Phase 2: Query Layer + Competitor Analysis - Research

**Researched:** 2026-03-11
**Domain:** SQLite aggregate queries, CLI subcommand extension, heuristic/deterministic data pipeline
**Confidence:** HIGH

## Summary

Phase 2 adds an `analyze` subcommand to the existing channel-assistant CLI that produces a competitor analysis report at `context/competitors/analysis.md`. The phase splits cleanly into two parts: (1) deterministic Python/SQL for channel stats and outlier detection (DATA-05, ANLZ-01), and (2) heuristic Claude reasoning for topic clustering and title pattern extraction (ANLZ-02, ANLZ-03).

The existing codebase is well-structured with `Database`, `Channel`/`Video` models, and argparse CLI. The main technical challenges are: SQLite lacks a built-in MEDIAN function (must compute in Python), upload frequency requires date-interval arithmetic, and the heuristic portion needs a clean data serialization format that Claude can consume at query time.

**Primary recommendation:** Add an `analyzer.py` module with pure functions for stats/outlier computation, a new `analyze` CLI subcommand that calls these functions, serializes results to a structured format, and writes the final report. The heuristic portions (clustering, patterns) are handled by Claude reading the serialized data -- the Python code only needs to extract and format the data, not perform NLP.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **[DETERMINISTIC]** DATA-05 (channel stats) and ANLZ-01 (outlier detection): Pure Python/SQL computation
- **[HEURISTIC]** ANLZ-02 (topic clustering) and ANLZ-03 (title patterns): Claude reasons over structured data at query time. No NLP libraries.
- Data flow: Code extracts full video lists from SQLite as structured dicts/JSON, Claude receives the full dataset, Claude performs reasoning, Claude writes analysis to file
- Full video list per channel loaded into Claude's context (all titles, views, dates, durations, tags)
- Single comprehensive report written to `context/competitors/analysis.md` with sections: Channel Stats, Outlier Videos, Topic Clusters, Title Patterns
- Overwritten on each full analysis run (latest snapshot, no history)
- ASCII table in markdown for stats (Windows-safe)
- Outliers: single list sorted by performance multiplier (highest first), across all channels; threshold >= 2x channel median
- Topic clusters: two-level hierarchy (Broad theme > specific topics) with saturation assessment using coverage count, recency, and performance
- Title patterns: structural formulas AND emotional hooks, ranked by performance, sample size flagged when <5
- Single `/channel-assistant analyze` subcommand runs all four analyses
- Always analyzes ALL channels; no per-channel or per-analysis-type filtering
- Freshness check: warn if data older than 7 days but never block
- Chat output: brief summary + file path only; full report in file

### Claude's Discretion
- Exact cluster names and hierarchy structure
- How to present saturation levels (scores, labels, or narrative)
- Title pattern categorization taxonomy
- Internal code module structure for the query functions
- Whether to add new database query methods or compose from existing ones

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DATA-05 | Per-channel summary stats: total videos, avg views, median views, upload frequency, most recent upload | Deterministic: new `get_channel_summary_stats()` function computing aggregates from existing `get_videos_by_channel()` data |
| ANLZ-01 | Outlier detection per channel (views >= 2x channel median) with performance multiplier | Deterministic: compute median per channel in Python, filter videos, sort by multiplier |
| ANLZ-02 | Topic clustering with saturation assessment | Heuristic: Python extracts full video dataset as structured text, Claude reasons over it to identify clusters |
| ANLZ-03 | Title pattern extraction from top-performing videos | Heuristic: Python extracts video titles + performance data, Claude identifies structural and emotional patterns |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| sqlite3 (stdlib) | Python 3.14 | Database queries | Already used in Phase 1, zero dependencies |
| statistics (stdlib) | Python 3.14 | Median calculation | `statistics.median()` handles the MEDIAN gap in SQLite |
| datetime (stdlib) | Python 3.14 | Upload frequency calculation | Date parsing and interval arithmetic |
| json (stdlib) | Python 3.14 | Data serialization for Claude context | Already used for tags serialization |
| argparse (stdlib) | Python 3.14 | CLI subcommand | Already used in Phase 1 CLI |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib (stdlib) | Python 3.14 | File path handling | Writing analysis.md output |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| statistics.median() | SQL window functions | SQLite supports window functions but MEDIAN is still not built-in; Python is clearer |
| Plain dict serialization | pandas DataFrames | Massive overkill for 150-500 videos; adds dependency for no benefit |

**Installation:**
```bash
# No installation needed -- all stdlib
```

## Architecture Patterns

### Recommended Project Structure
```
.claude/skills/channel-assistant/scripts/channel_assistant/
    __init__.py
    models.py          # Existing -- no changes needed
    database.py        # Existing -- may add 1-2 query methods
    registry.py        # Existing -- no changes
    scraper.py         # Existing -- no changes
    migrate.py         # Existing -- no changes
    cli.py             # Existing -- add 'analyze' subcommand
    analyzer.py        # NEW -- deterministic stats + outlier computation
```

### Pattern 1: Analyzer as Pure Functions Module
**What:** A new `analyzer.py` module containing pure functions that take Video/Channel lists and return computed results as dicts. No database access inside -- data is passed in.
**When to use:** When computation is separate from data retrieval.
**Example:**
```python
# analyzer.py
import statistics
from datetime import datetime
from .models import Video, Channel


def compute_channel_stats(channel: Channel, videos: list[Video]) -> dict:
    """Compute summary stats for a single channel.

    Returns dict with: total_videos, avg_views, median_views,
    upload_frequency_days, most_recent_upload
    """
    if not videos:
        return {
            "channel_name": channel.name,
            "total_videos": 0,
            "avg_views": 0,
            "median_views": 0,
            "upload_frequency_days": None,
            "most_recent_upload": None,
        }

    view_counts = [v.views for v in videos if v.views is not None]
    avg_views = int(statistics.mean(view_counts)) if view_counts else 0
    median_views = int(statistics.median(view_counts)) if view_counts else 0

    # Upload frequency: average days between uploads
    dates = sorted(
        [datetime.strptime(v.upload_date, "%Y-%m-%d")
         for v in videos if v.upload_date]
    )
    if len(dates) >= 2:
        total_span = (dates[-1] - dates[0]).days
        freq = total_span / (len(dates) - 1)
    else:
        freq = None

    most_recent = max(v.upload_date for v in videos if v.upload_date) if any(v.upload_date for v in videos) else None

    return {
        "channel_name": channel.name,
        "total_videos": len(videos),
        "avg_views": avg_views,
        "median_views": median_views,
        "upload_frequency_days": round(freq, 1) if freq else None,
        "most_recent_upload": most_recent,
    }


def detect_outliers(channel: Channel, videos: list[Video], threshold: float = 2.0) -> list[dict]:
    """Find videos with views >= threshold * channel median views.

    Returns list of dicts sorted by multiplier descending.
    """
    view_counts = [v.views for v in videos if v.views is not None]
    if not view_counts:
        return []

    median = statistics.median(view_counts)
    if median == 0:
        return []

    outliers = []
    for v in videos:
        if v.views is not None and v.views >= threshold * median:
            outliers.append({
                "title": v.title,
                "channel": channel.name,
                "views": v.views,
                "multiplier": round(v.views / median, 1),
                "upload_date": v.upload_date,
            })

    return sorted(outliers, key=lambda x: x["multiplier"], reverse=True)
```

### Pattern 2: CLI Analyze Command -- Deterministic Then Heuristic
**What:** The `analyze` subcommand runs deterministic computations in Python, then outputs structured data for Claude to reason over. The heuristic analysis is NOT done by the Python code.
**When to use:** Per the locked decision -- Claude performs reasoning, code performs computation.
**Example:**
```python
# In cli.py -- cmd_analyze
def cmd_analyze(args, db):
    """Run all analyses and write report."""
    db.init_db()
    channels = db.get_all_channels()
    if not channels:
        print("No channels in database. Run 'scrape' first.")
        return

    # Check freshness
    check_data_freshness(channels, db)

    # Deterministic: compute stats and outliers
    all_stats = []
    all_outliers = []
    all_videos_by_channel = {}

    for ch in channels:
        videos = db.get_videos_by_channel(ch.youtube_id)
        all_stats.append(compute_channel_stats(ch, videos))
        all_outliers.extend(detect_outliers(ch, videos))
        all_videos_by_channel[ch.name] = [
            {"title": v.title, "views": v.views, "upload_date": v.upload_date,
             "duration": v.duration, "tags": v.tags}
            for v in videos
        ]

    all_outliers.sort(key=lambda x: x["multiplier"], reverse=True)

    # Write deterministic sections (stats table, outlier list)
    # Write video data for heuristic consumption
    # Output path and summary to stdout
```

### Pattern 3: Data Serialization for Heuristic Consumption
**What:** Full video dataset serialized as structured text that Claude reads to perform topic clustering and title pattern analysis. Written to a scratch file or embedded in the analysis report.
**When to use:** Bridging deterministic data extraction with heuristic Claude reasoning.
**Key insight:** The video data for ANLZ-02 and ANLZ-03 needs to be formatted so Claude can reason over it. Two options:

**Option A (Recommended): All-in-one report generation**
The `analyze` command writes the deterministic sections (stats, outliers) directly to `analysis.md`, then writes the full video dataset to `.claude/scratch/video_data.json`. The command prints instructions telling Claude to read the scratch file and complete the heuristic sections of the report.

**Option B: Two-pass in CLI**
The CLI writes a complete draft report with the deterministic sections filled in and placeholder markers for heuristic sections. Claude fills in the placeholders.

Recommend Option A -- cleaner separation, and the scratch pad convention is already established.

### Anti-Patterns to Avoid
- **Don't import NLP libraries for clustering:** The decision is locked -- Claude does the reasoning, not scikit-learn or NLTK
- **Don't compute median in SQL:** SQLite has no MEDIAN aggregate function. Use Python's `statistics.median()`
- **Don't create separate analysis commands per type:** One `analyze` command runs everything
- **Don't store analysis results in the database:** Output is a markdown file, not a DB table
- **Don't make the Python code generate cluster names or pattern labels:** That is Claude's job

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Median calculation | Custom sorting + middle element | `statistics.median()` | Handles odd/even lists, single elements correctly |
| Upload frequency | Manual date subtraction | `datetime.strptime()` + timedelta arithmetic | Handles edge cases (single video, missing dates) |
| View formatting | Custom number formatting | f-string with `:,` format spec | `f"{views:,}"` gives "1,234,567" |
| ASCII tables | Custom spacing logic | Simple f-string alignment | `f"{'col':<20}"` -- no library needed for this scale |

**Key insight:** This phase is deliberately simple in terms of libraries. The complexity is in the heuristic reasoning (Claude's job), not the code.

## Common Pitfalls

### Pitfall 1: Median of Zero-View Videos
**What goes wrong:** Videos with 0 or None views skew median to 0, making every video an "outlier" at infinity multiplier.
**Why it happens:** Some videos may have None views if yt-dlp failed to fetch them.
**How to avoid:** Filter out None views before computing median. If median is 0, return empty outlier list.
**Warning signs:** Every video appearing as an outlier.

### Pitfall 2: Division by Zero in Multiplier
**What goes wrong:** If channel median is 0, computing `views / median` raises ZeroDivisionError.
**Why it happens:** Channel with all zero-view videos or no videos.
**How to avoid:** Guard clause: `if median == 0: return []`
**Warning signs:** Crash on `detect_outliers()` call.

### Pitfall 3: Upload Frequency with Single Video
**What goes wrong:** Cannot compute upload frequency with only 1 video (no intervals).
**Why it happens:** New or rarely-uploading channel.
**How to avoid:** Return None for upload_frequency when `len(dates) < 2`.
**Warning signs:** Division by zero or misleading "0 days" frequency.

### Pitfall 4: Date Parsing Inconsistencies
**What goes wrong:** `upload_date` format may vary (some "YYYYMMDD", some "YYYY-MM-DD").
**Why it happens:** yt-dlp returns dates in "YYYYMMDD" format by default, but the scraper may have normalized them.
**How to avoid:** Check the actual data in the database. The scraper stores `upload_date` from yt-dlp's `upload_date` field. Need to verify the format.
**Warning signs:** `ValueError` on `datetime.strptime()`.

### Pitfall 5: Windows Encoding in Report Output
**What goes wrong:** Video titles with non-ASCII characters (accents, special chars) cause encoding errors when writing to file.
**Why it happens:** Windows default encoding is cp1252, not UTF-8.
**How to avoid:** Always open files with `encoding="utf-8"` when writing `analysis.md`.
**Warning signs:** `UnicodeEncodeError` on write.

### Pitfall 6: Large Context for Heuristic Analysis
**What goes wrong:** With many channels and videos, the full video dataset could exceed practical context limits.
**Why it happens:** User decision says "full video list per channel" -- 3-5 channels at 50-100 videos = 5-15k tokens, which is fine.
**How to avoid:** At current scale (3-5 channels, 50-100 videos each), this is not a problem. If scale grows, truncate to most recent N videos per channel.
**Warning signs:** Context exceeding 15k tokens for video data alone.

## Code Examples

### Computing Median Views (stdlib)
```python
# Source: Python stdlib statistics module
import statistics

view_counts = [v.views for v in videos if v.views is not None]
median = statistics.median(view_counts)  # Returns float for even-length lists
median_int = int(median)  # Round down for display
```

### Upload Frequency Calculation
```python
from datetime import datetime

dates = sorted([
    datetime.strptime(v.upload_date, "%Y%m%d")  # or "%Y-%m-%d" -- verify format
    for v in videos
    if v.upload_date
])

if len(dates) >= 2:
    total_span = (dates[-1] - dates[0]).days
    avg_frequency_days = total_span / (len(dates) - 1)
else:
    avg_frequency_days = None
```

### Freshness Check
```python
from datetime import datetime, timedelta

def check_data_freshness(channels, db):
    """Warn if any channel data is older than 7 days."""
    cutoff = datetime.now() - timedelta(days=7)
    stale = []
    for ch in channels:
        stats = db.get_channel_stats(ch.youtube_id)
        if stats["last_scraped"]:
            scraped_dt = datetime.fromisoformat(stats["last_scraped"].replace("Z", "+00:00"))
            if scraped_dt.replace(tzinfo=None) < cutoff:
                stale.append(ch.name)
    if stale:
        print(f"Warning: Data for {', '.join(stale)} is older than 7 days.")
        print("Run: python .claude/skills/channel-assistant/scripts/channel_assistant/cli.py scrape")
```

### ASCII Stats Table Output
```python
def format_stats_table(all_stats: list[dict]) -> str:
    """Format channel stats as ASCII markdown table."""
    lines = []
    name_w = max(len(s["channel_name"]) for s in all_stats)
    name_w = max(name_w, len("Channel"))

    header = (
        f"{'Channel':<{name_w}}  "
        f"{'Videos':>6}  "
        f"{'Avg Views':>12}  "
        f"{'Median Views':>12}  "
        f"{'Upload Freq':>11}  "
        f"{'Latest Upload':>13}"
    )
    lines.append(header)
    lines.append("-" * len(header))

    for s in all_stats:
        freq = f"{s['upload_frequency_days']:.0f}d" if s["upload_frequency_days"] else "n/a"
        lines.append(
            f"{s['channel_name']:<{name_w}}  "
            f"{s['total_videos']:>6}  "
            f"{s['avg_views']:>12,}  "
            f"{s['median_views']:>12,}  "
            f"{freq:>11}  "
            f"{s['most_recent_upload'] or 'n/a':>13}"
        )

    return "\n".join(lines)
```

### Video Data Serialization for Heuristic Analysis
```python
def serialize_videos_for_analysis(all_videos_by_channel: dict) -> str:
    """Serialize video data for Claude to reason over.

    Returns structured text with all video metadata per channel.
    """
    sections = []
    for channel_name, videos in all_videos_by_channel.items():
        lines = [f"### {channel_name} ({len(videos)} videos)"]
        for v in sorted(videos, key=lambda x: x.get("views") or 0, reverse=True):
            views_str = f"{v['views']:,}" if v.get("views") else "n/a"
            tags_str = ", ".join(v.get("tags") or [])
            lines.append(
                f"- \"{v['title']}\" | {views_str} views | {v.get('upload_date', 'n/a')} | tags: [{tags_str}]"
            )
        sections.append("\n".join(lines))

    return "\n\n".join(sections)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SQLite PERCENTILE extension | Python statistics.median() | N/A | No external SQLite extensions needed |
| NLP-based topic clustering | LLM reasoning over structured data | 2024+ | Dramatically simpler code, better semantic understanding |
| Regex-based title pattern extraction | LLM pattern recognition | 2024+ | Catches nuanced patterns regex would miss |

**Key insight for this phase:** The "state of the art" for topic clustering and pattern extraction in an LLM-orchestrated system is to NOT write NLP code. Let the LLM do what it does best. The Python code's job is purely data extraction and formatting.

## Open Questions

1. **Upload date format in database**
   - What we know: yt-dlp returns `upload_date` in YYYYMMDD format by default
   - What's unclear: Whether the scraper normalizes to YYYY-MM-DD before storing
   - Recommendation: Check actual data in the database during implementation. Handle both formats with a try/except on `strptime`.

2. **Report generation flow for heuristic sections**
   - What we know: Python writes deterministic sections, Claude fills heuristic sections
   - What's unclear: Exact mechanism -- does the `analyze` command invoke Claude, or does it prepare data and the user/skill invokes Claude separately?
   - Recommendation: Per Architecture.md ("Claude Code itself is the orchestrator"), the `analyze` CLI command should: (1) compute deterministic stats/outliers, (2) write them to the report file, (3) write full video data to `.claude/scratch/`, (4) print summary + instructions. The channel-assistant skill then reads the scratch data and completes the heuristic sections using Claude reasoning. This keeps the Python code deterministic and the skill orchestration heuristic.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | none -- pytest runs from project root |
| Quick run command | `python -m pytest tests/test_channel_assistant/ -x -q` |
| Full suite command | `python -m pytest tests/test_channel_assistant/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-05 | Channel stats computation (avg, median, frequency) | unit | `python -m pytest tests/test_channel_assistant/test_analyzer.py::TestComputeChannelStats -x` | No -- Wave 0 |
| DATA-05 | Stats table formatting | unit | `python -m pytest tests/test_channel_assistant/test_analyzer.py::TestFormatStatsTable -x` | No -- Wave 0 |
| ANLZ-01 | Outlier detection with 2x threshold | unit | `python -m pytest tests/test_channel_assistant/test_analyzer.py::TestDetectOutliers -x` | No -- Wave 0 |
| ANLZ-01 | Outlier edge cases (zero median, no videos) | unit | `python -m pytest tests/test_channel_assistant/test_analyzer.py::TestDetectOutliersEdgeCases -x` | No -- Wave 0 |
| ANLZ-02 | Video data serialization for clustering | unit | `python -m pytest tests/test_channel_assistant/test_analyzer.py::TestSerializeVideos -x` | No -- Wave 0 |
| ANLZ-03 | Video data serialization for patterns | unit | Same as ANLZ-02 (shared serialization) | No -- Wave 0 |
| ANLZ-02 | Topic clustering output correctness | manual-only | Claude reasoning quality -- verified by reading analysis.md | N/A |
| ANLZ-03 | Title pattern output correctness | manual-only | Claude reasoning quality -- verified by reading analysis.md | N/A |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_channel_assistant/ -x -q`
- **Per wave merge:** `python -m pytest tests/test_channel_assistant/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_channel_assistant/test_analyzer.py` -- covers DATA-05, ANLZ-01, data serialization
- [ ] Update `tests/test_channel_assistant/conftest.py` -- add multi-channel, multi-video fixtures with varied view counts for stats/outlier testing

## Sources

### Primary (HIGH confidence)
- Existing codebase: `database.py`, `models.py`, `cli.py` -- direct code inspection
- Python stdlib docs: `statistics.median()`, `datetime.strptime()` -- well-established APIs
- Phase 2 CONTEXT.md -- locked user decisions

### Secondary (MEDIUM confidence)
- yt-dlp upload_date format: known from yt-dlp conventions (YYYYMMDD default), but should verify against actual stored data

### Tertiary (LOW confidence)
- None -- this phase uses only stdlib Python, no external libraries to verify

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all stdlib Python, no external dependencies, well-understood APIs
- Architecture: HIGH -- extends existing patterns (argparse subcommand, Database queries, pure functions)
- Pitfalls: HIGH -- identified from direct code inspection (nullable fields, zero-division, encoding)

**Research date:** 2026-03-11
**Valid until:** 2026-04-11 (stable -- stdlib only, no moving targets)
