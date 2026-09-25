# Conservation Fix Literature Note

## Purpose

This note records the literature constraints that inform
`BI-SOLVER-CONSERVATION-FIX-001`.

It intentionally separates:

1. statements supported by published LBM literature;
2. implementation-specific findings from this repository's conservation audit.

The exact repository defect

`sum_s inv_M[s,0] - 1 = +1.490116119e-8`

for the stored f32 D3Q19 MRT inverse matrix was **not** located as a directly
documented published case during the external two-pass search. It should be
treated as a repository-specific implementation defect established by our
audit evidence, not as a literature-known universal MRT bug.

## 1. Precision: FP32 is not inherently disqualified

Lehmann et al. (2022) benchmarked LBM with FP64, FP32 and reduced precision and
found the accuracy difference between FP64 and FP32 negligible in almost all
tested cases.

Reference:

Moritz Lehmann, Mathias J. Krause, Giorgio Amati, Marcello Sega,
Jens Harting, Stephan Gekle,
"Accuracy and performance of the lattice Boltzmann method with 64-bit,
32-bit, and customized 16-bit number formats",
Physical Review E 106, 015308 (2022).

DOI:
https://doi.org/10.1103/PhysRevE.106.015308

Implication for this project:

- do not replace the whole solver with FP64 merely because the present f32
  implementation drifts;
- identify the violated conservation identity and repair the smallest scope;
- retain a full-f64 path as a numerical reference and performance comparison.

## 2. Conserved moments are invariants of collision

In MRT LBM, density and momentum belong to the conserved moment subspace.
A collision implementation must therefore preserve the zeroth moment except
for explicitly modelled source/boundary terms.

For this repository's closed C0-C3 audit cases there are no mass sources.

Implementation invariant:

```text
sum_q f_q(post-collision) == m0(pre-collision)
```

to the expected arithmetic representation floor, without a persistent
one-sided bias.

This project will treat the invariant itself as the acceptance object rather
than accepting a small long-horizon drift merely because FP32 is used.

## 3. Color-gradient recoloring is intended to conserve component masses

Latva-Kokko & Rothman (2005) developed the recoloring treatment for
gradient-based immiscible LBM and explicitly discuss mass-conservation
constraints and sensitivity to small numerical errors.

Reference:

M. Latva-Kokko and D. H. Rothman,
"Diffusion properties of gradient-based lattice Boltzmann models of immiscible
fluids",
Physical Review E 71, 056702 (2005).

DOI:
https://doi.org/10.1103/PhysRevE.71.056702

Leclaire, Reggio & Trépanier (2012) numerically evaluated recoloring operators
in immiscible color-gradient LBM.

Reference:

S. Leclaire, M. Reggio, J.-Y. Trépanier,
"Numerical evaluation of two recoloring operators for an immiscible two-phase
flow lattice Boltzmann model",
Applied Mathematical Modelling 36 (2012) 2237-2252.

DOI:
https://doi.org/10.1016/j.apm.2011.08.027

Leclaire et al. (2012) / later 3D color-gradient formulations use perturbation
and recoloring operators under mass/momentum-conservation constraints.

Implication for this project:

after equilibrium + recoloring, enforce/verify separately

```text
sum_q g_r,q(post) == rho_r(pre)
sum_q g_b,q(post) == rho_b(pre)
```

and do not hide a per-colour leak inside a conserved combined total.

## 4. Recent conservative-recoloring work reinforces the component-mass requirement

A 2026 preprint by Jiang et al. examines a ternary color-gradient recoloring
case where a conventional partition can fail to conserve individual species
under directional non-equilibrium and proposes local conservative replacements.

Reference:

Fei Jiang, Yu Zhao, Chaozhong Qin, Shinsuke Mochizuki, Takeshi Tsuji,
"Mass-conservative recoloring schemes for ternary color-gradient lattice
Boltzmann models with miscible components" (2026 preprint).

