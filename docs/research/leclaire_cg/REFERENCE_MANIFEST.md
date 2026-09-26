# Leclaire/Latt CG reference manifest

Task: `BI-CG-LECLAIRE-IMPLEMENTATION-001`
Product branch: `agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001`
Base: `6c30260dfe0c8b61ea9609e6bffa5c487312cf06`

Purpose: record exactly which sources this task used, how each was obtained,
what role it plays, and which concrete page/equation identifiers are cited by
`PAPER_FORMULATION.md`. Every algorithmic statement in the formulation must be
traceable to a row of this manifest.

Access date for all items below: **2026-09-27** (all downloads verified by the
`%PDF-` header and a SHA256 digest).

## Acquisition note (honest provenance)

The task contract names the **科研通** document-delivery workflow as the
acquisition route. No 科研通 client, credential, or scripted interface exists in
this repository, in the user skill directory, or in the ZCode plugin cache, so
that specific route could not be driven from this session. Rather than stall,
each source was obtained from a **publisher-open or institutional-repository
copy**, which is the strongest available provenance: for every item the artifact
is the version of record deposited by the authors or published open access.
This substitution is recorded here rather than silently absorbed. No source was
taken from an unlicensed mirror.

## Files

Reference PDFs are staged at `docs/research/leclaire_cg/_refs/`. That directory
is listed in `.gitignore` **because this repository is public and R1/R2 are
copyrighted publisher versions**. The digests below are the binding identifiers;
they were verified against the exact bytes used to extract every quoted
equation.

| ID | File (under `_refs/`) | SHA256 |
|---|---|---|
| R1 | `leclaire_2017_PRE95_033306_cg_porous3d.pdf` | `435b4fa1df08d6366d34ef6397e4b8c67bf8e771c0ef5e9830461fd750ae32c3` |
| R2 | `leclaire_2017_IJMPC_cg_vs_pp_benchmark.pdf` | `91fc30f1d597adfafd95080cafe8599d67acfff3bc0917ad49b19a9f4e3d811c` |
| R3 | `akai2018_awr_wetting_bc_cg.pdf` | `073a343175a68e28a0e8a00f9b7c811f9236acb37bf6b15588a6d3a7dd30efdd` |
| R4 | `parmigiani2019_geofluids_transport_enhanced_separation.pdf` | `17aca930e58c1efb477ba84149eec4676a9dd07f24263fb9a30038eb3b0a2962` |

## Mandatory set

### R1 — canonical formulation

- DOI: `10.1103/PhysRevE.95.033306`
- S. Leclaire, A. Parmigiani, O. Malaspinas, B. Chopard, J. Latt,
  "Generalized three-dimensional lattice Boltzmann color-gradient method for
  immiscible two-phase pore-scale imbibition and drainage in porous media",
  Phys. Rev. E **95**, 033306 (2017).
- Role: **primary algorithm specification**. Equations, appendix tables and the
  stated operator ordering are treated as canonical.
- Obtained from: UNIGE *Archive ouverte*, published version,
  `https://archive-ouverte.unige.ch/unige:97528`.
- Page convention: the archived PDF carries a one-page UNIGE cover sheet, so
  **journal page `033306-M` = PDF page `M+1`**. All citations below give the
  equation number plus both page numbers where the distinction matters.
- Note: `PALABOS_LECLAIRE_CODE_TRACE.md` §1 records this file as
  `unige:94117`; the live identifier for the published version is
  `unige:97528`. Recorded here as a correction, not as a contradiction.

### R2 — same-group 3D CGM benchmark

- DOI: `10.1142/S0129183117500851`
- S. Leclaire, A. Parmigiani, B. Chopard, J. Latt, "Three-dimensional lattice
  Boltzmann method benchmarks between color-gradient and pseudo-potential
  immiscible multi-component models", Int. J. Mod. Phys. C **28**(07), 1750085
  (2017).
- Role: implementation/behaviour clarification — D3Q15/D3Q19/D3Q27 comparison,
  interface thickness, wetting and periodicity observations. Used here for
  (a) the explicit statement that the recoloring parameter controls numerical
  interface thickness independently of physical parameters, and (b) the
  warning that periodic closure can mask wetting-BC defects, which is the
  scientific basis of the required asymmetric killer test.
- Obtained from: same-group UNIGE archive deposition (local project corpus,
  `LBM/literature/leclaire_2017_IJMPC_cg_vs_pp_benchmark.pdf`).

