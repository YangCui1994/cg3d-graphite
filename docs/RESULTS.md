# Results — real-graphite exploratory runs (v1, 2026-09-13 → 09-15)

Chinese version: [`RESULTS_zh.md`](RESULTS_zh.md). Full method context:
[`ALGORITHM.md`](ALGORITHM.md). This record is **exploratory grade, not
validation grade** — read §6 before reusing any number.

## 1. Overview

| | |
|---|---|
| Geometry | BIL graphite scan119, 200³ subcrop offset (136,136,136), 0.128 µm/voxel → 25.6 µm cube, φ = 0.4475 (Otsu upper bound); buffered to 228×200×200 (§2) |
| Baseline | CapA = 0.06 (σ = 0.0606), ψ_solid = −0.68 (θ ≈ 30°), ν_r = ν_b = 0.1, quasi-steady tol 5e-7 / 15k window, 150k steps/rung cap |
| Runs | X1 stability probes + sanity · X2 drainage (9 rungs) · X3 imbibition–resaturation |
| Raw data | `results/data/` (per-run `report.json`, console logs); frame series and figsets were kept out of git |

## 2. X1 — the NaN diagnosis and the buffer fix (main methodological finding)

The raw 200³ geometry NaNs within 20 000 **equilibrium** steps (no drive, no
interface motion). The five-variant probe chain (`probe_gx1_nan.py`) localized
the trigger:

| Mode | Configuration | Result | Isolates |
|---|---|---|---|
| A | replicate driver (interface at membrane, ψ_solid=−0.68) | ρ→0 in 50 steps, NaN by 150; hotspots have EDT=1.0 single-pixel pores | baseline reproduced |
| B | fully wet start, no interface | **diverges faster** (ψ→+25 within 50) | rules out "interface-triggered" |
| D | B + ψ_solid=−1.0 (wall colour = flux colour) | still diverges (ψ→+1300) | rules out wettability/wall-colour flux |
| E | **no membrane, no reservoir**, plain bounce-back walls | **stable 3000 steps** (umax ~0.04 steady) | locks trigger = **reservoir/membrane forcing × sub-voxel-rough pores** |

Mechanism: the reservoir slab and the ψ-conditional membrane plane sit
directly on the real rough surface; a 1-lu throat under both "prescribed
ρ/ψ" and "bounce-back on two walls" collapses and diverges. The same layout
is stable on smooth sphere-pack surfaces — this is a surface-roughness ×
boundary-mechanism coupling, not a generic solver defect.

**Fix (zero solver changes)**: pad both x faces with 14 lu of open pore so
reservoir(8) + membrane(1) + clean channel(2+) sit entirely in the padding
(`make_geo_buffer.py`). Probe A + buffer-14 is stable (umax 0.019,
decaying). Buffer = 4 **still NaNs** — the padding must fully cover
reservoir + membrane plus margin.

Sanity run (`gx1b`, 228×200×200): 20 000 equilibration steps + three δ
levels, no NaN, leak 1.4e-8 pore volumes/step. Entry calibration:
δ 0.020 → S_nw 0.030 (pre-entry) · 0.040 → 0.069 · 0.080 → 0.217 (main
invasion).

## 3. X2 — primary drainage (gx2b_drain, full 9-rung ladder)

~525k steps total, ~11 h on a desktop RTX 5080; leak 1.8e-8/step. The first
4 rungs reproduce an interrupted first attempt **bit-for-bit**.

| δ | Pc | S_nw | exit | steps |
|---|---|---|---|---|
| 0.030 | 0.0100 | 0.039 | quasi-steady | 25k |
| 0.040 | 0.0133 | 0.098 | quasi-steady | 84k |
| 0.055 | 0.0183 | 0.298 | step cap | 150k |
| 0.074 | 0.0247 | 0.572 | step cap | 150k |
| 0.100 | 0.0333 | 0.628 | quasi-steady | 47k |
| 0.135 | 0.0450 | 0.654 | quasi-steady | 31k |
| 0.182 | 0.0607 | 0.671 | quasi-steady | 18k |
| 0.245 | 0.0817 | 0.680 | quasi-steady | 15k |
| 0.281 | 0.0937 | **0.684** | quasi-steady | 15k |

Driver saturations include the buffer volume; recomputed on the
graphite-only mask (x ∈ [14, 214)) the final state is S_nw = 0.678 →
**residual wetting saturation Sw = 0.322**.

Reading: the entry band is δ ≈ 0.04–0.075 (Pc 0.013–0.025), matching the
geometry audit's EDT entry estimate (Pc 0.0098–0.0264). The main invasion
spreads over two rungs (both hit the step cap while S_nw still crept — a
broad, gentle invasion band, in contrast to the very narrow Pc band of a
sphere packing). Beyond δ = 0.10 each rung equilibrates quickly; the plateau
holds at S_nw ≈ 0.68. No stability events; peak umax 0.097.

## 4. X3 — imbibition–resaturation trapped gas (gx3_ir)

