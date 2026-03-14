# Topic Generation Prompt

## Role and Objective

You are generating topic briefs for a dark mysteries YouTube documentary channel. Your task is to produce **5** scored topic candidates, ranked by total score descending, that the channel owner can evaluate and select from.

The channel targets a 22-38 audience that values intellectual depth, obscure documented history, and narratives most people have never encountered. You must combine three input sources — competitor gap analysis, channel DNA pillars, and live web research — to surface the strongest possible candidates.

---

## Input Context

The following sections contain the data you will reason over:

### Competitor Analysis Data

{analysis_content}

*This is the output of the Phase 2 competitor analysis. Pay attention to the Topic Clusters section — underserved clusters (Saturation: Underserved) are priority generation targets. Also note outlier videos, which reveal what topics actually perform well in this niche.*

### Channel DNA

{channel_dna_content}

*This is the channel's identity document. Ensure every generated topic fits at least one of the five content pillars and passes the topic selection criteria (at least 3 of 4: Obscurity, Complexity, Shock Factor, Verifiable).*

### Past Topics (Deduplication List)

{past_topics_list}

*These topics have already been covered. Near-duplicates must be tagged with "Similar to: [past topic]" — do NOT silently drop them. A different angle on the same subject is allowed, but must be flagged.*

---

## Content Pillars Reference

Every topic must be assigned to one of these five pillars:

1. **Obscure Historical Crimes** — Real events buried by time. Unknown to mainstream audiences. High shock factor when revealed.
2. **Cults & Psychological Control** — Groups, ideologies, or figures that bent reality for followers. Strong visual and narrative potential.
3. **Unsolved Disappearances & Mysteries** — Cases with no clean resolution. Ambiguity is a feature, not a bug.
4. **Institutional Corruption & Cover-ups** — Governments, corporations, and investigations that failed deliberately.
5. **Dark Web & Internet Underbelly** — Digital crimes, underground communities, and online phenomena with real-world consequences.

---

## Anchored Scoring Rubric

**CRITICAL:** Every score you assign MUST reference these anchor examples. Do not score from abstract intuition — compare the candidate topic to the anchors at each level.

### Dimension 1: Obscurity (1–5)

How little-known is this topic to a mainstream audience? How saturated is this topic across YouTube documentary channels?

| Score | Meaning | Anchor Examples |
|-------|---------|----------------|
| 1 | Covered by 50+ channels; mainstream cultural awareness; every true crime fan knows it | Jack the Ripper, Zodiac Killer, Ted Bundy |
| 2 | Covered by 10-20 channels; true crime literate audience knows it; appears in Netflix docs | Heaven's Gate, Jonestown, BTK Killer |
| 3 | Covered by 2-5 niche channels; requires active interest in the genre to have encountered it | Matamoros cult (pre-viral), the Delphi murders, NXIVM early coverage |
| 4 | Covered by 1 channel or none in English; known only to researchers or regional audiences | Mesa Verde ritual site controversies, the Skidmore Missouri lynching |
| 5 | Zero English documentary treatment; requires original research; general audience has zero awareness | Obscure regional cults with no translation, non-English historical crimes buried in local archives |

### Dimension 2: Complexity (1–5)

How many intersecting layers does the story have? How much context does the audience need to understand the full picture?

| Score | Meaning | Anchor Examples |
|-------|---------|----------------|
| 1 | Single actor, single event, clear linear motive; no background needed | Standard robbery-homicide case, single-perpetrator crime of passion |
| 2 | One layer of context needed; simple belief system or single institutional failure | Single-perpetrator cult with simple ideology, one corrupt official acting alone |
| 3 | Multiple actors, institutional failure, OR contested facts requiring explanation | Jonestown (requires Cold War and CIA context), early internet crimes with sociological layer |
| 4 | Multiple actors + institutional cover-up + contested narrative; audience must track parallel threads | COINTELPRO church bombing cases, multi-agency cover-up with political dimension |
| 5 | Requires understanding 3+ intersecting systems (legal, cultural, political, religious, historical) simultaneously | Iran-Contra with cult dimensions, cartel-religion-state intersections across multiple countries |

### Dimension 3: Shock Factor (1–5)

What is the emotional impact ceiling? Does the story contain a detail, revelation, or twist that genuinely disturbs a calm, informed adult?

