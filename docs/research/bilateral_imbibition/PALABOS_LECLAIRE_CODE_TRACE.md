# Palabos / Leclaire 2017 Color-Gradient Code Trace

Date: 2026-09-26

Status: historical/source archaeology only. No solver modification.

## Question

Trace the implementation lineage behind:

S. Leclaire, A. Parmigiani, O. Malaspinas, B. Chopard, J. Latt,
"Generalized three-dimensional lattice Boltzmann color-gradient method for
immiscible two-phase pore-scale imbibition and drainage in porous media",
Physical Review E 95, 033306 (2017).

The goal is to determine whether the authors' Palabos implementation can be
used as a source-level reference for cg3d-graphite.

## 1. What the paper explicitly says

The paper states that the presented CG method was implemented in PALABOS and
that open-source implementations were to be provided through PALABOS.

The paper also states that, at that time, only the three-dimensional CG code
was available, although the formulation was derived for D2Q9, D3Q15, D3Q19 and
D3Q27.

However, the conclusion uses weaker/future wording: the authors state that the
code was implemented and added to PALABOS and that they "intend to make" the
code available to the public under the same license.

This wording difference matters for interpreting the historical source record.

Public article:
https://doi.org/10.1103/PhysRevE.95.033306

UNIGE public full text:
https://archive-ouverte.unige.ch/unige:94117

## 2. Palabos release at the time of publication: v1.5r1

The PRE paper was published on 2017-03-14.

A contemporaneous 2017 publication records use of:

Palabos Software Version 1.5r1
http://www.palabos.org/images/palabos_releases/palabos-v1.5r1.tgz

with an access date of 2017-04-15.

Debian preserves the v1.5r1 source as:

palabos 1.5~r1+repack1

The preserved source tree contains the standard multiphase modules such as:

- free-surface machinery;
- He-Lee;
- multiPhaseTemplates;
- Shan-Chen lattices/processors;
- twoPhaseModel.

No Leclaire color-gradient / recoloring implementation is present in the
standard v1.5r1 multiPhysics source tree.

The Debian repack does not explain this absence: its excluded paths are
external/build/support directories, not the multiPhysics implementation tree.

Conclusion for v1.5r1:

**The standard public Palabos release contemporaneous with the paper does not
contain an identifiable Leclaire-2017 CG implementation.**

## 3. Palabos v2.0r0

A complete vendored copy of `palabos-v2.0r0` is preserved in the public
GitHub repository:

TylrA/cs6170-final/simulation/palabos-v2.0r0/

The snapshot contains the full main library layout, including `src/`,
`examples/`, `jlabos/` and the external libraries.

A recursive inspection of its `src/` tree found the following multiphase
families relevant to this question:

- `multiPhysics/heLeeProcessor3D.*`
- `multiPhysics/multiPhaseTemplates2D.h`
- `multiPhysics/multiPhaseTemplates3D.h`
- `multiPhysics/shanChenLattices2D.h`
- `multiPhysics/shanChenLattices3D.h`
- `multiPhysics/shanChenProcessor2D.*`
- `multiPhysics/shanChenProcessor3D.*`
- `multiPhysics/twoPhaseModel3D.*`

Repository-wide searches for terms characteristic of the 2017 CG
implementation (`recolor`, `color gradient`, `colorGradient`,
`Latva`, and Leclaire-specific CG references) found no corresponding
Palabos CG implementation. Occurrences of `beta` in the multiphase source
belong to the He-Lee model, not to Latva-Kokko recoloring.

Conclusion for v2.0r0:

**The standard v2.0r0 source snapshot also does not contain an identifiable
Leclaire-2017 CG module.**

## 4. v2.1r0, v2.2.0 and current Palabos

The official Palabos GitLab project was created in October 2019. The current
GitHub repository `omalaspinas/palabos` is a mirror of the official GitLab
repository.

Direct inspection of `src/multiPhysics/` at:

- tag `v2.1r0`;
- tag `v2.2.0`;
- current master;

shows the same relevant families (He-Lee, Shan-Chen, twoPhaseModel, etc.) and
no identifiable color-gradient / recoloring module.

Current Palabos explicitly contains a 3D Shan-Chen implementation, including:

- `src/multiPhysics/multiPhaseTemplates3D.h`:
  `shanChenInteraction(...)`;
