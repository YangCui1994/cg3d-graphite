"""Unit tests for PR-3 post-processing (Plan_20260919_v2 tasks 2.4-2.7):
label_periodic (connectivity + periodic merge) and eval_convergence.
Pure numpy — no solver import, runs in seconds.

Run:  python tests/test_postprocessing.py   (exit 0 = pass)
"""
import os
import sys

import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_common import label_periodic, eval_convergence  # noqa: E402

FAIL = []


def check(name, cond):
    print(('PASS ' if cond else 'FAIL ') + name)
    if not cond:
        FAIL.append(name)


def test_connectivity():
    m = np.zeros((5, 5, 5), bool)
    m[2, 2, 2] = True
    m[2, 3, 3] = True           # edge-diagonal ONLY (no face intermediates)
    _, s6 = label_periodic(m, conn=6)
    _, s18 = label_periodic(m, conn=18)
    _, s26 = label_periodic(m, conn=26)
    check('conn6 splits edge-diagonal (2 singletons)', len(s6) == 2)
    check('conn18 merges edge-diagonal (1 cluster, size 2)',
          len(s18) == 1 and s18[0] == 2)


def test_periodic_y():
    m = np.zeros((4, 6, 6), bool)
    m[2, 0, 3] = True
    m[2, 5, 3] = True           # same y-thread across the periodic seam
    lab, sp = label_periodic(m, conn=6, periodic_axes=(1, 2))
    lab_np, n_np = ndimage.label(m)
    check('periodic y merges the seam pair', len(sp) == 1 and sp[0] == 2)
    check('non-periodic baseline splits it', n_np == 2)


def test_periodic_zy():
    m = np.zeros((4, 6, 6), bool)
    m[1, 0, 0] = True
    m[1, 5, 0] = True
    m[2, 5, 0] = True           # connects in x to the next
    m[2, 5, 5] = True           # wraps z as well
    m[2, 0, 5] = True
    _, sp = label_periodic(m, conn=6, periodic_axes=(1, 2))
    # all five cells form one ring through y and z seams
    check('periodic y+z ring is one cluster', len(sp) == 1 and sp[0] == 5)


def test_sizes_count_interior_only():
    m = np.zeros((3, 4, 4), bool)
    m[:, 1, 1] = True           # a 3-cell bar in x
    _, sp = label_periodic(m, conn=6, periodic_axes=(1, 2))
    check('size counts interior cells once', len(sp) == 1 and sp[0] == 3)


def _n_sizes(mask, conn, axes):
    _, sizes = label_periodic(mask, conn=conn, periodic_axes=axes)
    return len(sizes), [int(v) for v in sizes]