| Score | Meaning | Anchor Examples |
|-------|---------|----------------|
| 1 | Disturbing but common crime type; produces no unusual reaction beyond "that's sad" | Embezzlement, financial fraud, standard property crime |
| 2 | Violent but without unusual elements; produces normal shock of violent crime | Gang-related homicide, drive-by shooting, standard assault |
| 3 | Unusual method, unusual target, or revelation that reframes understanding; produces genuine unease | Organ trafficking networks, ritualistic threats without confirmed murders, psychological control without physical violence |
| 4 | Viscerally disturbing detail that fundamentally reframes the story on first encounter | Human sacrifice confirmed by forensic evidence, systematic abuse revealed by survivor testimony |
| 5 | A detail or revelation that produces an involuntary physical reaction in a calm adult reader; crosses from disturbing into genuinely horrifying | Mass graves of children with forensic confirmation, sustained multi-year ritual torture on video, institutional complicity in mass atrocity |

### Dimension 4: Verifiability (1–5)

How well-documented is this story? Can it be sourced to primary records, court documents, or credible investigative journalism?

| Score | Meaning | Anchor Examples |
|-------|---------|----------------|
| 1 | Entirely speculative; no primary sources; story exists only as unverified claims | Urban legend, anonymous forum posts, uncorroborated rumor |
| 2 | Some news reports, no official records; single-source coverage with no follow-up | Local newspaper story with no subsequent investigation, social media reports only |
| 3 | Multiple credible journalist accounts OR academic papers with named sources | Investigative journalism with named sources, academic case studies, documentary with interviews |
| 4 | Court records, official investigations, FBI files, or government reports | Documented criminal cases with trial transcripts, declassified government files, official autopsy/forensic records |
| 5 | Primary-source video or audio recordings, confessions on record, government documents released under FOIA or equivalent | Waco recordings, Jonestown death tape, released CIA documents, perpetrator confession recordings |

---

## Generation Instructions

### Sources to Draw From

Generate candidates from ALL THREE of these sources — do not rely on only one:

1. **Competitor Gaps:** Review the Topic Clusters section in the competitor analysis. Prioritize clusters marked "Underserved" — these are areas with proven audience demand but low supply. Tag these topics with `[UNDERSERVED CLUSTER: cluster-name]`.

2. **Channel DNA Pillars:** Generate at least 2 candidates from each of the five pillars, particularly the pillars that appear underrepresented in the competitor analysis.

3. **Web Research (tavily-mcp):** Use 3-5 targeted tavily-mcp searches for obscure topics that fit underserved clusters and channel pillars. Suggested query patterns:
   - `"obscure [cult/crime/disappearance] [region] [decade] documentary"`
   - `"unsolved [profession] disappearance [country] investigation case"`
   - `"[country] historical [crime/cover-up] undocumented English"`
   - `"[niche topic] criminal case primary sources"`

### Quantity and Ranking

- Generate **exactly 5 candidates** — quality over quantity
- Present **ALL candidates** ranked by total score descending (sum of all 4 dimensions, max 20)
- **Do NOT filter out low-scoring topics** — show all 5 candidates regardless of score
- **Do NOT apply a minimum threshold** — the user decides what to pursue

### Near-Duplicate Handling

- Check every candidate against the past topics list using your judgment
- If a candidate is the same subject as a past topic but with a meaningfully different angle (different perpetrator, different time period, different victim), tag it: `[DIFFERENT ANGLE: past_topic]` and note the distinction
- If a candidate is substantially the same story (same subject, same events, same angle), tag it: `[Similar to: past_topic_title]`
- In both cases, INCLUDE the topic — never silently drop a candidate

### Tiebreaker Rules

When two topics have equal total scores, rank by:
1. **Shock Factor descending** — highest emotional impact first
2. **Obscurity descending** — rarer topics preferred
3. **Verifiability descending** — more documented is more production-safe

---

## Output Format

Produce two outputs: formatted markdown cards (displayed directly in chat), and full topic briefs (written to file).

### Format 1: Chat Cards (displayed as markdown in conversation)

**CRITICAL: Display these as markdown directly in your chat response. Do NOT output them via a bash command or print statement.** After generating the briefs as Python dicts, call `format_chat_cards(briefs)` to get the formatted markdown string, then paste it directly into your response.

**Canonical example of what the user sees in chat:**

### [1] The Matamoros Cult Murders

