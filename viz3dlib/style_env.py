"""viz3dlib.style_env — Styles, views, window/DPI constants, env check, small shared helpers."""
from __future__ import annotations

import sys


# x[0:WALL_T) and x[nx-WALL_T:) are solid walls in the run_pcs_cg3d layout:
#   wall | inlet reservoir | mem_b | pore domain | mem_r | outlet reservoir | wall
WALL_T = 3


STYLE = {
    'report': dict(
        bg='white',
        solid='#b0b0b0',            # opaque, geometry panel
        ghost=('#8a8a8f', 0.16),    # translucent context
        wet='#2166ac',
        # amber, NOT the 2D series' dark red: blue-vs-darkred is only
        # dL=0.067 in grayscale (blue-vs-#d62728 is 0.008), i.e. liquid and
        # gas become the same grey in a B/W print.  Amber keeps the warm
        # family and gives dL=0.224; see VIZ_3D_STYLE.md.
        nw='#e08214',
        overflow=('#7f7f7f', 0.9),   # darker than the ghost so it still reads
        text='#1a1a1a',
        box='#8a8a8f',
        # Matte: a broad specular highlight washes the shading gradient out
        # and the gradient is what carries the 3D form.  Keep it tight and
        # weak.
        specular=0.08, specular_power=30,
        # alpha for the majority fluid in the two-phase panel ("glass")
        glass=0.30,
        psi_cmap=['#2166ac', '#f2f2f2', '#e08214'],
        # Chromatic only (no grays — those are reserved for solid/ghost) and
        # greens/magentas first: the phase colours (blue wet, amber non-wet)
        # are reserved, so a 4-cluster figure must not lead with a blue or
        # amber blob that reads as "liquid"/"gas".
        clusters=['#009E73', '#CC79A7', '#8C564B', '#8172B2', '#B79F00',
                  '#55A868', '#4C72B0', '#D55E00', '#56B4E9', '#E69F00',
                  '#0072B2', '#DD8452'],
    ),
    'slide': dict(
        bg='#1b1b1b',
        solid='#8a8a8f',
        ghost=('#8a8a8f', 0.20),    # dark grounds swallow low alpha
        wet='#2f7fd0',
        nw='#f5f5f5',               # white gas — only readable on a dark ground
        overflow=('#9a9a9a', 0.9),
        text='#f0f0f0',
        box='#6e6e73',
        specular=0.08, specular_power=30,
        glass=0.30,
        psi_cmap=['#2f7fd0', '#2b2b2b', '#f5f5f5'],        clusters=['#009E73', '#CC79A7', '#E69F00', '#A0E7A0', '#E8A0C8',
                  '#F0E442', '#D55E00', '#8CD0E3', '#F5C6A5', '#FFD86B',
                  '#56B4E9', '#9FD8F5'],
    ),
}


# Camera presets.  'iso' keeps the matplotlib elev/azim used by
# vis3d_report.py (up = z, so the z axis fills the frame height).  'front'
# puts up = y so the frame is landscape: the thin axis is vertical, the
# inlet-to-outlet x axis runs left-to-right, and the line of sight is mostly
# along z -- pair it with cut_axis='z', since you must cut along the view
# direction to expose the interior.
CAM_ELEV, CAM_AZIM = 18.0, -55.0


VIEWS = {
    'iso': dict(elev=CAM_ELEV, azim=CAM_AZIM, up=(0, 0, 1)),
    'front': dict(dirv=(0.25, 0.20, 0.95), up=(0, 1, 0)),
    # looking down onto a horizontal cut plane (pair with cut_axis='z',
    # cut_keep='lo' so the exposed face points up at the camera)
    'top': dict(elev=58.0, azim=-55.0, up=(0, 0, 1)),
}


WINDOW = (1800, 1500)


DPI_SCALE = 2          # screenshot(scale=2) -> ~300 dpi at 6 in print width


# inset (in psi units) applied to both fluid surfaces in the two-phase panel.
# 0 = the two bodies share the psi=0 boundary exactly (VTK resolves the
# coincident topology); raise it if that shared interface ever speckles.
LEVEL_GAP = 0.0


def check_env():
    """Fail with the fix, not a bare ModuleNotFoundError.

    On this machine a bare `python` is the *base* conda env, while pyvista
    lives in the `lbm` env, so the first symptom is an unhelpful
    "No module named 'pyvista'" from deep inside a render call.
    """
    try:
        __import__('numpy')
        __import__('pyvista')
    except ImportError as exc:
        raise SystemExit(
            f'viz3d: cannot import {exc.name} with interpreter\n'
            f'  {sys.executable}\n'
            'viz3d needs pyvista/vtk, which are installed in the conda env '
            '`lbm`, not in the base env a bare `python` resolves to.  Use '
            'either:\n'
            '  conda activate lbm   &&  python viz3d.py <args>\n'
            '  viz3d.cmd <args>                       (launcher, this dir)\n'
            '  "C:/Users/yangc/anaconda3/envs/lbm/python.exe" viz3d.py <args>'
        ) from None
    for mod, why in (('scipy', 'clusters/explore'),
                     ('matplotlib', 'slices'),
                     ('PIL', 'qa_stats/gif')):
        try:
            __import__(mod)
        except ImportError:
            print(f'  note: {mod} is missing — {why} will not work '
                  f'(pip install {mod})', file=sys.stderr)


def _style(name):
    if name not in STYLE:
        raise SystemExit(f'unknown style {name!r}; pick from {list(STYLE)}')
    return STYLE[name]


# ----------------------------------------------------------------- helpers
def _warn(what, exc):
    """Cosmetic failures must be visible, never silently swallowed."""
    print(f'  ! {what}: {type(exc).__name__}: {exc}')
