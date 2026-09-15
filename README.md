# cg3d-graphite

Pore-scale two-phase Lattice-Boltzmann simulation of drainage and imbibition
in a **real Li-ion graphite-anode microstructure** (lab X-ray nano-CT), with
the application target of **electrolyte filling / trapped gas in battery
electrodes**.

The solver is a 3D **D3Q19 MRT color-gradient (Rothman–Keller)**
two-phase model written in [Taichi](https://github.com/taichi-dev/taichi),
driven by a stepped capillary-pressure ladder through
ψ-Dirichlet reservoirs and semi-permeable membranes, so the simulation is an
**open system** with pressure boundaries on both ends. Visualization is a
scripted offscreen [PyVista](https://docs.pyvista.org) pipeline
(slice montages, 6-panel figsets, per-cluster renderings, GIF animations)
with mandatory inlet/outlet flow markers.

中文版文档见 [README_zh.md](README_zh.md)。

## What was done with it

Three core runs on a 200³ subcrop of BIL graphite scan119
(0.128 µm/voxel → a 25.6 µm cube of real graphite electrode):

| Run | What | Headline result |
|---|---|---|
| X1 sanity + NaN probes | stability of the reservoir/membrane layout on a sub-voxel-rough real surface | **Forcing conditions must not sit on the rough face**: the raw layout NaNs within ~200 equilibrium steps; a 14-lu open-pore buffer at both x faces fixes it with **zero solver changes** |
| X2 drainage (`run_pcs_cg3d.py`) | 9-rung capillary-pressure ladder | entry band Pc 0.013–0.025 (matches EDT estimate); plateau S_nw → 0.684; residual wetting saturation in the graphite region **Sw = 0.322** |
| X3 imbibition–resaturation (`run_ir_cg3d.py`) | drain to S_i = 0.558, then step δ back to 0 | trapped gas **S_nr = 0.171**, 32 clusters, largest ganglion = 66.7 % of trapped gas = 12 % of pore volume — inside the Finney-RCP validation band (0.16–0.20) |

Selected figures live in [`results/figures/`](results/figures/); the full
numbers and honest caveats are in [`docs/RESULTS.md`](docs/RESULTS.md).

**Exploratory grade.** The median throat of this graphite (p50 = 1.73 lu) is
*narrower* than the CG interface width (2.2 lu), so the flowing subset of the
pore space is set by the p95+ throats and all conclusions are
exploration-grade, not validation-grade. See the seven honest boundaries in
`docs/RESULTS.md §6` before reusing any number.

## Repository layout

| Path | Content |
|---|---|
| `lbm_solver_cg3d.py` | The solver: D3Q19 MRT color-gradient two-phase, race-free per-colour membranes, ρ-prescribed ψ-Dirichlet reservoirs, per-node wettability field. Taichi, GPU by default (`LBM_ARCH=cpu` to force CPU) |
| `run_pcs_cg3d.py` | Primary-drainage driver: stepped δ ladder → Pc–S curve, quasi-steady exit criterion, per-rung snapshots + incremental `report_partial.json` |
| `run_ir_cg3d.py` | Imbibition–resaturation driver: drain to a chosen S_i, then step δ back down (state carried across rungs in one implementation) |
| `make_geo_buffer.py` | Pads the 14-lu open-pore buffer (the NaN fix) onto the raw 200³ geometry |
| `probe_gx1_nan.py` | The 5-variant NaN diagnostic chain (A/B/C/D/E) that localized the divergence trigger |
| `audit_graphite_geo.py` | Geometry audit: percolation fraction, throat EDT statistics, best-window selection, entry-pressure estimate |
| `process_electrode_BIL.py` | Raw BIL nano-CT stack → segmented npz cube (pipeline used to build the geometry) |
| `viz3d.py` (+ `viz3d.cmd`) | Offscreen PyVista rendering: `figset` (6 panels), `animate` (GIF), slice montages, per-cluster colouring, inlet/outlet flow markers |
| `graphite_figs.py`, `graphite_slices_v2.py`, `graphite_imb_pair.py` | 2D result figures (Pc–S curve, constant-pressure slice series, imbibition before/after) |
| `data/geo_graphite_200.npz` | The simulation geometry: graphite scan119 200³ subcrop, offset (136,136,136), φ = 0.4475 (int8 solid mask) |
| `results/figures/` | Selected figures + drainage-invasion GIF |
| `results/data/` | Run `report.json` files and console logs (small; the full frame series and figsets stay out of git) |
| `docs/` | Method, results, and ops documentation (bilingual) |

### Relationship to the LBM 2phase tree

Twelve files in this repo are copy pairs with
`LBM/source_code/taichi_LBM3D/2phase/` (the LBM working tree, reorganized
into category subdirectories 2026-09-16): `lbm_solver_cg3d.py`,
`run_pcs_cg3d.py`, `run_ir_cg3d.py`, `make_geo_buffer.py`,
`audit_graphite_geo.py`, `probe_gx1_nan.py`, `process_electrode_BIL.py`,
`viz3d.py`, `viz3d.cmd`, `graphite_figs.py`, `graphite_slices_v2.py`,
`graphite_imb_pair.py`. Content is identical except for (a) CRLF vs LF line
endings in some pairs and (b) the 2phase copies of six files carrying
2phase-layout adaptations (a `sys.path` bootstrap header, a `data/` path
prefix, parent-directory `chdir`); this repo stays flat and
repo-root-relative. When changing a shared file, edit one side, re-diff,
then port deliberately — do not copy blindly.

## Quickstart

Requirements: Python 3.10+, CUDA GPU recommended (a 200³ run needs
≈ 4.6 GB VRAM; CPU works but is ~14× slower), then
`pip install -r requirements.txt`.

```bash
# 1. Rebuild the buffered geometry (228x200x200 = 200^3 cube + 14-lu open buffer per x face)
cp data/geo_graphite_200.npz .
python make_geo_buffer.py            # writes geo_graphite_228b14.npz

# 2. Primary drainage, 9-rung ladder (~11 h on a desktop RTX 5080)
python run_pcs_cg3d.py --geo geo_graphite_228b14.npz --capa 0.06 \
  --psi-solid -0.68 --ds 0.030 0.040 0.055 0.074 0.100 0.135 0.182 0.245 0.281 \
  --max-steps 150000 --dump-every 20000 --tag gx2b_drain

# 3. Imbibition-resaturation (drain 3 rungs to S_i≈0.56, then imbibe to delta=0; ~17 h)
python run_ir_cg3d.py --geo geo_graphite_228b14.npz --capa 0.06 \
  --psi-solid -0.68 --ds-drain 0.030 0.055 0.074 \
  --ds-imbibe 0.055 0.040 0.025 0.012 0.0 --max-steps 150000 --tag gx3_ir

# 4. Figures
python graphite_figs.py --tag-drain gx2b_drain --tag-ir gx3_ir --picks 6
python viz3d.py figset --run results_pcs_cg3d/gx3_ir --cutaway 0.5 --out gx3_figset
python viz3d.py animate --series results_pcs_cg3d/gx2b_drain/frames \
  --out anim_gx_drain --duration 800 --gif-width 900 --opaque both --view iso
```

Before changing anything, read [`docs/BC_IC_OUTPUT.md`](docs/BC_IC_OUTPUT.md)
(the operational reference for boundaries / initial conditions / output
selection, Chinese) — it explains the x-layout semantics, the
ψ_solid → contact-angle registry, and why the buffer rule must not be
skipped on rough geometries.

## Documentation

| Doc | Content |
|---|---|
| [`docs/ALGORITHM.md`](docs/ALGORITHM.md) / [`_zh`](docs/ALGORITHM_zh.md) | The method: lattice, MRT moments, colour recoloring, wettability, reservoir/membrane pressure boundaries, the ρ-corrected equilibrium |
| [`docs/RESULTS.md`](docs/RESULTS.md) / [`_zh`](docs/RESULTS_zh.md) | Full run record: NaN diagnosis chain, drainage ladder table, imbibition trapped-gas statistics, honest boundaries, exact reproduce commands |
| [`docs/BC_IC_OUTPUT.md`](docs/BC_IC_OUTPUT.md) | Ops reference for opening new simulations (boundaries / ICs / output defaults) |
| [`docs/VIZ_3D_STYLE.md`](docs/VIZ_3D_STYLE.md) | 3D visualization spec: camera recipes, colour palette with measured grayscale safety, flow-marker placement rules |

## Operational notes (learned the hard way)

- **JIT compile tax**: first solver instantiation in a process costs ~5.5 min
  (unrolled MRT kernels). Batch drivers should reuse one instance and re-init
  per case; never launch one process per rung.
- **Never edit an imported `.py` while a batch runs** — Taichi hot-reloads it
  mid-run and corrupts the batch.
- Output defaults follow the project rule "never head/tail-only": frames are
  dumped every 20 000 steps with the rung δ in the filename, and each rung
  writes an incremental `report_partial.json` so interrupted ladders lose
  nothing.
- Don't run PyVista rendering in parallel with GPU simulations on the same
  card.

## Data source and license

The geometry shipped in `data/` derives from the
**Battery Imaging Library (BIL)**, graphite-anode nano-CT scan 119
(pristine, 0.128 µm/voxel), licensed **CC-BY-4.0**:

- BIL: <https://www.batteryimaginglibrary.com>
- Paper: R. Docherty et al., *Battery Imaging Library*, 2025,
  DOI [10.26434/chemrxiv-2025-sbp73](https://doi.org/10.26434/chemrxiv-2025-sbp73)
- Scan record: [10.5281/zenodo.18601879](https://doi.org/10.5281/zenodo.18601879)
  (file `A-A015A-Anode-Fresh`)

If you use the geometry, cite the BIL website and the paper above.
`process_electrode_BIL.py` shows how the raw stack was segmented and cropped.

## Code license

MIT — see [LICENSE](LICENSE). This project is a derivative of
[yjhp1016/taichi_LBM3D](https://github.com/yjhp1016/taichi_LBM3D)
(MIT, © 2021 Jianhui Yang, Liang Yang): the 3D solver in this repo is a
class-based rewrite whose numerical tables (moment matrix, recoloring pairs,
relaxation layout) come from that upstream, with four known upstream defects
fixed (see the solver docstring and `docs/ALGORITHM.md §7`).
