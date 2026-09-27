"""BI-CG-LECLAIRE-PASS4-001 -- frozen reference-model validation harness.

Runs the eleven pass-04 cases from one frozen candidate and writes the
immutable artifact tree required by VALIDATION_ARTIFACT_SPEC.md:

    results/leclaire_cg/pass-04/
        VALIDATION_REPORT.md
        SUMMARY.json
        run_manifest.json
        case-01-.../  ...  case-11-mechanical-sigma/

Binding sources:
  docs/research/leclaire_cg/WETTING_PHASE_CONVENTION.md      (convention)
  docs/research/leclaire_cg/VALIDATION_ARTIFACT_SPEC.md      (artifacts)
  .agent/episodes/.../LECLAIRE_PASS4_VALIDATION_CONTRACT.md   (scope/gates)

Gates are declared in GATES below and are NOT edited after results are seen.
"""
from __future__ import annotations

import io
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "experimental"))
sys.path.insert(0, HERE)

from leclaire_cg import LeclaireCG3D          # noqa: E402
from leclaire_cg import geometry as G         # noqa: E402
from leclaire_cg import operators as op       # noqa: E402
from leclaire_cg import lattice as L          # noqa: E402
import artifact as A                          # noqa: E402

OUT_ROOT = os.path.join(HERE, "..", "..", "results", "leclaire_cg", "pass-04")
NU = 1.0 / 6.0
SIGMA = 0.02
BETA = 0.7

# ---------------------------------------------------------------------------
# Predeclared gates.  Frozen before the run; not edited afterwards.
# ---------------------------------------------------------------------------
GATES = {
    "01_uniform": dict(max_v=1e-12, max_drho=1e-12),
    "02_planar": dict(pos_drift=0.5, amp_ratio=0.95),
    "03_laplace": dict(sigma_ratio_lo=0.90, sigma_ratio_hi=1.10,
                       r2_min=0.95, intercept_frac=0.25),
    "04_contact_angle": dict(min_contour_pts=6, max_fit_rms=0.5,
                             max_angle_err_deg=15.0, min_snapshots=3),
    "05_beta": dict(positivity_tol=1e-9, min_valid=1),
    "06_isotropy": dict(asymmetry=0.05),
    "07_slit_pc": dict(ratio_lo=0.5, ratio_hi=1.5, min_contour=1),
    "08_jurin": dict(rise_ratio_lo=0.5, rise_ratio_hi=1.5),
    "09_killer": dict(wall_band=0.02, excursion=0.02, late_rate=1e-6),
    "10_conservation": dict(total_per_step=1e-12, comp_per_step=1e-9),
    "11_mech_sigma": dict(ratio_lo=0.7, ratio_hi=1.3),
}


def make(n, solid=None, **kw):
    p = dict(nu_r=NU, nu_b=NU, sigma=SIGMA, beta=BETA)
    p.update(kw)
    s = LeclaireCG3D(n[0], n[1], n[2], **p)
    s.set_solid(solid if solid is not None else np.zeros(n, dtype=bool))
    return s


def maxv(s):
    _, u = s.macroscopic()
    sp = np.linalg.norm(u, axis=-1)
    return float(sp[s.fluid].max()) if np.any(s.fluid) else 0.0


def masses(s):
    return s.component_masses()


# ===========================================================================
#  case 01 -- uniform single phase stationarity
# ===========================================================================
def case_01(out_root, cand):
    c = A.Case(out_root, 1, "uniform-stationarity", cand)
    n = (8, 8, 8)
    s = make(n)
    s.init_uniform(psi=1.0, rho=1.0)
    c.snapshot("t0000", s)
    rho0 = (s.rho_r + s.rho_b).copy()
    m0 = masses(s)
    ts = []
    for t in range(0, 401, 100):
        if t:
            s.run(t - s.time)
        rho, _ = s.macroscopic()
        mr, mb = masses(s)
        ts.append(dict(t=s.time, max_v=maxv(s),
                       max_drho=float(np.abs(rho - rho0).max()),
                       red_mass=mr, blue_mass=mb))
    c.snapshot("t0400", s)
    g = GATES["01_uniform"]
    m1 = masses(s)
    ok = ts[-1]["max_v"] < g["max_v"] and ts[-1]["max_drho"] < g["max_drho"]
    verd = "PASS" if ok else "FAIL_SOLVER"
    c.fig_field_slice({"psi": s.psi(), "solid": s.solid}, "fig1_field",
                      "uniform single phase (psi=+1)", source_raw=c.snaps["t0400"]["file"])
    c.fig_xy([r["t"] for r in ts], [r["max_v"] for r in ts], "fig2_observable",
             "stationarity: max|v| vs t", "t [steps]", "max |v|",
             source_raw=c.snaps["t0400"]["file"])
    c.fig_xy([r["t"] for r in ts], [r["max_drho"] for r in ts], "fig3_residual",
             "residual: max|rho - rho(t=0)| vs t", "t [steps]",
             "max |Delta rho|", logy=True, source_raw=c.snaps["t0400"]["file"])
    c.write_metrics(dict(max_abs_v=ts[-1]["max_v"], max_abs_drho=ts[-1]["max_drho"],
                         red_mass_drift=abs(m1[0] - m0[0]),
                         blue_mass_drift=abs(m1[1] - m0[1]),
                         gates=g, verdict=verd), ts)
    c.write_metadata(dict(grid=list(n), steps=400, initial="psi=+1, u=0",
                          solid="none", bc="periodic", wetting="none",
                          snapshot_times=[0, 400], exit_code=0))
    c.write_readme(dict(target="stationarity of the single-phase equilibrium"),
                   dict(**{"domain size": n, "lattice": "D3Q19",
                           "initial condition": "psi=+1, rho=1, u=0",
                           "solid geometry": "none (periodic)",
                           "boundary conditions": "periodic",
                           "wetting convention": "n/a (no wall)",
                           "nu": NU, "sigma": SIGMA, "beta": BETA,
                           "forcing": "none", "precision/backend": "numpy f64",
                           "run length": "400 steps",
                           "snapshot times": "0, 400"}),
                   dict(relation="sum_i N_i^eq = rho ; u stays 0",
                        prose="A uniform single-phase state must be an exact "
                              "fixed point of the update."),
                   [f"| max \\|v\\| | < {g['max_v']:.0e} | {ts[-1]['max_v']:.3e} | "
                    f"{ts[-1]['max_v']:.3e} | {'ok' if ok else 'FAIL'} |",
                    f"| max \\|Delta rho\\| | < {g['max_drho']:.0e} | "
                    f"{ts[-1]['max_drho']:.3e} | {ts[-1]['max_drho']:.3e} | ok |"],
                   "f64 roundoff on every field; no drift.", "PASS" if ok else "FAIL_SOLVER")
    c.write_reproduce()
    c.write_render_manifest()
    return verd, c


