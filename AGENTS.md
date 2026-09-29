# AGENTS.md

## Project purpose

This repository is a research codebase for pore-scale two-phase LBM simulations in realistic porous media, with current emphasis on drainage, imbibition, electrolyte infiltration, gas displacement, and trapped gas in battery-electrode structures.

The current priority is **scientifically traceable research work**, not turning the repository into a generic LBM framework.

## Required reading before changes

Before modifying code, read the repository README and the documentation relevant to the task.

For any change touching solver physics, boundaries, initial conditions, convergence, or scientific interpretation, read at minimum:

- `docs/BC_IC_OUTPUT.md`
- `docs/ALGORITHM.md`
- relevant sections of `docs/RESULTS.md`

Do not infer boundary semantics from variable names alone.

## Task discipline

Work from an explicit task description. The task may be supplied through a file or prompt, but it must define at least:

- objective;
- allowed scope;
- requirements;
- constraints;
- requested validation.

Do not silently broaden the task.

If a required scientific assumption, boundary condition, convergence rule, or acceptance criterion is unresolved, do not choose one implicitly. Report it as a human/modeling decision.

## Three kinds of correctness

Keep these separate:

1. **Code correctness** — whether the requested implementation is correct.
2. **Numerical correctness** — whether deterministic numerical tests or benchmarks pass.
3. **Physical/modeling correctness** — whether the setup represents the intended physical process.

Passing tests does not by itself establish physical validity.

## Scientific-change guardrails

Do not change any of the following unless the task explicitly authorizes it:

- physical model or numerical formulation;
- boundary-condition meaning;
- initial-condition meaning;
- convergence/stopping criteria;
- contact-angle or wettability interpretation;
- scientific claim scope;
- default physical parameters used by existing published/reported runs.

If such a change appears necessary, stop and describe:

- the issue;
- the proposed alternatives;
- which existing results or validations may become stale.

## Validation and evidence

Prefer deterministic evidence over self-assessment.

When validation is requested, record the exact command and outcome.

Distinguish explicitly between:

- PASS;
- FAIL;
- NOT_RUN;
- INCONCLUSIVE / NOT_CONVERGED.

Never report an unrun validation as passed.

For scientific simulations, process completion (`exit code = 0`) is not the same as physical convergence.

Do not rerun an expensive GPU simulation repeatedly merely to obtain a passing result.

## Candidate freezing

Before acceptance-style validation, stop editing the candidate source.

Validation intended as acceptance evidence should be attributable to an identifiable source state (commit or captured diff).

Do not edit imported Python modules while a Taichi batch using them is running.

## GPU / long-run safety

Do not start expensive GPU simulations unless the task requests them or the user explicitly authorizes them.

Do not run PyVista rendering in parallel with GPU simulation on the same GPU.

Do not terminate, reset, overwrite, or reuse an existing long-running simulation directory unless explicitly authorized.

## Repository-specific constraints

The repository contains shared/copy-paired files with the separate `LBM/source_code/taichi_LBM3D/2phase/` working tree.

When changing one of those files:

- note that a paired copy may exist;
- do not blindly copy changes across trees;
- do not modify files outside this repository unless the task explicitly authorizes it;
- report whether synchronization may be required.

Use actual repository interfaces. Do not invent CLI flags, output paths, or configuration options.

## Git behavior

Default behavior:

- do not force-push;
- do not rewrite shared history;
- do not merge to `master`;
- do not delete branches or worktrees;
- do not modify unrelated dirty files.

Branch creation, commit, push, or PR creation should follow the task or external controller instruction.

## Executor output

At the end of an execution task, produce a concise execution report using the structure in:

`.agent/templates/EXECUTION_REPORT.md`

The report is an executor claim, not the sole source of truth. Git diff, commit identity, command logs, and validation outputs may later be captured independently by a controller/reviewer.

## Review output

When acting as a reviewer, use:

`.agent/templates/REVIEW.md`

Do not modify code while performing a review unless the task explicitly combines review and execution.

## Handoff

When work must continue in another session or agent, use:

`.agent/templates/HANDOFF.md`

Keep handoffs compact. Reference durable files and commits rather than copying the full conversation history.
