"""Canonical validation matrix for the L17_CORE Leclaire-2017 candidate.

Task: BI-CG-LECLAIRE-IMPLEMENTATION-001.

Runs the ten required tests, writes one machine-readable JSON per test plus
a ``summary.json`` and a per-test exit code, and returns a process exit code
that is 0 only when every test reached a verdict.

Verdict vocabulary (AGENTS.md "Validation and evidence"):
    PASS          the pre-declared acceptance statement is met
    FAIL          the acceptance statement is not met
    INCONCLUSIVE  the measurement is not attributable to the model
    NOT_RUN       the test did not execute

The acceptance statements are declared in ``TESTS`` below, before the runs,
and are not edited afterwards.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                "experimental"))

from leclaire_cg import LeclaireCG3D            # noqa: E402
from leclaire_cg import geometry as G           # noqa: E402
from leclaire_cg import operators as op         # noqa: E402
from leclaire_cg import lattice as L            # noqa: E402

RESULTS = os.path.join(os.path.dirname(__file__), "..", "..", "results",
                       "leclaire_cg")

NU = 1.0 / 6.0
SIGMA = 0.02
BETA = 0.7


# ======================================================================
#  helpers
# ======================================================================
def make(n, solid=None, **kw):
    params = dict(nu_r=NU, nu_b=NU, sigma=SIGMA, beta=BETA)
    params.update(kw)
    s = LeclaireCG3D(n[0], n[1], n[2], **params)
    s.set_solid(solid if solid is not None else
                np.zeros(n, dtype=bool))
    return s


def masses(s):
    return s.component_masses()


def z_profile(psi):
    return psi[psi.shape[0] // 2, psi.shape[1] // 2, :]


def max_fluid_velocity(s):
    """max |u| over FLUID nodes.

    Whole-domain max|u| is misleading in any geometry with solid nodes:
    a solid node holds only what streaming delivered, so rho there can be
    small and u = mom/rho large, and the number is not a physical
    velocity.  Measured on the asymmetric-ledge geometry: whole-domain
    1.41 versus fluid-only 0.021.  Only the fluid value is a spurious-
    current diagnostic.
    """
    _, u = s.macroscopic()
    sp = np.linalg.norm(u, axis=-1)
    return float(sp[s.fluid].max()) if np.any(s.fluid) else 0.0


# ======================================================================
#  test 1 -- uniform single-phase stationarity
# ======================================================================
def test_01_uniform(steps=400, n=(8, 8, 8)):
    s = make(n)
    s.init_uniform(psi=1.0, rho=1.0)
    rho0 = (s.rho_r + s.rho_b).copy()
    m0 = masses(s)
    s.run(steps)
    rho, u = s.macroscopic()
    m1 = masses(s)
    res = dict(
        max_abs_v=max_fluid_velocity(s),
        max_abs_drho=float(np.abs(rho - rho0).max()),
        red_mass_drift=abs(m1[0] - m0[0]),
        blue_mass_drift=abs(m1[1] - m0[1]),
        blue_max=float(s.rho_b.max()),
        steps=steps, grid=list(n),
    )
    res["verdict"] = "PASS" if (res["max_abs_v"] < 1e-12
                                and res["max_abs_drho"] < 1e-12) else "FAIL"
    res["acceptance"] = "max|v| < 1e-12 and max|drho| < 1e-12 (machine precision)"
    return res


# ======================================================================
#  test 2 -- planar interface stationarity
# ======================================================================
def test_02_planar(steps=1000, n=(6, 6, 32)):
    s = make(n)
    s.init_psi(G.planar_interface(n[0], n[1], n[2], width=2.0))
    p0 = z_profile(s.psi())
    c0 = G.interface_position_1d(p0)
    amp0 = float(np.abs(p0).max())
    trace = []
    for t in range(0, steps + 1, max(1, steps // 10)):
        if t:
            s.run(t - s.time)
        p = z_profile(s.psi())
        trace.append(dict(t=s.time,
                          pos=float(G.interface_position_1d(p)),
                          amp=float(np.abs(p).max()),
                          spurious_v=max_fluid_velocity(s)))
    c1 = trace[-1]["pos"]
    res = dict(
        interface_pos_initial=float(c0),
        interface_pos_final=float(c1),
        interface_pos_drift=float(abs(c1 - c0)) if np.isfinite(c1) else None,
        amplitude_initial=amp0,
        amplitude_final=trace[-1]["amp"],
        amplitude_ratio=trace[-1]["amp"] / amp0 if amp0 else None,
        max_spurious_v=trace[-1]["spurious_v"],
        trace=trace,
        steps=steps, grid=list(n),
    )
    # A stationary planar interface must keep both its position AND its
    # phase amplitude.  Position alone is not enough: a dissolved
    # interface is trivially "stationary".
    ok = (res["interface_pos_drift"] is not None
          and res["interface_pos_drift"] < 0.5
          and res["amplitude_ratio"] is not None
          and res["amplitude_ratio"] > 0.95)
    res["verdict"] = "PASS" if ok else "FAIL"
    res["acceptance"] = ("interface position drift < 0.5 lu AND final |psi|max "
                         "> 0.95 * initial (i.e. the interface survives)")
    return res


# ======================================================================
#  test 3 -- Laplace droplet
# ======================================================================
def test_03_laplace(steps=1200, n=(26, 26, 26), radii=(5.0, 7.0, 9.0)):
    out = []
    for R in radii:
        s = make(n)
        s.init_psi(G.droplet(n[0], n[1], n[2], R,
                             center=(n[0] / 2, n[1] / 2, n[2] / 2)))
        psi0 = float(np.abs(s.psi()).max())
        s.run(steps)
        rho, u = s.macroscopic()
        X, Y, Z = G.grid(*n)
        r = np.sqrt((X - n[0] / 2) ** 2 + (Y - n[1] / 2) ** 2
                    + (Z - n[2] / 2) ** 2)
        ins = r < R - 3.5
        outs = r > R + 3.5
        dp = float((rho[ins].mean() - rho[outs].mean()) / 3.0)
        psi1 = float(np.abs(s.psi()).max())
        # interface width of the equilibrium profile, for the R/w ratio
        rmid = r[:, n[1] // 2, n[2] // 2]
        wfit, _ = G.interface_width_tanh(s.psi()[:, n[1] // 2, n[2] // 2])
        out.append(dict(R=R, dp=dp, sigma_measured=dp * R / 2.0,
                        sigma_input=SIGMA,
                        sigma_ratio=(dp * R / 2.0) / SIGMA if SIGMA else None,
                        psi_peak_initial=psi0, psi_peak_final=psi1,
                        psi_peak_ratio=psi1 / psi0 if psi0 else None,
                        interface_width=float(wfit),
                        R_over_w=float(R / wfit) if wfit > 0 else None,
                        max_abs_v=max_fluid_velocity(s)))
    res = dict(runs=out, steps=steps, grid=list(n), sigma_input=SIGMA)
    ratios = [o["sigma_ratio"] for o in out]
    res["sigma_ratio_range"] = [min(ratios), max(ratios)]
    survived = all(o["psi_peak_ratio"] is not None
                   and o["psi_peak_ratio"] > 0.95 for o in out)
    res["droplet_survived"] = survived
    # A Laplace law is demonstrated if the droplet survives AND the
    # implied sigma is radius-independent.  Agreement with the INPUT
    # sigma is reported separately as a calibration ratio, because R1
    # Eq. (18) fixes A = (9/4) omega sigma and the measured value depends
    # on the discrete |F|, which is the one element of the formulation
    # with an unresolved published coefficient set (R5).
    spread = max(ratios) - min(ratios)
    res["sigma_ratio_spread"] = float(spread)
    res["laplace_law_demonstrated"] = bool(survived and spread < 0.15)
    res["verdict"] = "PASS" if (survived and spread < 0.15
                                and min(ratios) > 0.7) else (
        "FAIL" if not survived else "FAIL")
    res["acceptance"] = ("droplet survives every radius AND the implied "
                         "sigma is radius-independent within 15% AND the "
                         "calibration ratio sigma_meas/sigma_input >= 0.7")
    return res


# ======================================================================
#  test 4 -- static contact angle
# ======================================================================
def test_04_contact_angle(steps=2000, n=(24, 24, 20), thetas_deg=(60.0, 90.0,
                                                                 120.0)):
    out = []
    for th in thetas_deg:
        s = make(n, solid=G.wall_slab(n[0], n[1], n[2], thickness=2),
                 theta_c=np.deg2rad(th))
        s.init_psi(G.hemi_droplet_on_wall(n[0], n[1], n[2], radius=6.0))
        s.run(steps)
        psi = s.psi()
        # contact-line radius: where psi = 0 at the first fluid layer
        k0 = 2
        row = psi[:, :, k0]
        x = np.arange(n[0])[:, None]
        y = np.arange(n[1])[None, :]
        cxy = np.array([n[0] / 2, n[1] / 2])
        rr = np.sqrt((x - cxy[0]) ** 2 + (y - cxy[1]) ** 2)
        pos = rr[row > 0]
        rb = float(pos.max()) if pos.size else 0.0
        pos_all = rr[row < 0]
        # apex height along the centre column
        col = psi[n[0] // 2, n[1] // 2, :]
        ok = np.where(col > 0)[0]
        apex = float(ok.max() - (k0 - 1)) if ok.size else 0.0
        theta_meas = float(np.degrees(2.0 * np.arctan(apex / rb))
                           ) if rb > 0 else None
        out.append(dict(theta_prescribed_deg=th, rb=rb, apex=apex,
                        theta_measured_deg=theta_meas,
                        psi_peak=float(np.abs(psi).max())))
    res = dict(runs=out, steps=steps, grid=list(n))
    meas = [o for o in out if o["theta_measured_deg"] is not None
            and o["psi_peak"] > 0.9]
    if len(meas) == len(out) and all(
            abs(o["theta_measured_deg"] - o["theta_prescribed_deg"]) < 15.0
            for o in meas):
        res["verdict"] = "PASS"
    elif not meas:
        res["verdict"] = "FAIL"
        res["reason"] = ("no run kept a measurable droplet (|psi|peak <= 0.9 "
                         "on every prescribed angle)")
    else:
        res["verdict"] = "FAIL"
    res["acceptance"] = ("every prescribed angle keeps |psi|peak > 0.9 AND "
                         "measured theta within 15 deg")
    return res


# ======================================================================
#  test 5 -- interface width versus beta
# ======================================================================
def test_05_width_vs_beta(steps=600, n=(6, 6, 32),
                          betas=(0.0, 0.5, 0.7, 1.0, 1.5, 2.0)):
    out = []
    for b in betas:
        s = make(n, beta=b)
        s.init_psi(G.planar_interface(n[0], n[1], n[2], width=2.0))
        s.run(steps)
        p = z_profile(s.psi())
        w, _ = G.interface_width_tanh(p)
        out.append(dict(beta=b, width=float(w),
                        psi_peak=float(np.abs(p).max()),
                        slope=float(np.abs(np.diff(p)).max())))
    res = dict(runs=out, steps=steps, grid=list(n))
    # The paper's claim (R2) is that beta controls the numerical interface
    # thickness.  At this resolution the measured quantity is the terminal
    # interface state as a function of beta, and the defining property is
    # that a physical diffuse interface has |psi| -> 1 in BOTH bulks.
    peaks = [o["psi_peak"] for o in out]
    res["psi_peak_min"] = float(min(peaks))
    res["psi_peak_max"] = float(max(peaks))
    physical = [o for o in out if o["psi_peak"] > 0.95]
    res["n_beta_with_physical_interface"] = len(physical)
    if physical:
        widths = [o["width"] for o in physical]
        res["widths_physical"] = widths
        res["betas_physical"] = [o["beta"] for o in physical]
        res["monotone_in_beta"] = bool(
            all(b <= a + 1e-9 for a, b in zip(widths, widths[1:])))
        # |psi| > 1 means the recolouring pushed a component population
        # past the physical range; recorded because it is a real
        # over-sharpening signature at large beta.
        res["betas_with_psi_above_one"] = [o["beta"] for o in out
                                           if o["psi_peak"] > 1.0]
        res["verdict"] = "PASS"
    else:
        res["verdict"] = "FAIL"
        res["reason"] = ("no value of beta produced an interface whose bulk "
                         "phases survive (|psi|max > 0.95); the terminal "
                         "states are non-physical fine-scale colour patterns")
    res["acceptance"] = ("at least one beta keeps |psi|max > 0.95 in both "
                         "bulks, i.e. a physical diffuse interface exists; "
                         "the report states that eta (R1 Eq.19 refinement "
                         "law) is NOT determined by this test")
    res["note"] = ("widths are the fitted tanh width of the TERMINAL state; "
                   "see EXECUTION_REPORT.md for the terminal-state "
                   "characterisation at these parameters")
    return res


# ======================================================================
#  test 6 -- dynamic isotropy (capillary wave, two wave directions)
# ======================================================================
def test_06_isotropy(steps=600, n=(32, 16, 16)):
    out = []
    for wave_axis, normal_axis in ((0, 2), (1, 2)):
        s = make(n)
        s.init_psi(G.sine_interface(n[0], n[1], n[2], amp=1.5, k=1,
                                    width=2.0, wave_axis=wave_axis,
                                    normal_axis=normal_axis))
        amps = []
        for t in (0, 100, 200, 400, 600):
            if t:
                s.run(t - s.time)
            psi = s.psi()
            prof = np.moveaxis(psi, normal_axis, -1)
            prof = prof.reshape(-1, prof.shape[-1]).mean(axis=0)
            amps.append(float(np.abs(prof).max()))
        out.append(dict(wave_axis=wave_axis, normal_axis=normal_axis,
                        amplitude_trace=amps, amplitude_final=amps[-1],
                        max_abs_v=max_fluid_velocity(s)))
    res = dict(runs=out, steps=steps, grid=list(n))
    a0, a1 = out[0]["amplitude_final"], out[1]["amplitude_final"]
    res["amplitude_asymmetry"] = float(abs(a0 - a1) / max(a0, a1, 1e-30))
    res["verdict"] = "PASS" if res["amplitude_asymmetry"] < 0.05 else "FAIL"
    res["acceptance"] = ("the terminal interface response agrees for a wave "
                         "vector along x and along y to within 5% relative")
    return res


# ======================================================================
#  test 7 -- static slit capillary pressure
# ======================================================================
def test_07_slit_pc(steps=1500, gaps=(10, 12), n=(12, 12, 32)):
    """Static capillary pressure in a sealed slit.

    The slit is closed at both ends by solid, so there is no "top" and
    "bottom" reservoir: the only meaningful pressure difference is the one
    ACROSS the meniscus, between the wetting fluid on one side and the
    non-wetting fluid on the other.  The meniscus is located from the
    psi = 0 crossing and the two sides are sampled inside the fluid
    region only, three nodes clear of it.
    """
    out = []
    for gap in gaps:
        solid = G.slit(n[0], n[1], n[2], gap=gap, wall=2)
        s = make(n, solid=solid, wetting="none")
        z0 = 2 + gap // 2
        psi = np.full(n, -1.0)
        psi[:, :, :z0] = 1.0
        s.init_psi(psi)
        s.run(steps)
        rho, _ = s.macroscopic()
        zz = np.arange(n[2])[None, None, :] * np.ones(n)
        col = s.psi()[n[0] // 2, n[1] // 2, :]
        fluid_col = ~solid[n[0] // 2, n[1] // 2, :]
        zi = int(np.argmin(np.where(fluid_col, np.abs(col), np.inf)))
        wet_solid = solid[n[0] // 2, n[1] // 2, :]
        # sampling windows must fit inside the slit AND clear the
        # interface by more than its own width; a too-thin slit yields
        # empty windows, which is a measurement defect and is reported as
        # INCONCLUSIVE rather than as a physics failure.
        lo = fluid_col & (zz[0, 0] < zi - 3) & (zz[0, 0] >= 2)
        hi = fluid_col & (zz[0, 0] > zi + 3) & (zz[0, 0] < 2 + gap)
        bot = np.broadcast_to(lo, n) if lo.any() else None
        top = np.broadcast_to(hi, n) if hi.any() else None
        rb = float(rho[bot].mean()) if bot is not None else None
        rt = float(rho[top].mean()) if top is not None else None
        dp = (rt - rb) / 3.0 if (rt is not None and rb is not None) else None
        out.append(dict(gap=gap, meniscus_z=zi,
                        rho_wetting_side=rb, rho_nonwetting_side=rt, dp=dp,
                        pc_analytic=2.0 * SIGMA / gap,
                        pc_ratio=(dp / (2.0 * SIGMA / gap))
                        if dp is not None else None,
                        psi_peak=float(np.abs(s.psi()).max()),
                        max_abs_v=max_fluid_velocity(s)))
    res = dict(runs=out, steps=steps, grid=list(n))
    measurable = all(o["dp"] is not None for o in out)
    ok = measurable and all(o["psi_peak"] > 0.9 and o["dp"] > 0 for o in out)
    if not measurable:
        res["verdict"] = "INCONCLUSIVE"
        res["reason"] = ("the sampling windows inside the slit are empty, so "
                         "the pressure difference was not measured at all; "
                         "this is a measurement defect, not a physics result")
    else:
        res["verdict"] = "PASS" if ok else "FAIL"
    res["acceptance"] = ("each slit keeps |psi|peak > 0.9 AND a positive "
                         "pressure difference across the meniscus is "
                         "measured; the ratio to 2 sigma cos(theta)/gap is "
                         "reported but not gated, because the contact angle "
                         "here is the model's own (wetting='none') rather "
                         "than a prescribed one")
    return res


# ======================================================================
#  test 8 -- simple capillary imbibition
# ======================================================================
def test_08_imbibition(steps=1500, n=(10, 10, 40), gap=8):
    solid = np.ones(n, dtype=bool)
    solid[1:-1, 1:-1, :] = False
    s = make(n, solid=solid, wetting="none")
    psi = np.full(n, -1.0)
    psi[:, :, :6] = 1.0
    psi[solid] = 0.0
    s.init_psi(psi)
    front = []
    for t in range(0, steps + 1, max(1, steps // 8)):
        if t:
            s.run(t - s.time)
        p = s.psi()
        col = p[n[0] // 2, n[1] // 2, :]
        wet = np.where(col > 0.0)[0]
        front.append(dict(t=s.time, z=float(wet.max()) if wet.size else 0.0))
    res = dict(front=front, steps=steps, grid=list(n), gap=gap)
    z0, z1 = front[0]["z"], front[-1]["z"]
    res["front_advance"] = float(z1 - z0)
    res["verdict"] = "PASS" if res["front_advance"] > 2.0 else "FAIL"
    res["acceptance"] = ("the wetting front advances by more than 2 lu with "
                         "no imposed pressure difference")
    return res


# ======================================================================
#  test 9 -- asymmetric complex-wall killer test
# ======================================================================
def test_09_killer(steps=1500, n=(28, 16, 16), band=3):
    solid = G.asymmetric_ledge(n[0], n[1], n[2])
    s = make(n, solid=solid)
    psi = np.full(n, -1.0)
    psi[:, :, :n[2] // 2] = 1.0
    psi[solid] = 0.0
    s.init_psi(psi)
    wb = G.wall_band(n, solid, thickness=band)
    m0 = masses(s)
    wall_r0 = float(s.rho_r[wb].sum())
    ncomp0, _ = G.labelled_components(np.where(solid, -1.0, s.psi()), 0.5)
    trace = []
    for t in range(0, steps + 1, max(1, steps // 8)):
        if t:
            s.run(t - s.time)
        rho_r_now = s.rho_r
        trace.append(dict(
            t=s.time,
            wall_band_red=float(rho_r_now[wb].sum()),
            red_total=float(s.rho_r.sum()),
            blue_total=float(s.rho_b.sum()),
            max_abs_v=max_fluid_velocity(s),
        ))
    m1 = masses(s)
    ncomp1, sizes1 = G.labelled_components(np.where(solid, -1.0, s.psi()), 0.5)
    res = dict(
        steps=steps, grid=list(n), band=band,
        wall_band_red_initial=wall_r0,
        wall_band_red_final=trace[-1]["wall_band_red"],
        wall_band_red_change=trace[-1]["wall_band_red"] - wall_r0,
        wall_band_red_relative=(trace[-1]["wall_band_red"] - wall_r0)
        / max(wall_r0, 1e-30),
        red_drift=abs(m1[0] - m0[0]),
        blue_drift=abs(m1[1] - m0[1]),
        n_components_initial=ncomp0, n_components_final=ncomp1,
        component_sizes_final=sizes1[:5],
        max_abs_v=trace[-1]["max_abs_v"],
        trace=trace,
    )
    res["verdict"] = "PASS" if (abs(res["wall_band_red_relative"]) < 0.02
                                and res["n_components_final"] <= 1) else "FAIL"
    res["acceptance"] = ("wall-band red mass changes by < 2% AND the domain "
                         "stays single-component, with no imposed pressure "
                         "difference and a non-cancelling geometry")
    res["note"] = ("R2 warns that periodic closure can hide wall-directed "
                   "mass transfer; the ledge geometry is one-sided, closed "
                   "on all four lateral faces, and driven by no pressure "
                   "difference, so a wall-directed transfer cannot cancel")
    return res


# ======================================================================
#  test 10 -- conservation audit
# ======================================================================
def test_10_conservation(steps=1000, n=(8, 8, 24)):
    """Total and component mass drift, L17_CORE vs the overlay arm."""
    out = []
    for overlay in (None, "f64_arithmetic"):
        s = make(n, conservation_overlay=overlay)
        s.init_psi(G.planar_interface(n[0], n[1], n[2], width=2.0))
        m0 = masses(s)
        t0 = (s.rho_r + s.rho_b).sum()
        trace = []
        for t in range(0, steps + 1, max(1, steps // 10)):
            if t:
                s.run(t - s.time)
            mr, mb = masses(s)
            trace.append(dict(t=s.time, red=float(mr), blue=float(mb),
                              total=float(mr + mb)))
        mr1, mb1 = masses(s)
        out.append(dict(
            overlay=overlay, steps=steps, grid=list(n),
            red_drift=abs(mr1 - m0[0]), blue_drift=abs(mb1 - m0[1]),
            total_drift=abs((mr1 + mb1) - t0),
            red_drift_per_step=abs(mr1 - m0[0]) / steps,
            blue_drift_per_step=abs(mb1 - m0[1]) / steps,
            total_drift_per_step=abs((mr1 + mb1) - t0) / steps,
            red_mass=m0[0], trace=trace,
        ))
    res = dict(runs=out)
    core = out[0]
    res["verdict"] = "PASS" if core["total_drift_per_step"] < 1e-12 \
                             and core["red_drift_per_step"] < 1e-9 \
                             and core["blue_drift_per_step"] < 1e-9 else "FAIL"
    res["acceptance"] = ("L17_CORE (no overlay) total-mass drift < 1e-12 and "
                         "component drift < 1e-9 per step; the overlay arm is "
                         "reported separately and is NOT described as "
                         "paper-faithful")
    return res


TESTS = [
    ("01_uniform_single_phase", test_01_uniform),
    ("02_planar_interface", test_02_planar),
    ("03_laplace_droplet", test_03_laplace),
    ("04_static_contact_angle", test_04_contact_angle),
    ("05_interface_width_vs_beta", test_05_width_vs_beta),
    ("06_dynamic_isotropy", test_06_isotropy),
    ("07_static_slit_capillary_pressure", test_07_slit_pc),
    ("08_simple_imbibition", test_08_imbibition),
    ("09_asymmetric_killer", test_09_killer),
    ("10_conservation_audit", test_10_conservation),
]


def run_all(quick=False):
    os.makedirs(RESULTS, exist_ok=True)
    summary = dict(
        task="BI-CG-LECLAIRE-IMPLEMENTATION-001",
        candidate="L17_CORE",
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        host=platform.node(), python=sys.version.split()[0],
        numpy=np.__version__,
        parameters=dict(nu=NU, sigma=SIGMA, beta=BETA, chi=1.0),
        tests={},
    )
    overall = 0
    for name, fn in TESTS:
        t0 = time.time()
        try:
            res = fn() if not quick else _quick(fn)
            code = 0
        except Exception as exc:                    # noqa: BLE001
            res = dict(verdict="NOT_RUN", error=f"{type(exc).__name__}: {exc}")
            code = 1
        res["wall_seconds"] = time.time() - t0
        res["exit_code"] = code
        summary["tests"][name] = res
        with open(os.path.join(RESULTS, f"{name}.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(res, fh, indent=2)
        print(f"[{res['verdict']:>12s}] {name}  "
              f"({res['wall_seconds']:.1f} s, exit {code})", flush=True)
        if code:
            overall = 1
    with open(os.path.join(RESULTS, "summary.json"), "w",
              encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    return overall


def _quick(fn):
    return fn(steps=30)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    sys.exit(run_all(quick=args.quick))
