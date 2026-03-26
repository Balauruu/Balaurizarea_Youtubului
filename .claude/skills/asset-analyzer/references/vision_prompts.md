# Documentary Vision Prompts

Prompts for the two-pass analysis workflow. All frames are 512px wide.

---

## Triage Prompt (Pass 1)

Used with one mid-scene frame per scene. Goal: classify scene relevance cheaply.

```
You are triaging footage for the documentary "[PROJECT_NAME]".
Context for this video: [CONTEXT]
Relevant visual needs: [SHOT_REFS_OR_GENERAL_NEEDS]

For each frame (one per detected scene), answer:
- What does this scene show?
- Relevant (yes/no/maybe) to the project?
- If relevant, which visual need does it serve?

Be terse. This is triage, not full analysis.
```

---

## Full Analysis Prompt — Project Mode (Pass 2)

Used with 2fps frames from relevant scenes. Goal: detailed segment identification.

```
You are analyzing footage for the documentary "[PROJECT_NAME]".
This video: [TITLE] — [CONTEXT]
This scene range: [START_SEC]s to [END_SEC]s
Visual needs this video may serve: [RELEVANT_SHOTLIST_ENTRIES]

For each frame, describe:
1. Content: people, locations, objects, text on screen, era markers
2. Footage type: interview/talking head, archival film, b-roll, news broadcast, document close-up, cartoon/animation
3. Mood and atmosphere
4. Which shotlist entry this could serve (cite shot ID)
5. Scope: "project" (topic-specific) or "global" (reusable atmospheric/b-roll)

Reference timestamps. Be specific — "grey institutional building with barred windows, overcast, 1950s Quebec" not "a building".
```

---

## Full Analysis Prompt — Standalone Mode (Pass 2)

Used when no project context is available (standalone video analysis).

```
You are analyzing documentary footage.
This video: [TITLE]
This scene range: [START_SEC]s to [END_SEC]s

For each frame, describe:
1. Content: people, locations, objects, text on screen, era markers
2. Footage type: interview/talking head, archival film, b-roll, news broadcast, document close-up, cartoon/animation
3. Mood and atmosphere
4. Era/decade if identifiable
5. Potential documentary use

Reference timestamps. Be specific and concrete.
```

---

## Batch Context Template

Prepend to every vision batch call:

```
Batch [N] of [TOTAL].
Video: [FILENAME]
Time range: [START_TS]s — [END_TS]s
Previous batch summary: [PREV_SUMMARY or "N/A — first batch"]

Analyze the following [COUNT] frames in order:
```
