"""Bilateral-imbibition episode runner (A0 bootstrap, BI-VALIDATION-001).

Lightweight LOCAL orchestration for the ZCode executor/reviewer loop
defined by .agent/episodes/bilateral-imbibition-v0.1/.  Reuses the
proven subprocess/session/provenance patterns of the V1 Controller
(.agent/controller/controller.py: --json envelope sessionId extraction,
--resume for executor rework, timeout process-tree kill,
GIT_TERMINAL_PROMPT=0) but is episode-oriented: stage state machine,
candidate freezing, fresh-reviewer isolation, bounded rework, V0->V3
promotion.

Not a replacement for the V1 Controller and NOT a scientific component:
A0 explicitly forbids touching CG3D solver physics.

Commands (run from the control checkout root):
  python .agent/episodes/bilateral-imbibition-v0.1/runner/episode_runner.py
      init            # create episode_state.json
      init-product    # create product branch + worktree from the
                      #   declared product execution base (V0 time)
      run-smoke       # A0 isolation smoke: E1/R1(fail)/E2(resume)/R2(pass)
      start-stage V0  # begin the real loop (authorized after A0 review)
      run             # drive the current stage round to its boundary
      status          # print machine state

State: .agent_runtime/episodes/BI-VALIDATION-001/episode_state.json
(atomic writes; every transition persists stage/attempt/session IDs/
candidate SHAs/decisions, so a crashed runner resumes with unambiguous
provenance or stops HUMAN_REQUIRED per the checkpoint contract).

Session isolation model:
  - executor: fresh session for attempt 1; --resume <id> for rework
    unless the previous REVIEW.md contains RESET_CONTEXT: YES;
  - reviewer: ALWAYS a fresh session (never --resume); the prompt
    carries ONLY contract paths / candidate SHA / report path / output
    paths — structurally no executor transcript;
  - sessions run inside a dedicated git worktree; after every reviewer
    session the runner verifies the product tree still matches the
    frozen candidate (reviewer product-file modification = violation).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

EPISODE_DIR = Path(__file__).resolve().parents[1]        # .../bilateral-imbibition-v0.1
REPO_ROOT = EPISODE_DIR.parents[2]                       # control checkout root
STATE_DIR = REPO_ROOT / ".agent_runtime" / "episodes" / "BI-VALIDATION-001"
STATE_PATH = STATE_DIR / "episode_state.json"

EPISODE_ID = "BI-VALIDATION-001"
PRODUCT_BRANCH = "agent-episode/BI-VALIDATION-001"
PRODUCT_BASE = "9ede55c8ef7589b61606e11c033c84d9bcd1de94"   # declared master base
SMOKE_BRANCH = "agent-episode/BI-VALIDATION-001-smoke"
STAGES = ["V0", "V1", "V2", "V3"]
STAGE_CONTRACTS = {
    "V0": "STAGE_V0_BASELINE.md",
    "V1": "STAGE_V1_DYNAMIC_WETTING.md",
    "V2": "STAGE_V2_BILATERAL.md",
    "V3": "STAGE_V3_BUFFER_SENSITIVITY.md",
}
ZCODE = ["node", "C:/Program Files/ZCode/resources/glm/zcode.cjs"]
ZCODE_MODE = "yolo"
SESSION_TIMEOUT_S = 7200          # real stages; smoke uses 1800
SMOKE_TIMEOUT_S = 1800
DECISIONS = ("PASS", "CHANGES_REQUESTED", "HUMAN_REQUIRED")
SMOKE_MARKER_REQ = ("the single required line 'SMOKE-PASS-TOKEN-7f3a' "
                    "plus a short free-text description")


class RunnerError(RuntimeError):
    pass


def utc_now() -> str:
    return (datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            .replace("+00:00", "Z"))


# ---------------------------------------------------------------- state
def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    tmp.replace(path)


def load_state() -> dict:
    if not STATE_PATH.exists():
        raise RunnerError(f"no episode state at {STATE_PATH}; run init")
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    state["updated_at"] = utc_now()
    _atomic_write_json(STATE_PATH, state)


def fresh_state() -> dict:
    return dict(
        episode_id=EPISODE_ID,
        episode_dir=EPISODE_DIR.as_posix(),
        product_branch=PRODUCT_BRANCH,
        product_base=PRODUCT_BASE,
        worktree=None,
        smoke=dict(status="PENDING", branch=SMOKE_BRANCH, sessions=[],
                   candidates=[], decisions=[], checks={}),
        stages={s: dict(status="READY" if s == "V0" else "LOCKED",
                        attempts=0, executor_sessions=[],
                        reviewer_sessions=[], candidates=[],
                        decisions=[]) for s in STAGES},
        current_stage="V0",
        episode_status="SMOKE_PENDING",
        history=[],
    )


def record(state: dict, event: str, **facts) -> None:
    state["history"].append(dict(event=event, at=utc_now(), **facts))
    print(f"[{utc_now()}] {event} "
          + " ".join(f"{k}={v}" for k, v in facts.items() if v is not None),
          flush=True)


# ------------------------------------------------------------- sessions
def _parse_envelope(stdout: str):
    candidates = [stdout.strip(),
                  *reversed([ln.strip() for ln in stdout.splitlines()
                             if ln.strip()])]
    for cand in candidates:
        try:
            value = json.loads(cand)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(value, dict):
            return value
    return None


class SessionResult:
    def __init__(self, proc: dict):
        self.__dict__.update(proc)
        self.envelope = _parse_envelope(proc["stdout"])

    @property
    def session_id(self):
        if not self.envelope:
            return None
        v = self.envelope.get("sessionId")
        return v if isinstance(v, str) and v else None


def _run_process(command, cwd, timeout_s):
    """Popen with hard-timeout process-tree kill (V1-controller pattern)."""
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    opts = {}
    if os.name == "nt":
        opts["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        opts["start_new_session"] = True
    proc = subprocess.Popen(command, cwd=cwd, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env, **opts)
    try:
        out, err = proc.communicate(timeout=timeout_s)
        timed_out = False
    except subprocess.TimeoutExpired:
        timed_out = True
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                           text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, check=False)
            if proc.poll() is None:
                proc.kill()
        else:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        out, err = proc.communicate()
    return subprocess.CompletedProcess(command, proc.returncode, out,
                                       err), timed_out


def launch_session(worktree: Path, prompt: str, *, resume: str | None,
                   timeout_s: int, log_path: Path) -> SessionResult:
    """One headless ZCode session.  Command, prompt, exit code, timing
    and stdout/stderr tail are appended to log_path as durable
    isolation/provenance evidence (the prompt record IS the proof of
    what context the session did and did not receive)."""
    command = [*ZCODE, "--cwd", str(worktree), "--mode", ZCODE_MODE,
               "--json"]
    if resume:
        command += ["--resume", resume]
    command += ["-p", prompt]
    started_wall, started = utc_now(), time.monotonic()
    proc, timed_out = _run_process(command, str(worktree), timeout_s)
    elapsed = round(time.monotonic() - started, 3)
    result = dict(command=command, prompt=prompt, resume=resume,
                  started_at=started_wall, finished_at=utc_now(),
                  elapsed_s=elapsed, exit_code=proc.returncode,
                  timed_out=timed_out, stdout=proc.stdout,
                  stderr=proc.stderr[-4000:])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    print(f"[session] exit={result['exit_code']} elapsed={elapsed}s "
          f"resume={bool(resume)} timed_out={timed_out}", flush=True)
    return SessionResult(result)


# ------------------------------------------------------------------ git
def _git(worktree: Path, *args: str) -> str:
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    p = subprocess.run(["git", "-C", str(worktree), *args], text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       env=env)
    if p.returncode != 0:
        raise RunnerError(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout.strip()


def head_sha(worktree: Path) -> str:
    return _git(worktree, "rev-parse", "HEAD")


def worktree_dirty(worktree: Path) -> list[str]:
    out = _git(worktree, "status", "--porcelain")
    return [ln[3:].strip() for ln in out.splitlines() if ln.strip()]


def stage_run_dir(stage: str, attempt: int) -> Path:
    return STATE_DIR / stage / f"round-{attempt:02d}"


# -------------------------------------------------------------- prompts
def executor_prompt(stage: str, attempt: int, *, contract: Path,
                    branch: str, base_sha: str, review: Path | None,
                    marker_req: str | None, marker_flawed: bool,
                    report: Path, marker: Path | None,
                    resume_note: str | None) -> str:
    parts = [
        f"You are the ZCode EXECUTOR for episode {EPISODE_ID}, stage "
        f"{stage}, attempt {attempt}.",
        f"First read AGENTS.md in your working tree, then read the Stage "
        f"Contract at {contract.as_posix()}.",
        f"Product branch: {branch} (execution base {base_sha[:12]}). "
        f"Commit your candidate to this branch. Never merge, never "
        f"force-push, never rewrite history.",
    ]
    if review is not None:
        parts.append(
            f"This is a REWORK round. Read the reviewer findings at "
            f"{review.as_posix()} and address ONLY the requested "
            f"corrections. Do not broaden scope.")
    if resume_note:
        parts.append(resume_note)
    if marker is not None:
        if marker_flawed:
            parts.append(
                f"Round task: write the candidate marker file at "
                f"{marker.as_posix()}.  As documented in the smoke "
                f"contract, round 1 intentionally plants the defect: "
                f"write a short marker WITHOUT the token so the reviewer "
                f"can exercise the failure path. Do not add the token in "
                f"this round.")
        else:
            parts.append(
                f"Round task: fix the candidate marker file at "
                f"{marker.as_posix()} so it satisfies the contract: it "
                f"must contain {marker_req}.")
    parts += [
        f"Write your execution report to {report.as_posix()} (absolute "
        f"path; plain markdown with: stage/attempt, base SHA, candidate "
        f"SHA after you commit, changed files, commands run, exit codes, "
        f"deviations).",
        "Stop after committing the candidate and writing the report.",
    ]
    return "\n".join(parts)


def reviewer_prompt(stage: str, attempt: int, *, contract: Path,
                    episode_contract: Path, candidate_sha: str,
                    report: Path, review_out: Path,
                    reviewer_evidence_dir: Path) -> str:
    return "\n".join([
        f"You are the independent ZCode REVIEWER for episode "
        f"{EPISODE_ID}, stage {stage}, attempt {attempt}. You are a "
        f"fresh session; judge only the frozen candidate below.",
        f"Read the Episode Contract at {episode_contract.as_posix()} and "
        f"the Stage Contract at {contract.as_posix()}.",
        f"Candidate commit (frozen): {candidate_sha}. Verify with git in "
        f"your working tree that HEAD is exactly this commit; if it is "
        f"not, decide HUMAN_REQUIRED.",
        f"Read the executor's execution report at {report.as_posix()}. "
        f"Inspect the candidate diff itself (git show {candidate_sha}); "
        f"do not trust the report alone.",
        f"Write your review to {review_out.as_posix()} with FIRST LINES "
        f"exactly like:",
        "```",
        f"stage: {stage}",
        f"attempt: {attempt}",
        f"candidate: {candidate_sha}",
        f"execution_report: {report.as_posix()}",
        "```",
        "then sections: binding; coverage; findings; decision; "
        "rationale; next action; and for a CHANGES_REQUESTED rework "
        "round add 'RESET_CONTEXT: YES|NO'.",
        "The decision must be exactly one of PASS, CHANGES_REQUESTED, "
        "HUMAN_REQUIRED, stated on a 'Decision:' line and nowhere else "
        "as a decision.",
        "WRITE RESTRICTION: you must NOT modify any product file, "
        "commit, branch, test, or executor artifact. You may only write "
        f"the review file and reviewer-owned evidence under "
        f"{reviewer_evidence_dir.as_posix()}.",
    ])


# ------------------------------------------------- review parse/validate
def parse_review(review_path: Path, stage: str, attempt: int,
                 candidate_sha: str) -> tuple[str, bool]:
    """Returns (decision, reset_context).  Validates the binding header
    and rejects ambiguous decisions."""
    text = review_path.read_text(encoding="utf-8").replace("\r", "")
    head = text[:600]
    if f"candidate: {candidate_sha}" not in head:
        raise RunnerError(
            f"review does not bind to candidate {candidate_sha}")
    for key, want in (("stage", stage), ("attempt", str(attempt))):
        m = re.search(rf"^{key}:\s*(.+)$", head, re.M)
        if not m or m.group(1).strip() != want:
            raise RunnerError(f"review binding {key} != {want!r}")
    decisions = [d.strip().upper().rstrip(".")
                 for d in re.findall(r"^Decision:\s*(\S+)", text, re.M)]
    if not decisions:
        raise RunnerError("review has no 'Decision:' line")
    if len(set(decisions)) != 1 or decisions[0] not in DECISIONS:
        raise RunnerError(f"review decision ambiguous or unknown: "
                          f"{decisions}")
    rc = re.search(r"^RESET_CONTEXT:\s*(\S+)", text, re.M)
    return decisions[0], (rc is not None
                          and rc.group(1).strip().upper() == "YES")


def product_clean(worktree: Path, expected_sha: str, context: str) -> None:
    """Reviewer write-restriction enforcement: after a reviewer session
    the product tree must be exactly the frozen candidate."""
    sha = head_sha(worktree)
    dirty = worktree_dirty(worktree)
    if sha != expected_sha or dirty:
        raise RunnerError(
            f"{context}: product tree changed during review "
            f"(head={sha[:12]} expected={expected_sha[:12]}, "
            f"dirty={dirty}) — reviewer write-restriction violation")


# ---------------------------------------------------------------- smoke
def cmd_init(args) -> None:
    if STATE_PATH.exists():
        print("state exists:", STATE_PATH)
        return
    save_state(fresh_state())
    print("initialized", STATE_PATH)


def _make_worktree(name: str, branch: str) -> Path:
    wt = REPO_ROOT.parent / "cg3d-episode-worktrees" / name
    if not wt.exists():
        _git(REPO_ROOT, "worktree", "add", "-b", branch, str(wt),
             PRODUCT_BASE)
    return wt


def cmd_init_product(args) -> None:
    state = load_state()
    if state["episode_status"] not in ("A0_REVIEW", "RUNNING"):
        raise RunnerError("A0 smoke/external review not complete; product "
                          "branch creation is not authorized yet")
    wt = _make_worktree(EPISODE_ID, PRODUCT_BRANCH)
    state["worktree"] = wt.as_posix()
    record(state, "product-initialized", branch=PRODUCT_BRANCH,
           base=PRODUCT_BASE, worktree=state["worktree"])
    save_state(state)
    print("product worktree ready:", state["worktree"])


def cmd_run_smoke(args) -> None:
    state = load_state()
    if state["smoke"]["status"] == "PASS":
        print("smoke already PASS")
        return
    wt = _make_worktree(f"{EPISODE_ID}-smoke", SMOKE_BRANCH)
    contract = EPISODE_DIR / "runner" / "SMOKE_CONTRACT.md"
    marker = wt / "smoke" / "marker.md"
    smoke_dir = STATE_DIR / "SMOKE"
    log = smoke_dir / "session_log.jsonl"
    checks: dict[str, bool] = {}

    base = head_sha(wt)
    record(state, "smoke-start", branch=SMOKE_BRANCH, base=base)

    # ---- round 1: E1 fresh, planted defect ---------------------------
    d1 = smoke_dir / "round-01"
    rep1, rev1 = d1 / "execution_report.md", d1 / "review.md"
    p1 = executor_prompt(
        "SMOKE", 1, contract=contract, branch=SMOKE_BRANCH, base_sha=base,
        review=None, marker_req=SMOKE_MARKER_REQ, marker_flawed=True,
        report=rep1, marker=marker,
        resume_note="You have no previous context: this is round 1.")
    e1 = launch_session(wt, p1, resume=None, timeout_s=SMOKE_TIMEOUT_S,
                        log_path=log)
    state["smoke"]["sessions"].append(
        dict(role="executor", attempt=1, session_id=e1.session_id,
             exit_code=e1.exit_code, elapsed_s=e1.elapsed_s))
    c1 = head_sha(wt)
    marker_committed = ("smoke/marker.md" in _git(
        wt, "show", "--name-only", "--pretty=format:", c1)) if c1 != base \
        else False
    checks["executor_wrote_candidate_marker"] = (
        marker_committed and c1 != base and not worktree_dirty(wt))
    state["smoke"]["candidates"].append(dict(attempt=1, sha=c1, base=base))
    save_state(state)
    record(state, "smoke-candidate-1", sha=c1,
           marker_committed=marker_committed)

    # ---- round 1: R1 fresh reviewer (distinct session) -----------------
    p2 = reviewer_prompt(
        "SMOKE", 1, contract=contract,
        episode_contract=EPISODE_DIR / "EPISODE_PLAN.md", candidate_sha=c1,
        report=rep1, review_out=rev1,
        reviewer_evidence_dir=d1 / "reviewer_evidence")
    r1 = launch_session(wt, p2, resume=None, timeout_s=SMOKE_TIMEOUT_S,
                        log_path=log)
    state["smoke"]["sessions"].append(
        dict(role="reviewer", attempt=1, session_id=r1.session_id,
             exit_code=r1.exit_code, elapsed_s=r1.elapsed_s))
    save_state(state)
    product_clean(wt, c1, "smoke round-01 review")
    decision1, _ = parse_review(rev1, "SMOKE", 1, c1)
    state["smoke"]["decisions"].append(
        dict(attempt=1, decision=decision1, sha=c1))
    checks["reviewer_distinct_fresh_session"] = (
        e1.session_id is not None and r1.session_id is not None
        and r1.session_id != e1.session_id)
    checks["reviewer_received_marker_and_contract"] = (
        str(contract.as_posix()) in p2 and candidate_sha_in(c1, p2)
        and str(rep1.as_posix()) in p2)
    checks["reviewer_prompt_has_no_transcript"] = (
        "executor conversation" not in p2.lower()
        and "transcript" not in p2.lower()
        and "chain-of-thought" not in p2.lower())
    checks["reviewer_did_not_modify_product"] = True   # product_clean passed
    record(state, "smoke-review-1", decision=decision1,
           session=r1.session_id)

    if decision1 != "CHANGES_REQUESTED":
        raise RunnerError(f"smoke expected CHANGES_REQUESTED in round 1, "
                          f"got {decision1} — isolation scenario broken "
                          f"(see {rev1})")

    # ---- round 2: E2 resumes E1 ---------------------------------------
    d2 = smoke_dir / "round-02"
    rep2, rev2 = d2 / "execution_report.md", d2 / "review.md"
    p3 = executor_prompt(
        "SMOKE", 2, contract=contract, branch=SMOKE_BRANCH, base_sha=c1,
        review=rev1, marker_req=SMOKE_MARKER_REQ, marker_flawed=False,
        report=rep2, marker=marker,
        resume_note="Continue from your previous session context.")
    e2 = launch_session(wt, p3, resume=e1.session_id,
                        timeout_s=SMOKE_TIMEOUT_S, log_path=log)
    state["smoke"]["sessions"].append(
        dict(role="executor", attempt=2, session_id=e2.session_id,
             exit_code=e2.exit_code, elapsed_s=e2.elapsed_s,
             resumed_from=e1.session_id))
    c2 = head_sha(wt)
    checks["rework_candidate_created"] = (
        c2 != c1 and marker.exists()
        and "SMOKE-PASS-TOKEN-7f3a" in marker.read_text(encoding="utf-8"))
    state["smoke"]["candidates"].append(dict(attempt=2, sha=c2, base=c1))
    save_state(state)
    record(state, "smoke-candidate-2", sha=c2)

    # ---- round 2: R2 NEW fresh reviewer --------------------------------
    p4 = reviewer_prompt(
        "SMOKE", 2, contract=contract,
        episode_contract=EPISODE_DIR / "EPISODE_PLAN.md", candidate_sha=c2,
        report=rep2, review_out=rev2,
        reviewer_evidence_dir=d2 / "reviewer_evidence")
    r2 = launch_session(wt, p4, resume=None, timeout_s=SMOKE_TIMEOUT_S,
                        log_path=log)
    state["smoke"]["sessions"].append(
        dict(role="reviewer", attempt=2, session_id=r2.session_id,
             exit_code=r2.exit_code, elapsed_s=r2.elapsed_s))
    save_state(state)
    product_clean(wt, c2, "smoke round-02 review")
    decision2, _ = parse_review(rev2, "SMOKE", 2, c2)
    state["smoke"]["decisions"].append(
        dict(attempt=2, decision=decision2, sha=c2))
    checks["second_candidate_new_fresh_reviewer"] = (
        r1.session_id is not None and r2.session_id is not None
        and r2.session_id != r1.session_id
        and r2.session_id != e1.session_id)

    if decision2 != "PASS":
        raise RunnerError(f"smoke expected PASS in round 2, got "
                          f"{decision2} (see {rev2})")

    # ---- promotion ------------------------------------------------------
    state["smoke"]["status"] = "PASS"
    state["smoke"]["checks"] = checks
    state["episode_status"] = "A0_REVIEW"      # stop for external review
    checks["pass_promotes_cleanly"] = (
        state["smoke"]["status"] == "PASS"
        and state["episode_status"] == "A0_REVIEW"
        and state["stages"]["V0"]["status"] == "READY")
    record(state, "smoke-pass", all_checks=all(checks.values()))
    save_state(state)

    _write_smoke_report(smoke_dir / "smoke_report.md", base, c1, c2,
                        decision1, decision2, checks, state)
    if not all(checks.values()):
        raise RunnerError(f"smoke checks failed: "
                          f"{[k for k, v in checks.items() if not v]}")
    print("SMOKE PASS — report:", smoke_dir / "smoke_report.md")


def candidate_sha_in(sha: str, prompt: str) -> bool:
    return sha in prompt or sha[:12] in prompt


def _write_smoke_report(path: Path, base, c1, c2, d1, d2, checks,
                        state) -> None:
    sess = {f'{s["role"]}-{s["attempt"]}': s["session_id"]
            for s in state["smoke"]["sessions"]}
    lines = [
        "# A0 Runner-Bootstrap Isolation Smoke — PASS",
        "",
        f"- date: {utc_now()}",
        f"- episode: {EPISODE_ID}",
        f"- runner: {Path(__file__).as_posix()}",
        f"- smoke branch: {SMOKE_BRANCH} (base {base[:12]}, worktree "
        f"checked out by the runner; control checkout untouched)",
        f"- candidates: C1 {c1} (planted defect) -> C2 {c2} (fix)",
        f"- decisions: round1={d1}, round2={d2}",
        f"- sessions: {json.dumps(sess, indent=1)}",
        "",
        "## Isolation checks",
        "",
    ]
    lines += [f"- {k}: **{v}**" for k, v in checks.items()]
    lines += [
        "",
        "Reviewer prompts contain only contract paths, candidate SHA,",
        "report path and output paths (verbatim prompts preserved in",
        "session_log.jsonl); no executor transcript is passed at any",
        "point. Product-tree cleanliness was verified with git status",
        "after every reviewer session (write-restriction enforcement).",
        "",
        "Evidence files (local runtime): session_log.jsonl, round-01/,",
        "round-02/ (execution reports, reviews, reviewer evidence).",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ------------------------------------------------------------- real loop
def cmd_start_stage(args) -> None:
    state = load_state()
    if state["episode_status"] != "A0_REVIEW" and \
            state["episode_status"] != "RUNNING":
        raise RunnerError(
            f"episode status {state['episode_status']} does not "
            f"authorize starting stages (A0 external review must pass "
            f"first)")
    stage = args.stage.upper()
    if stage not in STAGES:
        raise RunnerError(f"unknown stage {stage}")
    if STAGES.index(stage) != STAGES.index(state["current_stage"]):
        raise RunnerError(f"stage {stage} not reachable (current "
                          f"{state['current_stage']})")
    if not state.get("worktree"):
        cmd_init_product(argparse.Namespace())
        state = load_state()
    st = state["stages"][stage]
    st["status"] = "EXECUTING"
    st["attempts"] += 1
    state["current_stage"] = stage
    state["episode_status"] = "RUNNING"
    record(state, "stage-start", stage=stage, attempt=st["attempts"])
    save_state(state)
    print(f"stage {stage} attempt {st['attempts']} EXECUTING — run `run` "
          f"to drive the round")


def cmd_run(args) -> None:
    state = load_state()
    stage = state["current_stage"]
    st = state["stages"][stage]
    if st["status"] not in ("EXECUTING", "REWORK"):
        raise RunnerError(f"stage {stage} status {st['status']}: nothing "
                          f"to run (use start-stage)")
    worktree = Path(state["worktree"] or "")
    if not worktree.exists():
        raise RunnerError("product worktree missing; run init-product")
    attempt = st["attempts"]
    d = stage_run_dir(stage, attempt)
    log = d / "session_log.jsonl"
    contract = EPISODE_DIR / STAGE_CONTRACTS[stage]

    prev_review = None
    resume = None
    if st["status"] == "REWORK":
        prev_review = stage_run_dir(stage, attempt - 1) / "review.md"
        _, reset_ctx = parse_review(
            prev_review, stage, attempt - 1, st["candidates"][-1]["sha"])
        if not reset_ctx and st["executor_sessions"]:
            resume = st["executor_sessions"][-1]["session_id"]

    base = head_sha(worktree)
    rep = d / "execution_report.md"
    prompt = executor_prompt(
        stage, attempt, contract=contract, branch=PRODUCT_BRANCH,
        base_sha=base, review=prev_review, marker_req=None,
        marker_flawed=False, report=rep, marker=None,
        resume_note=None if st["status"] == "EXECUTING" else
        "Continue from your previous session context.")
    exe = launch_session(worktree, prompt, resume=resume,
                         timeout_s=SESSION_TIMEOUT_S, log_path=log)
    st["executor_sessions"].append(
        dict(attempt=attempt, session_id=exe.session_id,
             exit_code=exe.exit_code, resumed_from=resume))
    csha = head_sha(worktree)
    if csha == base:
        save_state(state)
        raise RunnerError("executor produced no candidate commit; review "
                          "cannot start (candidate binding requires a "
                          "commit)")
    st["status"] = "CANDIDATE_READY"
    st["candidates"].append(dict(attempt=attempt, sha=csha, base=base,
                                 report=rep.as_posix()))
    record(state, "candidate-ready", stage=stage, attempt=attempt, sha=csha)
    save_state(state)

    rev = d / "review.md"
    rprompt = reviewer_prompt(
        stage, attempt, contract=contract,
        episode_contract=EPISODE_DIR / "EPISODE_PLAN.md",
        candidate_sha=csha, report=rep, review_out=rev,
        reviewer_evidence_dir=d / "reviewer_evidence")
    rev_s = launch_session(worktree, rprompt, resume=None,
                           timeout_s=SESSION_TIMEOUT_S, log_path=log)
    st["reviewer_sessions"].append(
        dict(attempt=attempt, session_id=rev_s.session_id,
             exit_code=rev_s.exit_code))
    save_state(state)
    product_clean(worktree, csha, f"{stage} round-{attempt:02d} review")
    decision, _ = parse_review(rev, stage, attempt, csha)
    st["decisions"].append(dict(attempt=attempt, decision=decision,
                                sha=csha))
    record(state, "review-decision", stage=stage, attempt=attempt,
           decision=decision)
    if decision == "PASS":
        st["status"] = "PASS"
        if stage == "V3":
            state["episode_status"] = "CHECKPOINT_READY"
            record(state, "checkpoint-ready", stage=stage)
        else:
            nxt = STAGES[STAGES.index(stage) + 1]
            state["stages"][nxt]["status"] = "READY"
            state["current_stage"] = nxt
            record(state, "promote", stage=stage, next_stage=nxt)
    elif decision == "CHANGES_REQUESTED":
        if attempt >= 3:
            st["status"] = "HUMAN_REQUIRED"
            state["episode_status"] = "HUMAN_REQUIRED"
            record(state, "attempt-limit", stage=stage, attempts=attempt)
        else:
            st["status"] = "REWORK"
            record(state, "rework", stage=stage,
                   next_attempt=attempt + 1)
    else:
        st["status"] = "HUMAN_REQUIRED"
        state["episode_status"] = "HUMAN_REQUIRED"
        record(state, "human-required", stage=stage)
    save_state(state)
    print(f"[{stage}] decision={decision}; stage status {st['status']}; "
          f"episode={state['episode_status']}")


def cmd_status(args) -> None:
    state = load_state()
    print(json.dumps(
        dict(episode_status=state["episode_status"],
             current_stage=state["current_stage"],
             smoke=state["smoke"]["status"],
             stages={s: dict(status=v["status"], attempts=v["attempts"])
                     for s, v in state["stages"].items()},
             updated_at=state.get("updated_at")), indent=1))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("init-product")
    sub.add_parser("run-smoke")
    p = sub.add_parser("start-stage")
    p.add_argument("stage")
    sub.add_parser("run")
    sub.add_parser("status")
    args = ap.parse_args()
    handlers = dict(init=cmd_init, **{
        "init-product": cmd_init_product, "run-smoke": cmd_run_smoke,
        "start-stage": cmd_start_stage, "run": cmd_run,
        "status": cmd_status})
    handlers[args.cmd](args)


if __name__ == "__main__":
    main()
