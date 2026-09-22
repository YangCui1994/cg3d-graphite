# REVIEW — CG3D-IMB-002 / Review 001

## Binding

- Task: `CG3D-IMB-002 Production-Geometry Direct-Imbibition Pilot`
- Task commit: `ef13a4dbf1a90fde991b5ab8bde2c62b82ffdf47`
- Simulation source used by all pilot runs: `ef13a4dbf1a90fde991b5ab8bde2c62b82ffdf47`
- Evidence / post-processing commit: `45fdf5f105124e7fc52a13f3c675b7336212985e`
- Branch: `agent-dev/direct-imbibition-pilot`
- Review mode: independent static/evidence review

## Decision

`PASS`

This PASS accepts the bounded production-geometry pilot as valid **pilot evidence** for the accepted direct-imbibition baseline.

It does **not** establish physical convergence, a preferred `prewet_layers` value, quantitative industrial filling validity, or trapped-gas saturation.

---

## Source integrity

PASS.

All three GPU pilot runs used source commit `ef13a4d`.

Relative to the accepted Step-0 baseline, that commit only added the pilot task document; solver/protocol/direct-imbibition physics were unchanged.

The later commit `45fdf5f` adds only:

- deterministic post-processing helper `imb_pilot_figs.py`;
- durable validation summary;
- small comparison/QA figures.

The analysis helper is post-hoc and does not enter the simulation path.

---

## Geometry gate

PASS.

Evidence records:

- production geometry exists;
- shape = `(228, 200, 200)`;
- structured `real_x=[14,214]`;
- graphite-region porosity = 0.4475;
- buffer slabs remain open pore;
- geometry solid bytes match the accepted baseline.

No solid-occupancy inference was used for real-domain bounds.

---

## Pilot execution

PASS.

The requested order was followed:

1. N=4
2. N=2
3. N=6

Each case:

- ran sequentially on the production GPU;
- used `delta=0`, `psi_solid=-0.68`, `capa=0.06`;
- reached exactly 10,000 steps;
- exited via the configured `max-steps` pilot horizon;
- returned exit code 0;
- showed finite sampled diagnostics and finite final phase field;
- remained below the configured `umax-cap=0.12`;
- preserved the accepted phase/boundary orientation.

No full production campaign or retry-until-pass behavior was introduced.

---

## Main observed pilot results

### Final real-region gas saturation

| prewet N | initial binary gas saturation | final binary gas saturation @10k | gas-fraction decrease |
|---:|---:|---:|---:|
| 2 | 0.9898 | 0.9581 | 0.0317 |
| 4 | 0.9799 | 0.9484 | 0.0315 |
| 6 | 0.9700 | 0.9390/0.9391 | 0.0310 |

The three cases therefore exhibit very similar net early-time liquid uptake over the 10,000-step pilot.

The N=2 minus N=6 gas-saturation spread is approximately:

- initial: 0.0199;
- 10k: 0.0190.

Within this bounded pilot, the separation remains close to the imposed initial pre-wet offset rather than strongly amplifying.

This is a descriptive pilot observation only.

### Direction / stability

Evidence is consistent with intended +x liquid invasion:

- reported liquid-front advance is about +5 lu in each case;
- `u_bulk_x` is positive;
- reservoir phase-flux counters are consistent with liquid supply from the left and gas removal at the right;
- no NaN / rough-boundary instability recurrence is reported;
- no phase-direction reversal is reported.

The task's bounded stability question is therefore satisfied.

---

## Comparison evidence

PASS.

Committed evidence includes:

- `gas_saturation_real_vs_step.png`
- `imbibition_slices_compare.png`
- `final_phase_profile_compare.png`
- initial-state profile/slice figures for N=2/4/6
- `initial_state_compare.png`

The post-processing helper:

- reads saved frames only;
- uses explicit `real_x`;
- distinguishes binary and continuous gas saturation;
- documents frame quantization;
- does not claim remaining gas is trapped.

A rendering bug in the first slice-comparison attempt was disclosed, localized to the new plotting helper, fixed, and the figures regenerated. Simulation data were not affected.

---

## Requirement disposition

| Requirement | Review |
|---|---|
| production geometry gate | PASS |
| N=4 → 2 → 6 execution order | PASS |
| fixed 10k horizon | PASS |
| no convergence overclaim | PASS |
| numerical finite/stability pilot | PASS |
| intended +x invasion direction | PASS |
| no rough-boundary failure recurrence in pilot | PASS |
| pre-wet sensitivity comparison | PASS |
| durable validation summary | PASS |
| same-time slices | PASS |
| time-history comparison | PASS |
| endpoint x-profile comparison | PASS |
| raw large outputs excluded from Git | PASS |
| trapped-gas analysis | NOT IMPLEMENTED / correctly deferred |
| physical validation of preferred N | OUT OF SCOPE |

---

## Non-blocking notes

### 1. `umax` terminology

The evidence table reports the last sampled `umax_last`, not a strict maximum over every timestep of the 10k run.

For this pilot the values are safely below the cap and no `umax-cap` termination occurred, so this does not affect acceptance.

Future automated evidence should distinguish:

- `umax_last`;
- maximum sampled `umax`;
- true per-step maximum if ever required.

### 2. Pilot plotting helper is layout-specific

`imb_pilot_figs.py` is appropriately narrow for this task, but it assumes the baseline layout in a few places (default wall/reservoir thickness and membrane markers x=11/217).

Do not treat it as a general geometry-independent visualization API without a later cleanup.

### 3. Front-position metric provenance

The durable summary reports approximately +5 lu front motion, but the front-extraction calculation is not exposed as a first-class reusable metric in the committed helper.

The saturation trajectories and same-time slice evidence are sufficient for this task. If front position becomes a quantitative scientific observable later, define the threshold/connectivity rule explicitly and validate it.

---

## Scientific interpretation boundary

This review accepts only the following bounded observation:

> On the accepted 228x200x200 buffered graphite setup, all three N=2/4/6 direct-imbibition cases remain numerically stable over the first 10,000 steps, show intended +x liquid invasion, and have very similar incremental liquid uptake; most of the separation in gas saturation between the three trajectories remains close to the initially imposed pre-wet offset.

This review does not conclude:

- that N=2, 4, or 6 is physically preferable;
- that the system is converged;
- that remaining gas is trapped;
- that the outlet model is physically final;
- that the model quantitatively reproduces industrial electrolyte filling.

---

## Next action

The next modeling decision should determine which scientific question to resolve next before extending the production campaign. The most direct candidates are:

1. whether the initial sharp liquid/gas interface should be retained or replaced by a diffuse equilibrium-like interface;
2. whether the pilot horizon should be extended to determine when the N=2/4/6 trajectories lose or retain memory of the initial pre-wet offset;
3. how to define outlet-connected versus trapped gas for later filling analysis.
