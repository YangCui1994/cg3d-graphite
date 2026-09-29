# 05 — Validation evidence map

## Production evidence to preserve

| Evidence | Recorded result | What it does not establish |
|---|---|---|
| [V1c](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/levelc_v1c/EXECUTION_REPORT.md) | both differential hydraulic gates pass after probe-validity analysis | universal Washburn law or absence of all entrance losses |
| [V2 primary](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/levelc_v2/v2_primary/EXECUTION_REPORT.md) | max mirror error 0.0013 lu; blue drift 6.7e-4; one trapped cluster; interaction NOT_REACHED | successful front collision or real-air compression |
| [conservation diagnosis](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/conservation_audit/EXECUTION_REPORT.md) | finite-precision total/colour bookkeeping mechanisms localized | physical model fidelity |
| [fix comparison](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/conservation_fix/CANDIDATE_COMPARISON.md) | T1/T2 uniform-state regression led to T3 selection | all colour drift closed at that earlier stage |
| [colour closure](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/colour_closure/EXECUTION_REPORT.md), [ablations](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/colour_closure/CANDIDATE_COMPARISON.md) | T3+C1X+A2 selected; V2 blue error about 5.2e-7; extended horizons and regressions | backend-independent conservation or readiness of every battery configuration |

These are stored report claims; this audit did not rerun the production simulations. Later [external acceptance](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/.agent/evidence/BI-COLOUR-CLOSURE-001/EXTERNAL_SCIENTIFIC_REVIEW_PASS.md) must be read at its exact scope.

## L17 Pass-06 — preserve record and separate interpretation

Source: [machine summary](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/leclaire_cg/pass-06/SUMMARY.json), [report](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/leclaire_cg/pass-06/VALIDATION_REPORT.md), [run manifest](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/leclaire_cg/pass-06/run_manifest.json). Computation source is `9773a43`, evidence tip `5dca114`.

| Case / retained evidence | Stored verdict | Scientific reading at audit date |
|---|---|---|
| [01 uniform](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/leclaire_cg/pass-06/case-01-uniform-stationarity/metrics.json) | PASS | stationary-state check only |
| [02 planar](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/leclaire_cg/pass-06/case-02-planar-interface/metrics.json) | PASS | drift ~0.00567 lu, near-stationary interface |
| [03 Laplace](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/leclaire_cg/pass-06/case-03-laplace-multi-radius/metrics.json) | FAIL_SOLVER | free-intercept sigma/input=1.12692; zero-intercept ~1.0412; high R² does not close calibration |
| [04 contact angle](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/leclaire_cg/pass-06/case-04-contact-angle/metrics.json) | PASS | 65.19/95.70/129.40 degrees for 60/90/120; within 15-degree project gate, not arbitrary accuracy |
| [05 beta-width](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/leclaire_cg/pass-06/case-05-beta-width-validity/metrics.json) | PASS | positivity-valid beta interval only; not a physical refinement calibration |
| [06 axis symmetry](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/leclaire_cg/pass-06/case-06-axis-symmetry-isotropy/metrics.json) | PASS | cubic-axis symmetry, not general rotational isotropy |
| [07 slit Pc](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/leclaire_cg/pass-06/case-07-slit-capillary-pressure/metrics.json) | PASS | signed 60/90/120 check; 90 degrees uses absolute near-zero gate |
| [08 Jurin](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/leclaire_cg/pass-06/case-08-jurin-equilibrium/metrics.json) | FAIL_SOLVER | measured node-threshold rise 1 lu vs coded 8 lu; later review rejects applicability of that theory |
| [09 asymmetric wall](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/leclaire_cg/pass-06/case-09-asymmetric-wall/metrics.json) | FAIL_SOLVER | wall-band change -0.068308; global component excursions ~2.7e-13; no stationary reference for attribution |
| [10 conservation](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/leclaire_cg/pass-06/case-10-conservation/metrics.json) | PASS | isolated NumPy/f64 only |
| [11 mechanical sigma](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/leclaire_cg/pass-06/case-11-mechanical-sigma/metrics.json) | PASS | ratio ~0.999995 with premises checked and distributions retained |

**FACT:** recorded count is 8/3. **SOURCE CLAIM:** latest [fresh review](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/.agent/evidence/BI-CG-LECLAIRE-JURIN-PROVENANCE-CLOSURE-001/FRESH_REVIEW.md) is CHANGES_REQUESTED and advocates INVALID_TEST/out-of-scope for case-08 and more cautious interpretation of case-09. This pack does not issue replacement verdicts or edit stored metrics.

## Evidence access and reproducibility levels

- Manifest → case metadata → metrics/time series → raw NPZ → instrument/figure code is the inspection path. Summaries are not independent observations.
- The fresh review reports full rerun equivalence (320/320 metric fields, 39/39 raw files) and independent diagnostic reconstructions. These are **reviewer claims**, not reruns performed for this pack.
- Static audit confirms frozen source and evidence-tip solver/tests are identical, and identifies the broken per-case import path described in [06](06_FAILURE_CASE_STUDIES.md). A full-matrix command working does not prove each delivered reproducer works.
- The gravity-scaling control cited in commit prose is not durable in the inspected Pass-06 bundle; review staging measurements do not repair that archival gap.
- Top-level L17 reports and Pass-04/05 artifacts remain historical; do not pool their verdicts with Pass-06. The control review is later than the product headline.