DOI / record:
https://doi.org/10.2139/ssrn.7211143

This is not the same binary algorithm as this repository and must not be cited
as proof of our exact defect. It is relevant because it demonstrates that:

- total-mass conservation can hide component/species drift;
- conservative local repartitioning can be a legitimate correction strategy;
- non-equilibrium directional information must be checked when designing such
  a correction.

## 5. Existing 3D color-gradient literature

Liu, Valocchi & Kang presented a D3Q19 color-gradient model whose perturbation
step is derived under mass and momentum conservation and which applies a
recoloring step for phase segregation.

Reference:

Haihu Liu, Albert J. Valocchi, Qinjun Kang,
"Three-dimensional lattice Boltzmann model for immiscible two-phase flow
simulations",
Physical Review E 85, 046309 (2012).

DOI:
https://doi.org/10.1103/PhysRevE.85.046309

PubMed:
https://pubmed.ncbi.nlm.nih.gov/22680576/

This is useful as a model-level constraint, not as evidence for any one
floating-point repair.

## 6. External search result: what was NOT found

Two search passes were performed.

Pass 1:
- MRT conserved moments;
- single precision / roundoff in LBM;
- color-gradient recoloring mass conservation;
- zeroth-moment corrections.

Pass 2 expanded to:
- implementation precision;
- inverse transform / moment matrix;
- open-source / numerical implementation discussions;
- conservative local corrections.

No directly matching publication was found that reports:

```text
D3Q19 MRT
+ stored inverse matrix cast to float32
+ column-sum error ~1e-8
+ deterministic linear mass growth ~1e-8 per step
```

Therefore the repository's matrix diagnosis remains an original,
implementation-specific empirical/numerical finding.

## 7. Repository-specific diagnosis that the literature does not replace

Current audit evidence:

```text
sum_s inv_M[s,0] - 1 = +1.490116119e-8
C3 GPU total drift  ~= +1.556e-8 / step
C3 CPU total drift  ~= +1.517e-8 / step
V2 production       ~= +1.53e-8 / step
```

The quantitative correspondence is stronger evidence for this codebase than
any generic precision statement.

A second colour-channel closure defect exists independently.

## 8. Design implications for the solver-fix task

The fix task must compare alternatives before selecting one.

### Total-distribution channel

T1 — stored-matrix zeroth-moment projection

T2 — local post-reconstruction zeroth-moment projection, designed to preserve
momentum exactly

T3 — full-f64 MRT roundtrip numerical reference

Also explicitly demonstrate that:

```text
f64 accumulator + unchanged f32 inv_M
```

does not remove the matrix-identity bias.

### Colour channel

C1 — local per-colour zeroth-moment projection after equilibrium/recoloring

C2 — any literature-supported alternative found by the executor's own search

Do not assume recoloring itself is the dominant source until the equilibrium
sum and recoloring increments are measured separately.

## 9. Literature-informed acceptance principles

The selected production fix should:

1. enforce the relevant conservation identities locally;
2. remove persistent one-sided drift rather than merely reduce global error;
3. preserve momentum and the validated stress/wetting/surface-tension behaviour;
4. keep FP32 where possible;
5. use FP64 as a reference unless evidence shows it is required in production;
6. retain explicit per-colour conservation tests in future regressions.


## 10. Citation errata from external solver-fix review

Two metadata corrections are part of the durable record:

- Dubois & Philippi, "Multiple relaxation times lattice Boltzmann schemes with
  projection", Physics of Fluids 37, 037179 (2025), DOI
  **10.1063/5.0254041**.
- The 3D D3Q19 immiscible paper linked by PMID 22680576 is **Liu, Valocchi &
  Kang**, Physical Review E **85**, 046309 (2012), DOI
  **10.1103/PhysRevE.85.046309**; it is not a Leclaire PRE 86 paper.

These papers provide model/numerical context only. Neither is evidence of the
repository-specific f32 inverse-column-sum defect.
