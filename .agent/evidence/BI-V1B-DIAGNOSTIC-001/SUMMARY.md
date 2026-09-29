# SUMMARY — BI-V1B-DIAGNOSTIC-001

- **Candidate SHA:** `a9c6db87da2eeb3572607152391fe6863394ebee`
  (branch `agent-task/BI-V1B-DIAGNOSTIC-001`, base `e9540bca…`,
  producer `da9a13d…`; remote branch verified at the candidate SHA)
- **Reviewer decision:** **HUMAN_REQUIRED** (fresh session
  `sess_b2c10344-a1db-4d78-aa5e-01ee20391d91`, exit 0; see `REVIEW.md`)

## Static same-slit calibration (V1b-B)

| Case | `Pc_static` | `C_static = Pc·h/(2σ)` | `theta_static_slit` |
|---|---|---|---|
| h=26 | 3.1316e-3 | 0.6705 | 47.90° |
| h=40 | 2.2845e-3 | 0.7525 | 41.19° |

h26/h40 relative difference of `C_static`: **11.53% > 10% gate (FAIL)**;
both angles far from the 30° droplet registry — the registry does not
transfer quantitatively to the slit geometry.

## Corrected dynamic filling (V1b-C)

| Case | `V_meas` | `Pc_dynamic` | `V_hyd` | mismatch `|V/V_hyd−1|` |
|---|---|---|---|---|
| h=26 (L_hyd=241) | 4.9743e-3 | 2.8844e-3 | 6.7422e-3 | **26.2% (FAIL)** |
| h=40 (L_hyd=241) | 5.5878e-3 | 1.7970e-3 | 9.9415e-3 | **43.8% (FAIL)** |

Fronts stable, monotonic, `R2[x,t]` ≈ 1−2e-6; gates g1–g6 PASS;
g7 (V/V_hyd ≤ 10%) and g8 (gas-leg Poiseuille, 0.72–0.78×) FAIL.

## Length scan (V1b-D)

h=26: L1=241, V1=4.9743e-3; L2=477, V2=3.0002e-3 →
**`L_eq` = 117.7 lu, `L_eq/L1` = 0.49** (old V1 ≈ 0.78 — halved but
still order-one; reviewer further finds `L_eq/L1` ≈ 0.78 at h=40).

## Maximum five unresolved scientific issues (reviewer blocking findings)

1. `V_meas/V_hyd` fails 26–44% with no finite measurement/implementation
   correction closing it (g7; contract §12 HUMAN criterion met).
2. Static slit scaling inconsistent across resolution (11.5% > 10%) and
   the 30° droplet registry does not transfer (θ_slit 41–48°).
3. Residual order-one extra hydraulic resistance that also scales with
   slit height (`L_eq/L1` 0.49 at h26, ≈0.78 at h40) — blocks V2 on its
   own per the V1 external review's stop rule.
4. The hydraulic deficit is not yet attributed to any mechanism
   (boundary forcing vs moving contact line vs spurious-current
   dissipation vs effective-viscosity deviation).
5. `Pc_dynamic` (and `Pc_dynamic/Pc_static` = 0.92/0.79) carries an
   8–9% methodology bias from measurement-band overlap with the
   interface distortion zone — must be corrected before external use.

Full review: `REVIEW.md` in this directory (blocking findings B1–B5,
non-blocking findings, independent recalculations).  Executor bundle on
the product branch: `results/levelc_v1b/` (EXECUTION_REPORT.md,
PROVENANCE.md, MANIFEST.json, per-run data, console logs + exit codes).
No solver change; no parameter tuning; V2/V3 not started.