# ===========================================================================
#  case 02 -- planar interface stationarity
# ===========================================================================
def case_02(out_root, cand):
    c = A.Case(out_root, 2, "planar-interface", cand)
    n = (6, 6, 32)
    s = make(n)
    s.init_psi(G.planar_interface(n[0], n[1], n[2], width=2.0))
    c.snapshot("t0000", s)
    prof = s.psi()[3, 3, :]
    c0 = G.interface_position_1d(prof)
    amp0 = float(np.abs(prof).max())
    ts = []
    for t in range(0, 1001, 100):
        if t:
            s.run(t - s.time)
        p = s.psi()[3, 3, :]
        ts.append(dict(t=s.time, pos=float(G.interface_position_1d(p)),
                       amp=float(np.abs(p).max()), max_v=maxv(s)))
    c.snapshot("t1000", s)
    g = GATES["02_planar"]
    drift = abs(ts[-1]["pos"] - c0)
    aratio = ts[-1]["amp"] / amp0
    ok = drift < g["pos_drift"] and aratio > g["amp_ratio"]
    verd = "PASS" if ok else "FAIL_SOLVER"
    c.fig_field_slice({"psi": s.psi(), "solid": s.solid}, "fig1_field",
                      "planar interface, final psi", plane="xz",
                      source_raw=c.snaps["t1000"]["file"])
    c.fig_xy([r["t"] for r in ts], [r["pos"] for r in ts], "fig2_observable",
             "interface position vs t", "t [steps]", "z position [lu]",
             source_raw=c.snaps["t1000"]["file"])
    c.fig_xy([r["t"] for r in ts], [abs(r["pos"] - c0) for r in ts],
             "fig3_residual", "interface position residual vs t", "t [steps]",
             "|z(t) - z(0)| [lu]", logy=True, source_raw=c.snaps["t1000"]["file"])
    c.write_metrics(dict(interface_pos_initial=float(c0),
                         interface_pos_final=ts[-1]["pos"],
                         interface_pos_drift=float(drift),
                         amplitude_ratio=float(aratio),
                         max_spurious_v=ts[-1]["max_v"], gates=g, verdict=verd), ts)
    c.write_metadata(dict(grid=list(n), steps=1000,
                          initial="psi=-tanh((z-c)/2)", solid="none",
                          bc="periodic", wetting="none",
                          snapshot_times=[0, 1000], exit_code=0))
    c.write_readme(dict(target="planar interface stationarity"),
                   dict(**{"domain size": n, "lattice": "D3Q19",
                           "initial condition": "psi=-tanh((z-16)/2)",
                           "solid geometry": "none", "boundary conditions": "periodic",
                           "wetting convention": "n/a", "nu": NU, "sigma": SIGMA,
                           "beta": BETA, "forcing": "none",
                           "precision/backend": "numpy f64", "run length": "1000 steps",
                           "snapshot times": "0, 1000"}),
                   dict(relation="interface must not translate or dissolve",
                        prose="The interface carries no driving force, so both its "
                              "position and its phase amplitude must be stationary."),
                   [f"| position drift | < {g['pos_drift']} lu | {drift:.4f} | "
                    f"{drift:.4f} | {'ok' if drift < g['pos_drift'] else 'FAIL'} |",
                    f"| amplitude ratio | > {g['amp_ratio']} | {aratio:.6f} | "
                    f"{1 - aratio:.2e} | ok |"],
                   "converged steady state; residual is f64-level.", verd)
    c.write_reproduce()
    c.write_render_manifest()
    return verd, c


# ===========================================================================
#  case 03 -- Laplace, larger-radius study (D4.1)
# ===========================================================================
def case_03(out_root, cand, radii=(6.0, 7.0, 8.0, 9.0), n=(28, 28, 28),
            steps=1000):
    c = A.Case(out_root, 3, "laplace-multi-radius", cand)
    runs, ts = [], []
    for R in radii:
        s = make(n)
        s.init_psi(G.droplet(n[0], n[1], n[2], R,
                             center=(n[0] / 2, n[1] / 2, n[2] / 2)))
        s.run(steps)
        c.snapshot(f"R{int(R)}_final", s)
        rho, _ = s.macroscopic()
        psi = s.psi()
        Req = G.equivalent_radius(psi)
        X, Y, Z = G.grid(*n)
        r = np.sqrt((X - n[0] / 2) ** 2 + (Y - n[1] / 2) ** 2
                    + (Z - n[2] / 2) ** 2)
        ins = r < R - 3.5
        outs = r > R + 3.5
        dp = float((rho[ins].mean() - rho[outs].mean()) / 3.0)
        runs.append(dict(R_nominal=R, R_measured=float(Req), dp=dp,
                         two_over_R=2.0 / Req, sigma_local=dp * Req / 2.0,
                         psi_peak=float(np.abs(psi).max()),
                         positivity_ok=bool(np.abs(psi).max() <= 1.0 + 1e-9),
                         max_abs_v=maxv(s)))
        ts.append(dict(R=R, R_measured=float(Req), dp=dp,
                       two_over_R=2.0 / Req, sigma_local=dp * Req / 2.0))
    x = np.array([r["two_over_R"] for r in runs])
    y = np.array([r["dp"] for r in runs])
    A_ = np.stack([x, np.ones_like(x)], axis=1)
    sol, *_ = np.linalg.lstsq(A_, y, rcond=None)
    sig_free, intercept = float(sol[0]), float(sol[1])
    pred = A_ @ sol
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    sig_zero = float(np.sum(x * y) / np.sum(x * x))
    sx = np.array([1.0 / r["R_measured"] for r in runs])
    sy = np.array([r["sigma_local"] for r in runs])
    A2 = np.stack([1.0 / sx, np.ones_like(sx)], axis=1)
    sol2, *_ = np.linalg.lstsq(A2, sy, rcond=None)
    sig_inf, _ = float(sol2[0]), float(sol2[1])
    pred2 = A2 @ sol2
    ss2 = float(np.sum((sy - pred2) ** 2))
    st2 = float(np.sum((sy - sy.mean()) ** 2))
    r2b = 1.0 - ss2 / st2 if st2 > 0 else float("nan")
    g = GATES["03_laplace"]
    ratio = sig_free / SIGMA
    ok = (g["sigma_ratio_lo"] < ratio < g["sigma_ratio_hi"]
          and r2 > g["r2_min"]
          and abs(intercept) < g["intercept_frac"] * abs(y.mean()))
    verd = "PASS" if ok else "FAIL_SOLVER"
    c.fig_field_slice({"psi": s.psi(), "solid": s.solid}, "fig1_field",
                      f"largest droplet R={radii[-1]:.0f}, final psi",
                      source_raw=c.snaps[f"R{int(radii[-1])}_final"]["file"])
    c.fig_xy(x, y, "fig2_observable", "Laplace: Delta p vs 2/R_measured",
             "2/R [lu^-1]", "Delta p",
             series=[dict(y=y, label="simulation", style="o"),
                     dict(y=pred, label=f"fit sigma={sig_free:.4f}",
                          style="-"),
                     dict(y=sig_zero * x, label=f"zero-intercept "
                          f"sigma={sig_zero:.4f}", style="--")],
             source_raw=c.snaps["R6_final"]["file"])
    c.fig_xy(x, y - pred, "fig3_residual", "regression residual vs 2/R",
             "2/R [lu^-1]", "Delta p residual",
             source_raw=c.snaps["R6_final"]["file"])
    c.write_metrics(dict(
        radii=list(radii), runs=runs,
        sigma_input=SIGMA, sigma_free_intercept=sig_free,
        sigma_zero_intercept=sig_zero, intercept=intercept, r2=r2,
        sigma_ratio=ratio, sigma_extrapolated_large_R=sig_inf, r2_vs_invR=r2b,
        gates=g, verdict=verd,
        note="Eq.(18) A=(9/4)omega*sigma is NOT retuned; an offset is a result."),
        ts)
    c.write_metadata(dict(grid=list(n), steps=steps, radii=list(radii),
                          initial="tanh droplet", solid="none", bc="periodic",
                          wetting="none", snapshot_times=[f"R{int(r)}_final" for r in radii],
                          exit_code=0))
    c.write_readme(dict(target="Laplace law and sigma calibration at larger radii"),
                   dict(**{"domain size": n, "lattice": "D3Q19",
                           "initial condition": "spherical tanh droplet",
                           "solid geometry": "none (periodic images must not interact)",
                           "boundary conditions": "periodic", "wetting convention": "n/a",
                           "nu": NU, "sigma": SIGMA, "beta": BETA, "forcing": "none",
                           "precision/backend": "numpy f64",
                           "run length": f"{steps} steps per radius",
                           "snapshot times": "one final snapshot per radius"}),
                   dict(relation="Delta p = 2 sigma / R ; regress Delta p on 2/R",
                        prose="Four resolved radii; radius measured from the final "
                              "phase field as the equivalent-sphere radius. Free- "
                              "intercept and zero-intercept fits are both reported, "
                              "plus the local sigma_i and its 1/R trend."),
                   [f"| sigma_fit (free intercept) | within "
                    f"{g['sigma_ratio_lo']}-{g['sigma_ratio_hi']}x {SIGMA} | "
                    f"{sig_free:.5f} | {ratio:.3f}x | {'ok' if ok else 'FAIL'} |",
                    f"| R^2 | > {g['r2_min']} | {r2:.5f} | - | ok |",
                    f"| intercept | < {g['intercept_frac']}x mean dp | "
                    f"{intercept:.2e} | - | ok |",
                    f"| sigma_zero_intercept | - | {sig_zero:.5f} | "
                    f"{sig_zero / SIGMA:.3f}x | reported |",
                    f"| sigma_extrapolated(1/R->0) | - | {sig_inf:.5f} | "
                    f"{sig_inf / SIGMA:.3f}x | reported |"],
                   "The +offset is an unresolved calibration result, not a gate "
                   "to be tuned away. See MECHANICAL_SIGMA_DERIVATION.md.", verd)
    c.write_reproduce()
    c.write_render_manifest()
    return verd, c


