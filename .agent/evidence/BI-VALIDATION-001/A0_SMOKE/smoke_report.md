# A0 Runner-Bootstrap Isolation Smoke — PASS

- date: 2026-09-23T08:12:14Z
- episode: BI-VALIDATION-001
- runner: D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-graphite/.agent/episodes/bilateral-imbibition-v0.1/runner/episode_runner.py
- smoke branch: agent-episode/BI-VALIDATION-001-smoke (base 9ede55c8ef75, worktree checked out by the runner; control checkout untouched)
- candidates: C1 bbda7ff8e2fc53c501760daaf2e78d24e6338974 (planted defect) -> C2 ad828860d5528403ae8e77217f6b108745711b22 (fix)
- decisions: round1=CHANGES_REQUESTED, round2=PASS
- sessions: {
 "executor-1": "sess_578fa632-fd94-4219-b84e-a89116bd209e",
 "reviewer-1": "sess_620b35a3-f2f3-4535-b009-7118d995197c",
 "executor-2": "sess_578fa632-fd94-4219-b84e-a89116bd209e",
 "reviewer-2": "sess_de4dc1c1-f02f-45f9-a466-c454f106cdcc"
}

## Isolation checks

- executor_wrote_candidate_marker: **True**
- reviewer_distinct_fresh_session: **True**
- reviewer_received_marker_and_contract: **True**
- reviewer_prompt_has_no_transcript: **True**
- reviewer_did_not_modify_product: **True**
- rework_candidate_created: **True**
- second_candidate_new_fresh_reviewer: **True**
- pass_promotes_cleanly: **True**

Reviewer prompts contain only contract paths, candidate SHA,
report path and output paths (verbatim prompts preserved in
session_log.jsonl); no executor transcript is passed at any
point. Product-tree cleanliness was verified with git status
after every reviewer session (write-restriction enforcement).

Evidence files (local runtime): session_log.jsonl, round-01/,
round-02/ (execution reports, reviews, reviewer evidence).
