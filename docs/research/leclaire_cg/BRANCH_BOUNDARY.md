# Leclaire/Latt CG branch boundary

Task: `BI-CG-LECLAIRE-IMPLEMENTATION-001`

## Relationship to the existing solver

This is a parallel algorithm-development line.

```text
accepted current CG
    |
    +-- bilateral / revised-V3 line
    |
    +-- Leclaire/Latt CG research line
```

The Leclaire branch is intentionally near-isolated at the physics/model layer.

Shared assets are limited to algorithm-independent validation infrastructure:
canonical geometries, metric definitions, provenance format, conservation
diagnostics and reviewer process.

A validation method may be reused; a validation result may not.

## Product branch

`agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001`

Exact base:

`6c30260dfe0c8b61ea9609e6bffa5c487312cf06`

## Promotion rule

No result in this branch changes production by default.

Promotion requires:
1. paper-fidelity review;
2. independent fresh review;
3. external scientific review;
4. explicit owner decision on which individual modules, if any, are promoted.

A full-paper implementation and a later optimization must remain separately
identifiable so that improvements can be attributed by ablation.
