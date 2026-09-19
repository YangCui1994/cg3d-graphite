# Baseline freeze — provenance

Frozen 2026-09-19 (Plan_20260919_v2, Phase 0). These are byte-for-byte
copies of the pre-audit X2/X3 results. **Do not modify** — every later
numerical change is compared against these (Phase 5, `docs/NUMERICAL_AUDIT_2026_09.md`).

| file | content | produced by |
| --- | --- | --- |
| `gx2b_drain_report.json` | X2 graphite drainage Pc–S ladder report | `run_pcs_cg3d.py` (gx2b) |
| `gx3_ir_report.json` | X3 graphite imbibition–residual report | `run_ir_cg3d.py` (gx3) |
| `results_pcs_cg3d_gx1.log` | gx1 probe log (NaN incident, see docs) | `run_pcs_cg3d.py` |
| `results_pcs_cg3d_gx1b.log` | gx1b probe log (14-lu buffer geometry) | `run_pcs_cg3d.py` |
| `results_pcs_cg3d_gx2.log` | X2 ladder console log | `run_pcs_cg3d.py` |
| `results_pcs_cg3d_gx2b.log` | X2b ladder console log | `run_pcs_cg3d.py` |
| `results_pcs_cg3d_gx3.log` | X3 ladder console log | `run_ir_cg3d.py` |

## Source revision

- upstream git commit: `3ae993e` ("Add project plan for numerical correctness
  and validation") — the tip of master when the audit campaign started;
  solver/driver code identical to the earlier cleanup merge `b339114`.
- baseline tag: `baseline-pre-audit-2026-09` (points at `201a99c`, i.e. the
  plan document itself; code content equals `3ae993e`).

## Environment

- GPU: NVIDIA GeForce RTX 5080, driver 595.95
- conda env `lbm`: python 3.10.21, taichi 1.7.4, numpy 2.2.6, scipy 1.15.3,
  pyvista 0.49.0, vtk 9.7.0
- geometry: `data/geo_graphite_200.npz` (200^3, from
  `process_electrode_BIL.py`) with 14-lu open buffer via `make_geo_buffer.py`
- no random seeds involved: geometry is a fixed npz, initial condition is
  deterministic (uniform colour + reservoir densities)
