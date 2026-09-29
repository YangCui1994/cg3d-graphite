# V1c Fresh Reviewer Contract

Task: BI-V1C-CLOSURE-001

Review the frozen V1c candidate independently.

Verify:

- exact candidate SHA and clean worktree;
- descendant of \`a9c6db87da2eeb3572607152391fe6863394ebee\`;
- no solver changes;
- only V1c-authorized files changed;
- artifact provenance binds to final producer revision.

Recompute from committed evidence:

\[
C_\mathrm{static}(h)=P_ch/(2\sigma)
\]

for h=26/40/60/80.

Assess whether the resolution sequence is coherent; do not force a specific extrapolation model.

For h26 and h40 independently recompute:

\[
L_\mathrm{eff}=P_{c,\mathrm{dynamic}}h^2/(12\mu V)
\]

and

\[
a_h=\Delta L_\mathrm{eff}/\Delta L
\]

Hard gates:

- \(|a_{26}-1|\le0.10\)
- \(|a_{40}-1|\le0.10\)

Inspect pressure-band construction directly from source and evidence. Confirm that invalid/insufficient bulk bands fail explicitly.

Check front/stability gates and mass accounting.

Review the proposed technical-document update for factual consistency with the frozen candidate. The document is part of the deliverable.

Decision exactly one of:

PASS / CHANGES_REQUESTED / HUMAN_REQUIRED

Even PASS requires external scientific review before V2.
