# TASK

## ID

`ADS-DUMMY-001-R1`

## Objective

Create a harmless text artifact that proves the first executor round reached the task worktree.

## Scope

### Allowed

- `ads_dummy.txt`
- `.agent_runtime/execution_report.md`

### Do not modify

- solver, driver, test, data, result, or scientific-documentation files
- agent protocol or controller files

## Requirements

1. Create `ads_dummy.txt` at the repository root.
2. Its exact UTF-8 content must be `round 1 complete` followed by one newline.
3. Write the required execution report.

## Constraints

- Do not install anything.
- Do not run a simulation or use the GPU.
- Do not modify any scientific or numerical behavior.

## Scientific / Modeling Assumptions

- **Accepted:** This task has no scientific or modeling effect.
- **Unresolved:** None.

## Validation Requested

```text
python -c "from pathlib import Path; assert Path('ads_dummy.txt').read_text(encoding='utf-8') == 'round 1 complete\n'"
```

## Evidence Requested

- changed-files list and diff;
- validation command, exit code, and result;
- candidate commit.

## Git Policy

- Controller commit and push to the task branch are allowed.
- Do not merge any branch.

## Human Decisions Reserved

- Review decision and whether to start Round 2.

## Notes / References

This is an infrastructure-only dummy task.
