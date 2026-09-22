"""Periodic connected-component labelling — topology tests.

Task CG3D-PERIODIC-CONN-002.  ``cg3d.diagnostics.label_periodic`` must
reproduce the 3D 6/18/26 neighbour topology on a domain that is periodic along
an arbitrary subset of axes.  In particular a neighbour relation may cross
TWO periodic seams at once (wrapped edge) or all THREE (wrapped corner), and
a relation that would need to wrap a NON-periodic axis must never merge.

The last test compares ``label_periodic`` against an independent brute-force
torus oracle over a matrix of masks x connectivity x periodic-axis subset;
the oracle shares no code with the implementation.

Host-side only: numpy + scipy.ndimage, no solver/Taichi import.

Run:  python tests/test_periodic_connectivity.py   (exit 0 = pass)
"""
import os
import sys

import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run_common import label_periodic  # noqa: E402

FAIL = []

# number of non-zero offset components a connectivity level allows:
# 6 = faces only, 18 = faces + edges, 26 = faces + edges + corners.
_CONN_LEVEL = {6: 1, 18: 2, 26: 3}

_AXIS_SUBSETS = [tuple(i for i in range(3) if k >> i & 1) for k in range(1, 8)]


def check(name, cond):
    print(('PASS ' if cond else 'FAIL ') + name)
    if not cond:
        FAIL.append(name)


def cubes(shape, *cells):
    m = np.zeros(shape, bool)
    for c in cells:
        m[c] = True
    return m


def n_sizes(mask, conn, axes):
    """(number of components, sizes sorted descending) from label_periodic."""
    _, sizes = label_periodic(mask, conn=conn, periodic_axes=axes)
    return len(sizes), [int(v) for v in sizes]


def canonical(labels):
    """Label-number independent partition: every component is renumbered by
    its smallest flat index (-1 outside the mask), so two label arrays are
    equal iff they describe the same partition."""
    flat = np.asarray(labels).ravel()
    out = np.full(flat.size, -1, np.int64)
    for v in np.unique(flat):
        if v:
            idx = np.flatnonzero(flat == v)
            out[idx] = idx[0]
    return out


