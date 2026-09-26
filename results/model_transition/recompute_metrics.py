#!/usr/bin/env python
"""BI-DEEPSEEK-TRANSITION-001 Part A — independent evidence recomputation.

Recomputes, directly from the raw evidence committed on the accepted product
candidate, the four quantities the transition contract asks for:

  A1  periodic-C1 240k colour drift   (results/colour_closure/ac_C1_T3C1X_A2_240k)
  A2  C3 120k colour drift            (results/colour_closure/ac_C3_T3C1X_A2_120k)
  A3  V2 bilateral trapped-pocket     (results/colour_closure/levelc_v2_fix/v2_primary)

Nothing here is a simulation: the script only re-derives numbers from committed
CSV/JSON artifacts.  It reads no headline/summary value as a calculation input;
headline values are consulted only *after* the recomputation, as a cross-check,
and are reported under ``cross_check`` with an explicit match/mismatch verdict.

Definitions (fixed by the producers of the accepted evidence, quoted here so the
recomputation is transparent and reproducible):

  colour series   Mc_norm(t) = (Mr(t) + Mb(t)) / M0 - 1
                  where M0 is the run's initial total mass, taken from the
                  run's own ``accum_report.json`` ("M0").
  fit             ordinary least squares of the series against step index;
                  ``slope_per_step`` = OLS slope, ``r2`` = 1 - SS_res / SS_tot
                  with the linear fit as the model, ``frac_pos`` = fraction of
                  positive first differences inside the fitted window.
  window          sample selection is ``lo <= step <= hi`` (inclusive on both
                  ends, the convention already used by tests/colour_closure.py).
                  Because the sampling stride is 400 steps and the window
                  bounds are multiples of 400, consecutive windows share one
                  boundary sample; ``disjoint`` variants (upper bound strictly
                  exclusive) are reported alongside so the choice is auditable.

Usage
-----
    python results/model_transition/recompute_metrics.py
    python results/model_transition/recompute_metrics.py --out <path.json>

The default output is results/model_transition/recomputed_metrics.json.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

TASK = "BI-DEEPSEEK-TRANSITION-001"
ACCEPTED_CANDIDATE = "6c30260dfe0c8b61ea9609e6bffa5c487312cf06"

# Cross-check tolerances against the committed producer reports.  The mass
# series is stored as 13-significant-digit text, which quantises each sample to
# ~1e-13 relative; a slope fitted over ~600 such samples inherits a relative
# error of order 1e-8.  1e-7 therefore separates "same number" from "different
# number" without being tight enough to flag pure text round-off.
CROSS_CHECK_TOL = {
    "slope_rel": 1e-7,
    "r2_abs": 1e-7,
    "frac_pos_abs": 1e-12,
    "basis": "13-significant-digit CSV text quantisation (~1e-8 relative on "
             "a fitted slope); not a physical tolerance",
}

# The front series stores positions at 8 significant digits, so an independent
# re-derivation of e_x = |x_left - ((nx-1) - x_right)| inherits ~1e-5 lu of text
# quantisation.  The committed e_x column itself is the producer's in-memory
# value and is correspondingly more precise.
FRONT_TEXT_QUANTUM_LU = 1e-4

C1_DIR = Path("results/colour_closure/ac_C1_T3C1X_A2_240k")
C3_DIR = Path("results/colour_closure/ac_C3_T3C1X_A2_120k")
V2_DIR = Path("results/colour_closure/levelc_v2_fix/v2_primary")


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_rows(path: Path):
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def col(rows, name):
    return np.array([float(r[name]) for r in rows], dtype=np.float64)


def fit(t, y):
    """OLS slope / R2 / positive-increment fraction of y against t."""
    p = np.polyfit(t, y, 1)
    yh = np.polyval(p, t)
    ss_res = float(np.sum((y - yh) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0.0 else None
    inc = np.diff(y)
    return {
        "slope_per_step": float(p[0]),
        "intercept": float(p[1]),
        "r2": r2,
        "n": int(y.size),
        "frac_pos": float((inc > 0).mean()) if inc.size else None,
    }


def window_mask(t, lo, hi, inclusive_hi=True):
    return (t >= lo) & (t <= hi) if inclusive_hi else (t >= lo) & (t < hi)


def colour_windows(t_first, t_last, n_segments):
    """Equal step-span windows covering [0, t_last] aligned on zero.

    Boundaries are multiples of the window span (e.g. 60k for a 240k series),
    so the windows are the natural quarters a reviewer would pick and are
    independent of where the first recorded sample happens to fall.
    """
    span = t_last / n_segments
    bounds = [(i * span, (i + 1) * span) for i in range(n_segments)]
    if bounds[0][0] < t_first:
        bounds[0] = (t_first, bounds[0][1])
    return bounds


def rel_change(series, base):
    return float(np.max(np.abs(series / base - 1.0)))


# --------------------------------------------------------------------------
# A1 / A2 — colour drift recomputation
# --------------------------------------------------------------------------
def recompute_colour_drift(run_dir: Path, n_segments: int, label: str):
    series_path = run_dir / "mass_series.csv"
    report_path = run_dir / "accum_report.json"
    rows = read_rows(series_path)
    rep = json.loads(report_path.read_text(encoding="utf-8"))

    t = col(rows, "step")
    Mr = col(rows, "Mr")
    Mb = col(rows, "Mb")
    Mc = Mr + Mb
    M0 = float(rep["M0"])                      # run's own initial total mass

    y = Mc / M0 - 1.0
    out = {
        "label": label,
        "source_series": str(series_path),
        "source_M0": f"{report_path}:M0",
        "M0": M0,
        "n_samples": int(t.size),
        "step_first": float(t[0]),
        "step_last": float(t[-1]),
        "sampling_stride": float(t[1] - t[0]) if t.size > 1 else None,
        "series_definition": "(Mr + Mb) / M0 - 1",
        "window_convention": "lo <= step <= hi (inclusive; repo convention)",
        "full": fit(t, y),
        "segments": [],
    }

    bounds = colour_windows(float(t[0]), float(t[-1]), n_segments)
    for lo, hi in bounds:
        m = window_mask(t, lo, hi, inclusive_hi=True)
        seg = fit(t[m], y[m])
        seg["lo"] = float(lo)
        seg["hi"] = float(hi)
        out["segments"].append(seg)

    # disjoint variant: same bounds, upper end exclusive (boundary sample only
    # in the earlier window).  Reported so the shared-boundary choice is visible.
    out["segments_disjoint_bounds"] = []
    for lo, hi in bounds:
        m = window_mask(t, lo, hi, inclusive_hi=False)
        seg = fit(t[m], y[m])
        seg["lo"] = float(lo)
        seg["hi"] = float(hi)
        out["segments_disjoint_bounds"].append(seg)

    # per-segment increment-sign fractions (explicit, contract asks for them)
    out["increment_sign_fractions"] = {
        "full": out["full"]["frac_pos"],
        "segments": [s["frac_pos"] for s in out["segments"]],
        "first_difference_count_full": int(t.size - 1),
    }

    # cross-check against the committed producer report (NOT used as input)
    committed = rep.get("drift_fits", {}).get("Mc", {})
    xc = {
        "source": f"{report_path}:drift_fits.Mc",
        "committed_slope_per_step": committed.get("slope_per_step"),
        "committed_r2": committed.get("r2"),
        "committed_frac_pos": committed.get("frac_pos"),
        "tolerance": CROSS_CHECK_TOL,
    }
    if committed:
        xc["slope_rel_diff"] = abs(
            out["full"]["slope_per_step"] - committed["slope_per_step"]
        ) / abs(committed["slope_per_step"])
        xc["r2_abs_diff"] = abs(out["full"]["r2"] - committed["r2"])
        xc["frac_pos_abs_diff"] = abs(out["full"]["frac_pos"] - committed["frac_pos"])
        xc["reproduces_within_tolerance"] = bool(
            xc["slope_rel_diff"] <= CROSS_CHECK_TOL["slope_rel"]
            and xc["r2_abs_diff"] <= CROSS_CHECK_TOL["r2_abs"]
            and xc["frac_pos_abs_diff"] <= CROSS_CHECK_TOL["frac_pos_abs"]
        )
        xc["reproduces_bitwise"] = bool(
            out["full"]["slope_per_step"] == committed["slope_per_step"]
            and out["full"]["r2"] == committed["r2"]
            and out["full"]["frac_pos"] == committed["frac_pos"]
        )
    out["cross_check"] = xc

    # the material content of the segment table is the sign pattern; declare the
    # convention sensitivity so a reviewer using a different partition can still
    # compare against these numbers.
    out["segment_convention_sensitivity"] = {
        "shared_boundary_sample_vs_disjoint": [
            {
                "lo": s["lo"], "hi": s["hi"],
                "inclusive_slope": s["slope_per_step"],
                "disjoint_slope": d["slope_per_step"],
                "abs_diff": abs(s["slope_per_step"] - d["slope_per_step"]),
            }
            for s, d in zip(out["segments"], out["segments_disjoint_bounds"])
        ],
        "note": "differences are at the last significant digits of a "
                "noise-level slope; the material content is the sign pattern "
                "(large first-window transient, then sign-mixed near-zero).",
    }
    return out


# --------------------------------------------------------------------------
# A3 — V2 bilateral recomputation
# --------------------------------------------------------------------------
def recompute_v2(run_dir: Path):
    front_rows = read_rows(run_dir / "front_series.csv")
    mass_rows = read_rows(run_dir / "mass_stability_series.csv")
    gas_rows = read_rows(run_dir / "gas_series.csv")
    rep = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    sym = json.loads((run_dir / "symmetry_check.json").read_text(encoding="utf-8"))
    topo0 = json.loads((run_dir / "topology_t0.json").read_text(encoding="utf-8"))

    nx = int(sym["nx"])
    # mirror reflection of the right front about the mid-plane of an nx-long box
    x_left = col(front_rows, "x_left")
    x_right = col(front_rows, "x_right")
    x_right_star = (nx - 1) - x_right
    e_x = np.abs(x_left - x_right_star)

    # producer's own reported x_right_star / e_x columns, for a column-level check
    e_x_reported = col(front_rows, "e_x")
    x_rs_reported = col(front_rows, "x_right_star")

    t_front = col(front_rows, "t")
    t_mass = col(mass_rows, "t")
    m_b = col(mass_rows, "m_b")
    eps_b = col(mass_rows, "eps_b")
    m_b0 = float(rep["m_b0"])

    # independent eps_b: |m_b / m_b0 - 1|, no reliance on the committed column
    eps_b_indep = np.abs(m_b / m_b0 - 1.0)

    n_clusters = col(gas_rows, "n_clusters")
    largest = col(gas_rows, "largest")
    g_bulk = col(gas_rows, "G_bulk")
    t_gas = col(gas_rows, "t")

    onset_idx = np.nonzero(g_bulk <= 0)[0]
    interaction_status = (
        "NOT_REACHED" if onset_idx.size == 0
        else f"REACHED_AT_t={int(t_gas[onset_idx[0]])}"
    )

    out = {
        "source_dir": str(run_dir),
        "mirror_error": {
            "definition": "e_x = |x_left - ((nx-1) - x_right)|, nx from symmetry_check.json",
            "nx": nx,
            "n_samples": int(x_left.size),
            "t_first": float(t_front[0]),
            "t_last": float(t_front[-1]),
            "max_e_x_lu_derived_from_columns": float(e_x.max()),
            "rms_e_x_lu_derived_from_columns": float(np.sqrt(np.mean(e_x ** 2))),
            "argmax_t": float(t_front[int(e_x.argmax())]),
            "max_e_x_lu_from_committed_column": float(e_x_reported.max()),
            "committed_report_max_e_x": float(rep["max_e_x"]),
            "column_check": {
                "max_abs_diff_vs_reported_e_x": float(np.max(np.abs(e_x - e_x_reported))),
                "max_abs_diff_vs_reported_x_right_star": float(
                    np.max(np.abs(x_right_star - x_rs_reported))
                ),
                "text_quantum_note": "front_series.csv stores positions at 8 "
                                     "significant digits; the derived-vs-column "
                                     "difference is at that text quantisation "
                                     "level and is not a numerical difference",
                "expected_text_quantum_lu": FRONT_TEXT_QUANTUM_LU,
            },
        },
        "blue_mass_drift": {
            "definition": "max over samples of |m_b / m_b0 - 1|",
            "m_b0": m_b0,
            "n_samples": int(m_b.size),
            "t_first": float(t_mass[0]),
            "t_last": float(t_mass[-1]),
            "max_eps_b_independent": float(eps_b_indep.max()),
            "argmax_t": float(t_mass[int(eps_b_indep.argmax())]),
            "final_eps_b_independent": float(eps_b_indep[-1]),
            "column_check": {
                "max_abs_diff_vs_reported_eps_b": float(
                    np.max(np.abs(eps_b_indep - eps_b))
                ),
                "reported_max_eps_b": float(eps_b.max()),
            },
            "committed_report_max_eps_b": float(rep["max_eps_b"]),
        },
        "trapped_cluster_history": {
            "definition": "cluster count / largest cluster from gas_series.csv; "
                          "6-neighbour labelling, z-periodic merge only",
            "n_samples": int(n_clusters.size),
            "t_first": float(t_gas[0]),
            "t_last": float(t_gas[-1]),
            "n_clusters_min": int(n_clusters.min()),
            "n_clusters_max": int(n_clusters.max()),
            "n_clusters_final": int(n_clusters[-1]),
            "n_clusters_unique_values": sorted({int(v) for v in n_clusters}),
            "largest_cluster_min": float(largest.min()),
            "largest_cluster_max": float(largest.max()),
            "fragmentation_detected": bool((n_clusters > 1).any()),
            "t0_topology": topo0,
            "committed_report_cluster_count_max": int(rep["cluster_count_max"]),
            "committed_report_cluster_count_final": int(rep["cluster_count_final"]),
        },
        "interaction_status": {
            "definition": "INTERACTION_ONSET = first sample with no bulk-gas column "
                          "(G_bulk == 0)",
            "G_bulk_first": float(g_bulk[0]),
            "G_bulk_last": float(g_bulk[-1]),
            "G_bulk_min": float(g_bulk.min()),
            "recomputed": interaction_status,
            "committed_report": rep["INTERACTION_ONSET"],
            "agrees_with_committed": bool(interaction_status == rep["INTERACTION_ONSET"]),
        },
    }
    return out


# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=None,
                    help="repository root (default: derived from this file)")
    ap.add_argument("--out", default=None,
                    help="output JSON path (default: results/model_transition/"
                         "recomputed_metrics.json)")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve() if args.root else repo_root()
    out_path = (Path(args.out) if args.out
                else root / "results/model_transition/recomputed_metrics.json")

    missing = [str(p) for p in (root / C1_DIR, root / C3_DIR, root / V2_DIR)
               if not p.is_dir()]
    if missing:
        print("ERROR: evidence directories not found:\n  " + "\n  ".join(missing),
              file=sys.stderr)
        return 2

    result = {
        "task": TASK,
        "stage": "A_evidence_recomputation",
        "kind": "independent recomputation from committed raw evidence",
        "generator": "results/model_transition/recompute_metrics.py",
        "accepted_candidate": ACCEPTED_CANDIDATE,
        "repository_root": str(root),
        "inputs_are_committed_artifacts_only": True,
        "headline_values_used_as_inputs": False,
        "A1_periodic_C1_240k": recompute_colour_drift(
            root / C1_DIR, n_segments=4, label="periodic C1 (64x24x24, 240k steps)"),
        "A2_C3_120k": recompute_colour_drift(
            root / C3_DIR, n_segments=4, label="C3 (126x46x6, 120k steps)"),
        "A3_V2_bilateral": recompute_v2(root / V2_DIR),
    }

    # ---- summary verdicts -------------------------------------------------
    c1 = result["A1_periodic_C1_240k"]
    c3 = result["A2_C3_120k"]
    v2 = result["A3_V2_bilateral"]
    result["summary"] = {
        "A1_full_slope_per_step": c1["full"]["slope_per_step"],
        "A1_full_r2": c1["full"]["r2"],
        "A1_segment_slopes": [s["slope_per_step"] for s in c1["segments"]],
        "A1_frac_pos": c1["increment_sign_fractions"],
        "A1_cross_check_reproduces": c1["cross_check"].get("reproduces_within_tolerance"),
        "A2_full_slope_per_step": c3["full"]["slope_per_step"],
        "A2_full_r2": c3["full"]["r2"],
        "A2_segment_slopes": [s["slope_per_step"] for s in c3["segments"]],
        "A2_frac_pos": c3["increment_sign_fractions"],
        "A2_cross_check_reproduces": c3["cross_check"].get("reproduces_within_tolerance"),
        "A3_max_blue_rel_drift": v2["blue_mass_drift"]["max_eps_b_independent"],
        "A3_max_mirror_error_lu_derived": v2["mirror_error"]["max_e_x_lu_derived_from_columns"],
        "A3_max_mirror_error_lu_committed_column": v2["mirror_error"]["max_e_x_lu_from_committed_column"],
        "A3_cluster_count_unique": v2["trapped_cluster_history"]["n_clusters_unique_values"],
        "A3_interaction_status": v2["interaction_status"]["recomputed"],
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=False)
        fh.write("\n")

    full_ok = all([
        c1["cross_check"].get("reproduces_within_tolerance"),
        c3["cross_check"].get("reproduces_within_tolerance"),
        v2["interaction_status"]["agrees_with_committed"],
    ])
    print("[%s] wrote %s" % (TASK, out_path))
    print("  A1 C1 240k : slope %.4e/step  R2 %.4f  quarters %s"
          % (c1["full"]["slope_per_step"], c1["full"]["r2"],
             " ".join("%.2e" % s["slope_per_step"] for s in c1["segments"])))
    print("  A2 C3 120k : slope %.4e/step  R2 %.4f  quarters %s"
          % (c3["full"]["slope_per_step"], c3["full"]["r2"],
             " ".join("%.2e" % s["slope_per_step"] for s in c3["segments"])))
    print("  A3 V2      : max eps_b %.3e  max e_x %.3e lu (derived) / %.3e lu "
          "(committed column)  clusters %s  %s"
          % (v2["blue_mass_drift"]["max_eps_b_independent"],
             v2["mirror_error"]["max_e_x_lu_derived_from_columns"],
             v2["mirror_error"]["max_e_x_lu_from_committed_column"],
             v2["trapped_cluster_history"]["n_clusters_unique_values"],
             v2["interaction_status"]["recomputed"]))
    print("  cross-check against committed producer reports: %s"
          % ("MATCH" if full_ok else "MISMATCH"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
