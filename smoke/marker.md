# SMOKE-1 Marker

Infrastructure rehearsal marker for the smoke mini-episode, not scientific content.

- Episode: BI-VALIDATION-001
- Stage: SMOKE-1 (A0 runner isolation test)
- Round: 1 of the stage's bounded rework cycle
- Candidate type: single-file marker commit on the smoke product branch

This file exists so the orchestration path can be exercised end to end: an executor
commit, a fresh reviewer session bound to that commit, and the routing of the review
result back to the executor. It carries no model, solver, or boundary-condition meaning.