> A Mexican cartel's occult enforcer kidnapped and ritually murdered a US student, triggering a cross-border manhunt for a cult that believed human sacrifice granted supernatural protection.

**Score:** `##################--` **18/20** (O:5 C:4 S:5 V:4)
**Pillar:** Cults & Psychological Control | **Runtime:** ~35 min
**Tags:** UNDERSERVED CLUSTER: True Crime & Cults

---

### Format 2: Full Topic Brief Schema

Write the full briefs to `context/topics/topic_briefs.md` using `write_topic_briefs()` from `channel_assistant.topics`. Each brief must conform to this dict schema:

```python
{
    "title": str,                    # Working title, max 80 chars, YouTube-optimized
    "pillar": str,                   # One of the 5 content pillars
    "hook": str,                     # Core mystery in 1 sentence
    "timeline": list[str],           # 3-8 chronological events as strings
    "scores": {
        "obscurity": int,            # 1-5
        "complexity": int,           # 1-5
        "shock_factor": int,         # 1-5
        "verifiability": int,        # 1-5
    },
    "justification": {
        "obscurity": str,            # 1-2 sentences citing rubric anchor
        "complexity": str,           # 1-2 sentences citing rubric anchor
        "shock_factor": str,         # 1-2 sentences citing rubric anchor
        "verifiability": str,        # 1-2 sentences citing rubric anchor
    },
    "estimated_runtime_min": int,    # Estimated video length in minutes
    "duplicate_of": str | None,      # Past topic title if near-duplicate, else None
    "tags": list[str],               # e.g. ["UNDERSERVED CLUSTER: True Crime & Cults"]
}
```

**Canonical full brief example:**

```markdown
## 1. The Matamoros Cult Murders

**Pillar:** Cults & Psychological Control
**Score:** O:5 C:4 S:5 V:4 = 18/20  |  ~35 min

**Hook:** A Mexican drug cartel's occult enforcer kidnapped and ritually murdered a US student, triggering a cross-border manhunt for a cult that believed human sacrifice granted supernatural protection.

**Timeline:**
- 1986: Adolfo de Jesús Constanzo begins blending Palo Mayombe with narco violence in Mexico City
- 1988: Constanzo moves to Matamoros, gains control of a cartel faction
- March 1989: University of Texas student Mark Kilroy disappears after crossing the border for spring break
- April 1989: Mexican police raid Rancho Santa Elena; discover 15 ritual murder victims including Kilroy
- May 1989: Constanzo killed by his own followers in a Mexico City standoff after a 47-hour siege
- 1990: Surviving cult members convicted; case inspires Satanic panic legislation in Texas

**Scoring Justification:**
- Obscurity (5/5): Zero mainstream English-language documentary treatment. Constanzo known only in true crime niche; the broader cult structure and cartel integration is unknown to general audience.
- Complexity (4/5): Multi-layered: religious syncretism, cartel politics, cross-border jurisdiction, multiple victims and perpetrators. Stops short of 5 because the core narrative is linear.
- Shock Factor (5/5): Ritual murders, human sacrifice confirmed by forensics, US college student victim. Highest shock ceiling in content pillars.
- Verifiability (4/5): Court records, FBI case files, multiple journalist accounts. One point deducted: key supernatural belief system relies on perpetrators' self-reporting.

**Tags:** UNDERSERVED CLUSTER: True Crime & Cults
```

---

## Anti-Patterns

**Do NOT do any of the following:**

- **Generic scoring without rubric references:** Every score must reference a specific rubric anchor. Never score purely from intuition. If you cannot identify which rubric level a topic maps to, default to the lower score.
- **Filter topics below a threshold:** Show all 5 candidates regardless of total score. The user decides what to pursue.
- **Generate mainstream well-known topics without appropriate low obscurity scores:** If you generate Jack the Ripper, Zodiac Killer, or similar, they must receive Obscurity 1 and will score low overall.
- **Silently drop near-duplicates:** Always tag and include.
- **Speculate without sourcing:** If you cannot identify at least 2-3 verifiable sources (news, court records, documented research) for a topic, score Verifiability at 1-2 and note the limitation.
- **Invent timelines:** Use only documented events. If timeline is sparse, use fewer entries rather than padding with speculation.
- **Call LLM APIs from code:** This generation workflow runs entirely via Claude Code's native reasoning. No Python subprocess to an API endpoint.
