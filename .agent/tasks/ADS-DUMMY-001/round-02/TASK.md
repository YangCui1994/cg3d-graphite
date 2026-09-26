# TASK

## ID

`ADS-DUMMY-001-R2`

## Objective

Extend the Round 1 artifact and prove that the executor resumes the same parent-task session.

## Scope

### Allowed

- `ads_dummy.txt`
- `.agent_runtime/execution_report.md`

### Do not modify

- solver, driver, test, data, result, or scientific-documentation files
- agent protocol or controller files

## Requirements

1. Preserve the existing first line of `ads_dummy.txt`.
2. Append `round 2 complete` followed by one newline.
3. The exact final UTF-8 content must be two lines: `round 1 complete` and `round 2 complete`.
4. Write the required execution report.

## Constraints

- Do not install anything.
- Do not run a simulation or use the GPU.
- Do not modify any scientific or numerical behavior.

## Scientific / Modeling Assumptions

- **Accepted:** This task has no scientific or modeling effect.
- **Unresolved:** None.

## Validation Requested

```text
python -c "from pathlib import Path; assert Path('ads_dummy.txt').read_text(encoding='utf-8') == 'round 1 complete\nround 2 complete\n'"
```

## Evidence Requested

- changed-files list and diff;
- validation command, exit code, and result;
- candidate commit;
- controller process evidence showing `--resume` used the Round 1 session ID.

## Git Policy

- Controller commit and push to the task branch are allowed.
- Do not merge any branch.

## Human Decisions Reserved

- Review decision and parent-task closure.

## Notes / References

Start this round only after Round 1 is reviewed.
