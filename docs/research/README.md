# Research Documentation Index

This directory contains scientific documents for several solver lines and
development stages.

## Start here

**Current scientific source-of-truth:**

\`SCIENCE_MASTERLINE.md\`

Read this first when the question is:
- what model are we currently using?
- which paper defines which part?
- what differs between production CG and Leclaire CG?
- what is validated?
- what remains unresolved?

## Detailed science documents

### Production / bilateral line

\`bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md\`

Role:
historical algorithm/implementation evolution, V0/V1/V2/conservation/bilateral
work.

Do not treat its oldest headline/status text as the current scientific state;
use \`SCIENCE_MASTERLINE.md\` for that.

\`bilateral_imbibition/CONSERVATION_FIX_LITERATURE_NOTE.md\`

Role:
literature and reasoning around finite-precision conservation.

\`bilateral_imbibition/PALABOS_LECLAIRE_CODE_TRACE.md\`

Role:
historical source-code archaeology for the Leclaire/Palabos implementation.

### Leclaire reference line

Detailed formulation documents currently live on the product branch while the
reference implementation is being closed:

- \`docs/research/leclaire_cg/PAPER_FORMULATION.md\`
- \`docs/research/leclaire_cg/CURRENT_VS_LECLAIRE_MAP.md\`
- \`docs/research/leclaire_cg/FOLLOWUP_OPTIMIZATION_MAP.md\`
- \`docs/research/leclaire_cg/REFERENCE_MANIFEST.md\`
- \`docs/research/leclaire_cg/MECHANICAL_SIGMA_DERIVATION.md\`

Once the reference line passes scientific closure, these should be synchronized
into the durable control/main science branch rather than left branch-local.

Control-branch documents:
- \`leclaire_cg/VALIDATION_ARTIFACT_SPEC.md\`
- \`leclaire_cg/VALIDATION_ATLAS.md\`
- \`leclaire_cg/WETTING_PHASE_CONVENTION.md\`
- \`leclaire_cg/BRANCH_BOUNDARY.md\`

Important:
the current \`WETTING_PHASE_CONVENTION.md\` contains a known Pass-4 wall-normal
sign error; \`SCIENCE_MASTERLINE.md\` and external review R3 contain the current
science correction until that file is revised.

## Evidence and reviews

\`.agent/evidence/**\`

Role:
immutable task/reviewer evidence.

These are not the scientific entry point.

## Rule of thumb

\`\`\`text
What is scientifically true now?
    -> SCIENCE_MASTERLINE.md

What exactly does the paper say?
    -> PAPER_FORMULATION.md / source paper

How does production differ from L17?
    -> CURRENT_VS_LECLAIRE_MAP.md

How did the code evolve?
    -> ALGORITHM_IMPLEMENTATION_EVOLUTION.md

What did a benchmark actually show?
    -> VALIDATION_ATLAS.md + results/pass-NN/

Why was a task accepted/rejected?
    -> .agent/evidence/**
\`\`\`