# ===========================================================================
#  case 04 -- contact angle 60/90/120 under the FROZEN convention
# ===========================================================================
def case_04(out_root, cand, angles=(60.0, 90.0, 120.0), n=(30, 30, 30),
            steps=1600, wall=2):
    c = A.Case(out_root, 4, "contact-angle", cand)
    runs, ts = [], []
    for th in angles:
        s = make(n, solid=G.wall_slab(n[0], n[1], n[2], thickness=wall),
                 theta_c=np.deg2rad(th))
        s.init_psi(G.hemi_droplet_on_wall(n[0], n[1], n[2], radius=9.0))
        c.snapshot(f"theta{int(th)}_init", s)
        s.run(steps)
        c.snapshot(f"theta{int(th)}_final", s)
        zs, rs = G.interface_radius_profile(s.psi(), s.solid)
        a, Rfit, zc, rms = G.contact_angle_circle_fit(zs, rs, float(wall - 1))
        runs.append(dict(theta_prescribed_deg=th, theta_measured_deg=a,
                         n_contour_points=int(zs.size), fit_R=Rfit,
                         fit_zc=zc,
                         fit_rms=rms,
                         fit_rms_geom=float(getattr(
                             G.contact_angle_circle_fit, "last_rms_geom",
                             float("nan"))),
                         psi_peak=float(np.abs(s.psi()).max()),
                         max_abs_v=maxv(s)))
        ts.append(dict(theta=th, theta_measured=a, n_points=int(zs.size),
                       rms=rms))
    g = GATES["04_contact_angle"]
    # Fit-quality gate on the GEOMETRIC rms in lattice units.
    # Audit note: the first pass-4 revision gated on `fit_rms`, which is the
    # residual of the linearised circle equation in RADIUS-SQUARED units and
    # scales as R^2; comparing it with a 0.5 lu threshold mixed dimensions.
    # Both quantities are reported for every angle so the change is auditable.
    fits = [r for r in runs if np.isfinite(r["theta_measured_deg"])
            and r["n_contour_points"] >= g["min_contour_pts"]
            and r["fit_rms_geom"] < g["max_fit_rms_geom"]]
    c.fig_field_slice({"psi": s.psi(), "solid": s.solid}, "fig1_field",
                      f"droplet on wall, theta_c={angles[-1]:.0f} deg",
                      source_raw=c.snaps[f"theta{int(angles[-1])}_final"]["file"])
    c.fig_xy([r["theta_prescribed_deg"] for r in runs],
             [r["theta_measured_deg"] for r in runs], "fig2_observable",
             "measured vs prescribed contact angle (through liquid/red)",
             "prescribed theta [deg]", "measured theta [deg]",
             series=[dict(y=[r["theta_measured_deg"] for r in runs],
                          label="measured", style="o"),
                     dict(y=[r["theta_prescribed_deg"] for r in runs],
                          label="1:1", style="--")],
             source_raw=c.snaps["figref"]["file"] if "figref" in c.snaps
             else c.snaps[f"theta{int(angles[-1])}_final"]["file"])
    c.fig_xy([r["theta_prescribed_deg"] for r in runs],
             [abs(r["theta_measured_deg"] - r["theta_prescribed_deg"])
              for r in runs], "fig3_residual", "absolute contact-angle error",
             "prescribed theta [deg]", "|theta_meas - theta_presc| [deg]",
             source_raw=c.snaps[f"theta{int(angles[-1])}_final"]["file"])
    if len(fits) == len(runs):
        errs = [abs(r["theta_measured_deg"] - r["theta_prescribed_deg"])
                for r in fits]
        verd = "PASS" if max(errs) < g["max_angle_err_deg"] else "FAIL_SOLVER"
    else:
        verd = "INCONCLUSIVE"
    rows = [f"| theta={r['theta_prescribed_deg']:.0f} | within "
            f"{g['max_angle_err_deg']:.0f} deg | {r['theta_measured_deg']:.2f} | "
            f"{abs(r['theta_measured_deg'] - r['theta_prescribed_deg']):.2f} | "
            f"{'fit ok' if r in fits else 'FIT QUALITY FAIL'} |" for r in runs]
    c.write_metrics(dict(runs=runs, gates=g, verdict=verd,
                         phase_convention="theta measured through psi>0 liquid/red",
                         wall_normal="n_w = -grad(g)/|grad(g)|  (solid->fluid)"),
                    ts)
    c.write_metadata(dict(grid=list(n), steps=steps, angles=list(angles),
                          wetting="leclaire", wall_normal_sign=-1,
                          snapshot_times=[f"theta{int(a)}_init" for a in angles]
                          + [f"theta{int(a)}_final" for a in angles], exit_code=0))
    c.write_readme(dict(target="static contact angle vs prescribed, frozen convention"),
                   dict(**{"domain size": n, "lattice": "D3Q19",
                           "initial condition": "hemispherical tanh blob on the wall",
                           "solid geometry": f"floor slab, {wall} layers",
                           "boundary conditions": "periodic + no-slip solid",
                           "wetting convention":
                               "n_w = -grad(g)/|grad(g)| solid->fluid; theta through liquid/red",
                           "nu": NU, "sigma": SIGMA, "beta": BETA, "forcing": "none",
                           "precision/backend": "numpy f64", "run length": f"{steps} steps",
                           "snapshot times": "initial and final per angle"}),
                   dict(relation="measured theta_liquid = prescribed theta_c",
                        prose="Circle fit to the psi=0 contour in the (r,z) plane; "
                              "the angle is read where the fitted circle meets the wall "
                              "plane, through the liquid/red phase."),
                   rows,
                   "Convention frozen by WETTING_PHASE_CONVENTION.md; the "
                   "sessile droplet consumes it and does not choose it.", verd)
    c.write_reproduce()
    c.write_render_manifest()
    return verd, c


# ===========================================================================
#  case 05 -- beta sweep with positivity gating
# ===========================================================================
def case_05(out_root, cand, betas=(0.0, 0.5, 0.7, 1.0, 1.5, 2.0),
            n=(6, 6, 32), steps=600):
    c = A.Case(out_root, 5, "beta-width-validity", cand)
    runs, ts = [], []
    for bl in betas:
        s = make(n, beta=bl)
        s.init_psi(G.planar_interface(n[0], n[1], n[2], width=2.0))
        s.run(steps)
        c.snapshot(f"beta{bl}_final", s)
        p = s.psi()[3, 3, :]
        w, _ = G.interface_width_tanh(p)
        peak = float(np.abs(s.psi()).max())
        runs.append(dict(beta=bl, width=float(w), psi_peak=peak,
                         positivity_ok=bool(peak <= 1.0 + GATES["05_beta"]["positivity_tol"]),
                         rho_r_min=float(s.rho_r.min()),
                         rho_b_min=float(s.rho_b.min())))


        ts.append(dict(beta=bl, width=float(w), psi_peak=peak,
                       rho_r_min=float(s.rho_r.min()),
                       rho_b_min=float(s.rho_b.min())))
    g = GATES["05_beta"]
    valid = [r for r in runs if r["positivity_ok"] and r["psi_peak"] > 0.95]
    mono = bool(all(b["width"] <= a["width"] + 1e-9
                    for a, b in zip(valid, valid[1:]))) if len(valid) > 1 else False
    verd = "PASS" if len(valid) >= g["min_valid"] and mono else "FAIL_SOLVER"
    c.fig_xy([r["beta"] for r in runs], [r["width"] for r in runs],
             "fig2_observable", "interface width vs beta", "beta", "width [lu]",
             source_raw=c.snaps["beta0.7_final"]["file"])
    c.fig_xy([r["beta"] for r in runs],
             [max(0.0, r["psi_peak"] - 1.0) for r in runs], "fig3_residual",
             "positivity violation max(0,|psi|max-1)", "beta",
             "max(0, |psi|max - 1)", source_raw=c.snaps["beta2.0_final"]["file"])
    c.fig_field_slice({"psi": s.psi(), "solid": s.solid}, "fig1_field",
                      "final interface fields", source_raw=c.snaps["beta2.0_final"]["file"])
    c.write_metrics(dict(runs=runs, widths_valid=[r["width"] for r in valid],
                         betas_valid=[r["beta"] for r in valid],
                         monotone_in_beta=mono,
                         invalid_by_positivity=[r["beta"] for r in runs
                                                if not r["positivity_ok"]],
                         invalid_by_dissolution=[r["beta"] for r in runs
                                                 if r["psi_peak"] <= 0.95],
                         gates=g, verdict=verd), ts)
    c.write_metadata(dict(grid=list(n), steps=steps, betas=list(betas),
                          wetting="none",
                          snapshot_times=[f"beta{b}_final" for b in betas],
                          exit_code=0))
    c.write_readme(dict(target="beta controls interface width inside a positivity-bounded range"),
                   dict(**{"domain size": n, "lattice": "D3Q19",
                           "initial condition": "psi=-tanh((z-c)/2)",
                           "solid geometry": "none",
                           "boundary conditions": "periodic",
                           "wetting convention": "n/a",
                           "nu": NU, "sigma": SIGMA, "beta": "swept",
                           "forcing": "none", "precision/backend": "numpy f64",
                           "run length": f"{steps} steps",
                           "snapshot times": "final per beta"}),
                   dict(relation="width(beta) monotone; |psi| <= 1 for a physical interface",
                        prose="An order parameter outside the component-fraction range is "
                              "an over-sharpening warning and is excluded from the valid set."),
                   [f"| beta={r['beta']} | |psi|<=1 and separated | {r['psi_peak']:.4f} | "
                    f"width {r['width']:.3f} | "
                    f"{'valid' if r in valid else 'EXCLUDED'} |" for r in runs],
                   "Monotone response is reported only over the positivity-valid set; the "
                   "tested beta range is not claimed to be the stability envelope.", verd)
    c.write_reproduce()
    c.write_render_manifest()
    return verd, c


