# Implementation reference map — Latt/Palabos and independent codes

Inspected 2026-09-29 through upstream GitHub files and repository metadata. These are code-reading/benchmark candidates, not validated replacements or imported dependencies. No code was copied or executed. Commit pins identify inspected snapshots, not universally recommended versions.

## Original L17 implementation: known boundary

Reuse the existing [Palabos/Leclaire code trace](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/docs/research/bilateral_imbibition/PALABOS_LECLAIRE_CODE_TRACE.md). It records historical releases/forks and same-group publication evidence for a runnable Palabos CG extension. Its bounded searches did **not recover identifiable original L17 author source**. This is not proof that the source never existed publicly. “Latt CG” here means the Leclaire et al. 2017 method with Jonas Latt as coauthor, not a separately verified Latt code package.

**INFERENCE:** an archival request to the authors/group for a version, supplementary archive or publication-era branch is more targeted than repeating broad Palabos searches. No contact is authorized or sent by this document. Record exact paper/variant and code provenance if recovered; even author code still requires verification.

## Inspected reusable ideas and code entry points

| Source / pinned entry | What was observed | Useful role and limits |
|---|---|---|
| Palabos, [`multiComponentSandstone.cpp`](https://github.com/omalaspinas/palabos/blob/8f8ecd277204f9d24019834068906128565c9346/examples/gpuExamples/multiComponentPorous/multiComponentSandstone.cpp) | `ForcedShanChenD3Q19Descriptor`, two fluid lattices, `ShanChenMultiComponentProcessor3D`, accelerated multicomponent path | SC porous-geometry/example and performance-architecture reference; **not L17 CG** and not evidence of suitable real-gas physics |
| Palabos, [`shanChenProcessor3D.hh`](https://github.com/omalaspinas/palabos/blob/8f8ecd277204f9d24019834068906128565c9346/src/multiPhysics/shanChenProcessor3D.hh) | identified SC processor source | entry for future force/component audit; full derivation not reconstructed here |
| Oliveira thesis code, [`GpuCollision.cu`](https://github.com/oliveirajp/Thesis/blob/85eb29711bf3c4ca8dad82214ace1d8d97465f9a/Source%20code/lbm-solver_final/GpuCollision.cu) | `calculateColorGradient3D`, `calculateHOColorGradient3D`, `gpuCollBgkwGC3D`, `gpuCollEnhancedBgkwGC3D`; explicit perturbation/recoloring logic | independent gradient/sign/normalization and GPU implementation cross-check; BGK/enhanced paths must not be equated to exact L17 MRT |
| LBPM, [color model documentation](https://github.com/OPM/LBPM/blob/6d686d354e5b8140841d3601e4c8c0e4e4b77e48/docs/source/userGuide/models/color/index.rst), [`cpu/Color.cpp`](https://github.com/OPM/LBPM/blob/6d686d354e5b8140841d3601e4c8c0e4e4b77e48/cpu/Color.cpp) | documentation describes D3Q19 MRT momentum and two D3Q7 mass-transport distributions | candidate architecture for comparison with production's colorblind distribution plus scalars; no measured memory/speed superiority established |
| LBPM, [grayscale model documentation](https://github.com/OPM/LBPM/blob/6d686d354e5b8140841d3601e4c8c0e4e4b77e48/docs/source/userGuide/models/greyscaleColor/greyscaleColor.rst), [`models/GreyscaleColorModel.cpp`](https://github.com/OPM/LBPM/blob/6d686d354e5b8140841d3601e4c8c0e4e4b77e48/models/GreyscaleColorModel.cpp) | documentation describes Darcy–Brinkman grayscale regions coupled with color model, modified recoloring and constituent parameters; flags boundary considerations | useful unresolved-porosity route on the CG side; requires calibration and applicability checks for battery binder, not automatic adoption |

The LBPM code tree also exposes CPU/CUDA color and grayscale operators and color gradient, mass/bounceback and square-tube tests. Their presence is an inspection fact, not a claim that those tests passed here. Other candidates in the existing archaeology document remain leads, not freshly reviewed implementations.

## Source and reuse discipline

Repository metadata identified Palabos as AGPL-3.0 and LBPM as GPL-3.0; the thesis repository metadata did not identify a license. This is an inventory observation, not a legal determination. Before any later copying, check file-level terms and compatibility. Reading implementations to develop comparisons is distinct from deciding to import them.

For each future port/cross-check, map paper equation → source function → convention (phase sign, stencil norm, force timing, fluid mask) → minimal verification. Preserve variant differences; agreement between two implementations is supporting evidence, not proof of correctness. Primary papers define the method claim, recovered author code could clarify intended implementation, independent code provides a cross-check, and project artifacts establish only project-specific outcomes.
