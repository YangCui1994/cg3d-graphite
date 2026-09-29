# START — BI-CG-LECLAIRE-WETTING-CLOSURE-001 — DeepSeek Executor

Continue in the existing Leclaire executor session.

Pull agent-dev/bilateral-episode-v0.1 with fast-forward only.

Read in full:
1. docs/research/SCIENCE_MASTERLINE.md
2. docs/research/leclaire_cg/WETTING_PHASE_CONVENTION.md
3. .agent/episodes/bilateral-imbibition-v0.1/LECLAIRE_WETTING_CLOSURE_CONTRACT.md
4. .agent/evidence/BI-CG-LECLAIRE-PASS4-001/FRESH_REVIEW.md
5. .agent/evidence/BI-CG-LECLAIRE-PASS4-001/EXTERNAL_SCIENTIFIC_REVIEW_R3_CHANGES_REQUESTED.md
6. docs/research/leclaire_cg/VALIDATION_ARTIFACT_SPEC.md
7. AGENTS.md

Continue on product branch:
agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001

Starting tip:
ca10d6503857f2d6349ce313dd97561d9406fd9e

Do not merge the control branch into the product branch.

Canonical correction:

~~~text
red = liquid/electrolyte/wetting
blue = gas/non-wetting
psi = (rho_red-rho_blue)/rho
F = grad(psi) = gas -> liquid
g = 1 solid, 0 fluid
n_w = +grad(g)/|grad(g)| = fluid -> solid
theta = measured through liquid/red
~~~

For a sessile red/liquid drop above a horizontal wall:

~~~text
cos(theta_liquid) = -(z_c-z_wall)/R
~~~

Pass-4 used the complementary wall-normal and circle-fit conventions. Fix both
from source/geometry; do not calibrate the sign from desired output.

Execution order:
1. Fix wall-normal convention and liquid-side angle instrument.
2. Replace circular convention tests with independent analytic geometry tests.
3. Fix gitignore/raw NPZ tracking.
4. Fix and smoke-test the entire harness before freezing.
5. Keep the current valid slit-Pc geometry.
6. Keep the current reachable Jurin geometry.
7. Clean science/provenance text required before freeze.
8. Run unit checks and cheap smoke paths for every case.
9. Freeze a NEW Pass-5 source candidate SHA.
10. After freeze modify no source/harness/gate/artifact code.
11. Run the full Pass-5 matrix once from that exact SHA.
12. Commit raw NPZ + figures + metrics + manifests under pass-05.
13. Verify every render-manifest raw path is tracked and reproducible from Git.
14. Update report/atlas/current headline.
15. Prepare fresh-review request.
16. STOP.

Mechanical sigma remains exploratory unless its premises and recomputability are
actually closed. Do not retune R1 Eq.(18). Do not touch production, Taichi/f32,
V3, graphite, separator or PCS.

Final status must include:
- task ID
- product branch
- starting tip
- new frozen Pass-5 source SHA
- Pass-5 evidence/package tip SHA
- unit-check count
- full matrix verdict counts
- contact-angle 60/90/120 liquid-side measurements
- slit-Pc 60/90/120 signs and ratios
- Jurin measured/theory rise
- tracked raw NPZ count
- report/atlas paths
- NEXT_ACTION = fresh independent review
