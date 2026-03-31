# Workflow Correctness Rubric

Score 1-5 based on whether Claude follows the SKILL.md workflow correctly.

| Score | Criteria |
|---|---|
| 1 | Wrong scripts invoked or wrong order |
| 2 | Right scripts but wrong arguments or missing steps |
| 3 | Correct flow but skipped checkpoints (no user approval points) |
| 4 | Correct flow with checkpoints, minor issues |
| 5 | Perfect flow: correct scripts, correct args, all checkpoints, appropriate model routing |

**Checkpoints that MUST exist:**
- After embedding: report how many videos, frames, time taken
- After search: present candidates for approval before extraction
- After discovery: present inventory for user selection
- Before extraction: confirm approved segments
