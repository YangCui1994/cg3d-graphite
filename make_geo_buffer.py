"""Make the buffered graphite geometry (X1' fix): pad k=14 OPEN pore layers
at both x faces of geo_graphite_200.npz so the driver's reservoir slab
[3,11), membrane plane x=11 and 2 lu of clean channel sit entirely in the
padding, decoupled from the rough graphite face (probe evidence: raw geo
NaNs within 200 steps; buffer=4 still NaN because the reservoir overlaps
the real 1-lu throats; buffer=14 stable 4000 steps).

Output: geo_graphite_228b14.npz (solid int8, 228^3).
"""
import numpy as np

SRC = 'geo_graphite_200.npz'
DST = 'geo_graphite_228b14.npz'
K = 14

solid = np.load(SRC)['solid'].astype(np.int8)
pad = np.zeros((solid.shape[0] + 2 * K,) + solid.shape[1:], dtype=np.int8)
pad[K:K + solid.shape[0]] = solid
meta = [
    'graphite_scan119 200^3 subcrop offset(136,136,136) + 14 lu OPEN pore '
    'buffer at both x faces (membrane-decoupling fix, 2026-09-13)',
    f'reservoir[3,11)+mem x=11+clean channel 2 lu all inside padding; '
    f'real graphite occupies x=[{K},{K + solid.shape[0]})',
    'graphite-region phi=0.4475 perc_frac=0.985 (audit_graphite_geo.json); '
    'voxel=0.128um; S_nw from driver includes buffer volume -> recompute '
    'graphite-only in analysis',
]
np.savez(DST, solid=pad, meta=np.array(meta))
z = np.load(DST)
print(f'{DST}: shape={z["solid"].shape} phi_pore={(z["solid"] == 0).mean():.4f} '
      f'graphite_phi={(z["solid"][K:K + 200] == 0).mean():.4f}')
