# PROVENANCE — BI-CG-LECLAIRE-IMPLEMENTATION-001

Records exactly what was executed, against which source state, on which
machine, and how each reported number can be regenerated.

## Binding

| item | value |
|---|---|
| task | `BI-CG-LECLAIRE-IMPLEMENTATION-001` |
| repository | `https://github.com/YangCui1994/cg3d-graphite` |
| control branch | `agent-dev/bilateral-episode-v0.1` (read only) |
| product branch | `agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001` |
| product base | `6c30260dfe0c8b61ea9609e6bffa5c487312cf06` |
| control tip read at task start | `dddd2c4` |
| worktree used | `D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-CG-LECLAIRE-IMPLEMENTATION-001` |

The control branch was **not** merged into the product branch, as the task
requires. The product branch is `base + the commits listed below`.

## Commit chain

| commit | kind | content |
|---|---|---|
| `245d6e6` | `formulation:` | `PAPER_FORMULATION.md`, `CURRENT_VS_LECLAIRE_MAP.md`, `FOLLOWUP_OPTIMIZATION_MAP.md`, `IMPLEMENTATION_PLAN.md`, `REFERENCE_MANIFEST.md`, `.gitignore` entry. No code. |
| `dbe47d3` | `formulation-fix:` | Table IV shell-grouping correction |
| `030ab33` | `implementation:` | `experimental/leclaire_cg/**`, `tests/leclaire_cg/**` |
| `d2177e5` | `implementation-fix:` | colour-gradient sign and normalisation |
| `33b0a33` | `implementation-fix:` | recolouring on fluid sites; underflow removal |
| `22fe2d3` | `implementation-fix:` | R1 steps (2)/(4)/(5) on fluid sites only |
| `8873a67` | `implementation-fix:` | wall normal must use the full stencil |
| `51cc61a` | `validation:` | **pass 1** evidence, report, provenance |
| see `git log` | `research:` / `validation:` | **pass 2**: R5 obtained; Eq. (18) constant corrected; matrix re-run |

The contract asks for at least three logical commits
(`formulation:` / `implementation:` / `validation:`). That structure is
preserved. The additional `-fix:` commits are the mechanism the contract
itself prescribes for corrections (section 10) and none rewrites an earlier
commit.

**Two validation passes are recorded.** Pass 1 produced 6 PASS / 4 FAIL and
left the Laplace calibration offset unexplained. Pass 2 produced
**7 PASS / 3 FAIL** — test 3 is the only verdict that changed. Between the passes R5 was
obtained, which ruled out the gradient-stencil hypothesis and led to the
discovery of an arithmetic error in the Eq. (18) constant. Pass 2 re-ran
the whole matrix on the corrected candidate. Pass-1 evidence is retained
in the history rather than overwritten, because "what we believed before
the fix" is part of the provenance.

## Frozen artefacts — verified unmodified

| artefact | requirement | value at review time |
|---|---|---|
| `lbm_solver_cg3d.py` | unchanged from the base | blob `1b7db4ac27448b5b982cead1ea86e719c59e6684` |
| production defaults / gates | unchanged | no file outside the four allowed paths is touched |
| V0/V1c/V2 result files | unchanged | untouched |

Verification:

```
git diff --name-only 6c30260dfe0c8b61ea9609e6bffa5c487312cf06..HEAD
git hash-object lbm_solver_cg3d.py
```

The expected change set is exactly: `.gitignore`, `docs/research/leclaire_cg/**`,
`experimental/leclaire_cg/**`, `tests/leclaire_cg/**`, `results/leclaire_cg/**`,
`results/leclaire_cg_run.log`, `results/unit_checks.log`.

## Reference sources

Reference PDFs are staged at `docs/research/leclaire_cg/_refs/` and are
**gitignored**: this repository is public and R1/R2 are copyrighted
publisher versions.

| ID | DOI | SHA256 (first 16) | status |
|---|---|---|---|
| R1 | `10.1103/PhysRevE.95.033306` | `435b4fa1df08d636` | UNIGE `unige:97528`, staged |
| R2 | `10.1142/S0129183117500851` | `91fc30f1d597adfa` | UNIGE, staged |
| R3 | `10.1016/j.advwatres.2018.03.014` | `073a343175a68e28` | Imperial Spiral, CC-BY, staged |
| R4 | `10.1155/2019/5176410` | `17aca930e58c1efb` | PolyPublie, CC-BY, staged |
| R5 | `10.1007/s10915-013-9772-2` | `f18e3bfd81e65cc7` | **obtained pass 2**, staged |

