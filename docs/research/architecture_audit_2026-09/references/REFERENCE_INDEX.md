# Reference index and missing-literature queue

Access/status date: 2026-09-29. “Missing” means unavailable as a verified full-text extraction in this audit, not proof of no open copy or no prior acquisition. This session used repository evidence and bounded primary-source/author-record discovery; no new PDF analysis or Z Code / DeepSeek acquisition workflow ran.

## Existing CG corpus — reuse, do not duplicate

Binding hashes and original locations: [existing manifest](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/docs/research/leclaire_cg/REFERENCE_MANIFEST.md). Detailed equation extraction: [existing formulation](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/docs/research/leclaire_cg/PAPER_FORMULATION.md). `_refs/` is gitignored and absent from this public clone. Existing manifest says R1–R5 were acquired; those acquisition claims/hashes were not reverified against PDF bytes here.

| ID | Source | Role / availability / next need |
|---|---|---|
| R1 | Leclaire et al. (2017), *Generalized three-dimensional lattice Boltzmann color-gradient method for immiscible two-phase pore-scale imbibition and drainage in porous media*, [DOI](https://doi.org/10.1103/PhysRevE.95.033306) | canonical L17 extraction exists; obtain exact manifest PDF for disputed equations, not a new summary |
| R2 | Leclaire et al. (2017), *Three-dimensional lattice Boltzmann method benchmarks between color-gradient and pseudo-potential immiscible multi-component models*, [DOI](https://doi.org/10.1142/S0129183117500851) | direct historical comparator; extract exact PP variant, parameter matching and limitations before generalizing |
| R3 | Akai, Bijeljic & Blunt (2018), *Wetting boundary condition for the color-gradient lattice Boltzmann method: validation with analytical and experimental data*, [DOI](https://doi.org/10.1016/j.advwatres.2018.03.014) | optional later CG wetting route; not L17 core; existing extraction/variant map |
| R4 | Parmigiani et al. (2019), *Characterization of transport-enhanced phase separation in porous media using a lattice-Boltzmann method*, [DOI](https://doi.org/10.1155/2019/5176410) | later application variant, not automatic correction of R1 |
| R5 | Leclaire et al. (2014), *High order spatial generalization of 2D and 3D isotropic discrete gradient operators with fast evaluation on GPUs*, [DOI](https://doi.org/10.1007/s10915-013-9772-2) | **priority CG PDF**: full table-to-D3Q19 mapping remains unresolved despite older closure language |
| R0 | background 2011 isotropic-colour-gradient entry in existing manifest, DOI `10.1016/j.compfluid.2011.04.001` | manifest says not obtained; title/year/volume/page metadata not independently checked here; verify before citation/extraction |

Production attribution starts at [ADR-001](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/docs/adr/001-hydrodynamic-equilibrium.md) and [algorithm](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/docs/ALGORITHM.md), with Gunstensen / Tölke / Ahrenholz / Guo / Latva–Kokko references. Do not treat that name list as a fully reconstructed pedigree; in particular the min-amplitude recolouring origin remains unidentified. The repository also retains finite-precision papers under `results/conservation_fix/literature/`, indexed in [the existing search report](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/conservation_fix/LITERATURE_AND_IMPLEMENTATION_SEARCH.md). They concern arithmetic, not selection of gas physics.

## SC full-text acquisition/extraction queue

Titles/identifiers below were located on publisher, author-preprint or institutional records; status is **metadata/abstract checked, full formulation NOT extracted in this audit**. This is a targeted starter corpus, not an exhaustive or latest-to-2026 review.

| Priority / ID | Paper and verified route | What it must resolve |
|---|---|---|
| P0 / SC1 | Shan & Chen (1993), *Lattice Boltzmann model for simulating flows with multiple phases and components*, [publisher DOI](https://doi.org/10.1103/PhysRevE.47.1815) | original model classes, force and component definitions; historical baseline only |
| P0 / SC2 | Li et al., *Lattice Boltzmann methods for multiphase flow and phase-change heat transfer*, [author review](https://arxiv.org/abs/1508.00940) | consistency/stability/forcing taxonomy; select relevant primary works, do not import phase-change physics by default |
| P0 / SC3 | Liu et al., *Multiphase lattice Boltzmann simulations for porous media applications — a review*, [author review](https://arxiv.org/abs/1404.7523) | porous-media comparison criteria, MCMP versus other families and validation scope |
| P0 / SC4 | Li & Luo (2013), *Achieving tunable surface tension in the pseudopotential lattice Boltzmann modeling of multiphase flows*, [author paper](https://arxiv.org/abs/1306.6445) | exact source-term mechanism, mechanical stability and limits of independent tuning |
| P0 / SC5 | Li, Luo & Li (2013), *Lattice Boltzmann modeling of multiphase flows at large density ratio with an improved pseudopotential model*, [author paper](https://arxiv.org/abs/1211.6932), [DOI](https://doi.org/10.1103/PhysRevE.87.053301) | improved MRT forcing, density-ratio and interface-width/stability tradeoffs; applicability to noncondensable gas remains to check |
| P0 / SC6 | Coelho et al., *Wetting boundary conditions for multicomponent pseudopotential lattice Boltzmann*, [author paper v2](https://arxiv.org/abs/2009.12584v2), [DOI](https://doi.org/10.1002/fld.4988) | actual multicomponent wetting at inclined/curved walls; dimensional and geometry limits |
| P0 / SC7 | Wang, D'Ortona & Guichardon (2023), *Improved partially saturated method for the lattice Boltzmann pseudopotential multicomponent flows*, [publisher](https://doi.org/10.1103/PhysRevE.107.035301) | complex-wall treatment, isotropy, mass conservation and dissolved-component effects; priority if full text needs user access |
| P1 / SC8 | *Contact angles in the pseudopotential lattice Boltzmann modeling of wetting*, [author paper](https://arxiv.org/abs/1410.2569) | compare wall interaction implementations rather than one generic “SC wetting” claim |
| P1 / SC9 | *Implementation of contact angles in pseudopotential lattice Boltzmann simulations with curved boundaries*, [author paper](https://arxiv.org/abs/1908.04443), [DOI](https://doi.org/10.1103/PhysRevE.100.053313) | virtual-density / wall mass-layer and spurious-current issues; distinguish model class from SC6/SC7 |

R2 belongs in the P0 comparison reading even though already present in the project's acquisition manifest. A contemporary candidate-specific follow-up search beyond these seed papers is still needed before calling a final method ranking “modern/comprehensive.” Do not use review abstracts as substitutes for primary equation extraction.

## What the user can supply for the next session

First: R5 and R2 exact PDFs from the existing library, SC6/SC7 full text, and previous SC code/configuration/evidence. Next: SC2/SC3 reviews and SC4/SC5 equations for candidate selection. Open preprints are already identified for many entries, so manual acquisition may only be needed where existing files or publisher access are required.

For every received PDF, record hash, version, page offset, equations/tables used, assumptions, and unresolved transcription. Extract only the sections needed for the chosen model comparison, with page references to return to the PDF. No claim about a model's entire capability should rest on a single old benchmark.


## Application and comparison sources recovered from cloud context

These entries close a gap in the first pack: generic SC reviews alone do not represent the battery filling and unresolved-binder question. Status is metadata/abstract or author publication record verified, **not full-text equation extraction**. Numerical setup values mentioned by earlier chat assistants have not been promoted to facts.

| Priority / source | Why it matters; extraction needed |
|---|---|
| P0 — Lautenschlaeger et al. (2022), *Understanding Electrolyte Filling of Lithium-Ion Battery Electrodes on the Pore Scale Using the Lattice Boltzmann Method*, [DOI](https://doi.org/10.1002/batt.202200090), [institutional record](https://publikationen.bibliothek.kit.edu/1000146654) | directly addresses realistic cathodes, nanoporous binder, pressure/saturation and residual gas; extract actual multicomponent formulation, geometry mapping, validation and scope |
| P0 — Lautenschlaeger et al., *Homogenized Lattice Boltzmann Model for Simulating Multi-Phase Flows in Heterogeneous Porous Media*, [DOI](https://doi.org/10.1016/j.advwatres.2022.104320), [author preprint](https://arxiv.org/abs/2206.11524) | abstract explicitly combines grayscale and multicomponent Shan–Chen for heterogeneous media/electrode filling; compare assumptions and parameters to a CG grayscale route; record preprint version (v2 includes a supplementary-figure correction) |
| P1 — Zahid & Cunningham (2025), *Review of the Color Gradient Lattice Boltzmann Method for Simulating Multi-Phase Flow in Porous Media: Viscosity, Gradient Calculation, and Fluid Acceleration*, [DOI](https://doi.org/10.3390/fluids10050128), [author publication record](https://engineers.usf.edu/jcunningham/publications-new) | more recent CG variant map, particularly viscosity/gradient/forcing; publisher full text was not inspected in this audit |
| P1 — Yang & Boek (2013), *A comparison study of multi-component Lattice Boltzmann models for flow in porous media applications*, [DOI](https://doi.org/10.1016/j.camwa.2012.11.022) | historical SC/free-energy/CG comparison; recover exact variants and matched controls, do not turn its ranking into a modern universal verdict |

**Revised acquisition order:** obtain/reuse R2 and R5, the two application-specific P0 papers, and prior SC project assets first; use SC2/SC3 to select the modern candidate and then extract candidate-specific forcing/wetting primary papers (including SC6/SC7 where relevant). Many items have public access routes, so a “missing extraction” does not necessarily require the owner to locate a PDF. Original L17 author code is separately tracked in the [implementation reference map](IMPLEMENTATION_REFERENCE_MAP.md).
