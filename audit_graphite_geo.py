"""X0 (PLAN_3d_graphite_exploratory_v1): audit BIL graphite_scan119 products,
pick best 200^3 native-res subcrop, write driver-ready npz.

Run from 2phase/:  python audit_graphite_geo.py
Outputs: geo_graphite_200.npz, results_pcs_cg3d/graphite_geo_audit.json
Bounded stdout (~20 lines). No GPU.
"""
import json
import os

import numpy as np
from scipy import ndimage

BASE = '../../../data/electrode_BIL/processed/graphite_scan119'
OUT_NPZ = 'geo_graphite_200.npz'
OUT_JSON = 'results_pcs_cg3d/graphite_geo_audit.json'
S18 = ndimage.generate_binary_structure(3, 2)  # 18-conn ~ D3Q19 streaming


def perc_frac(pore):
    """Fraction of pore voxels in clusters spanning axis-0 (in-box x-flow)."""
    lab, n = ndimage.label(pore, structure=S18)
    if n == 0:
        return 0.0, 0
    sl = np.index_exp[0, :, :], np.index_exp[-1, :, :]
    touch = np.unique(np.concatenate([lab[sl[0]], lab[sl[1]]]))
    touch = touch[touch > 0]
    if len(touch) == 0:
        return 0.0, n
    mask = np.isin(lab, touch)
    return float(mask.sum() / pore.sum()), n


def edt_stats(pore):
    d = ndimage.distance_transform_edt(pore)
    r = d[pore]
    return dict(p50=float(np.percentile(r, 50)), p95=float(np.percentile(r, 95)),
                max=float(r.max()))


def main():
    os.makedirs('results_pcs_cg3d', exist_ok=True)
    out = {}

    # -- three existing products ------------------------------------------
    cube = np.load(f'{BASE}/cube_native.npy')
    out['native'] = dict(shape=list(cube.shape), phi=float((cube == 0).mean()))
    for name in ('lbm_half', 'lbm_quarter'):
        z = np.load(f'{BASE}/{name}.npz')
        key = 'solid' if 'solid' in z.files else z.files[0]
        a = z[key]
        pore = a == 0
        pf, nc = perc_frac(pore)
        out[name] = dict(shape=list(a.shape), key=key, phi=float(pore.mean()),
                         perc_frac=pf, n_clusters=nc)
        print(f"{name}: shape={a.shape} key={key} phi={pore.mean():.3f} "
              f"perc={pf:.3f} clusters={nc}")

    pore_full = cube == 0
    pf_full, nc_full = perc_frac(pore_full)
    out['native'].update(perc_frac=pf_full, n_clusters=nc_full)
    print(f"cube_native 336^3: phi={out['native']['phi']:.4f} "
          f"perc_frac={pf_full:.4f} clusters={nc_full}")
    if pf_full < 0.01:
        print('GATE FAIL: full cube does not percolate in x -> stop, report.')
        json.dump(out, open(OUT_JSON, 'w'), indent=1)
        return

    # -- 200^3 window scan (27 windows, in-window x-percolation) ----------
    N = 200
    offs = [0, 68, 136]
    best = None
    for ox in offs:
        for oy in offs:
            for oz in offs:
                w = cube[ox:ox + N, oy:oy + N, oz:oz + N]
                pw = w == 0
                pf, nc = perc_frac(pw)
                phi = float(pw.mean())
                cand = dict(offset=(ox, oy, oz), perc_frac=pf, phi=phi, n_clu=nc)
                if best is None or pf > best['perc_frac']:
                    best = cand
    out['window_scan_best'] = best
    print(f"best 200^3 window: offset={best['offset']} perc_frac="
          f"{best['perc_frac']:.4f} phi={best['phi']:.4f} clusters={best['n_clu']}")
    if best['perc_frac'] < 0.05:
        print('WARN: best window barely percolates; ladder may stall (X1 will show).')

    ox, oy, oz = best['offset']
    solid = cube[ox:ox + N, oy:oy + N, oz:oz + N].astype(np.int8)
    es = edt_stats(solid == 0)
    out['window_edt_vox'] = es
    print(f"window pore-EDT vox: p50={es['p50']:.2f} p95={es['p95']:.2f} "
          f"max={es['max']:.2f}")
    pc_est = dict(
        entry_pc_min=2 * 0.0606 / es['max'],     # widest throat
        entry_pc_p95=2 * 0.0606 / es['p95'],
        delta_entry_min=3 * 2 * 0.0606 / es['max'],
        delta_entry_p95=3 * 2 * 0.0606 / es['p95'])
    out['entry_estimate'] = {k: round(v, 4) for k, v in pc_est.items()}
    print(f"entry estimate (sigma=0.0606): Pc {pc_est['entry_pc_min']:.4f}"
          f"..{pc_est['entry_pc_p95']:.4f} -> delta "
          f"{pc_est['delta_entry_min']:.4f}..{pc_est['delta_entry_p95']:.4f}")

    meta = [f"graphite_scan119 200^3 native-res subcrop",
            f"origin_xyz={(ox, oy, oz)} from 336^3 cube",
            f"phi={best['phi']:.4f} perc_frac={best['perc_frac']:.4f}",
            f"voxel=0.128um Otsu(upper-bound porosity) source=BIL CC-BY-4.0",
            f"axis0=flow(x); driver overwrites x-edge 3 layers as wall"]
    np.savez(OUT_NPZ, solid=solid, meta=np.array(meta))
    out['npz'] = OUT_NPZ
    json.dump(out, open(OUT_JSON, 'w'), indent=1)
    print(f"saved {OUT_NPZ} and {OUT_JSON}")


if __name__ == '__main__':
    main()