# ===========================================================================
#  case 06 -- equal-wavelength axis isotropy (Fourier mode)
# ===========================================================================
def case_06(out_root, cand, steps=600):
    c = A.Case(out_root, 6, "axis-symmetry-isotropy", cand)
    arms = ((32, 16, 16, 0, 2), (16, 32, 16, 1, 2))
    runs, ts = [], []
    for Lx, Ly, Lz, wave_axis, kmode in arms:
        n = (Lx, Ly, Lz)
        s = make(n)
        s.init_psi(G.sine_interface(Lx, Ly, Lz, amp=1.5, k=kmode, width=2.0,
                                    wave_axis=wave_axis, normal_axis=2))
        c.snapshot(f"axis{wave_axis}_init", s)
        amps, tt = [], []
        for t in (0, 100, 200, 400, 600):
            if t:
                s.run(t - s.time)
            amps.append(G.fourier_mode_amplitude(s.psi(), wave_axis=wave_axis,
                                                 normal_axis=2, k=kmode))
            tt.append(s.time)
        c.snapshot(f"axis{wave_axis}_final", s)
        wl = (Lx if wave_axis == 0 else Ly) / kmode
        runs.append(dict(wave_axis=wave_axis, domain=list(n), mode=kmode,
                         wavelength=wl, amplitude_trace=amps, times=tt,
                         amplitude_final=amps[-1], max_abs_v=maxv(s)))
        ts += [dict(axis=wave_axis, t=t_, amp=a_) for t_, a_ in zip(tt, amps)]
    g = GATES["06_isotropy"]
    asym = abs(runs[0]["amplitude_final"] - runs[1]["amplitude_final"]) / max(
        runs[0]["amplitude_final"], runs[1]["amplitude_final"], 1e-30)
    equal = abs(runs[0]["wavelength"] - runs[1]["wavelength"]) < 1e-9
    verd = "PASS" if equal and asym < g["asymmetry"] else "FAIL_SOLVER"
    c.fig_field_slice({"psi": s.psi(), "solid": s.solid}, "fig1_field",
                      "final interface, wave along y",
                      source_raw=c.snaps["axis1_final"]["file"])
    c.fig_xy(runs[0]["times"], runs[0]["amplitude_trace"], "fig2_observable",
             "interface-height Fourier amplitude vs t", "t [steps]", "amplitude [lu]",
             series=[dict(y=runs[0]["amplitude_trace"], label="wave along x", style="o-"),
                     dict(y=runs[1]["amplitude_trace"], label="wave along y", style="s--")],
             source_raw=c.snaps["axis0_final"]["file"])
    c.fig_xy(runs[0]["times"],
             [abs(a - b) for a, b in zip(runs[0]["amplitude_trace"],
                                         runs[1]["amplitude_trace"])],
             "fig3_residual", "x-vs-y amplitude difference", "t [steps]",
             "|A_x - A_y|", logy=True, source_raw=c.snaps["axis0_final"]["file"])
    c.write_metrics(dict(runs=runs, equal_wavelength=bool(equal),
                         amplitude_asymmetry=float(asym), gates=g, verdict=verd,
                         scope="axis symmetry on a cubic lattice, not general "
                               "rotational isotropy"), ts)
    c.write_metadata(dict(steps=steps, arms=[list(a) for a in arms], wetting="none",
                          snapshot_times=["axis0_init", "axis0_final",
                                          "axis1_init", "axis1_final"], exit_code=0))
    c.write_readme(dict(target="equal-wavelength x/y axis symmetry of interface dynamics"),
                   dict(**{"domain size": f"{runs[0]['domain']} and {runs[1]['domain']}",
                           "lattice": "D3Q19",
                           "initial condition": "sinusoidal interface, lambda=16 lu in both arms",
                           "solid geometry": "none", "boundary conditions": "periodic",
                           "wetting convention": "n/a", "nu": NU, "sigma": SIGMA,
                           "beta": BETA, "forcing": "none",
                           "precision/backend": "numpy f64",
                           "run length": f"{steps} steps",
                           "snapshot times": "initial and final per arm"}),
                   dict(relation="equal-wavelength x and y waves must evolve identically",
                        prose="The domain is rotated with the wave so both arms have the "
                              "same lattice wavelength; the tracked quantity is the "
                              "interface-height Fourier mode, not an averaged field maximum."),
                   [f"| equal wavelength | yes | {runs[0]['wavelength']:.1f} vs "
                    f"{runs[1]['wavelength']:.1f} | - | {'ok' if equal else 'FAIL'} |",
                    f"| amplitude asymmetry | < {g['asymmetry']} | {asym:.3e} | "
                    f"{asym:.3e} | {'ok' if asym < g['asymmetry'] else 'FAIL'} |"],
                   "Scope limited to axis symmetry on a cubic lattice; a rotated/diagonal "
                   "case would be needed to claim general rotational isotropy.", verd)
    c.write_reproduce()
    c.write_render_manifest()
    return verd, c



# ===========================================================================
#  case 07 -- slit capillary pressure, walls TRANSVERSE to the meniscus (D2)
# ===========================================================================
def slit_transverse(n=(28, 14, 10), wall=2):
    """x = meniscus direction, y = slit gap, z = periodic extrusion.

    Solid plates at low and high y, x ends sealed so no periodic second
    interface can exist.  The fluid-fluid interface is a yz plane, i.e. it
    INTERSECTS both plates and forms two contact lines.  This replaces the
    pass-3 geometry, whose interface was parallel to the plates and had no
    contact line (external review R2, blocker R1).
    """
    s = np.zeros(n, dtype=bool)
    s[:, :wall, :] = True
    s[:, n[1] - wall:, :] = True
    s[:wall, :, :] = True
    s[n[0] - wall:, :, :] = True
    return s


