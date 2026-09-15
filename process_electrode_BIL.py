"""Segment BIL electrode nano-CT volumes and crop LBM-ready subvolumes.

Input : LBM/data/electrode_BIL/<sample>/<name>.tiff   (uint16 absorption CT, ~0.128 um/voxel)
Output: LBM/data/electrode_BIL/processed/<sample>/
          cube_native.npy   uint8 {0=pore, 1=solid}, largest cube fully inside the sample
          lbm_half.npz      block-2x downsampled binary (pore fraction>=0.5 -> pore)
          lbm_quarter.npz   block-4x downsampled binary
          seg_report.json   porosity / surface density / pore-throat stats
          preview_seg.png   orthogonal slices: raw | segmented

Method (kept deliberately simple):
  air floor  : values <= AIR_TOL above the reconstruction floor are air (outside + pores)
  sample     : largest connected component of ~air, closed; cube grown from centroid
               while every boundary slice stays >= 95% sample
  solid      : 3x3x3 median filter -> Otsu threshold inside the cube
  cleanup    : drop 3D components < MIN_COMP vox on both phases

Run:  python process_electrode_BIL.py            (from 2phase/, uses lbm env)
"""
import json
import os
import sys

import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage.filters import threshold_otsu

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "data", "electrode_BIL"))
PROC_ROOT = os.path.join(DATA_ROOT, "processed")

SAMPLES = {
    "nmc811_scan121": dict(tif="LN210035-167-4-Fresh.tiff", voxel_um=0.128),
    "graphite_scan119": dict(tif="A-A015A-Anode-Fresh.tiff", voxel_um=0.128),
}

AIR_TOL = 1200        # values within AIR_TOL of the global floor count as air
CLOSE_RADIUS = 4      # sealing radius for the sample surface before cube fitting
SLICE_SAMPLE_FRAC = 0.95
CUBE_STEP = 16
MIN_COMP = 30


def find_floor(vol):
    """Reconstruction floor = the sharp low peak shared by background air."""
    lo = vol.min()
    hi = lo + AIR_TOL
    return lo, (vol <= hi)


def largest_cc(mask):
    lab, n = ndi.label(mask)
    if n == 0:
        return mask
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    return lab == sizes.argmax()


