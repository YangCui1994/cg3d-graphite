# START — BI-CG-LECLAIRE-PASS4-001 — DeepSeek Executor

Continue in the same executor context if available.

## Sync

Pull \`agent-dev/bilateral-episode-v0.1\` with fast-forward only.

Read in full, in this order:

1. \`docs/research/leclaire_cg/WETTING_PHASE_CONVENTION.md\`
2. \`.agent/episodes/bilateral-imbibition-v0.1/LECLAIRE_PASS4_VALIDATION_CONTRACT.md\`
3. \`docs/research/leclaire_cg/VALIDATION_ARTIFACT_SPEC.md\`
4. \`docs/research/leclaire_cg/VALIDATION_ATLAS.md\`
5. \`.agent/evidence/BI-CG-LECLAIRE-IMPLEMENTATION-001/FRESH_REVIEW.md\`
6. \`.agent/evidence/BI-CG-LECLAIRE-IMPLEMENTATION-001/EXTERNAL_SCIENTIFIC_REVIEW_R2_CHANGES_REQUESTED.md\`
7. \`AGENTS.md\`

## Product branch

Continue on:

\`agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001\`

Starting branch tip:
\`a12c14f553c5a03a815dbfc96d5aa09a6f33083e\`

Do not merge the control branch into the product branch. Read the control
documents, then implement on the product branch.

## Order

1. Freeze the wetting convention and add analytic convention unit tests.
2. Fix contact-angle validation under that convention.
3. Replace test 07 with a geometry that has a real wall-intersecting meniscus.
4. Replace test 08 with a reachable closed-system Jurin equilibrium case.
5. Add the larger-radius Laplace diagnostic.
6. Derive and add the planar mechanical-sigma diagnostic.
7. Add raw-snapshot + rendering infrastructure required by the artifact spec.
8. Rerun the corrected asymmetric-wall case with visual outputs.
9. Freeze code.
10. Run the full pass-04 matrix once.
11. Generate the pass-04 validation report/atlas from the same frozen evidence.
12. Clean stale/superseded durable-document statements.
13. Commit/push everything.
14. Prepare the fresh-review request.
15. STOP.

Do not tune R1 Eq.(18) to force a PASS.
Do not port to Taichi/f32.
Do not touch production/V3/graphite/PCS.

Return a compact final status containing:
- stage ID;
- product branch;
- starting tip;
- frozen source candidate SHA;
- evidence/package tip SHA;
- unit-check count;
- pass-04 verdict counts;
- paths to the validation report and atlas;
- list of generated case directories;
- NEXT_ACTION = fresh independent review.