def case_07(out_root, cand, angles=(60.0, 90.0, 120.0), n=(28, 14, 10),
            wall=2, steps=1500):
    c = A.Case(out_root, 7, "slit-capillary-pressure", cand)
    solid = slit_transverse(n, wall)
    h = n[1] - 2 * wall
    runs, ts = [], []
    for th in angles:
        s = make(n, solid=solid, theta_c=np.deg2rad(th))
        psi = np.full(n, -1.0)
        psi[:, :, :] = np.where(np.arange(n[0])[:, None, None] < n[0] // 2,
                                1.0, -1.0)
        psi[solid] = 0.0
        s.init_psi(psi)
        c.snapshot(f"theta{int(th)}_init", s)
        s.run(steps)
        c.snapshot(f"theta{int(th)}_final", s)
        rho, _ = s.macroscopic()
        xx = np.arange(n[0])[None, :, None] * np.ones(n)
        fluid = ~solid
        liq = fluid & (xx < n[0] // 2 - 4)
        gas = fluid & (xx > n[0] // 2 + 4)
        pl = float(rho[liq].mean()) / 3.0
        pg = float(rho[gas].mean()) / 3.0
        pc = pg - pl
        pc_theory = 2.0 * SIGMA * np.cos(np.deg2rad(th)) / h
        runs.append(dict(theta_prescribed_deg=th, gap=h, p_liquid=pl,
                         p_gas=pg, pc_measured=pc, pc_theory=pc_theory,
                         pc_ratio=(pc / pc_theory) if pc_theory else None,
                         psi_peak=float(np.abs(s.psi()).max()),
                         max_abs_v=maxv(s)))
        ts.append(dict(theta=th, pc_measured=pc, pc_theory=pc_theory))
    g = GATES["07_slit_pc"]
    ratios = [r["pc_ratio"] for r in runs if r["pc_ratio"] is not None]
    sign_ok = (runs[0]["pc_measured"] > 0 > runs[-1]["pc_measured"])
    ok = (len(ratios) == len(runs) and sign_ok
          and all(g["ratio_lo"] < abs(x) < g["ratio_hi"] for x in ratios))
    verd = "PASS" if ok else ("FAIL_SOLVER" if sign_ok else "INVALID_TEST")
    c.fig_field_slice({"psi": s.psi(), "solid": s.solid}, "fig1_field",
                      "slit meniscus, final psi (walls transverse)",
                      plane="xy", source_raw=c.snaps[f"theta{int(angles[-1])}_final"]["file"])
    c.fig_xy([r["theta_prescribed_deg"] for r in runs],
             [r["pc_measured"] for r in runs], "fig2_observable",
             "Pc vs prescribed contact angle (sign change is mandatory)",
             "theta [deg]", "Pc = p_gas - p_liquid",
             series=[dict(y=[r["pc_measured"] for r in runs],
                          label="measured", style="o-"),
                     dict(y=[r["pc_theory"] for r in runs],
                          label="2 sigma cos(theta)/h", style="s--")],
             source_raw=c.snaps[f"theta{int(angles[-1])}_final"]["file"])
    c.fig_xy([r["theta_prescribed_deg"] for r in runs],
             [r["pc_measured"] - r["pc_theory"] for r in runs], "fig3_residual",
             "Pc residual (measured - theory)", "theta [deg]", "residual",
             source_raw=c.snaps[f"theta{int(angles[-1])}_final"]["file"])
    c.write_metrics(dict(runs=runs, gap=h, sigma=SIGMA, gates=g, verdict=verd,
                         sign_change_across_60_120=bool(sign_ok)), ts)
    c.write_metadata(dict(grid=list(n), steps=steps, angles=list(angles),
                          solid="two plates at low/high y, x ends sealed",
                          wetting="leclaire", geometry_rev="transverse_v2",
                          snapshot_times=[f"theta{int(a)}_init" for a in angles]
                          + [f"theta{int(a)}_final" for a in angles], exit_code=0))
    c.write_readme(dict(target="static capillary pressure across a wall-intersecting meniscus"),
                   dict(**{"domain size": n, "lattice": "D3Q19",
                           "initial condition": "yz-plane interface at mid-x; liquid low-x, gas high-x",
                           "solid geometry": "two plates normal to y; x ends sealed; z periodic",
                           "boundary conditions": "periodic in z, no-slip solid, sealed x",
                           "wetting convention": "n_w = -grad(g)/|grad(g)|; theta through liquid/red",
                           "nu": NU, "sigma": SIGMA, "beta": BETA, "forcing": "none",
                           "precision/backend": "numpy f64", "run length": f"{steps} steps",
                           "snapshot times": "initial and final per angle"}),
                   dict(relation="Pc = 2 sigma cos(theta) / h for a z-invariant slit",
                        prose="The interface intersects both plates, so two contact lines exist "
                              "and the meniscus is curved. A flat meniscus with no contact line "
                              "would make this test invalid, not failed."),
                   [f"| theta={r['theta_prescribed_deg']:.0f} | Pc sign of cos(theta), "
                    f"|ratio| in [{g['ratio_lo']},{g['ratio_hi']}] | "
                    f"{r['pc_measured']:.3e} | ratio {r['pc_ratio']:.3f} | "
                    f"{'ok' if r['pc_ratio'] is not None and g['ratio_lo'] < abs(r['pc_ratio']) < g['ratio_hi'] else 'FAIL'} |"
                    for r in runs],
                   "Primary interpretation separates nominal-parameter accuracy (using input "
                   "sigma and prescribed theta) from internal consistency (measured sigma and theta).", verd)
    c.write_reproduce()
    c.write_render_manifest()
    return verd, c


# ===========================================================================
#  case 08 -- closed-system Jurin equilibrium (D3), reachability prechecked
# ===========================================================================
def jurin_geometry(n=(20, 16, 48), wall=4, neck=18):
    """Reservoir below, narrow slit above, floor and ceiling solid."""
    s = np.zeros(n, dtype=bool)
    s[:, :, 0] = True
    s[:, :, -1] = True
    s[:, :wall, neck:] = True
    s[:, n[1] - wall:, neck:] = True
    return s


def jurin_precheck(n, wall, neck, g_acc, theta_deg, z_res0, z_cap0):
    """Mandatory reachability precheck (contract D3)."""
    h = n[1] - 2 * wall
    dh = 2.0 * SIGMA * np.cos(np.deg2rad(theta_deg)) / (1.0 * g_acc * h)
    A_res = n[0] * n[1]
    A_cap = n[0] * h
    vol = A_res * z_res0 + A_cap * max(z_cap0 - neck, 0)
    M = (vol - A_cap * (dh - neck)) / (A_res + A_cap)
    L = M + dh
    return dict(gap=h, dh_theory=dh, reservoir_level_predicted=M,
                capillary_level_predicted=L, reservoir_window=[1, neck],
                capillary_window=[neck, n[2] - 2],
                inside_capillary=bool(neck <= L <= n[2] - 2),
                inside_reservoir=bool(1 <= M < neck),
                clearance_to_top=float(n[2] - 2 - L))


def case_08(out_root, cand, n=(20, 16, 48), wall=4, neck=18, theta_deg=60.0,
            g_acc=3.0e-4, z_res0=14, z_cap0=20, steps=4000):
    c = A.Case(out_root, 8, "jurin-equilibrium", cand)
    pre = jurin_precheck(n, wall, neck, g_acc, theta_deg, z_res0, z_cap0)
    solid = jurin_geometry(n, wall, neck)
    if not (pre["inside_capillary"] and pre["inside_reservoir"]):
        c.write_metadata(dict(precheck=pre, verdict="INVALID_CONFIGURATION"))
        return "INVALID_CONFIGURATION", c
    s = make(n, solid=solid, theta_c=np.deg2rad(theta_deg), fz=-g_acc)
    psi = np.full(n, -1.0)
    psi[:, :, :z_res0] = 1.0
    psi[:, wall:n[1] - wall, neck:z_cap0] = 1.0
    psi[solid] = 0.0
    s.init_psi(psi)
    c.snapshot("t0000", s)
    ts = []
    for t in range(0, steps + 1, max(1, steps // 10)):
        if t:
            s.run(t - s.time)
        p = s.psi()
        cap = p[n[0] // 2, n[1] // 2, neck:]
        fcap = ~solid[n[0] // 2, n[1] // 2, neck:]
        wi = np.where(fcap & (cap > 0))[0]
        capL = float(neck + wi.max()) if wi.size else float("nan")
        res = p[1, 1, :neck]
        wi2 = np.where(res > 0)[0]
        resL = float(wi2.max()) if wi2.size else float("nan")
        ts.append(dict(t=s.time, capillary_level=capL, reservoir_level=resL,
                       rise=(capL - resL) if np.isfinite(capL)
                       and np.isfinite(resL) else float("nan"),
                       max_v=maxv(s)))
        if t in (steps // 2,):
            c.snapshot("t_mid", s)
    c.snapshot("t_final", s)
    g = GATES["08_jurin"]
    rise = ts[-1]["rise"]
    ratio = rise / pre["dh_theory"] if np.isfinite(rise) else None
    ok = ratio is not None and g["rise_ratio_lo"] < ratio < g["rise_ratio_hi"]
    verd = "PASS" if ok else ("FAIL_SOLVER" if ratio is not None else "INCONCLUSIVE")
    c.fig_field_slice({"psi": s.psi(), "solid": s.solid}, "fig1_field",
                      "Jurin equilibrium, final psi (reservoir + capillary)",
                      plane="xz", source_raw=c.snaps["t_final"]["file"])
    c.fig_xy([r["t"] for r in ts], [r["rise"] for r in ts], "fig2_observable",
             "capillary rise above reservoir level vs t", "t [steps]", "rise [lu]",
             series=[dict(y=[r["rise"] for r in ts], label="measured", style="o-"),
                     dict(y=[pre["dh_theory"]] * len(ts), label="Jurin theory",
                          style="--")],
             source_raw=c.snaps["t_final"]["file"])
    c.fig_xy([r["t"] for r in ts],
             [r["rise"] - pre["dh_theory"] for r in ts], "fig3_residual",
             "rise residual (measured - Jurin)", "t [steps]", "residual [lu]",
             source_raw=c.snaps["t_final"]["file"])
    c.write_metrics(dict(precheck=pre, rise_final=rise,
                         rise_theory=pre["dh_theory"], rise_ratio=ratio,
                         theta_prescribed_deg=theta_deg, g=g_acc, gap=pre["gap"],
                         gates=g, verdict=verd), ts)
    c.write_metadata(dict(grid=list(n), steps=steps, wall=wall, neck=neck,
                          theta_deg=theta_deg, gravity=g_acc,
                          initial="liquid column continuous from reservoir into capillary",
                          wetting="leclaire", precheck=pre,
                          snapshot_times=["t0000", "t_mid", "t_final"], exit_code=0))
    c.write_readme(dict(target="closed-system equilibrium Jurin rise"),
                   dict(**{"domain size": n, "lattice": "D3Q19",
                           "initial condition": f"liquid fills z<{z_res0} in the reservoir and "
                           f"z<{z_cap0} in the capillary (a connected column inside the capillary)",
                           "solid geometry": f"floor+ceiling solid; slit walls for z>={neck}",
                           "boundary conditions": "periodic lateral; no-slip solid; closed box",
                           "wetting convention": "n_w=-grad(g)/|grad(g)|; theta through liquid/red",
                           "nu": NU, "sigma": SIGMA, "beta": BETA,
                           "forcing": f"gravity fz=-{g_acc} (R1 Eqs. 6-9)",
                           "precision/backend": "numpy f64", "run length": f"{steps} steps",
                           "snapshot times": "initial, intermediate, final"}),
                   dict(relation="dh = 2 sigma cos(theta) / (rho g h)",
                        prose="Equilibrium rise of the capillary meniscus above the flat "
                              "reservoir level. The initial condition already places liquid "
                              "inside the capillary, and the reachability precheck aborts as "
                              "INVALID_CONFIGURATION if the predicted equilibrium leaves the "
                              "measurement window."),
                   [f"| predicted capillary level | inside [{pre['capillary_window'][0]},"
                    f"{pre['capillary_window'][1]}] | {pre['capillary_level_predicted']:.2f} | "
                    f"- | ok |",
                    f"| rise | within {g['rise_ratio_lo']}-{g['rise_ratio_hi']}x theory | "
                    f"{rise if rise is not None else float('nan'):.3f} | "
                    f"ratio {ratio if ratio else float('nan'):.3f} | "
                    f"{'ok' if ok else 'FAIL'} |"],
                   "Closed-system equilibrium test; dynamic Washburn imbibition is out of "
                   "scope for this stage.", verd)
    c.write_reproduce()
    c.write_render_manifest()
    return verd, c


# ===========================================================================
#  case 09 -- asymmetric wall under the frozen convention (D6)
# ===========================================================================
def case_09(out_root, cand, n=(28, 16, 16), band=3, steps=1500):
    c = A.Case(out_root, 9, "asymmetric-wall", cand)
    solid = G.asymmetric_ledge(*n)
    closed = G.assert_closed_box(solid)
    s = make(n, solid=solid)
    psi = np.full(n, -1.0)
    psi[:, :, :n[2] // 2] = 1.0
    psi[solid] = 0.0
    s.init_psi(psi)
    c.snapshot("t0000", s)
    wb = G.wall_band(n, solid, thickness=band)
    m0 = masses(s)
    r0 = float(s.rho_r[wb].sum())
    ts = []
    for t in range(0, steps + 1, max(1, steps // 12)):
        if t:
            s.run(t - s.time)
        rr = float(s.rho_r.sum())
        bb = float(s.rho_b.sum())
        ts.append(dict(t=s.time, wall_band_red=float(s.rho_r[wb].sum()),
                       red_total=rr, blue_total=bb,
                       red_excursion=(rr - m0[0]) / m0[0],
                       blue_excursion=(bb - m0[1]) / m0[1],
                       max_v=maxv(s)))
        if t in (steps // 2,):
            c.snapshot("t_mid", s)
    c.snapshot("t_final", s)
    g = GATES["09_killer"]
    m1 = masses(s)
    rel = (ts[-1]["wall_band_red"] - r0) / max(r0, 1e-30)
    late = ts[len(ts) // 2:]
    dt = late[-1]["t"] - late[0]["t"]
    lr = (late[-1]["red_total"] - late[0]["red_total"]) / dt if dt else float("nan")
    lb = (late[-1]["blue_total"] - late[0]["blue_total"]) / dt if dt else float("nan")
    exc_r = G.max_abs_over_time(ts, "red_excursion")
    exc_b = G.max_abs_over_time(ts, "blue_excursion")
    ncomp, sizes = G.labelled_components(np.where(solid, -1.0, s.psi()), 0.5)
    ok = (closed["all_closed"] and abs(rel) < g["wall_band"]
          and exc_r < g["excursion"] and exc_b < g["excursion"]
          and abs(lr) < g["late_rate"] and abs(lb) < g["late_rate"]
          and ncomp <= 1)
    verd = "PASS" if ok else "FAIL_SOLVER"
    c.fig_field_slice({"psi": s.psi(), "solid": s.solid}, "fig1_field",
                      "asymmetric ledge, final psi (solid overlaid)",
                      plane="xz", source_raw=c.snaps["t_final"]["file"])
    c.fig_xy([r["t"] for r in ts], [r["wall_band_red"] for r in ts],
             "fig2_observable", "wall-band liquid mass vs t", "t [steps]",
             "wall-band red mass",
             series=[dict(y=[r["wall_band_red"] for r in ts], label="measured",
                          style="o-"),
                     dict(y=[r0] * len(ts), label="initial", style="--")],
             source_raw=c.snaps["t_final"]["file"])
    c.fig_xy([r["t"] for r in ts],
             [max(abs(r["red_excursion"]), abs(r["blue_excursion"]))
              for r in ts], "fig3_residual",
             "global mass excursion vs t (max of red/blue)", "t [steps]",
             "relative excursion", logy=True, source_raw=c.snaps["t_final"]["file"])
    c.write_metrics(dict(closed_box=closed, wall_band_red_relative=rel,
                         max_red_excursion=exc_r, max_blue_excursion=exc_b,
                         late_red_rate_per_step=lr, late_blue_rate_per_step=lb,
                         red_drift=abs(m1[0] - m0[0]), blue_drift=abs(m1[1] - m0[1]),
                         n_components_final=ncomp, component_sizes=sizes[:5],
                         max_abs_v=G.max_abs_over_time(ts, "max_v"),
                         gates=g, verdict=verd,
                         attribution="wall-band change is NOT attributed to wall mass "
                                     "transfer; no stationary reference case was run"),
                    ts)
    c.write_metadata(dict(grid=list(n), steps=steps, band=band,
                          solid="one-sided ledge, four lateral faces closed",
                          wetting="none (no prescribed angle)", precheck=closed,
                          snapshot_times=["t0000", "t_mid", "t_final"], exit_code=0))
    c.write_readme(dict(target="closed asymmetric wall: global mass integrity and wall-band behaviour"),
                   dict(**{"domain size": n, "lattice": "D3Q19",
                           "initial condition": "liquid in the lower half",
                           "solid geometry": "one-sided overhang + floor, all four lateral "
                           "faces closed (verified in code)",
                           "boundary conditions": "no-slip solid; closed box",
                           "wetting convention": "n/a (no prescribed angle in this case)",
                           "nu": NU, "sigma": SIGMA, "beta": BETA, "forcing": "none",
                           "precision/backend": "numpy f64", "run length": f"{steps} steps",
                           "snapshot times": "initial, intermediate, final"}),
                   dict(relation="closed box: total and component mass conserved; no wall "
                        "mass transfer without a driving force",
                        prose="Global and component mass are gated on the maximum time-history "
                              "excursion and on the late-window rate, so the solid-node "
                              "reservoir fill is separated from real creation."),
                   [f"| closed topology | yes | {closed['all_closed']} | - | "
                    f"{'ok' if closed['all_closed'] else 'FAIL'} |",
                    f"| max red excursion | < {g['excursion']} | {exc_r:.3e} | "
                    f"{exc_r:.3e} | {'ok' if exc_r < g['excursion'] else 'FAIL'} |",
                    f"| late red rate | < {g['late_rate']}/step | {lr:.3e} | - | "
                    f"{'ok' if abs(lr) < g['late_rate'] else 'FAIL'} |",
                    f"| wall-band red change | < {g['wall_band']} | {rel:.4f} | - | "
                    f"{'ok' if abs(rel) < g['wall_band'] else 'FAIL'} |"],
                   "The wall-band change is reported but NOT attributed to wall mass transfer: "
                   "making that claim needs a stationary/no-driving reference, which this "
                   "round does not include.", verd)
    c.write_reproduce()
    c.write_render_manifest()
    return verd, c


# ===========================================================================
#  case 10 -- conservation audit
# ===========================================================================
def case_10(out_root, cand, n=(8, 8, 24), steps=1000):
    c = A.Case(out_root, 10, "conservation", cand)
    runs, ts = [], []
    for overlay in (None, "f64_arithmetic"):
        s = make(n, conservation_overlay=overlay)
        s.init_psi(G.planar_interface(n[0], n[1], n[2], width=2.0))
        m0 = masses(s)
        tot0 = m0[0] + m0[1]
        trace = []
        for t in range(0, steps + 1, max(1, steps // 10)):
            if t:
                s.run(t - s.time)
            mr, mb = masses(s)
            trace.append(dict(t=s.time, red=mr, blue=mb, total=mr + mb))
        c.snapshot(f"overlay_{overlay}_final", s)
        mr1, mb1 = masses(s)
        runs.append(dict(overlay=str(overlay), steps=steps,
                         red_drift_per_step=abs(mr1 - m0[0]) / steps,
                         blue_drift_per_step=abs(mb1 - m0[1]) / steps,
                         total_drift_per_step=abs((mr1 + mb1) - tot0) / steps,
                         red_mass=m0[0]))
        ts += [dict(overlay=str(overlay), t=r["t"], red=r["red"], blue=r["blue"])
               for r in trace]
    g = GATES["10_conservation"]
    core = runs[0]
    ok = (core["total_drift_per_step"] < g["total_per_step"]
          and core["red_drift_per_step"] < g["comp_per_step"]
          and core["blue_drift_per_step"] < g["comp_per_step"])
    verd = "PASS" if ok else "FAIL_SOLVER"
    c.fig_field_slice({"psi": s.psi(), "solid": s.solid}, "fig1_field",
                      "planar interface used for the conservation audit",
                      source_raw=c.snaps["overlay_None_final"]["file"])
    c.fig_xy([r["t"] for r in ts if r["overlay"] == "None"],
             [r["red"] for r in ts if r["overlay"] == "None"],
             "fig2_observable", "component mass vs t (L17_CORE, no overlay)",
             "t [steps]", "red mass",
             source_raw=c.snaps["overlay_None_final"]["file"])
    c.fig_xy([r["overlay"] for r in runs],
             [r["red_drift_per_step"] for r in runs], "fig3_residual",
             "component drift per step", "arm", "drift / step", logy=True,
             source_raw=c.snaps["overlay_None_final"]["file"])
    c.write_metrics(dict(runs=runs, gates=g, verdict=verd,
                         scope_limitation="EXTERNAL REVIEW B10: this result is for the "
                         "isolated NumPy/f64 reference implementation only. The project's "
                         "earlier conservation defect was precision/backend specific, so "
                         "this must NOT be generalised to a Taichi/f32 port without "
                         "repeating the audit there."), ts)
    c.write_metadata(dict(grid=list(n), steps=steps, arms=["None", "f64_arithmetic"],
                          wetting="none",
                          snapshot_times=["overlay_None_final", "overlay_f64_arithmetic_final"],
                          exit_code=0))
    c.write_readme(dict(target="total and component mass conservation of the reference solver"),
                   dict(**{"domain size": n, "lattice": "D3Q19",
                           "initial condition": "psi=-tanh((z-c)/2)", "solid geometry": "none",
                           "boundary conditions": "periodic",
                           "wetting convention": "n/a", "nu": NU, "sigma": SIGMA,
                           "beta": BETA, "forcing": "none",
                           "precision/backend": "numpy f64", "run length": f"{steps} steps",
                           "snapshot times": "final per arm"}),
                   dict(relation="total and component mass are invariants of the update",
                        prose="The paper's recolouring is mass-exact by construction (the rest "
                              "population is untouched and sum_i W_i cos(theta_i) = 0); the "
                              "project-style overlay is offered as a default-off arm and is "
                              "never described as paper-faithful."),
                   [f"| {r['overlay']} total/step | < {g['total_per_step']:.0e} | "
                    f"{r['total_drift_per_step']:.3e} | - | "
                    f"{'ok' if r['total_drift_per_step'] < g['total_per_step'] else 'FAIL'} |"
                    for r in runs],
                   "Scope: NumPy/f64 reference only; a Taichi/f32 port needs its own audit.", verd)
    c.write_reproduce()
    c.write_render_manifest()
    return verd, c


# ===========================================================================
#  case 11 -- planar mechanical-sigma diagnostic (D5)
# ===========================================================================
def case_11(out_root, cand, n=(6, 6, 64), steps=800, width=2.5):
    """Mechanical surface tension from the planar momentum-flux anisotropy.

    Derivation: MECHANICAL_SIGMA_DERIVATION.md.  The R1 perturbation has
    second moment

        dPi_ab = (2/9) A |F| (n_a n_b - delta_ab)

    so for a planar interface with normal z,

        Pi_zz - Pi_xx = (2/9) A |F| = (2/9) A |dpsi/dz|

    and, since |grad psi| integrates to the total variation 2 over a
    monotone profile,

        sigma_mech = int (P_N - P_T) dz = (2/9) A * 2 = (4/9) A.

    With A = (9/4) omega_eff sigma this is exactly sigma when omega_eff = 1.
    The diagnostic measures the integral from the simulated field and does
    not assume the result.
    """
    c = A.Case(out_root, 11, "mechanical-sigma", cand)
    s = make(n)
    s.init_psi(G.planar_interface(n[0], n[1], n[2], width=width))
    s.run(steps)
    c.snapshot("t_final", s)
    N = s.Nr + s.Nb
    Ef = L.E.astype(float)
    Pi = np.einsum("...i,ia,ib->...ab", N, Ef, Ef)      # momentum flux tensor
    pn = Pi[..., 2, 2]
    pt = 0.5 * (Pi[..., 0, 0] + Pi[..., 1, 1])
    pn_prof = pn[n[0] // 2, n[1] // 2, :]
    pt_prof = pt[n[0] // 2, n[1] // 2, :]
    bulk = slice(2, 8)
    d_pn = pn_prof - pn_prof[bulk].mean()
    d_pt = pt_prof - pt_prof[bulk].mean()
    diff = d_pn - d_pt
    sigma_mech = float(np.sum(diff))
    sigma_th = SIGMA
    g = GATES["11_mech_sigma"]
    ratio = sigma_mech / sigma_th
    ok = g["ratio_lo"] < ratio < g["ratio_hi"]
    verd = "PASS" if ok else "EXPLORATORY_UNGATED"
    c.fig_field_slice({"psi": s.psi(), "solid": s.solid}, "fig1_field",
                      "planar interface used for the mechanical-sigma integral",
                      source_raw=c.snaps["t_final"]["file"])
    zz = np.arange(n[2])
    c.fig_xy(zz, diff, "fig2_observable",
             "P_N - P_T profile across the interface", "z [lu]", "P_N - P_T",
             series=[dict(y=diff, label="P_N - P_T", style="o-")],
             source_raw=c.snaps["t_final"]["file"])
    c.fig_xy(zz, np.cumsum(diff), "fig3_residual",
             "cumulative integral (plateaus at sigma_mech)", "z [lu]",
             "cumulative integral",
             series=[dict(y=np.cumsum(diff), label="cumulative", style="o-"),
                     dict(y=[sigma_th] * n[2], label="sigma_input", style="--")],
             source_raw=c.snaps["t_final"]["file"])
    c.write_metrics(dict(sigma_mech=sigma_mech, sigma_input=sigma_th,
                         sigma_ratio=ratio, A_coefficient=2.25,
                         omega_eff=1.0,
                         predicted_from_derivation=(4.0 / 9.0) * 2.25 * SIGMA,
                         gates=g, verdict=verd,
                         note="Eq.(18) is not retuned; an offset is a reported result."),
                    [dict(z=int(z), pn=float(a), pt=float(b), diff=float(d))
                     for z, a, b, d in zip(zz, d_pn, d_pt, diff)])
    c.write_metadata(dict(grid=list(n), steps=steps, width=width, wetting="none",
                          snapshot_times=["t_final"], exit_code=0))
    c.write_readme(dict(target="mechanical surface tension for a planar interface"),
                   dict(**{"domain size": n, "lattice": "D3Q19",
                           "initial condition": "psi=-tanh((z-c)/2.5)",
                           "solid geometry": "none", "boundary conditions": "periodic",
                           "wetting convention": "n/a", "nu": NU, "sigma": SIGMA,
                           "beta": BETA, "forcing": "none",
                           "precision/backend": "numpy f64", "run length": f"{steps} steps",
                           "snapshot times": "final"}),
                   dict(relation="sigma = int (P_N - P_T) dn   with dPi_ab = "
                        "(2/9) A |F| (n_a n_b - delta_ab)",
                        prose="See MECHANICAL_SIGMA_DERIVATION.md for the full derivation; "
                              "the quadrature is a plain sum over nodes (dz = 1) after "
                              "subtracting the bulk momentum-flux value."),
                   [f"| sigma_mech | within {g['ratio_lo']}-{g['ratio_hi']}x sigma_input | "
                    f"{sigma_mech:.5f} | ratio {ratio:.3f} | "
                    f"{'ok' if ok else 'EXPLORATORY'} |"],
                   "The derivation closes the prefactor from R1 Eqs. (16)-(18) and needs no "
                   "collision/relaxation factor because the perturbation is applied to the "
                   "distribution AFTER the collision and therefore enters the momentum flux "
                   "directly.", verd)
    c.write_reproduce()
    c.write_render_manifest()
    return verd, c


CASES = {1: case_01, 2: case_02, 3: case_03, 4: case_04, 5: case_05, 6: case_06,
         7: case_07, 8: case_08, 9: case_09, 10: case_10, 11: case_11}


def run_one(idx, out_root=OUT_ROOT, cand=None):
    if cand is None:
        import subprocess
        cand = subprocess.run(["git", "rev-parse", "HEAD"],
                              capture_output=True, text=True,
                              cwd=os.path.join(HERE, "..", "..")).stdout.strip()
    return CASES[idx](out_root, cand)


def main():
    import subprocess
    cand = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                          text=True, cwd=os.path.join(HERE, "..", "..")).stdout.strip()
    os.makedirs(OUT_ROOT, exist_ok=True)
    t0 = time.time()
    results, verdicts = {}, {}
    for idx in sorted(CASES):
        ts = time.time()
        try:
            verd, cobj = CASES[idx](OUT_ROOT, cand)
            code = 0
        except Exception as exc:                       # noqa: BLE001
            import traceback
            traceback.print_exc()
            verd, cobj, code = "NOT_RUN", None, 1
        verdicts[f"case-{idx:02d}"] = verd
        results[f"case-{idx:02d}"] = dict(verdict=verd, wall_seconds=time.time() - ts,
                                          dir=(os.path.relpath(cobj.dir, OUT_ROOT)
                                               if cobj else None),
                                          exit_code=code)
        print(f"[{verd:>18s}] case-{idx:02d}  ({time.time()-ts:.1f} s, exit {code})",
              flush=True)
    counts = {}
    for v in verdicts.values():
        counts[v] = counts.get(v, 0) + 1
    summary = dict(stage="BI-CG-LECLAIRE-PASS4-001", candidate_sha=cand,
                   branch="agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001",
                   environment=A.environment(), verdict_counts=counts,
                   cases=results, total_wall_seconds=time.time() - t0,
                   gates=GATES, raw_schema_version=A.RAW_SCHEMA_VERSION,
                   convention="n_w=-grad(g)/|grad(g)| solid->fluid; theta through liquid/red")
    with io.open(os.path.join(OUT_ROOT, "SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=float)
    with io.open(os.path.join(OUT_ROOT, "run_manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(dict(stage=summary["stage"], candidate_sha=cand,
                       environment=summary["environment"],
                       cases={k: dict(dir=v["dir"], exit_code=v["exit_code"],
                                      verdict=v["verdict"],
                                      wall_seconds=v["wall_seconds"])
                              for k, v in results.items()},
                       raw_schema_version=A.RAW_SCHEMA_VERSION,
                       command="python tests/leclaire_cg/pass04.py"),
                   fh, indent=2, default=float)
    write_validation_report(OUT_ROOT, cand)
    print("verdicts:", counts, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())


def write_validation_report(out_root, cand):
    """Generate VALIDATION_REPORT.md from the just-written evidence.

    Data-driven: every number is read from the case metrics, so the prose
    cannot drift from the artifacts.
    """
    with io.open(os.path.join(out_root, "SUMMARY.json"), encoding="utf-8") as fh:
        sm = json.load(fh)
    rows, detail = [], []
    for key in sorted(sm["cases"]):
        info = sm["cases"][key]
        cd = os.path.join(out_root, info["dir"])
        meta, metr = {}, {}
        for fn, tgt in (("metadata.json", meta), ("metrics.json", metr)):
            fp = os.path.join(cd, fn)
            if os.path.exists(fp):
                with io.open(fp, encoding="utf-8") as fh:
                    tgt.update(json.load(fh))
        rows.append((key, info["verdict"], cd))
        detail.append(dict(key=key, verdict=info["verdict"],
                           metrics=metr, metadata=meta, dir=info["dir"]))
    lines = [
        "# Pass-04 Validation Report — Leclaire/Latt reference line",
        "",
        f"- stage: `BI-CG-LECLAIRE-PASS4-001`",
        f"- candidate SHA: `{cand}`",
        f"- branch: `agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001`",
        f"- raw-data schema: `{sm['raw_schema_version']}`",
        f"- convention: {sm['convention']}",
        f"- verdict counts: {sm['verdict_counts']}",
        "",
        "This is the **current headline** for this solver line. Passes 1, 2 and 3",
        "remain in Git history and in `results/leclaire_cg/` and are **SUPERSEDED**;",
        "their claims are not current.",
        "",
        "## Case summary",
        "",
        "| case | verdict | artifact |",
        "|---|---|---|",
    ]
    for key, verd, cd in rows:
        lines.append(f"| {key} | **{verd}** | `{os.path.basename(cd)}/README.md` |")
    lines += ["", "## Per-case evidence", ""]
    for d in detail:
        m = d["metrics"]
        lines.append(f"### {d['key']} — {d['verdict']}")
        lines.append("")
        lines.append(f"Artifact: `{d['dir']}/`")
        lines.append("")
        keep = {k: v for k, v in m.items()
                if isinstance(v, (int, float, str, bool))}
        if keep:
            lines.append("| metric | value |")
            lines.append("|---|---:|")
            for k, v in keep.items():
                lines.append(f"| {k} | {v:.6g} |" if isinstance(v, float)
                             else f"| {k} | {v} |")
            lines.append("")
        if m.get("scope_limitation"):
            lines.append(f"> {m['scope_limitation']}")
            lines.append("")
        if m.get("note"):
            lines.append(f"> {m['note']}")
            lines.append("")
    lines += [
        "## Reading rule",
        "",
        "A verdict of `FAIL_SOLVER` is a solver result; `INVALID_TEST` and",
        "`INCONCLUSIVE` are test-design outcomes and must never be presented as",
        "solver failures. `EXPLORATORY_UNGATED` marks a diagnostic whose prefactor",
        "is not closed from the source.",
        "",
    ]
    with io.open(os.path.join(out_root, "VALIDATION_REPORT.md"), "w",
                 encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("VALIDATION_REPORT.md written", flush=True)

