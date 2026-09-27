"""Pass-04 artifact harness: per-case directory, raw snapshots, figures.

Implements VALIDATION_ARTIFACT_SPEC.md for the Leclaire reference line.

Layout written per case:
    <out>/case-NN-<name>/
        README.md
        metadata.json
        metrics.json
        metrics.csv
        raw/            compressed npz snapshots (schema-versioned)
        figures/        PNG + SVG renderings
        logs/
        render_manifest.json
        reproduce.py

Scratch/utility module for the pass-04 runner; it is committed because the
reproduce scripts and render manifests reference it.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import platform
import sys
import time

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt            # noqa: E402

RAW_SCHEMA_VERSION = "l17c_core_raw_v1"

# Frozen rendering conventions (VALIDATION_ARTIFACT_SPEC section 7)
PSI_VMIN, PSI_VMAX = -1.0, 1.0
CMAP_PSI = "RdBu_r"          # red = +psi = liquid, blue = -psi = gas
SOLID_RGBA = (0.25, 0.25, 0.25, 1.0)
FIG_DPI = 160


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def environment():
    return dict(
        host=platform.node(),
        platform=platform.platform(),
        python=sys.version.split()[0],
        numpy=np.__version__,
        matplotlib=matplotlib.__version__,
        backend="numpy-f64",
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )


class Case:
    """One validation case's artifact directory."""

    def __init__(self, out_root, idx, name, candidate_sha):
        self.dir = os.path.join(out_root, f"case-{idx:02d}-{name}")
        self.name = name
        self.idx = idx
        self.candidate = candidate_sha
        self.figs = []
        self.snaps = {}
        for sub in ("raw", "figures", "logs"):
            os.makedirs(os.path.join(self.dir, sub), exist_ok=True)
        self.t0 = time.time()

    # ---------------- raw snapshots ----------------
    def snapshot(self, label, solver, extra=None):
        """Retain compressed raw state sufficient to regenerate figures."""
        arrs = dict(
            solid=solver.solid.astype(np.int8),
            psi=solver.psi().astype(np.float32),
            rho_r=solver.rho_r.astype(np.float32),
            rho_b=solver.rho_b.astype(np.float32),
        )
        rho, u = solver.macroscopic()
        arrs["rho"] = rho.astype(np.float32)
        arrs["vel"] = u.astype(np.float32)
        arrs["speed"] = np.linalg.norm(u, axis=-1).astype(np.float32)
        if extra:
            for k, v in extra.items():
                arrs[k] = np.asarray(v, dtype=np.float32)
        arrs["schema_version"] = np.array(RAW_SCHEMA_VERSION)
        path = os.path.join(self.dir, "raw", f"{label}.npz")
        np.savez_compressed(path, **arrs)
        self.snaps[label] = dict(
            file=os.path.relpath(path, self.dir).replace("\\", "/"),
            sha256=_sha256(path), bytes=os.path.getsize(path),
            t=int(getattr(solver, "time", 0)),
            fields=sorted(k for k in arrs if k != "schema_version"),
            schema_version=RAW_SCHEMA_VERSION)
        return path

    # ---------------- figures ----------------
    def _save(self, fig, stem, plotted, source_raw, extra=None):
        png = os.path.join(self.dir, "figures", stem + ".png")
        svg = os.path.join(self.dir, "figures", stem + ".svg")
        fig.savefig(png, dpi=FIG_DPI, bbox_inches="tight")
        fig.savefig(svg, bbox_inches="tight")
        plt.close(fig)
        rec = dict(
            figure=os.path.relpath(png, self.dir).replace("\\", "/"),
            figure_svg=os.path.relpath(svg, self.dir).replace("\\", "/"),
            source_candidate_sha=self.candidate,
            source_raw=source_raw,
            plotted_variable=plotted,
            psi_scale=[PSI_VMIN, PSI_VMAX],
            colormap=CMAP_PSI,
            script="tests/leclaire_cg/pass04.py",
            script_version="pass-04",
        )
        if extra:
            rec.update(extra)
        self.figs.append(rec)
        return rec

    def fig_field_slice(self, arrays, stem, title, plane="xz", index=None,
                        level=0.0, source_raw=None):
        """Category A: geometry/field rendering."""
        psi = arrays["psi"]
        solid = arrays["solid"]
        if plane == "xz":
            k = psi.shape[1] // 2 if index is None else index
            f = psi[:, k, :].T
            s = solid[:, k, :].T
            xl, yl = "x [lu]", "z [lu]"
        else:
            k = psi.shape[2] // 2 if index is None else index
            f = psi[:, :, k].T
            s = solid[:, :, k].T
            xl, yl = "x [lu]", "y [lu]"
        fig, ax = plt.subplots(figsize=(5.4, 3.4))
        im = ax.imshow(np.where(s, np.nan, f), origin="lower", cmap=CMAP_PSI,
                       vmin=PSI_VMIN, vmax=PSI_VMAX, interpolation="nearest",
                       aspect="equal")
        ax.imshow(np.where(s, 1.0, np.nan), origin="lower",
                  cmap=matplotlib.colors.ListedColormap([SOLID_RGBA]),
                  vmin=0, vmax=1, interpolation="nearest", aspect="equal")
        # psi = 0 contour
        try:
            ax.contour(f, levels=[level], colors="k", linewidths=0.7,
                       origin="lower")
        except Exception:
            pass
        fig.colorbar(im, ax=ax, label=r"$\psi$  (+liquid/red, -gas/blue)",
                     fraction=0.046)
        ax.set_xlabel(xl)
        ax.set_ylabel(yl)
        ax.set_title(title, fontsize=9)
        ax.text(0.01, 0.99, f"candidate {self.candidate[:12]}",
                transform=ax.transAxes, va="top", fontsize=6, color="0.3")
        return self._save(fig, stem, "psi", source_raw, {"slice": plane,
                                                         "slice_index": int(k),
                                                         "isosurface_level": level})

    def fig_xy(self, x, y, stem, title, xlabel, ylabel, series=None,
               residual=None, source_raw=None, logy=False):
        """Category B/C: observable and residual."""
        series = series or [dict(y=y, label=ylabel, style="-")]
        fig, ax = plt.subplots(figsize=(5.0, 3.2))
        for s in series:
            ax.plot(x, s["y"], s.get("style", "-"), label=s["label"],
                    markersize=3)
        if logy:
            ax.set_yscale("log")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=9)
        if len(series) > 1:
            ax.legend(fontsize=7)
        ax.grid(alpha=0.25)
        ax.text(0.01, 0.99, f"candidate {self.candidate[:12]}",
                transform=ax.transAxes, va="top", fontsize=6, color="0.3")
        return self._save(fig, stem, ylabel, source_raw)

    # ---------------- text artifacts ----------------
    def write_metrics(self, metrics, timeseries=None):
        with io.open(os.path.join(self.dir, "metrics.json"), "w",
                     encoding="utf-8") as fh:
            json.dump(metrics, fh, indent=2, default=float)
        if timeseries:
            keys = sorted(timeseries[0].keys())
            with io.open(os.path.join(self.dir, "metrics.csv"), "w",
                         newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=keys)
                w.writeheader()
                for row in timeseries:
                    w.writerow(row)

    def write_metadata(self, meta):
        meta = dict(meta)
        meta.update(candidate_sha=self.candidate,
                    case_id=f"case-{self.idx:02d}",
                    case_name=self.name,
                    raw_schema_version=RAW_SCHEMA_VERSION,
                    wall_seconds=time.time() - self.t0)
        with io.open(os.path.join(self.dir, "metadata.json"), "w",
                     encoding="utf-8") as fh:
            json.dump(meta, fh, indent=2, default=float)

    def write_render_manifest(self):
        with io.open(os.path.join(self.dir, "render_manifest.json"), "w",
                     encoding="utf-8") as fh:
            json.dump(dict(candidate_sha=self.candidate,
                           raw_schema_version=RAW_SCHEMA_VERSION,
                           psi_scale=[PSI_VMIN, PSI_VMAX],
                           colormap=CMAP_PSI, dpi=FIG_DPI,
                           figures=self.figs), fh, indent=2)

    def write_readme(self, identity, setup, reference, table, actual,
                     verdict):
        # `verdict` doubles as the spec's section 4.5 interpretation
        # boundary (PASS / FAIL_SOLVER / FAIL_MEASUREMENT / INVALID_TEST /
        # INCONCLUSIVE); a separate parameter would duplicate it.
        lines = [
            f"# {self.name}", "",
            "## Case identity", "```text",
            f"Case ID:            case-{self.idx:02d}",
            f"Case name:          {self.name}",
            f"Solver mode:        L17_CORE (NumPy/f64 reference)",
            f"Candidate SHA:      {self.candidate}",
            f"Physical target:    {identity.get('target','')}",
            f"Reference/theory:   {reference.get('relation','')}",
            f"Verdict:            {verdict}",
            "```", "",
            "## Setup", "",
            "| item | value |", "|---|---|",
        ]
        for k, v in setup.items():
            lines.append(f"| {k} | {v} |")
        lines += ["", "## Standard / reference result", "",
                  reference.get("prose", ""), "",
                  f"```text\n{reference.get('relation','')}\n```", "",
                  "## Actual result", "",
                  "| quantity | expected | measured | error/residual | status |",
                  "|---|---:|---:|---:|---|"]
        lines += table
        lines += ["", "## Interpretation boundary", "", f"**{verdict}**", "",
                  actual]
        lines += ["", "## Artifacts", "",
                  "- `raw/` compressed raw fields (`%s`)" % RAW_SCHEMA_VERSION,
                  "- `figures/` PNG + SVG; regeneration paths in `render_manifest.json`",
                  "- `metrics.json` / `metrics.csv`",
                  "- `reproduce.py` re-runs this case from the frozen candidate",
                  "- `logs/` run log", ""]
        with io.open(os.path.join(self.dir, "README.md"), "w",
                     encoding="utf-8") as fh:
            fh.write("\n".join(lines))

    def write_reproduce(self):
        body = (
            '"""Regenerate this case from the frozen candidate."""\n'
            "import os, sys\n"
            "sys.path.insert(0, os.path.join(os.path.dirname(__file__),\n"
            "                                '..', '..', '..', 'tests',\n"
            "                                'leclaire_cg'))\n"
            "import pass04\n"
            f"pass04.run_one({self.idx}, out_root=os.path.join(os.path.dirname(__file__), '..'))\n")
        with io.open(os.path.join(self.dir, "reproduce.py"), "w",
                     encoding="utf-8") as fh:
            fh.write(body)