### R3 — later wetting-boundary improvement

- DOI: `10.1016/j.advwatres.2018.03.014`
- T. Akai, B. Bijeljic, M. J. Blunt, "Wetting boundary condition for the
  color-gradient lattice Boltzmann method: validation with analytical and
  experimental data", Adv. Water Resour. **116**, 56–66 (2018).
- Role: **later** wetting improvement. Explicitly *not* part of the canonical
  Leclaire-2017 baseline. Treated in `FOLLOWUP_OPTIMIZATION_MAP.md` as an
  individually switchable option; **not** enabled in `L17_CORE`.
- Licence: CC-BY (per the Spiral deposit record). Downloadable, and staged
  locally for verification.
- Obtained from: Imperial College London **Spiral** repository, CC-BY
  accepted/published version, handle `10044/1/58841`.

### R4 — later porous-media variant from the same line

- DOI: `10.1155/2019/5176410`
- A. Parmigiani, P. R. Di Palma, S. Leclaire, F. Habib, X.-Z. Kong,
  "Characterization of transport-enhanced phase separation in porous media
  using a lattice-Boltzmann method", Geofluids **2019**, 5176410.
- Role: later porous-media **application** of the same model family. Used only
  to document where the published line diverges from the 2017 baseline
  (D3Q15 lattice, per-node fictitious-density wetting, an additional
  mass-conservation recoloring step). Not used as a source of equations for
  `L17_CORE`.
- Licence: CC-BY 4.0 (publisher open access).
- Obtained from: PolyPublie (École Polytechnique de Montréal), published
  version, `https://publications.polymtl.ca/5075/`.

## Background source

### R0 — isotropic colour gradient (2011)

- DOI: `10.1016/j.compfluid.2011.04.001`
- S. Leclaire, M. Reggio, J.-Y. Trépanier, "Isotropic color gradient for
  simulating very high-density ratios with a two-phase flow lattice Boltzmann
  model", Comput. Fluids **40**, 93–103 (2011).
- Role: background only. **Not obtained.** No open copy exists: OpenAlex lists
  no OA location, and the PolyPublie record `16599` exposes no PDF.
  R1 does not cite this work for the gradient stencil (see next item), so its
  absence does not block the formulation.

### R5 — high-order isotropic discrete gradient operators (2014) — ADDED SOURCE

- DOI: `10.1007/s10915-013-9772-2`
- S. Leclaire, M. El-Hachem, J.-Y. Trépanier, M. Reggio, "High order spatial
  generalization of 2D and 3D isotropic discrete gradient operators with fast
  evaluation on GPUs", J. Sci. Comput. **59**, 545–573 (2014).
- **Why added:** R1 states that the colour and density gradients use a "3D
  fourth-order isotropic discretization" and cites *this* work as reference
  [88] (R1 PDF p.24 / journal 033306-23, reference list). R1 does **not**
  reproduce the stencil coefficients, so the canonical gradient operator is
  defined by an external source.
- **Status: NOT OBTAINED.** No open copy exists (OpenAlex lists no OA location;
  PolyPublie record `12018` exposes no PDF; no Wayback snapshot of a PDF).
  Consequence for the formulation: the gradient element is recorded as
  `UNRESOLVED` **in its exact published coefficient form**. The task's
  self-contained justification is instead supplied by an explicit lattice
  isotropy derivation (see `PAPER_FORMULATION.md` §6.3), which is labelled as
  *derived here* rather than attributed to R5. A reviewer must treat the
  gradient stencil as the one element whose paper-fidelity rests on a
  derivation rather than on a transcribed equation.

## Source discipline applied

- Every algorithmic statement in `PAPER_FORMULATION.md` carries a source DOI or
  is explicitly labelled `[DERIVED HERE]` or `UNRESOLVED`.
- The only paper added beyond the mandatory set is R5, recorded above with its
  DOI and its reason.
- No Palabos source was copied. Consistent with `LECLAIRE_REFERENCE_SET.md` and
  `PALABOS_LECLAIRE_CODE_TRACE.md`, the public Palabos lineage does not contain
  the 2017 CG implementation, and Palabos is AGPL in any case.
- Secondary independent implementations (Cranfield 2017 thesis, LBPM, CGLBM,
  openLBMPM) were **not** used as equation sources for this formulation. Where
  such code informed the decision to implement something a particular way, that
  is stated in `FOLLOWUP_OPTIMIZATION_MAP.md`, not here.