def test_periodic_wrapped_neighbours():
    """Torus topology (CG3D-PERIODIC-CONN-002): a neighbour relation that has
    to wrap TWO periodic seams at once (edge) or all THREE (corner) is a
    neighbour of that connectivity level — and a relation that would need a
    non-periodic axis must never merge.  Full matrix lives in
    tests/test_periodic_connectivity.py."""
    # y+z wrapped edge: (2,0,0) vs (2,5,5) differs by (0,-1,-1) through the
    # y and the z seam at the same time.
    m = np.zeros((4, 6, 6), bool)
    m[2, 0, 0] = True
    m[2, 5, 5] = True
    n6, s6 = _n_sizes(m, 6, (1, 2))
    n18, s18 = _n_sizes(m, 18, (1, 2))
    check('y+z wrapped edge split for conn=6', n6 == 2 and s6 == [1, 1])
    check('y+z wrapped edge merges for conn=18', n18 == 1 and s18 == [2])
    # x+y+z wrapped corner: (0,0,0) vs (4,4,4) differs by (-1,-1,-1).
    m = np.zeros((5, 5, 5), bool)
    m[0, 0, 0] = True
    m[4, 4, 4] = True
    n18c, _ = _n_sizes(m, 18, (0, 1, 2))
    n26c, s26c = _n_sizes(m, 26, (0, 1, 2))
    check('x+y+z wrapped corner split for conn=18', n18c == 2)
    check('x+y+z wrapped corner merges for conn=26', n26c == 1 and s26c == [2])
    # No false merge when one of the two axes the pair needs is non-periodic.
    m = np.zeros((6, 6, 4), bool)
    m[0, 0, 1] = True
    m[5, 5, 1] = True           # wrapped displacement (-1,-1,0)
    n_xy, s_xy = _n_sizes(m, 18, (0, 1))
    n_noy, _ = _n_sizes(m, 18, (1, 2))      # x not periodic
    n_nox, _ = _n_sizes(m, 18, (0, 2))      # y not periodic
    check('x+y wrapped edge merges for conn=18', n_xy == 1 and s_xy == [2])
    check('wrapped edge pair stays split with x non-periodic', n_noy == 2)
    check('wrapped edge pair stays split with y non-periodic', n_nox == 2)
    # Sizes stay exact across a wrapped merge (wrapped trio + isolated cell).
    m = np.zeros((4, 6, 6), bool)
    for c in ((2, 0, 0), (2, 5, 5), (2, 5, 4), (0, 2, 2)):
        m[c] = True
    n, s = _n_sizes(m, 18, (1, 2))
    check('sizes exact after wrapped merge', n == 2 and s == [3, 1]
          and sum(s) == int(m.sum()))


def test_eval_convergence():
    pore = 1000.0
    def mk(it0, s, pc, inj, u):
        # inj slope 0.4/500 steps = 8e-7 per pore cell per step < 1e-6 tol
        return [(it0 + 500 * i,
                 dict(s_nw=s, pc_measured=pc, inj_r=inj + 0.4 * i,
                      inj_b=inj, u_rms=u)) for i in range(5)]
    # all four criteria pass: flat everything, flux 0.5/500/1000 = 1e-6/pore
    w = mk(10000, 0.42, 0.03, 0.0, 1e-3)
    c = eval_convergence(w, pore, qs_tol=5e-7)
    check('flat window passes all four',
          c['criteria_passed'] == ['saturation', 'pressure', 'flux',
                                   'kinetic'])
    # saturation drifting
    w = mk(10000, 0.42, 0.03, 0.0, 1e-3)
    w[-1] = (w[-1][0], dict(w[-1][1], s_nw=0.421))
    c = eval_convergence(w, pore, qs_tol=5e-7)
    check('drifting saturation fails saturation only',
          c['criteria_passed'] == ['pressure', 'flux', 'kinetic'])
    # pc drifting 10x the 1% tol
    w = mk(10000, 0.42, 0.03, 0.0, 1e-3)
    w[0] = (w[0][0], dict(w[0][1], pc_measured=0.0335))
    c = eval_convergence(w, pore, qs_tol=5e-7)
    check('pc drift fails pressure only',
          c['criteria_passed'] == ['saturation', 'flux', 'kinetic'])
    # u_rms varying 50%
    w = mk(10000, 0.42, 0.03, 0.0, 1e-3)
    w[0] = (w[0][0], dict(w[0][1], u_rms=2e-3))
    c = eval_convergence(w, pore, qs_tol=5e-7)
    check('u_rms swing fails kinetic only',
          c['criteria_passed'] == ['saturation', 'pressure', 'flux'])
    # thresholds recorded for the report
    check('thresholds recorded', c['thresholds']['saturation_slope'] == 5e-7)
    # short window -> empty record, no crash
    c = eval_convergence([(1, {})], pore, qs_tol=5e-7)
    check('short window tolerated', c['criteria_passed'] == [])


def main():
    test_connectivity()
    test_periodic_y()
    test_periodic_zy()
    test_sizes_count_interior_only()
    test_periodic_wrapped_neighbours()
    test_eval_convergence()
    if FAIL:
        print(f'FAIL: {FAIL}')
        sys.exit(1)
    print('ALL PASS')


if __name__ == '__main__':
    main()
