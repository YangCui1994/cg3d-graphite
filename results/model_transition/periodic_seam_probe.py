#!/usr/bin/env python
"""BI-DEEPSEEK-TRANSITION-001 — read-only z-periodic seam probe.

Purpose
-------
The revised-V3 readiness question "should a periodic-BC sanity suite precede
V3?" needs one factual input that the conservation-focused C0-C3 isolation
matrix does not record: in the accepted V2 geometry (solid walls in x and y,
periodic in z, no solid and no interface crossing the z seam), how much
z-structure does the solution actually carry, and is any of it systematic?

This is *not* a simulation and *not* one of the proposed P0-P3 tests.  It only
reads artifacts that are already committed on the accepted candidate:

  results/colour_closure/levelc_v2_fix/v2_primary/fields_{initial,mid,final}.npz
  results/colour_closure/levelc_v2_fix/v2_primary/front_series.csv
  results/colour_closure/levelc_v2_fix/v2_primary/report.json

Reported quantities (all in lattice units, psi range is [-1, +1]):

  z_spread(field)[i,j] = max_k field[i,j,k] - min_k field[i,j,k]
  mirror   E_psi        = mean over fluid nodes of |psi(x) - psi(nx-1-x)|
                          (the definition the V2 driver itself records)

The mirror mean is recomputed here only to confirm the committed column; the
z-spread is the new information.

Usage
-----
    python results/model_transition/periodic_seam_probe.py
    python results/model_transition/periodic_seam_probe.py --out <path.json>
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

TASK = "BI-DEEPSEEK-TRANSITION-001"
V2_DIR = Path("results/colour_closure/levelc_v2_fix/v2_primary")
FIELDS = ("fields_initial.npz", "fields_mid.npz", "fields_final.npz")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def probe(run_dir: Path):
    rep = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    lay = rep["layout"]
    w0, w1 = lay["wall"]
    nx = int(rep["symmetry"]["nx"])

    out = {
        "source_dir": str(run_dir),
        "geometry": {
            "layout": lay,
            "nx": nx,
            "periodic_axes": "z only in the fluid sense; x and y are closed by "
                             "solid walls while their bc flags remain periodic",
            "solid_crosses_z_seam": False,
            "interface_crosses_z_seam": False,
        },
        "fields": {},
    }

    # fluid mask: outside the x walls; y walls are the first/last row
    fluid = np.zeros((nx, lay["liq_left"][1] - lay["liq_left"][0] + 1 + 1), dtype=bool)

    prev_spread = None
    patterns = {}
    for name in FIELDS:
        z = np.load(run_dir / name)
        psi = z["psi"]
        rho = z["rho"]
        ny = psi.shape[1]
        f = np.zeros(psi.shape, dtype=bool)
        f[w0:lay["wall_r"][0], :, :] = True
        f[:, 0, :] = False
        f[:, ny - 1, :] = False
        f = f & (psi.shape[0] > 0)

        sp_psi = psi.max(axis=2) - psi.min(axis=2)
        sp_rho = rho.max(axis=2) - rho.min(axis=2)
        f2 = f[:, :, 0]

        # x-mirror, mean over fluid (V2 driver definition) and max
        mir = np.abs(psi - psi[::-1, :, :])
        mr = np.abs(rho - rho[::-1, :, :])
        e_psi_mean = float(mir[f2].mean())
        e_psi_max = float(mir[f2].max())
        e_rho_mean = float(mr[f2].mean())

        # where does the z-spread live?
        i_max = np.unravel_index(np.argmax(np.where(f2, sp_psi, -np.inf)), sp_psi.shape)
        x_at_max = int(i_max[0])
        band = ("wall_adjacent" if x_at_max < w1 or x_at_max >= lay["wall_r"][0]
                else "liquid_buffer" if (x_at_max < lay["gas"][0] or x_at_max >= lay["gas"][1])
                else "gas_pocket")

        out["fields"][name] = {
            "z_spread_psi_max": float(sp_psi[f2].max()),
            "z_spread_psi_mean_fluid": float(sp_psi[f2].mean()),
            "z_spread_rho_max": float(sp_rho[f2].max()),
            "z_spread_rho_mean_fluid": float(sp_rho[f2].mean()),
            "z_spread_psi_argmax": {"i": x_at_max, "j": int(i_max[1]), "region": band},
            "x_mirror_E_psi_mean_fluid": e_psi_mean,
            "x_mirror_psi_max_fluid": e_psi_max,
            "x_mirror_E_rho_mean_fluid": e_rho_mean,
        }
        patterns[name] = sp_psi[f2].ravel()
        prev_spread = sp_psi[f2].max()

    # is the z-structure a persistent mode or noise? correlate mid vs final maps
    a, b = patterns["fields_mid.npz"], patterns["fields_final.npz"]
    if a.size and a.std() > 0 and b.std() > 0:
        corr = float(np.corrcoef(a, b)[0, 1])
    else:
        corr = None

    # cross-check the recomputed mirror mean against the committed series
    rows = list(csv.DictReader((run_dir / "front_series.csv").open("r", encoding="utf-8")))
    e_series = np.array([float(r["E_psi"]) for r in rows])
    out["z_structure_persistence"] = {
        "definition": "correlation of the per-(i,j) z-spread maps between the "
                      "mid and final committed fields",
        "pearson_r_mid_vs_final": corr,
        "interpretation": ("persistent systematic mode" if corr is not None and corr > 0.5
                           else "largely uncorrelated / noise-like" if corr is not None
                           else "undefined"),
    }
    out["cross_check"] = {
        "source": f"{run_dir}/front_series.csv:E_psi",
        "committed_E_psi_max": float(e_series.max()),
        "committed_E_psi_final": float(e_series[-1]),
        "note": "committed column is the running diagnostic; the field-based "
                "values above are for the three archived snapshots only",
    }
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    root = Path(args.root).resolve() if args.root else repo_root()
    run_dir = root / V2_DIR
    if not run_dir.is_dir():
        print(f"ERROR: {run_dir} not found", file=sys.stderr)
        return 2

    result = {
        "task": TASK,
        "stage": "read_only_periodic_seam_probe",
        "kind": "analysis of committed artifacts; no simulation executed",
        "generator": "results/model_transition/periodic_seam_probe.py",
        "probe": probe(run_dir),
    }
    out_path = (Path(args.out) if args.out
                else root / "results/model_transition/periodic_seam_probe.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
        fh.write("\n")

    print("[%s] wrote %s" % (TASK, out_path))
    for name, rec in result["probe"]["fields"].items():
        print("  %-20s z-spread psi max %.3e (mean %.3e)  rho max %.3e  "
              "E_psi mean %.3e"
              % (name, rec["z_spread_psi_max"], rec["z_spread_psi_mean_fluid"],
                 rec["z_spread_rho_max"], rec["x_mirror_E_psi_mean_fluid"]))
    print("  z-structure persistence: r=%s (%s)"
          % (result["probe"]["z_structure_persistence"]["pearson_r_mid_vs_final"],
             result["probe"]["z_structure_persistence"]["interpretation"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