- `src/multiPhysics/shanChenProcessor3D.hh`;
- D3Q19 Shan-Chen descriptors;
- a current porous-media GPU example based on the Shan-Chen multicomponent
  processor.

Therefore the current Palabos multiphase code must not be treated as the
source implementation of the Leclaire-2017 CG paper.

## 5. Important historical limitation

The public GitLab project starts in 2019, after the 2016 manuscript and 2017
publication. It therefore cannot, by itself, recover an unpublished/internal
2016-2017 development branch.

The current public repository exposes only `master` through the inspected
GitHub mirror.

The code archaeology currently supports the following possibilities:

1. **Most likely:** the CG implementation existed in a paper/development
   Palabos branch but was never included in a standard public release.
2. The implementation was distributed separately from the standard Palabos
   tarball and the distribution location is now lost/unindexed.
3. It was intended for public release but the release did not occur; the
   conclusion's "intend to make ... available" wording is compatible with this.
4. Less likely: it was merged into a standard release and later removed. This
   is weakened by its absence from both the contemporaneous v1.5r1 and the
   later complete v2.0r0 snapshot.

At present there is **no source-level evidence** that the code in the 2017
paper can be recovered from the normal Palabos release lineage.

## 6. Secondary implementations found

These are useful cross-checks but are NOT the authors' Palabos source.

### José Oliveira / Cranfield thesis (2017)

Public repository:
https://github.com/oliveirajp/Thesis

The August-2017 thesis states explicitly that its in-house 2D/3D GPU solver
follows the Leclaire color-gradient formulation. The source contains:

- explicit color-gradient evaluation;
- a perturbation operator;
- explicit recoloring parameter `beta`;
- 3D CUDA CG code.

This is an independent Cranfield implementation, not Palabos. It can be used
as a secondary equation-to-code cross-check.

### Other independent code bases

Public code searches also locate Leclaire-family CG ideas in repositories such
as:

- OPM/LBPM;
- Extremumm/CGLBM;
- BADChIMP-cpp;
- PorousMediaSimulation/openLBMPM.

These should be treated as independent implementations / modern comparisons,
not as provenance for the 2017 Palabos source.

## 7. Implication for cg3d-graphite

Do NOT replace the current CG implementation with the current Palabos
Shan-Chen code. It is a different multiphase model.

For a Leclaire audit, use the hierarchy:

1. **Canonical specification:** Leclaire et al. PRE 95, 033306 (2017),
   equations + appendices.
2. **Author software provenance:** historical Palabos claim, but source
   implementation currently unresolved.
3. **Secondary code-level checks:** independent implementations such as the
   2017 Cranfield code and later CG codes.
4. **Our implementation:** independently map each equation into Taichi and
   validate against canonical tests.

Do not copy Palabos source into this repository. Palabos is AGPL-licensed and,
more importantly, the currently public Palabos source is not the target
Leclaire CG implementation.

## 8. Next source-archeology targets

Before declaring the author implementation unrecoverable, the remaining
high-value searches are:

- archived snapshots of the pre-2019 `palabos.org` download/documentation
  site;
- old Palabos release or development tarballs outside the standard v1.5r1 and
  v2.0r0 packages;
- author-specific/public forks or archived branches from 2016-2018;
- research-data attachments associated with the PRE paper;
- code referenced by subsequent papers from the same author group.

If none yields an author source, the correct implementation strategy is a
clean-room, equation-level reimplementation with multiple independent
cross-checks rather than attempting to infer the missing Palabos branch.

## 9. Current trace verdict

```text
Leclaire 2017 paper              FOUND
paper equations / appendix       FOUND
paper claim: implemented Palabos CONFIRMED

Palabos v1.5r1 standard release  INSPECTED — CG source not found
Palabos v2.0r0 full snapshot     INSPECTED — CG source not found
Palabos v2.1r0                   INSPECTED — CG source not found
Palabos v2.2.0                   INSPECTED — CG source not found
Palabos current master           INSPECTED — CG source not found
current Palabos Shan-Chen path   CONFIRMED — not target algorithm

2017 author Palabos CG branch    NOT YET RECOVERED
secondary Leclaire-like code     FOUND
```

This is a provenance result, not evidence that the published algorithm is
incorrect or that Palabos never contained the code in any branch.