Drain 3 rungs to the post-knee state, then step δ back to 0 (one continuous
implementation). Drainage arm: δ 0.030 → 0.0393 (bit-identical to X2 d00) ·
0.055 → 0.2723 · 0.074 → 0.5579 → **S_i = 0.558**.

| δ (imbibition) | S_nw | exit | steps |
|---|---|---|---|
| 0.055 | 0.567 | quasi-steady | 15k |
| 0.040 | 0.565 | quasi-steady | 15k |
| 0.025 | 0.543 | quasi-steady | 37k |
| 0.012 | 0.405 | step cap | 150k |
| 0.000 | 0.177 | step cap | 150k |

**Trapped-gas end state: S_nr = 0.171** (tail-window mean; the last rung was
still creeping down at the cap, so read it as near an upper bound, band
~0.005–0.01). 32 trapped clusters; top sizes 430 341 / 57 161 / 53 435 /
28 251 / 26 450 / 16 393 / 11 606 / 7 773 voxels. **Largest ganglion = 66.7 %
of all trapped gas = 12.0 % of the graphite pore volume** — inside the
Finney-RCP validation band (S_nr 0.16–0.20, single mega-ganglion ~12 % of
pore), i.e. at this exploratory grade the *magnitude and morphology* of
trapping are robust to "sphere pack vs real electrode".

Physics note: the first two imbibition rungs barely move S_nw — non-wetting
phase retraction through throats needs a lower drive; the bulk resaturation
happens at δ ≤ 0.012.

## 5. Figure index

| File | Content |
|---|---|
| `results/figures/fig_gx_pcs.png` | full Pc–S drainage curve (9 rungs) |
| `results/figures/fig_gx_slices_v2.png` | constant-pressure invasion slice series (grey graphite / blue liquid / red gas) |
| `results/figures/fig_gx_solid_only.png` | structure slices + proportional boundary map (wall / inlet reservoir / membrane / buffer / graphite face / outlet reservoir) |
| `results/figures/fig_gx_ir.png` | I–R points + trapped-cluster size CCDF |
| `results/figures/fig_gx_imb_pair.png` | before/after imbibition: connected gas at S_i vs trapped clusters at S_nr |
| `results/figures/anim_gx_drain_d03_iso.gif` | main-invasion animation (7 frames, constant δ = 0.074, iso view, inlet/outlet arrows) |

## 6. Honest boundaries

1. φ = 0.4457 is an Otsu upper bound (carbon-binder domains counted as
   pore); threshold-sensitive by a few %.
2. Throat p50 = 1.73 lu < interface width 2.2 lu: fine pores are hydraulic
   dead zones; the flowing subset is set by p95+ throats. Without an NMC811
   control arm, curve anomalies cannot be attributed to graphite physics vs
   under-resolution artifacts (a known, deliberate limitation of this arm).
3. y/z periodic wrap of a real cube: artificial cross-face connectivity
   (declared, no mirror tiling).
4. Single realization, single window (offset (136,136,136)): no statistical
   spread.
5. The 14-lu buffer alters inlet-region flow (entry effects are absorbed
   there); the graphite interior is unaffected, and all quantitative
   saturations use the graphite-only mask.
6. Isolated ρ=0 pore cells (cavities fully enclosed by solid) exist in all
   modes incl. the stable one — a voxelization artifact, no flow
   contribution.
7. Single-phase permeability was not measured in this arm (it is the first
   gate of upgrading this line to a formal one).

## 7. Reproduce

```bash
cp data/geo_graphite_200.npz .
python make_geo_buffer.py                       # geo_graphite_228b14.npz
python probe_gx1_nan.py --mode A|B|C|D|E [--buffer 14]   # NaN chain
python run_pcs_cg3d.py --geo geo_graphite_228b14.npz --capa 0.06 \
  --psi-solid -0.68 --ds 0.030 0.040 0.055 0.074 0.100 0.135 0.182 0.245 0.281 \
  --max-steps 150000 --dump-every 20000 --tag gx2b_drain
python run_ir_cg3d.py --geo geo_graphite_228b14.npz --capa 0.06 \
  --psi-solid -0.68 --ds-drain 0.030 0.055 0.074 \
  --ds-imbibe 0.055 0.040 0.025 0.012 0.0 --max-steps 150000 --tag gx3_ir
python graphite_figs.py --tag-drain gx2b_drain --tag-ir gx3_ir --picks 6
python viz3d.py figset --run results_pcs_cg3d/gx3_ir --cutaway 0.5 --out gx3_figset
python viz3d.py animate --series results_pcs_cg3d/gx2b_drain/frames \
  --out anim_gx_drain --duration 800 --gif-width 900 --opaque both --view iso
```

Wall-clock on a desktop RTX 5080: drainage ~11 h, I–R ~17 h, each as a
single process (one JIT compile tax of ~5.5 min per process). Expect the
step-cap rungs to sit at the cap — that is the ladder design, not a bug.
