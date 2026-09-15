"""viz3dlib.anim — Frame series I/O, GIF assembly, montage grid, animate driver."""
from __future__ import annotations

import os
import numpy as np

from .panels import panel_cutaway
from .plotting import _crop3, surface
from .style_env import _style, _warn


def montage(pngs, out_png, cols=3):
    from PIL import Image

    ims = [Image.open(p).convert('RGB') for p in pngs if os.path.exists(p)]
    if not ims:
        return None
    w = max(i.width for i in ims)
    h = max(i.height for i in ims)
    rows = int(np.ceil(len(ims) / cols))
    sheet = Image.new('RGB', (w * cols, h * rows), 'white')
    for k, im in enumerate(ims):
        sheet.paste(im, ((k % cols) * w, (k // cols) * h))
    sheet.thumbnail((2400, 2400))
    sheet.save(out_png)
    print(f'  -> {out_png} (QA sheet)')
    return out_png


# ------------------------------------------------------------- animation
def _series_files(spec, skip=('f_solid',)):
    """Frame list from a directory, a glob, or a single file."""
    if os.path.isdir(spec):
        fs = sorted(os.path.join(spec, f) for f in os.listdir(spec)
                    if f.endswith('.npz')
                    and not any(f.startswith(s) for s in skip))
    elif any(ch in spec for ch in '*?['):
        import glob as _glob
        fs = sorted(_glob.glob(spec))
    else:
        fs = [spec]
    if not fs:
        raise SystemExit(f'no frames matched {spec!r}')
    return fs


def _load_frame(path):
    """(psi, solid|None, meta) from a dump frame.

    Accepts the CG naming (`psi`, or the int8 `psi_q` written by the
    runner's --dump-every, quantised at 0.01 = 1/220 of the phase range) and
    the Shan-Chen naming (`phase` = rho1-rho2, or rho1/rho2 themselves), so
    one animation path serves both solver families.
    """
    z = np.load(path)
    src = None
    for key, fn in (('psi', lambda a: a.astype(np.float32)),
                    ('psi_q', lambda a: a.astype(np.float32) / 100.0),
                    ('phase', lambda a: a.astype(np.float32)),
                    ('rho1', None)):
        if key == 'rho1':
            if 'rho1' in z.files and 'rho2' in z.files:
                psi = (z['rho1'].astype(np.float32)
                       - z['rho2'].astype(np.float32))
                src = 'rho1-rho2'
                break
            continue
        if key in z.files:
            psi = fn(z[key])
            src = key
            break
    else:
        raise SystemExit(f'{path} has no psi / psi_q / phase / rho1-rho2')
    solid = z['solid'].astype(np.int8) if 'solid' in z.files else None
    meta = {}
    for k in z.files:
        if k in ('psi', 'psi_q', 'phase', 'rho1', 'rho2', 'solid'):
            continue
        try:
            meta[k] = float(z[k])
        except Exception:                                    # noqa: BLE001
            pass
    return psi, solid, meta, src


def _frame_label(tag, meta, fmt=None):
    if fmt:
        try:
            return fmt.format(tag=tag, **meta)
        except Exception as exc:                              # noqa: BLE001
            _warn('label format', exc)
    parts = [tag]
    if 'it' in meta or 'step' in meta:
        parts.append(f'step {int(meta.get("it", meta.get("step", 0)))}')
    for key, name in (('Pc', 'Pc'), ('d', 'dP'), ('s_nw', 'S_nw')):
        if key in meta:
            parts.append(f'{name}={meta[key]:.4f}' if key in ('d', 'Pc')
                         else f'{name}={meta[key]:.3f}')
    return '   '.join(parts)


def make_gif(pngs, gif_path, duration=450, colors=256, max_width=None):
    """Assemble PNGs into a looping GIF; per-frame adaptive palette."""
    from PIL import Image

    ims = [Image.open(p).convert('RGB') for p in pngs]
    if max_width and ims[0].width > max_width:
        ims = [im.resize((max_width, max(1, round(im.height * max_width
                                                  / im.width))),
                         Image.LANCZOS) for im in ims]
    frames = [im.quantize(colors=colors, method=Image.MEDIANCUT)
              for im in ims]
    frames[0].save(gif_path, save_all=True, append_images=frames[1:],
                   duration=duration, loop=0, optimize=True)
    size = os.path.getsize(gif_path)
    print(f'  -> {gif_path}  {len(frames)} frames  {duration} ms  '
          f'{ims[0].width}x{ims[0].height}  {size / 1e6:.2f} MB')
    return gif_path


def animate(series, out_dir, style_name='report', cutaway=0.55,
            cut_axis='y', cut_keep='hi', window=(1000, 780), duration=450,
            ghost_alpha=0.15, scale_bar=None, decimate=None, solid_path=None,
            label_fmt=None, every=1, max_frames=None, colors=256,
            gif_width=None, tag=None, merge_solid=True, opaque='nw',
            view='iso'):
    """Render a frame series in a fixed camera and write a looping GIF.

    Defaults differ from the static panels on purpose:
      * cut on **y** (not x): cutting x throws away the downstream half of
        the box, so an advancing front would vanish at the cut plane.  A
        y-cut keeps inlet-to-outlet across the frame, inlet on the left.
      * the solid sits at an absolute opacity of 0.15 (not the static
        panels' faintest ghost) so the skeleton reads as a rock you can see
        the fluids through, rather than vanishing.
      * the glass/opaque assignment is frozen from the whole series, so the
        colours do not swap halfway through the clip.
    """
    fs = _series_files(series)[::max(every, 1)]
    if max_frames:
        fs = fs[:max_frames]
    tag = tag or os.path.basename(os.path.normpath(
        series if os.path.isdir(series) else os.path.dirname(series)))
    st = _style(style_name)
    os.makedirs(out_dir, exist_ok=True)
    print(f'[{tag}] {len(fs)} frames from {series}')

    psi0, solid, meta0, src = _load_frame(fs[0])
    print(f'     phase field from {src!r}')
    if solid is None:
        cand = os.path.join(series if os.path.isdir(series)
                            else os.path.dirname(series), 'f_solid.npz')
        src = solid_path or (cand if os.path.exists(cand) else None)
        if src is None:
            raise SystemExit('no solid in the frames and no --solid given')
        solid = np.load(src)['solid'].astype(np.int8)
        print(f'     solid from {src}  {solid.shape}')
    nx = psi0.shape[0]
    run = dict(psi=psi0, solid=solid, dom=slice(0, nx), tag=tag,
               R_lu=None, npz=fs[0], res_thick=0, meta={})

    # solid never changes: build (and crop) its mesh once for the whole clip
    solid_c, origin = _crop3(solid, cut_axis, cutaway, cut_keep)
    ghost = None
    if merge_solid:
        ghost = surface(solid_c.astype(np.float32), 0.5,
                        spacing=(1, 1, 1), origin=origin,
                        decimate=0.5 if decimate is None else decimate)
        print(f'     solid ghost mesh: {ghost.n_points} pts (built once)')

    # The opaque phase is frozen for the whole clip; flipping mid-animation
    # would read as a rendering bug.  Default 'nw' = the invading phase in
    # drainage stays solid, so the advancing front is never lost inside a
    # glass wash.  Pass opaque='wet' for an imbibition film.
    psi_last, _, meta_last, _ = _load_frame(fs[-1])
    pc, _ = _crop3(psi_last, cut_axis, cutaway, cut_keep)
    sc, _ = _crop3(solid, cut_axis, cutaway, cut_keep)
    frac_nw = float(((pc > 0.0) & (sc == 0)).sum()) / max((sc == 0).sum(), 1)
    print(f'     final S_nw(cropped)={frac_nw:.3f}; opaque={opaque} '
          f'(frozen for the whole clip)')

    pngs = []
    for k, f in enumerate(fs):
        psi, _, meta, _ = _load_frame(f)
        m = dict(meta0)
        m.update(meta)
        out_png = os.path.join(out_dir, f'anim_{k:04d}.png')
        panel_cutaway(run, out_png, st, focus='both', cutaway=cutaway,
                      cut_axis=cut_axis, cut_keep=cut_keep,
                      solid_mesh=ghost, psi_override=psi, opaque=opaque,
                      ghost_alpha=ghost_alpha, decimate=decimate,
                      scale_bar=scale_bar, window=window, view=view,
                      title=_frame_label(tag, m, label_fmt), quiet=True)
        pngs.append(out_png)
        if (k + 1) % 5 == 0 or k == len(fs) - 1:
            print(f'     frame {k + 1}/{len(fs)}', flush=True)
    montage([pngs[i] for i in np.linspace(0, len(pngs) - 1,
                                         min(8, len(pngs))).astype(int)],
            os.path.join(out_dir, f'{tag}_anim_qa.png'), cols=4)
    gif = os.path.join(out_dir, f'{tag}_drain.gif')
    make_gif(pngs, gif, duration=duration, colors=colors,
             max_width=gif_width)
    return gif
