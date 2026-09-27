"""Re-run the two cases that the harness bugs aborted, then rebuild the
pass-04 SUMMARY, run_manifest and VALIDATION_REPORT from the case dirs.

Documented deviation: cases 04 and 07 were re-run after a harness fix
(an unrenamed gate key and a broadcasting error).  Both re-runs used the
same frozen candidate and the same repaired driver; every other case in the
tree is from the single uninterrupted run.
"""
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "experimental"))
import pass04  # noqa: E402
import artifact as A  # noqa: E402

CAND = io.open('.cand').read().strip() if os.path.exists('.cand') else \
    pass04.__dict__.get('__cand__', 'unknown')

for idx in (4, 7):
    t = time.time()
    try:
        verd, c = pass04.CASES[idx](pass04.OUT_ROOT, CAND)
    except Exception:
        import traceback
        traceback.print_exc()
        verd = "NOT_RUN"
    print(f"[{verd}] case-{idx:02d} re-run ({time.time()-t:.1f}s)", flush=True)

# ---- rebuild SUMMARY.json / run_manifest.json / VALIDATION_REPORT.md ----
cases = {}
for idx in sorted(pass04.CASES):
    name = None
    for d in sorted(os.listdir(pass04.OUT_ROOT)):
        if d.startswith(f"case-{idx:02d}-"):
            name = d
            break
    if name is None:
        continue
    met = {}
    fp = os.path.join(pass04.OUT_ROOT, name, "metrics.json")
    if os.path.exists(fp):
        met = json.load(io.open(fp, encoding='utf-8'))
    cases[f"case-{idx:02d}"] = dict(verdict=met.get("verdict", "NOT_RUN"),
                                    dir=name, exit_code=0,
                                    wall_seconds=met.get("wall_seconds", 0.0))
counts = {}
for v in cases.values():
    counts[v["verdict"]] = counts.get(v["verdict"], 0) + 1
sm = dict(stage="BI-CG-LECLAIRE-PASS4-001", candidate_sha=CAND,
          branch="agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001",
          environment=A.environment(), verdict_counts=counts, cases=cases,
          gates=pass04.GATES, raw_schema_version=A.RAW_SCHEMA_VERSION,
          convention="n_w=-grad(g)/|grad(g)| solid->fluid; theta through liquid/red",
          rerun_note="cases 04 and 07 re-run after a harness fix (unrenamed gate "
                     "key, broadcasting error); all other cases from one "
                     "uninterrupted run of the same frozen candidate")
json.dump(sm, io.open(os.path.join(pass04.OUT_ROOT, "SUMMARY.json"), "w",
                      encoding='utf-8'), indent=2, default=float)
json.dump(dict(stage=sm["stage"], candidate_sha=CAND,
               environment=sm["environment"], cases=cases,
               raw_schema_version=A.RAW_SCHEMA_VERSION,
               command="python tests/leclaire_cg/pass04.py",
               rerun_note=sm["rerun_note"]),
          io.open(os.path.join(pass04.OUT_ROOT, "run_manifest.json"), "w",
                  encoding='utf-8'), indent=2, default=float)
pass04.write_validation_report(pass04.OUT_ROOT, CAND)
print("SUMMARY rebuilt:", counts, flush=True)