def reference(mask, conn, periodic_axes):
    """Brute-force torus oracle (independent of the implementation).

    Two occupied voxels are neighbours iff their displacement, with each
    periodic axis reduced to its minimum image and non-periodic axes left as
    they are, has |d| <= 1 on every axis, is not zero, and has at most
    ``_CONN_LEVEL[conn]`` non-zero components.  O(k^2) over occupied voxels,
    so only used on tiny grids.
    """
    m = np.asarray(mask, bool)
    dims = m.shape
    per = set(int(a) for a in periodic_axes)
    cells = np.argwhere(m)
    k = len(cells)
    parent = list(range(k))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i in range(k):
        for j in range(i + 1, k):
            d = cells[j] - cells[i]
            nz = 0
            for a in range(3):
                v = int(d[a])
                if a in per:
                    dd = int(dims[a])
                    v = ((v + dd // 2) % dd) - dd // 2
                if v > 1 or v < -1:
                    nz = -1
                    break
                if v:
                    nz += 1
            if 0 < nz <= _CONN_LEVEL[conn]:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[max(ri, rj)] = min(ri, rj)

    lab = np.zeros(dims, np.int64)
    roots = [find(i) for i in range(k)]
    uniq = sorted(set(roots))
    for idx, cell in enumerate(cells):
        lab[tuple(cell)] = uniq.index(roots[idx]) + 1
    return lab


def sizes_of(labels):
    counts = np.bincount(np.asarray(labels).ravel())[1:]
    return sorted((int(v) for v in counts), reverse=True)


def test_single_axis_seam():
    # (2,0,3) and (2,5,3): face neighbours across the y seam only.
    m = cubes((4, 6, 6), (2, 0, 3), (2, 5, 3))
    for conn in (6, 18, 26):
        n, s = n_sizes(m, conn, (1, 2))
        check(f'single y seam face pair merges (conn={conn})',
              n == 1 and s == [2])


def test_multi_seam_ring():
    # A 5-cell ring that runs through the y seam, across in x, through the z
    # seam and back, closing through the y seam again.  Every step crosses one
    # seam with no in-plane offset.
    m = cubes((4, 6, 6), (1, 0, 0), (1, 5, 0), (2, 5, 0), (2, 5, 5), (2, 0, 5))
    n, s = n_sizes(m, 6, (1, 2))
    check('y+z ring through two seams is one cluster (conn=6)',
          n == 1 and s == [5])


def test_wrapped_edge_yz():
    # (2,0,0) vs (2,5,5): wrapped displacement (0,-1,-1) -> an edge relation
    # that needs the y AND the z seam simultaneously.
    m = cubes((4, 6, 6), (2, 0, 0), (2, 5, 5))
    n6, s6 = n_sizes(m, 6, (1, 2))
    n18, s18 = n_sizes(m, 18, (1, 2))
    n26, s26 = n_sizes(m, 26, (1, 2))
    print(f'REPRO y+z wrapped edge   conn=6  axes=(1,2): n={n6} sizes={s6}')
    print(f'REPRO y+z wrapped edge   conn=18 axes=(1,2): n={n18} sizes={s18}')
    print(f'REPRO y+z wrapped edge   conn=26 axes=(1,2): n={n26} sizes={s26}')
    check('y+z wrapped edge stays split for conn=6', n6 == 2 and s6 == [1, 1])
    check('y+z wrapped edge merges for conn=18', n18 == 1 and s18 == [2])
    check('y+z wrapped edge merges for conn=26', n26 == 1 and s26 == [2])


def test_wrapped_edge_xy():
    # (0,0,1) vs (5,5,1): wrapped displacement (-1,-1,0), an edge needing the
    # x AND the y seam at once.
    m = cubes((6, 6, 4), (0, 0, 1), (5, 5, 1))
    n6, s6 = n_sizes(m, 6, (0, 1))
    n18, s18 = n_sizes(m, 18, (0, 1))
    check('x+y wrapped edge merges for conn=18 (both axes periodic)',
          n18 == 1 and s18 == [2])
    check('x+y wrapped edge stays split for conn=6', n6 == 2 and s6 == [1, 1])
    # Negative controls: the same geometric pair must stay split whenever one
    # of the two axes it needs is not periodic (no wrapping allowed there).
    for axes in ((0, 2), (1, 2), (0,), (1,), ()):
        for conn in (18, 26):
            n, _ = n_sizes(m, conn, axes)
            check(f'x+y wrapped edge stays split for conn={conn} axes={axes}',
                  n == 2)


def test_wrapped_corner_xyz():
    # (0,0,0) vs (4,4,4): wrapped displacement (-1,-1,-1), a corner relation
    # needing all three seams at once.
    m = cubes((5, 5, 5), (0, 0, 0), (4, 4, 4))
    n6, s6 = n_sizes(m, 6, (0, 1, 2))
    n18, s18 = n_sizes(m, 18, (0, 1, 2))
    n26, s26 = n_sizes(m, 26, (0, 1, 2))
    print(f'REPRO x+y+z wrapped corner conn=6  axes=(0,1,2): '
          f'n={n6} sizes={s6}')
    print(f'REPRO x+y+z wrapped corner conn=18 axes=(0,1,2): '
          f'n={n18} sizes={s18}')
    print(f'REPRO x+y+z wrapped corner conn=26 axes=(0,1,2): '
          f'n={n26} sizes={s26}')
    check('x+y+z wrapped corner stays split for conn=6',
          n6 == 2 and s6 == [1, 1])
    check('x+y+z wrapped corner stays split for conn=18',
          n18 == 2 and s18 == [1, 1])
    check('x+y+z wrapped corner merges for conn=26', n26 == 1 and s26 == [2])
    # Negative control: with one of the three axes not periodic it must stay
    # split even at conn=26.
    for axes in ((0, 1), (1, 2), (0, 2)):
        n, _ = n_sizes(m, 26, axes)
        check(f'x+y+z wrapped corner stays split for axes={axes}', n == 2)


def test_sizes_exact_after_wrapped_merge():
    # A wrapped edge pair plus one plain face neighbour -> 3-cell component,
    # plus an isolated cell that no wrap may swallow.
    m = cubes((4, 6, 6), (2, 0, 0), (2, 5, 5), (2, 5, 4), (0, 2, 2))
    n, s = n_sizes(m, 18, (1, 2))
    check('sizes exact after wrapped merge (3 + 1)', n == 2 and s == [3, 1])
    check('sizes sum to the occupied voxel count',
          sum(s) == int(np.asarray(m).sum()))


def test_control_separate_clusters_stay_separate():
    # Two 2-cell clusters inside a fully periodic domain, separated by gaps of
    # at least two cells along every wrapped direction: no merge at any conn.
    m = cubes((7, 7, 7), (1, 1, 1), (2, 1, 1), (4, 4, 4), (4, 5, 4))
    for conn in (6, 18, 26):
        n, s = n_sizes(m, conn, (0, 1, 2))
        check(f'separate clusters stay separate (conn={conn})',
              n == 2 and s == [2, 2])


def test_empty_periodic_axes_matches_scipy():
    rng = np.random.default_rng(7)
    m = rng.random((4, 5, 6)) < 0.35
    for conn, level in _CONN_LEVEL.items():
        lab, _ = label_periodic(m, conn=conn, periodic_axes=())
        struct = ndimage.generate_binary_structure(3, level)
        ref, nref = ndimage.label(m, structure=struct)
        check(f'empty periodic_axes == plain scipy label (conn={conn})',
              nref == len(np.unique(lab)) - 1
              and np.array_equal(canonical(lab), canonical(ref)))


def test_matrix_vs_bruteforce_oracle():
    masks = []
    for seed in (0, 1, 2, 3):
        rng = np.random.default_rng(seed)
        masks.append((f'random 4x5x6 seed={seed} p=0.25',
                      rng.random((4, 5, 6)) < 0.25))
        masks.append((f'random 4x5x6 seed={seed} p=0.45',
                      rng.random((4, 5, 6)) < 0.45))
    masks.append(('random 5x5x5 seed=9 p=0.3',
                  np.random.default_rng(9).random((5, 5, 5)) < 0.3))
    masks.append(('wrapped corner pair on 5^3',
                  cubes((5, 5, 5), (0, 0, 0), (4, 4, 4))))
    masks.append(('wrapped edge pair on 6x6x4',
                  cubes((6, 6, 4), (0, 0, 1), (5, 5, 1))))
    masks.append(('solid 4x4x4', np.ones((4, 4, 4), bool)))

    bad, total = [], 0
    for name, m in masks:
        for axes in _AXIS_SUBSETS:
            for conn in (6, 18, 26):
                total += 1
                got = np.asarray(label_periodic(m, conn=conn,
                                                periodic_axes=axes)[0])
                want = reference(m, conn, axes)
                if not np.array_equal(canonical(got), canonical(want)):
                    bad.append((name, conn, axes,
                                sizes_of(got), sizes_of(want)))
    check(f'brute-force oracle agreement over {total} mask/axis/conn combos',
          not bad)
    if bad:
        print(f'  {len(bad)} of {total} combos mismatch the oracle')
    for row in bad[:5]:
        print(f'  MISMATCH {row[0]} conn={row[1]} axes={row[2]}: '
              f'got sizes {row[3]}, oracle sizes {row[4]}')


def main():
    test_single_axis_seam()
    test_multi_seam_ring()
    test_wrapped_edge_yz()
    test_wrapped_edge_xy()
    test_wrapped_corner_xyz()
    test_sizes_exact_after_wrapped_merge()
    test_control_separate_clusters_stay_separate()
    test_empty_periodic_axes_matches_scipy()
    test_matrix_vs_bruteforce_oracle()
    if FAIL:
        print(f'FAIL: {FAIL}')
        sys.exit(1)
    print('ALL PASS')


if __name__ == '__main__':
    main()