def fit_cube(sample):
    """Largest axis-aligned cube (side multiple of 4) whose 6 boundary slices
    are each >= SLICE_SAMPLE_FRAC sample. Grows from the sample centroid."""
    z, y, x = [s // 2 for s in sample.shape]
    cz, cy, cx = [int(round(c)) for c in ndi.center_of_mass(sample)]
    side = CUBE_STEP
    Z, Y, X = sample.shape
    while True:
        nxt = side + CUBE_STEP
        half = nxt // 2
        z0, z1 = cz - half, cz + half
        y0, y1 = cy - half, cy + half
        x0, x1 = cx - half, cx + half
        if z0 < 0 or y0 < 0 or x0 < 0 or z1 > Z or y1 > Y or x1 > X:
            break
        cube = sample[z0:z1, y0:y1, x0:x1]
        frac = min(
            cube[0].mean(), cube[-1].mean(),
            cube[:, 0].mean(), cube[:, -1].mean(),
            cube[:, :, 0].mean(), cube[:, :, -1].mean(),
        )
        if frac < SLICE_SAMPLE_FRAC:
            break
        side = nxt
    half = side // 2
    z0, y0, x0 = cz - half, cy - half, cx - half
    return (z0, y0, x0, side)


def downsample_binary(binvol, factor):
    """Block-mean pore fraction, re-thresholded at 0.5."""
    z, y, x = binvol.shape
    z2, y2, x2 = z // factor * factor, y // factor * factor, x // factor * factor
    a = binvol[:z2, :y2, :x2].reshape(z2 // factor, factor, y2 // factor, factor, x2 // factor, factor)
    frac_pore = 1.0 - a.mean(axis=(1, 3, 5))  # mean of solid indicator
    return frac_pore < 0.5  # pore = True


def pore_stats(pore, voxel_um):
    """Porosity, solid surface density, pore-throat proxy from distance transform."""
    porosity = pore.mean()
    surf = ndi.binary_erosion(~pore).astype(np.int8)
    solid_surface = (~pore.astype(bool) & (surf == 0)).sum()  # solid voxels touching pore
    # distance (in voxels) from each pore voxel to nearest solid
    dist = ndi.distance_transform_edt(pore)
    d = dist[pore]
    throat = float(np.percentile(d, 95))  # ~radius of pore bodies; throats near the low tail of maxima
    return dict(
        porosity=round(float(porosity), 4),
        surface_density_um2_per_um3=round(float(solid_surface.sum() / pore.size * voxel_um ** -1), 6),
        pore_dist_max_vox=round(float(d.max()), 1),
        pore_dist_p50_vox=round(float(np.percentile(d, 50)), 2),
        pore_dist_p95_vox=round(throat, 2),
        pore_dist_p95_um=round(throat * voxel_um, 3),
    )


def process(name, meta):
    tif = os.path.join(DATA_ROOT, name, meta["tif"])
    outdir = os.path.join(PROC_ROOT, name)
    os.makedirs(outdir, exist_ok=True)
    print(f"[{name}] reading {tif}")
    vol = tifffile.imread(tif)

    lo, air = find_floor(vol)
    print(f"  floor={lo}, air fraction={air.mean():.3f}")
    sample = largest_cc(~air)
    sample = ndi.binary_closing(sample, structure=np.ones((3, 3, 3)), iterations=CLOSE_RADIUS)
    sample = largest_cc(sample)
    print(f"  sample bbox={np.where(sample.any(axis=(1, 2)))[0][[0, -1]]} ...")

    z0, y0, x0, side = fit_cube(sample)
    print(f"  cube side={side} at origin=({z0},{y0},{x0})")
    cube_raw = vol[z0:z0 + side, y0:y0 + side, x0:x0 + side].astype(np.uint16)

    med = ndi.median_filter(cube_raw, size=3)
    thr = threshold_otsu(med)
    solid = med > thr
    print(f"  otsu thr={thr:.0f}, raw porosity={(~solid).mean():.3f}")

    # drop tiny components on both phases: first tiny pores -> solid, then tiny solids -> pore
    def shrink_small(mask):
        lab, n = ndi.label(mask)
        if n >= 2:
            sizes = np.bincount(lab.ravel())
            sizes[0] = 0
            lut = sizes >= MIN_COMP
            mask &= lut[lab]

    pore = ~solid.copy()
    shrink_small(pore)        # tiny pore components become solid
    solid = ~pore
    shrink_small(solid)       # tiny solid specks become pore
    pore = ~solid
    print(f"  cleaned porosity={pore.mean():.3f}")

    stats = pore_stats(pore, meta["voxel_um"])
    stats.update(sample=name, cube_side_vox=side, voxel_um=meta["voxel_um"],
                 otsu_threshold=int(thr), cube_origin_zyx=[z0, y0, x0],
                 native_pore_frac=float(pore.mean()))
    print(f"  stats: {stats}")

    np.save(os.path.join(outdir, "cube_native.npy"), solid.astype(np.uint8))
    for factor, tag in ((2, "half"), (4, "quarter")):
        d = downsample_binary(pore, factor)  # True = pore
        np.savez_compressed(os.path.join(outdir, f"lbm_{tag}.npz"),
                            solid=(~d).astype(np.uint8),
                            voxel_um=np.float64(meta["voxel_um"] * factor))
        print(f"  saved lbm_{tag}.npz shape={d.shape}")

    # preview: raw vs segmented, mid slices
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 3, figsize=(13, 8.5))
    m = side // 2
    views = [(cube_raw[m], solid[m], f"XY z={m}"), (cube_raw[:, m], solid[:, m], f"XZ y={m}"), (cube_raw[:, :, m], solid[:, :, m], f"YZ x={m}")]
    for col, (raw, seg, ttl) in enumerate(views):
        axes[0, col].imshow(raw, cmap="gray"); axes[0, col].set_title(f"raw {ttl}")
        axes[1, col].imshow(seg, cmap="gray_r"); axes[1, col].set_title(f"solid=white {ttl}")
    for ax in axes.flat:
        ax.axis("off")
    fig.suptitle(f"{name}  porosity={stats['porosity']:.3f}  voxel={meta['voxel_um']} um")
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "preview_seg.png"), dpi=90)
    plt.close(fig)

    with open(os.path.join(outdir, "seg_report.json"), "w") as f:
        json.dump(stats, f, indent=1)
    print(f"  -> {outdir}")


if __name__ == "__main__":
    for name, meta in SAMPLES.items():
        process(name, meta)
