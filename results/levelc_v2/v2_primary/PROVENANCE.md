# PROVENANCE — BI-V2-BILATERAL-001

## Producer chain (all ancestors of the final candidate; the driver
file in the candidate is byte-identical to the last producer)

| Revision | Content | Role |
|---|---|---|
| `d689526` | driver + unit checks | attempt-1 (aborted: per-node rho guardrail stop at t=1000) |
| `2fcb552` | cluster per-root size fix | — |
| `9ed4bcb` | declared equil window (guardrails gate for t>5000) | attempt-2 (aborted at t=6000, same cause) |
| `052ab97` | bulk-node rho guardrail semantics + V1c-baseline evidence | **producer of the completed 60 000-step primary run** (`prov.run_head`) |
| this commit | `results/levelc_v2/**` | final candidate |

The two aborted attempts are part of the honest record (their stop
messages and logs were overwritten by the rerun; the causes and
evidence values are documented in EXECUTION_REPORT.md).  The completed
run is one continuous 60 000-step execution; its `report.json::prov`
records command / run_head `052ab97` / producer sha256
`3b618e2a…` / timestamps; every CSV has a `.prov.json` sidecar;
shell exit code 0 in `logs/v2_primary.exit`, mirrored in MANIFEST.json.

## Environment

GPU/CUDA, conda env `lbm`, python 3.10.21, taichi 1.7.4, scipy 1.15.3
(cluster labelling).  Fixed physics: CapA=0.06, nu=0.1 matched,
rho0=1, psi_solid=-0.68, z periodic, no reservoirs/membranes/forcing.

## Derived-artifact rule

No figures on the product branch; SVGs are generated on the control
branch from this committed numeric evidence by a committed script with
the candidate SHA in every caption.