Full digests, routes and roles: `REFERENCE_MANIFEST.md`.

## Validation pass 3 (post-review correction)

| item | value |
|---|---|
| candidate | `5a3929fa1cefb7359893d6c19ed0ec8a7c80a91d` |
| reviewed predecessor | `738e76f` |
| review | `.agent/evidence/BI-CG-LECLAIRE-IMPLEMENTATION-001/EXTERNAL_SCIENTIFIC_REVIEW_CHANGES_REQUESTED.md` |
| control tip read | `1c4f1a4` |
| unit checks | 59/59 (`results/leclaire_cg/UNIT_CHECKS.log`) |
| matrix | FAIL 3, INCONCLUSIVE 2, PASS 5, one uninterrupted run |

The candidate was frozen before the matrix was launched, and the evidence
below it is from that frozen state. Passes 1 and 2 remain in the history and
in `summary.json`'s companion files; nothing was overwritten.

**R5 provenance correction.** The earlier claim that 科研通 could not be
driven from this session was wrong and is retracted. R5 was obtained via the
`ablesci-paper-download` skill by DOI on 2026-09-27; the staged file's byte
count (1,078,397) matches the delivery record.

## Scope exclusions actually honoured

- `lbm_solver_cg3d.py` not modified ✓
- no V3 execution ✓
- no graphite, separator, PCS or gap work ✓
- no full porous-media production run ✓
- D3Q19 only ✓
- no Palabos source copied ✓

R1 Eqs. (21)–(29) regularized open boundaries are **not** implemented; the
constructor raises rather than falling back. A declared exclusion
(`IMPLEMENTATION_PLAN.md` §2, `FOLLOWUP_OPTIMIZATION_MAP.md` F4), not an
omission found at review.

## Environment

Recorded at run time in `results/leclaire_cg/summary.json` (`host`,
`python`, `numpy`); scipy is used for connected-component labelling and
profile fitting.

**Backend deviation, stated explicitly.** The production line runs Taichi
with CUDA; this candidate is a NumPy reference implementation. Reason: a
Taichi solver instance costs ~5.5 min of JIT on this machine and the cache
key includes an instance counter, so a second instance in one process
always misses. Consequence: **the candidate is not performance-comparable
to the production solver and no performance claim is made anywhere.**
Recorded in `IMPLEMENTATION_PLAN.md` §3.

## Reproducing the evidence

```
# table and operator checks (no simulation, ~5 s)
python tests/leclaire_cg/test_lattice_tables.py

# the ten-test canonical matrix (~15 min)
python tests/leclaire_cg/run_canonical.py
```

Both write into `results/leclaire_cg/`. Each test writes its own JSON with
`verdict`, `exit_code` and `wall_seconds`; `summary.json` aggregates them
with the environment block. The driver's process exit code is 0 only if
every test reached a verdict without an internal error; it is **not** a
statement about the verdicts.

## Known weaknesses of this provenance

Recorded rather than glossed, per the project rule that failed attempts
and weak links are as valuable as results:

1. **`PROVENANCE.md` was lost once.** It was written before a validation
   re-run and destroyed by `rm -rf results/leclaire_cg` in the same
   command that relaunched the matrix, then silently absent from the
   validation commit because `git status` was only inspected with
   `head`. It is restored here. The lesson is general: an evidence
   directory should not be deleted by the command that re-runs it.
2. The side studies quoted in the report (σ-versus-β calibration, the
   wall-storage saturation check, the R5-table cross-check) are not
   committed as scripts; only their invocations and outputs are recorded.
3. Per-test shell exit codes are captured by the driver; the driver's own
   exit code was logged by hand into `results/leclaire_cg_run.log`.
4. Reference PDFs are not in the repository, so a reviewer must re-obtain
   them and verify the digests. R5 was obtained via the **科研通**
   (`ablesci-paper-download`) workflow by DOI on 2026-09-27; any earlier
   statement that it came from a local search is retracted. Its digest is
   recorded so the reviewer can confirm they are reading the same bytes.
