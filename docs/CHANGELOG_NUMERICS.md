# CHANGELOG — numerical changes

One entry per modification that can change simulation results
(Plan_20260919_v2, rule 2: separate commit + theory source + regression
test + before/after). Entries appended top-down, newest first.

Format:

```text
## YYYY-MM-DD <task-id> <one-line summary>   (commit <hash>)
- What changed (file:line)
- Theory source / reasoning
- Regression evidence (test + before/after numbers)
```

## 2026-09-19 Phase 0 baseline frozen (no numerical change)

- Tag `baseline-pre-audit-2026-09` created; pre-audit results archived to
  `results/baseline/` (see `results/baseline/PROVENANCE.md` for revision +
  environment). requirements.txt pinned to the exact producing versions.
- No solver/driver code touched in this entry.
