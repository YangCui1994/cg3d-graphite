"""Bilateral-imbibition episode runner (A0 bootstrap + R1/R2/R3 rework,
BI-VALIDATION-001).

One GENERIC orchestration engine drives every stage — the harmless A0
smoke mini-episode AND the real V0-V3 stages follow exactly the same
code path (A0 external review finding B2).  Session/provenance patterns
are reused from the V1 Controller (headless zcode.cjs --json envelope
sessionId, --resume executor rework, timeout process-tree kill,
GIT_TERMINAL_PROMPT=0).

Engine guarantees (external reviews: R1 = B1-B8 + H1-H3,
R2 = B9-B13 + H4-H5, R3 = B14-B16):
  B1  rework increments the attempt number and binds to the immediately
      preceding round's review/candidate;
  B2  smoke and real stages share run_round()/run_episode()/publish();
  B3  a round that leaves the source unchanged is a VALIDATION-ONLY
      candidate — the review binds to the unchanged source SHA (no
      meaningless product commits);
  B4  real execution requires the explicit chain
      A0_REVIEW -> (approve-a0 with a PASS review bound to the runner
      commit) -> A0_APPROVED; start-stage/run/run-episode/init-product
      all refuse earlier;
  B5  every session is validated (exit 0, no timeout, non-null session
      id, artifact file freshly written — pre-checked NOT to exist)
      before the round advances; violations stop the round as ERROR
      without advancing state; the pre-review candidate worktree must
      be clean;
  B6  executor/reviewer prompts deliver the control-plane role
      contracts by absolute path (AGENTS.md, EPISODE_PLAN.md,
      EXECUTOR_CONTRACT.md / REVIEWER_CONTRACT.md, Stage Contract) —
      never relying on them existing in the product branch;
  B7  `run-episode` autonomously starts/promotes/reworks V0-V3 and
      stops on HUMAN_REQUIRED / ERROR / V3 CHECKPOINT_READY;
  B8  durable publication (contract snapshot + hash, candidate/report/
      review copies, session provenance, diff stat, attempt history)
      to the control-plane evidence directory with commit + push;
  B9  every publication ALSO pushes the product branch itself (normal
      non-force push; branch and exact SHA verified against the
      round's candidate; remote ref confirmed afterwards) so reviewed
      candidates are reachable from a remote ref, not only from the
      local worktree;
  B10 the stage contract is frozen at stage start into an immutable
      runtime snapshot; executor/reviewer prompts point at the
      snapshot, its hash is re-verified before every session and at
      publication, and the publication copies the frozen bytes (never
      the moving control-plane file; live drift is recorded, not
      followed);
  B11 approve-a0 requires a full 40-hex candidate binding exactly
      equal to the runner commit that produced the smoke — a PASS
      review with no (or short/wrong) binding is rejected;
  B12 the round base is pinned before each executor session; a failed
      executor session that advanced HEAD or left a dirty tree is an
      ORPHAN — the episode stops HUMAN_REQUIRED with the orphan state
      recorded (evidence-only publication), and an executor retry can
      never silently adopt the unreviewed commit as its base
      (base_guard);
  B13 the round phase is explicit and persisted (EXECUTING/REWORK =
      executor pending -> CANDIDATE_READY = candidate frozen, review
      pending); a failed REVIEWER session retries a FRESH reviewer
      against the SAME frozen candidate/report without rerunning the
      executor; a candidate that is no longer intact stops
      HUMAN_REQUIRED;
  H1  existing worktrees are identity-checked (branch, cleanliness,
      expected head) before reuse — ambiguous reuse is refused;
  H2  the reviewer write-restriction guarantee is exactly "persistent
      reviewer product modifications are detected and rejected"
      (post-session HEAD + git-status check).  No stronger sandbox is
      claimed in v0.1;
  H3  the stage contract is frozen at stage start (sha256 recorded in
      state, quoted in both prompts, copied into the publication);
  H4  top-level attach paths (run-smoke, init-product) derive the
      expected worktree HEAD from persisted state and pass it to the
      H1 identity check — a branch-correct, clean, but
      state-inconsistent worktree is refused;
  H5  a persisted ERROR stage is TERMINAL for `run-episode`
      (deterministic stop, never a busy loop); the explicit
      same-attempt retry is the `run` command;
  B14 a decided round is TWO-PHASE: the review decision is persisted
      as PUBLISH_PENDING, product + evidence publication runs FIRST,
      and PASS/promotion/rework is applied only after publication
      succeeded.  A publication failure leaves ERROR/publish_pending
      with NO promotion exposed; recovery (the `run` command, or a
      crash-resume of PUBLISH_PENDING) re-publishes the decided round
      and NEVER reruns an executor/reviewer session for it;
  B15 a VALID executor session that leaves a dirty tree is the same
      kind of pre-review source ambiguity as B12: terminal
      HUMAN_REQUIRED orphan (evidence-only publication — the
      unreviewed product state is never pushed), never a silent
      retry base;
  B16 approve-a0 freezes the APPROVED runner implementation (its git
      blob identity, resolved from the reviewed runner commit);
      every real entry point (init-product / start-stage / run /
      run-episode, including crash continuation) verifies the
      EXECUTING episode_runner.py is identical to the approved blob
      and refuses real execution otherwise (a changed runner requires
      a new A0 smoke + external review); every real stage record
      carries the approved runner identity.

Commands (control checkout root):
  init | run-smoke [--reset] | approve-a0 --review <path>
  | init-product | start-stage <S> | run | run-episode | status

State files (gitignored runtime):
  .agent_runtime/episodes/BI-VALIDATION-001/episode_state.json        (real)
  .agent_runtime/episodes/BI-VALIDATION-001/smoke_state.json          (smoke)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

EPISODE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = EPISODE_DIR.parents[2]
STATE_DIR = REPO_ROOT / ".agent_runtime" / "episodes" / "BI-VALIDATION-001"
STATE_PATH = STATE_DIR / "episode_state.json"
SMOKE_STATE_PATH = STATE_DIR / "smoke_state.json"
EVIDENCE_ROOT = REPO_ROOT / ".agent" / "evidence" / "BI-VALIDATION-001"

EPISODE_ID = "BI-VALIDATION-001"
PRODUCT_BRANCH = "agent-episode/BI-VALIDATION-001"
PRODUCT_BASE = "9ede55c8ef7589b61606e11c033c84d9bcd1de94"
SMOKE_BRANCH = "agent-episode/BI-VALIDATION-001-smoke-r3"
WORKTREE_ROOT = REPO_ROOT.parent / "cg3d-episode-worktrees"
ZCODE = ["node", "C:/Program Files/ZCode/resources/glm/zcode.cjs"]
ZCODE_MODE = "yolo"
SESSION_TIMEOUT_S = 7200
SMOKE_TIMEOUT_S = 1800
DECISIONS = ("PASS", "CHANGES_REQUESTED", "HUMAN_REQUIRED")
SMOKE_TOKEN = "SMOKE-PASS-TOKEN-7f3a"
MAX_ATTEMPTS = 3

CONTROL_DOCS = dict(
    agents=REPO_ROOT / "AGENTS.md",
    plan=EPISODE_DIR / "EPISODE_PLAN.md",
    executor=EPISODE_DIR / "EXECUTOR_CONTRACT.md",
    reviewer=EPISODE_DIR / "REVIEWER_CONTRACT.md",
)


class RunnerError(RuntimeError):
    pass


def utc_now() -> str:
    return (datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            .replace("+00:00", "Z"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------- config
def real_config() -> dict:
    return dict(
        mode="real",
        state_path=STATE_PATH,
        branch=PRODUCT_BRANCH,
        base=PRODUCT_BASE,
        worktree=WORKTREE_ROOT / EPISODE_ID,
        stages=[
            dict(name="V0", contract=EPISODE_DIR / "STAGE_V0_BASELINE.md"),
            dict(name="V1",
                 contract=EPISODE_DIR / "STAGE_V1_DYNAMIC_WETTING.md"),
            dict(name="V2", contract=EPISODE_DIR / "STAGE_V2_BILATERAL.md"),
            dict(name="V3",
                 contract=EPISODE_DIR / "STAGE_V3_BUFFER_SENSITIVITY.md"),
        ],
        evidence_subdir=None,          # per stage name
        run_root=STATE_DIR,
        timeout_s=SESSION_TIMEOUT_S,
    )


def smoke_config() -> dict:
    return dict(
        mode="smoke",
        state_path=SMOKE_STATE_PATH,
        branch=SMOKE_BRANCH,
        base=PRODUCT_BASE,
        worktree=WORKTREE_ROOT / f"{EPISODE_ID}-smoke-r3",
        stages=[
            dict(name="SMOKE-1",
                 contract=EPISODE_DIR / "runner" / "SMOKE_CONTRACT.md",
                 task="marker", planted_defect=True,
                 validation_only=False),
            dict(name="SMOKE-2",
                 contract=EPISODE_DIR / "runner"
                 / "SMOKE_VALIDATION_CONTRACT.md",
                 task="validation-only", validation_only=True),
        ],
        evidence_subdir="A0_SMOKE_R3",
        run_root=STATE_DIR,
        timeout_s=SMOKE_TIMEOUT_S,
    )


# ---------------------------------------------------------------- state
def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    tmp.replace(path)


def load_state(path: Path) -> dict:
    if not path.exists():
        raise RunnerError(f"no episode state at {path}; run init")
    return json.loads(path.read_text(encoding="utf-8"))


def save_state_at(path: Path, state: dict) -> None:
    state["updated_at"] = utc_now()
    _atomic_write_json(path, state)


def fresh_state(cfg: dict, *, episode_id: str) -> dict:
    return dict(
        episode_id=episode_id,
        mode=cfg["mode"],
        branch=cfg["branch"], base=cfg["base"],
        worktree=cfg["worktree"].as_posix(),
        episode_status="PENDING",          # READY once product/worktree ok
        current_stage=cfg["stages"][0]["name"],
        stages={s["name"]: dict(
            status="READY" if i == 0 else "LOCKED", attempts=0,
            executor_sessions=[], reviewer_sessions=[], candidates=[],
            decisions=[], contract_sha256=None, contract_snapshot=None,
            round_bases={}, pending=None) for i, s in
            enumerate(cfg["stages"])},
        runner_commit=None, a0_review=None,
        history=[],
    )


def record(state: dict, event: str, **facts) -> None:
    state["history"].append(dict(event=event, at=utc_now(), **facts))
    print(f"[{utc_now()}] {event} "
          + " ".join(f"{k}={v}" for k, v in facts.items() if v is not None),
          flush=True)


# ------------------------------------------------------------- sessions
def _parse_envelope(stdout: str):
    cands = [stdout.strip(),
             *reversed([ln.strip() for ln in stdout.splitlines()
                        if ln.strip()])]
    for c in cands:
        try:
            v = json.loads(c)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(v, dict):
            return v
    return None


class SessionResult:
    def __init__(self, proc: dict):
        self.__dict__.update(proc)
        self.envelope = _parse_envelope(proc.get("stdout", ""))

    @property
    def session_id(self):
        if not self.envelope:
            return None
        v = self.envelope.get("sessionId")
        return v if isinstance(v, str) and v else None


def _run_process(command, cwd, timeout_s):
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
    """Real headless ZCode session.  Command + verbatim prompt + exit
    code + timing + stdout/stderr tail are appended to log_path — the
    committed prompt record IS the isolation evidence (B2/B6)."""
    command = [*ZCODE, "--cwd", str(worktree), "--mode", ZCODE_MODE,
               "--json"]
    if resume:
        command += ["--resume", resume]
    command += ["-p", prompt]
    started_wall, started = utc_now(), time.monotonic()
    proc, timed_out = _run_process(command, str(worktree), timeout_s)
    result = dict(command=command, prompt=prompt, resume=resume,
                  started_at=started_wall, finished_at=utc_now(),
                  elapsed_s=round(time.monotonic() - started, 3),
                  exit_code=proc.returncode, timed_out=timed_out,
                  stdout=proc.stdout, stderr=proc.stderr[-4000:])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(result, indent=1, ensure_ascii=False) + "\n---\n")
    print(f"[session] exit={result['exit_code']} "
          f"elapsed={result['elapsed_s']}s resume={bool(resume)} "
          f"timed_out={timed_out}", flush=True)
    return SessionResult(result)


def validate_session(res, *, role: str, artifact: Path,
                     artifact_pre_exists: bool, context: str) -> None:
    """B5: a round may only advance past a fully successful session."""
    problems = []
    if res.exit_code != 0:
        problems.append(f"exit_code={res.exit_code}")
    if getattr(res, "timed_out", False):
        problems.append("timed_out")
    if not res.session_id:
        problems.append("missing session id")
    if artifact_pre_exists:
        problems.append(f"stale artifact already present: {artifact.name}")
    elif not artifact.exists():
        problems.append(f"artifact not written: {artifact.name}")
    if problems:
        raise RunnerError(f"{context}: {role} session invalid "
                          f"({'; '.join(problems)})")


# ------------------------------------------------------------------ git
def _git(worktree: Path, *args: str, check: bool = True) -> str:
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    p = subprocess.run(["git", "-C", str(worktree), *args], text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       env=env)
    if check and p.returncode != 0:
        raise RunnerError(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout.strip()


def head_sha(worktree: Path) -> str:
    return _git(worktree, "rev-parse", "HEAD")


def worktree_dirty(worktree: Path) -> list[str]:
    out = _git(worktree, "status", "--porcelain")
    return [ln[3:].strip() for ln in out.splitlines() if ln.strip()]


def product_at(worktree: Path, expected_sha: str, context: str) -> None:
    """H2 (narrowed claim): PERSISTENT product modifications are detected
    and rejected — post-session HEAD + git-status check."""
    sha = head_sha(worktree)
    dirty = worktree_dirty(worktree)
    if sha != expected_sha or dirty:
        raise RunnerError(
            f"{context}: product tree is not exactly the expected commit "
            f"(head={sha[:12]} expected={expected_sha[:12]}, "
            f"dirty={dirty})")


def make_worktree(cfg: dict, *, expected_head: str | None = None) -> Path:
    """Create/attach the episode worktree with H1/H4 identity checks."""
    wt = cfg["worktree"]
    branch = cfg["branch"]
    if wt.exists():
        cur_branch = _git(wt, "rev-parse", "--abbrev-ref", "HEAD")
        dirty = worktree_dirty(wt)
        if cur_branch != branch or dirty:
            raise RunnerError(
                f"refusing ambiguous worktree reuse {wt}: branch="
                f"{cur_branch!r} (want {branch!r}), dirty={dirty}")
        if expected_head is not None and head_sha(wt) != expected_head:
            raise RunnerError(
                f"refusing ambiguous worktree reuse {wt}: head="
                f"{head_sha(wt)[:12]} (state expects "
                f"{expected_head[:12]}); recover explicitly (reset the "
                f"worktree to the expected commit, or dispose of the "
                f"worktree) before reattaching")
        return wt
    parent = wt.parent
    parent.mkdir(parents=True, exist_ok=True)
    _git(REPO_ROOT, "worktree", "add", "-b", branch, str(wt),
         cfg["base"])
    return wt


def _expected_product_head(state: dict, cfg: dict) -> str:
    """H4: the worktree HEAD implied by persisted state — the declared
    base advanced by every started stage's latest (possibly
    validation-only) candidate."""
    head = cfg["base"]
    for s in cfg["stages"]:
        st = state["stages"][s["name"]]
        if st["status"] in ("LOCKED", "READY"):
            continue
        if st.get("candidates"):
            head = st["candidates"][-1]["sha"]
    return head


# --------------------------------------------------- runner identity (B16)
REL_RUNNER = Path(__file__).resolve().relative_to(REPO_ROOT).as_posix()


def _runner_blob_sha(commit: str | None = None) -> str:
    """B16: the git-blob identity of the runner implementation.  With
    `commit`, resolves the committed runner blob (the approved
    content); without, hashes the EXECUTING file the way git would
    (clean-filter/EOL safe, so a CRLF checkout still matches its LF
    blob)."""
    if commit:
        return _git(REPO_ROOT, "rev-parse", f"{commit}:{REL_RUNNER}")
    return _git(REPO_ROOT, "hash-object", str(Path(__file__).resolve()))


def _verify_approved_runner(state: dict) -> None:
    """B16: real execution may only run on the A0-approved runner
    implementation.  Evidence-only commits after approval are fine —
    only the runner FILE content matters."""
    ap = state.get("approved_runner")
    if not ap:
        return                     # no approval recorded: gate elsewhere
    cur = _runner_blob_sha()
    if cur != ap.get("runner_blob"):
        raise RunnerError(
            f"executing episode_runner.py (blob {cur[:12]}) differs "
            f"from the A0-approved implementation (blob "
            f"{(ap.get('runner_blob') or '?')[:12]}, commit "
            f"{str(ap.get('commit', '?'))[:12]}) — a changed runner "
            f"requires a new A0 smoke + external review")


# -------------------------------------------------------------- prompts
def _task_block(cfg_stage: dict, attempt: int) -> str:
    """Smoke stages carry explicit marker tasks; real stages execute the
    Stage Contract itself.  Same engine, different task text (B2)."""
    task = cfg_stage.get("task")
    if task == "marker":
        if attempt == 1 and cfg_stage.get("planted_defect"):
            return (
                f"Round task: write the candidate marker file "
                f"`smoke/marker.md` in your working tree and COMMIT it as "
                f"the round candidate.  As documented in the Stage "
                f"Contract, round 1 intentionally plants the defect: "
                f"write a short marker WITHOUT the required token so the "
                f"reviewer can exercise the failure path. Do not add the "
                f"token in this round.")
        return (
            f"Round task: make `smoke/marker.md` satisfy the Stage "
            f"Contract: it must contain the single required line "
            f"`{SMOKE_TOKEN}` (plus a short description) and COMMIT the "
            f"file as the round candidate.")
    if task == "validation-only":
        return (
            "Round task: VALIDATION-ONLY stage — do NOT create any commit "
            "and do NOT modify any product file. Run no GPU work. Simply "
            "verify (read-only) that `smoke/marker.md` at the current "
            "HEAD contains the required token, and write your execution "
            "report. The candidate for review is the UNCHANGED current "
            "HEAD commit.")
    return (
        "Round task: execute the Stage Contract above with the smallest "
        "coherent change, run the authorized validations, and commit the "
        "candidate to the product branch. If the correct result of this "
        "stage round is NO product change (e.g. a healthy baseline), "
        "leave the tree unchanged — the runner will treat the round as a "
        "validation-only candidate bound to the unchanged source SHA.")


def executor_prompt(state: dict, cfg: dict, cfg_stage: dict, attempt: int,
                    *, base_sha: str, report: Path,
                    prev_review: Path | None) -> str:
    stg = state["stages"][cfg_stage["name"]]
    contract = stg.get("contract_snapshot") \
        or Path(cfg_stage["contract"]).as_posix()
    parts = [
        f"You are the ZCode EXECUTOR for episode {EPISODE_ID}"
        + ("-SMOKE (harmless infrastructure rehearsal)"
           if cfg["mode"] == "smoke" else "")
        + f", stage {cfg_stage['name']}, attempt {attempt}.",
        "Read these control-plane documents FIRST (absolute read-only "
        "paths; they are authoritative even if absent from your working "
        "tree):",
        f"- project guardrails: {CONTROL_DOCS['agents'].as_posix()}",
        f"- Episode Contract: {CONTROL_DOCS['plan'].as_posix()}",
        f"- Executor Contract: {CONTROL_DOCS['executor'].as_posix()}",
        f"- Stage Contract (FROZEN snapshot — this file, not the "
        f"control-plane original, is the contract for this stage): "
        f"{contract} "
        f"(snapshot sha256 {stg['contract_sha256']})",
        f"Product branch: {cfg['branch']} (round base {base_sha[:12]}). "
        f"Work on this branch only. Never merge, never force-push, never "
        f"rewrite history.",
    ]
    if prev_review is not None:
        parts.append(
            f"This is a REWORK round. Read the reviewer findings at "
            f"{prev_review.as_posix()} and address ONLY the requested "
            f"corrections. Do not broaden scope.")
    parts.append(_task_block(cfg_stage, attempt))
    parts += [
        f"Write your execution report to {report.as_posix()} (absolute "
        f"path; plain markdown with: stage/attempt, base SHA, candidate "
        f"SHA (or 'validation-only, unchanged <SHA>' if you correctly "
        f"made no commit), changed files, commands run, exit codes, "
        f"deviations).",
        "Stop after committing the candidate (or deciding validation-"
        "only) and writing the report.",
    ]
    return "\n".join(parts)


def reviewer_prompt(state: dict, cfg: dict, cfg_stage: dict, attempt: int,
                    *, candidate_sha: str, validation_only: bool,
                    report: Path, review_out: Path,
                    evidence_dir: Path) -> str:
    stg = state["stages"][cfg_stage["name"]]
    contract = stg.get("contract_snapshot") \
        or Path(cfg_stage["contract"]).as_posix()
    kind = ("VALIDATION-ONLY candidate: the source is UNCHANGED at this "
            "SHA; there is intentionally no diff. Judge the execution "
            "report, the evidence it references, and read-only "
            "verification of the repository state."
            if validation_only else
            "Inspect the candidate diff itself (git show "
            f"{candidate_sha}); do not trust the report alone.")
    return "\n".join([
        f"You are the independent ZCode REVIEWER for episode "
        f"{EPISODE_ID}"
        + ("-SMOKE (harmless infrastructure rehearsal)"
           if cfg["mode"] == "smoke" else "")
        + f", stage {cfg_stage['name']}, attempt {attempt}. You are a "
        f"fresh session; judge only the frozen candidate below.",
        "Read these control-plane documents FIRST (absolute read-only "
        "paths):",
        f"- project guardrails: {CONTROL_DOCS['agents'].as_posix()}",
        f"- Episode Contract: {CONTROL_DOCS['plan'].as_posix()}",
        f"- Reviewer Contract: {CONTROL_DOCS['reviewer'].as_posix()}",
        f"- Stage Contract (FROZEN snapshot — this file, not the "
        f"control-plane original, is the contract for this stage): "
        f"{contract} "
        f"(snapshot sha256 {stg['contract_sha256']})",
        f"Candidate commit (frozen): {candidate_sha}. Verify with git in "
        f"your working tree that HEAD is exactly this commit; if it is "
        f"not, decide HUMAN_REQUIRED.",
        kind,
        f"Read the executor's execution report at {report.as_posix()}.",
        f"Write your review to {review_out.as_posix()} with FIRST LINES "
        f"exactly like:",
        "```",
        f"stage: {cfg_stage['name']}",
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
        f"{evidence_dir.as_posix()}.",
    ])


# ------------------------------------------------- review parse/validate
def parse_review(review_path: Path, stage: str, attempt: int,
                 candidate_sha: str) -> tuple[str, bool]:
    text = review_path.read_text(encoding="utf-8").replace("\r", "")
    head = text[:600]
    if f"candidate: {candidate_sha}" not in head:
        raise RunnerError(f"review does not bind to candidate "
                          f"{candidate_sha}")
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


# ------------------------------------------------------------ publication
def push_product_branch(cfg: dict, expected_sha: str) -> dict:
    """B9: durable product-branch push.  Verifies the worktree is on the
    expected product branch at the exact reviewed SHA, pushes the branch
    with a normal non-force push, then confirms the remote ref."""
    wt = cfg["worktree"]
    branch = _git(wt, "rev-parse", "--abbrev-ref", "HEAD")
    if branch != cfg["branch"]:
        raise RunnerError(f"product worktree is on branch {branch!r}, "
                          f"expected {cfg['branch']!r}")
    sha = head_sha(wt)
    if sha != expected_sha:
        raise RunnerError(f"product worktree head {sha[:12]} != expected "
                          f"candidate {expected_sha[:12]} — refusing to "
                          f"publish/push")
    _git(wt, "push", "origin", cfg["branch"])          # never forced
    remote = _git(wt, "ls-remote", "origin", f"refs/heads/{cfg['branch']}")
    rsha = remote.split()[0] if remote.split() else None
    if rsha != sha:
        raise RunnerError(f"remote ref {cfg['branch']} resolved to "
                          f"{(rsha or '?')[:12]} after push, expected "
                          f"{sha[:12]}")
    return dict(branch=cfg["branch"], remote_ref=sha, pushed_sha=sha,
                verified_at=utc_now())


def publish_round(state: dict, cfg: dict, cfg_stage: dict, attempt: int,
                  *, control_repo: Path | None = None,
                  push: bool = True, product_push=None) -> Path:
    """B8/B9: durable publication of one round.  Evidence goes to the
    control-plane directory (commit + push when push=True); the PRODUCT
    branch is pushed too (verified non-force push) so the reviewed
    candidate is reachable from a remote ref.  An orphan/evidence-only
    round (state['_pub_mode']) publishes evidence but skips the product
    push.  `control_repo`/`push=False` plus an injectable `product_push`
    let offline tests exercise both paths with no real remote."""
    if product_push is None and push:
        product_push = push_product_branch
    repo = control_repo or REPO_ROOT
    sub = cfg.get("evidence_subdir") or cfg_stage["name"]
    stage_dir = repo / ".agent" / "evidence" / EPISODE_ID / sub / \
        cfg_stage["name"]
    rnd = stage_dir / f"round-{attempt:02d}"
    rnd.mkdir(parents=True, exist_ok=True)
    st = state["stages"][cfg_stage["name"]]
    # B10: publish the FROZEN snapshot bytes, never the moving file
    snap = Path(st["contract_snapshot"]) if st.get("contract_snapshot") \
        else Path(cfg_stage["contract"])
    if st.get("contract_sha256") \
            and sha256_file(snap) != st["contract_sha256"]:
        raise RunnerError("frozen contract snapshot hash mismatch — "
                          "refusing to publish")
    (stage_dir / "contract_snapshot.md").write_text(
        snap.read_text(encoding="utf-8"), encoding="utf-8")
    drift = None
    if sha256_file(Path(cfg_stage["contract"])) != st.get("contract_sha256"):
        drift = ("live control-plane contract differs from the frozen "
                 "snapshot; sessions and this publication used the "
                 "FROZEN version")
    pub_mode = state.pop("_pub_mode", None)
    push_rec = None
    if pub_mode:
        push_rec = dict(skipped=True, reason=pub_mode)
    elif product_push is not None:
        cands = [c for c in st["candidates"] if c["attempt"] == attempt]
        expected = (cands[-1]["sha"] if cands
                    else head_sha(cfg["worktree"]))
        push_rec = product_push(cfg, expected)
    record = dict(
        stage=cfg_stage["name"], attempt=attempt,
        contract_sha256=st["contract_sha256"],
        contract_snapshot=st.get("contract_snapshot"),
        contract_drift=drift,
        branch=cfg["branch"],
        product_push=push_rec,
        pending=st.get("pending"),
        approved_runner=state.get("approved_runner"),
        candidates=st["candidates"], decisions=st["decisions"],
        executor_sessions=st["executor_sessions"],
        reviewer_sessions=st["reviewer_sessions"],
        runner_commit=state.get("runner_commit"),
        episode_status=state["episode_status"],
        published_at=utc_now(),
    )
    run_dir = state.get("_run_dirs", {}).get(cfg_stage["name"], {}).get(
        str(attempt))
    if run_dir:
        for name in ("execution_report.md", "review.md",
                     "session_log.jsonl"):
            f = Path(run_dir) / name
            if f.exists():
                shutil.copyfile(f, rnd / name)
        for cand in st["candidates"]:
            if cand["attempt"] == attempt and not cand.get(
                    "validation_only"):
                (rnd / "diff_stat.txt").write_text(
                    _git(cfg["worktree"], "show", "--stat", "--oneline",
                         cand["sha"]) + "\n", encoding="utf-8")
    (stage_dir / "stage_record.json").write_text(
        json.dumps(record, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8")
    if push:
        staged = _git(repo, "status", "--porcelain", "--",
                      stage_dir.as_posix())
        if staged:
            _git(repo, "add", stage_dir.as_posix())
            decision = (st.get("pending", {}).get("decision")
                        or (st["decisions"][-1]["decision"]
                            if st["decisions"] else "ERROR"))
            _git(repo, "commit", "-m",
                 f"episode({cfg['mode']}): publish {cfg_stage['name']} "
                 f"record (attempt {attempt}, {decision})")
            _git(repo, "push", "origin",
                 _git(repo, "rev-parse", "--abbrev-ref", "HEAD"))
    return stage_dir


# ------------------------------------------------------------ engine core
def _run_dir(cfg: dict, stage: str, attempt: int) -> Path:
    root = Path(cfg.get("run_root", STATE_DIR))
    return root / cfg["mode"] / stage / f"round-{attempt:02d}"


def _contract_snapshot_path(cfg: dict, name: str) -> Path:
    return Path(cfg["run_root"]) / cfg["mode"] / name / \
        "contract_snapshot.md"


def _verify_contract(st: dict, context: str) -> None:
    """B10: the frozen snapshot must still hash to the recorded value
    before any session (or publication) uses it."""
    snap = st.get("contract_snapshot")
    if not snap:
        raise RunnerError(f"{context}: stage contract snapshot not frozen")
    p = Path(snap)
    if not p.exists():
        raise RunnerError(f"{context}: frozen contract snapshot missing "
                          f"at {p}")
    if sha256_file(p) != st.get("contract_sha256"):
        raise RunnerError(f"{context}: frozen contract snapshot hash "
                          f"mismatch at {p} — refusing to continue")


def start_stage(state: dict, cfg: dict, name: str) -> None:
    """READY -> EXECUTING (attempt 1, contract frozen into an immutable
    runtime snapshot — H3/B10)."""
    if name not in state["stages"]:
        raise RunnerError(f"unknown stage {name}")
    names = [s["name"] for s in cfg["stages"]]
    if names.index(name) != names.index(state["current_stage"]):
        raise RunnerError(f"stage {name} not reachable (current "
                          f"{state['current_stage']})")
    st = state["stages"][name]
    if st["status"] != "READY":
        raise RunnerError(f"stage {name} status {st['status']}: cannot "
                          f"start")
    cfg_stage = [s for s in cfg["stages"] if s["name"] == name][0]
    snap = _contract_snapshot_path(cfg, name)
    snap.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(cfg_stage["contract"], snap)
    st["attempts"] = 1
    st["status"] = "EXECUTING"
    st["contract_snapshot"] = snap.as_posix()
    st["contract_sha256"] = sha256_file(snap)
    state["episode_status"] = "RUNNING"
    record(state, "stage-start", stage=name, attempt=1,
           contract_sha256=st["contract_sha256"][:16],
           contract_snapshot=snap.as_posix())


def _orphan_stop(state: dict, cfg: dict, cfg_stage: dict, st: dict,
                 stage_name: str, attempt: int, *, kind: str, base: str,
                 head: str, event: str, save, publisher) -> str:
    """Common terminal path for B12/B13 orphans: HUMAN_REQUIRED, orphan
    recorded, evidence-only publication (the product branch is NOT
    pushed from an ambiguous tree)."""
    st["status"] = "HUMAN_REQUIRED"
    state["episode_status"] = "HUMAN_REQUIRED"
    st["orphan"] = dict(stage=stage_name, attempt=attempt, kind=kind,
                        base=base, head=head)
    record(state, event, stage=stage_name, attempt=attempt,
           base=base[:12], head=head[:12])
    save(state)
    state["_pub_mode"] = "evidence-only"
    publisher(state, cfg, cfg_stage, attempt)
    return "HUMAN_REQUIRED"


def _finish_round(state: dict, cfg: dict, cfg_stage: dict, stage_name: str,
                  attempt: int, *, publisher, save) -> str:
    """B14 second phase: publish FIRST, apply the decision transition
    only after publication succeeded.  Called with the stage in
    PUBLISH_PENDING (decision persisted in st['pending']); on
    publication failure the stage becomes ERROR/publish_pending with
    NO transition applied (the next stage is never exposed), and the
    retry path re-publishes without rerunning any session."""
    st = state["stages"][stage_name]
    pending = st.get("pending") or {}
    decision = pending.get("decision")
    if pending.get("attempt") != attempt or not decision:
        raise RunnerError(f"{stage_name} round-{attempt:02d}: "
                          f"PUBLISH_PENDING without a decision pending "
                          f"for this attempt")
    try:
        publisher(state, cfg, cfg_stage, attempt)
    except Exception as e:              # publication failure must gate
        st["status"] = "ERROR"          # advancement (B14)
        st["error_phase"] = "publish_pending"
        st["error_stage_phase"] = "PUBLISH_PENDING"
        record(state, "publication-failed", stage=stage_name,
               attempt=attempt, decision=decision,
               error=str(e)[:300])
        save(state)
        return "ERROR"
    st["decisions"].append(dict(attempt=attempt, decision=decision,
                                sha=pending["sha"],
                                validation_only=pending[
                                    "validation_only"]))
    for k in ("error_phase", "error_stage_phase", "base_guard",
              "pending"):
        st.pop(k, None)
    outcome = decision
    if decision == "PASS":
        st["status"] = "PASS"
        names = [s["name"] for s in cfg["stages"]]
        if names.index(stage_name) == len(names) - 1:
            state["episode_status"] = "CHECKPOINT_READY"
            record(state, "checkpoint-ready", stage=stage_name)
        else:
            nxt = names[names.index(stage_name) + 1]
            state["stages"][nxt]["status"] = "READY"
            state["current_stage"] = nxt
            record(state, "promote", stage=stage_name, next_stage=nxt)
    elif decision == "CHANGES_REQUESTED":
        if st["attempts"] >= MAX_ATTEMPTS:
            st["status"] = "HUMAN_REQUIRED"
            state["episode_status"] = "HUMAN_REQUIRED"
            outcome = "HUMAN_REQUIRED"
            record(state, "attempt-limit", stage=stage_name,
                   attempts=st["attempts"])
        else:
            st["attempts"] += 1            # B1: rework = NEW attempt no.
            st["status"] = "REWORK"
            record(state, "rework", stage=stage_name,
                   next_attempt=st["attempts"])
    else:
        st["status"] = "HUMAN_REQUIRED"
        state["episode_status"] = "HUMAN_REQUIRED"
        record(state, "human-required", stage=stage_name)
    save(state)
    return outcome


def run_round(state: dict, cfg: dict, stage_name: str, *,
              launcher=launch_session, publisher=publish_round,
              save=None) -> str:
    """Drive ONE attempt of a stage through the generic path.  Returns
    the round outcome: PASS / CHANGES_REQUESTED / HUMAN_REQUIRED /
    ERROR.  Session failures never advance the round (B5); a failed
    session that touched the source is a terminal orphan (B12); a
    failed reviewer retries on the frozen candidate (B13)."""
    save = save or (lambda s: save_state_at(cfg["state_path"], s))
    cfg_stage = [s for s in cfg["stages"] if s["name"] == stage_name][0]
    st = state["stages"][stage_name]
    attempt = st["attempts"]                       # B1: per-round number
    d = _run_dir(cfg, stage_name, attempt)
    log = d / "session_log.jsonl"

    if st["status"] == "ERROR":
        # explicit retry of the same attempt (recovery after H5's
        # deterministic stop: the `run` command)
        stage_phase = st.pop("error_stage_phase", "EXECUTING")
        round_phase = st.pop("error_phase", "executor_pending")
        if round_phase == "publish_pending":
            # B14: the round was DECIDED but its publication failed —
            # restore the publish-pending phase (no session rerun)
            st["status"] = "PUBLISH_PENDING"
        elif round_phase == "review_pending":
            # B13: candidate already frozen — restore review-pending and
            # drop any stale/partial review (it is never parsed)
            st["status"] = "CANDIDATE_READY"
            (d / "review.md").unlink(missing_ok=True)
        else:
            st["status"] = stage_phase
            for name in ("execution_report.md", "review.md"):
                (d / name).unlink(missing_ok=True)
    if st["status"] not in ("EXECUTING", "REWORK", "CANDIDATE_READY",
                            "PUBLISH_PENDING"):
        raise RunnerError(f"stage {stage_name} status {st['status']}: "
                          f"use start-stage / run-episode")

    if st["status"] == "PUBLISH_PENDING":
        # B14 recovery: a decided round whose publication failed (or
        # whose publisher crashed).  Re-validate the frozen decision,
        # re-publish, and only then apply the transition.  No executor
        # or reviewer session is ever rerun for a decided round.
        p = st.get("pending") or {}
        rev = d / "review.md"
        problems = []
        if p.get("attempt") != attempt or not p.get("decision"):
            problems.append("no decision pending for this attempt")
        elif not st["candidates"] \
                or st["candidates"][-1]["attempt"] != attempt \
                or p.get("sha") != st["candidates"][-1]["sha"]:
            problems.append("pending decision does not bind to this "
                            "attempt's candidate")
        elif not rev.exists():
            problems.append("review.md missing")
        else:
            try:
                decision, _ = parse_review(rev, stage_name, attempt,
                                           p["sha"])
            except RunnerError as e:
                problems.append(f"review unparseable: {e}")
            else:
                if decision != p["decision"]:
                    problems.append(f"review now decides {decision} "
                                    f"(pending {p['decision']})")
        if problems:
            return _orphan_stop(
                state, cfg, cfg_stage, st, stage_name, attempt,
                kind="publish-pending-ambiguous",
                base=p.get("sha", "?"), head=head_sha(cfg["worktree"]),
                event="publish-pending-ambiguous",
                save=save, publisher=publisher)
        return _finish_round(state, cfg, cfg_stage, stage_name, attempt,
                             publisher=publisher, save=save)

    # ------------------------------------------- executor part (B12)
    if st["status"] in ("EXECUTING", "REWORK"):
        phase_at_entry = st["status"]
        prev_review = None
        resume = None
        if st["status"] == "REWORK":
            prev_review = _run_dir(cfg, stage_name, attempt - 1) / \
                "review.md"
            if not prev_review.exists():
                raise RunnerError(f"rework round {attempt} cannot find "
                                  f"the immediately preceding review "
                                  f"{prev_review}")
            _, reset_ctx = parse_review(prev_review, stage_name,
                                        attempt - 1,
                                        st["candidates"][-1]["sha"])
            if not reset_ctx and st["executor_sessions"]:
                resume = st["executor_sessions"][-1]["session_id"]

        # B12: pin this executor pass to a round base.  After a FAILED
        # executor session the guard demands the tree be exactly back
        # at that base — an unreviewed commit is never adopted silently
        guard = st.pop("base_guard", None)
        cur = head_sha(cfg["worktree"])
        if guard is not None and cur != guard:
            return _orphan_stop(
                state, cfg, cfg_stage, st, stage_name, attempt,
                kind="worktree-drift-since-failed-session", base=guard,
                head=cur, event="worktree-drifted-since-failed-session",
                save=save, publisher=publisher)
        base = cur
        st.setdefault("round_bases", {})[str(attempt)] = base
        save(state)
        _verify_contract(st, f"{stage_name} round-{attempt:02d} executor")

        rep = d / "execution_report.md"
        eprompt = executor_prompt(state, cfg, cfg_stage, attempt,
                                  base_sha=base, report=rep,
                                  prev_review=prev_review)
        rep_pre = rep.exists()
        exe = launcher(cfg["worktree"], eprompt, resume=resume,
                       timeout_s=cfg["timeout_s"], log_path=log)
        st["executor_sessions"].append(
            dict(attempt=attempt, session_id=exe.session_id,
                 exit_code=exe.exit_code, timed_out=exe.timed_out,
                 resumed_from=resume))
        try:
            validate_session(exe, role="executor", artifact=rep,
                             artifact_pre_exists=rep_pre,
                             context=f"{stage_name} round-{attempt:02d} "
                                     f"executor")
        except RunnerError as e:
            cur = head_sha(cfg["worktree"])
            dirty = worktree_dirty(cfg["worktree"])
            if cur != base or dirty:
                # B12 orphan: the failed session left unreviewed source
                # changes — terminal, never silently reused as a base
                st["orphan_dirty"] = dirty
                return _orphan_stop(
                    state, cfg, cfg_stage, st, stage_name, attempt,
                    kind="failed-session-source-change", base=base,
                    head=cur,
                    event="orphan-after-failed-executor-session",
                    save=save, publisher=publisher)
            st["base_guard"] = base
            st["error_phase"] = "executor_pending"
            st["error_stage_phase"] = phase_at_entry
            st["status"] = "ERROR"
            record(state, "executor-session-invalid", stage=stage_name,
                   attempt=attempt, error=str(e))
            save(state)
            publisher(state, cfg, cfg_stage, attempt)
            return "ERROR"
        csha = head_sha(cfg["worktree"])
        if worktree_dirty(cfg["worktree"]):
            # B15: a VALID session that left the tree dirty is pre-review
            # source ambiguity — same terminal treatment as a B12
            # orphan.  Never a silent retry base; the unreviewed product
            # state is never pushed (evidence-only publication).
            st["orphan_dirty"] = worktree_dirty(cfg["worktree"])
            return _orphan_stop(
                state, cfg, cfg_stage, st, stage_name, attempt,
                kind="dirty-worktree-before-review", base=base,
                head=csha, event="orphan-dirty-worktree-before-review",
                save=save, publisher=publisher)
        validation_only = (csha == base)
        if validation_only and cfg_stage.get("validation_only") is False:
            # head == base and tree clean: unambiguous, retryable
            st["error_phase"] = "executor_pending"
            st["error_stage_phase"] = phase_at_entry
            st["status"] = "ERROR"
            record(state, "no-candidate-where-commit-required",
                   stage=stage_name, attempt=attempt)
            save(state)
            publisher(state, cfg, cfg_stage, attempt)
            return "ERROR"
        st["status"] = "CANDIDATE_READY"            # B13: review pending
        st["candidates"].append(
            dict(attempt=attempt, sha=csha, base=base,
                 validation_only=validation_only))
        state.setdefault("_run_dirs", {}).setdefault(stage_name, {})[
            str(attempt)] = str(d)
        record(state, "candidate-ready", stage=stage_name, attempt=attempt,
               sha=csha, validation_only=validation_only)
        save(state)

    # ------------------------------------------- reviewer part (B13)
    cand = st["candidates"][-1]
    if cand["attempt"] != attempt:
        raise RunnerError(f"internal: last candidate is from attempt "
                          f"{cand['attempt']}, round is {attempt}")
    csha = cand["sha"]
    validation_only = cand["validation_only"]
    rep = d / "execution_report.md"
    cur = head_sha(cfg["worktree"])
    if cur != csha or worktree_dirty(cfg["worktree"]) or not rep.exists():
        return _orphan_stop(
            state, cfg, cfg_stage, st, stage_name, attempt,
            kind="candidate-not-intact", base=cand["base"], head=cur,
            event="candidate-not-intact-before-review",
            save=save, publisher=publisher)
    rev = d / "review.md"
    rev.unlink(missing_ok=True)     # stale/partial reviews are never parsed
    _verify_contract(st, f"{stage_name} round-{attempt:02d} reviewer")
    rprompt = reviewer_prompt(state, cfg, cfg_stage, attempt,
                              candidate_sha=csha,
                              validation_only=validation_only, report=rep,
                              review_out=rev,
                              evidence_dir=d / "reviewer_evidence")
    rev_s = launcher(cfg["worktree"], rprompt, resume=None,   # ALWAYS fresh
                     timeout_s=cfg["timeout_s"], log_path=log)
    st["reviewer_sessions"].append(
        dict(attempt=attempt, session_id=rev_s.session_id,
             exit_code=rev_s.exit_code, timed_out=rev_s.timed_out,
             resumed_from=None))
    try:
        validate_session(rev_s, role="reviewer", artifact=rev,
                         artifact_pre_exists=False,
                         context=f"{stage_name} round-{attempt:02d} "
                                 f"reviewer")
    except RunnerError as e:
        # B13: candidate provenance intact -> retry a FRESH reviewer on
        # the SAME frozen candidate next `run`; product no longer
        # intact -> terminal orphan
        cur = head_sha(cfg["worktree"])
        if cur == csha and not worktree_dirty(cfg["worktree"]):
            st["error_phase"] = "review_pending"
            st["error_stage_phase"] = "CANDIDATE_READY"
            st["status"] = "ERROR"
            record(state, "review-session-invalid", stage=stage_name,
                   attempt=attempt, error=str(e))
            save(state)
            publisher(state, cfg, cfg_stage, attempt)
            return "ERROR"
        return _orphan_stop(
            state, cfg, cfg_stage, st, stage_name, attempt,
            kind="reviewer-invalid-and-tree-moved", base=csha, head=cur,
            event="orphan-reviewer-invalid-tree-moved",
            save=save, publisher=publisher)
    try:
        product_at(cfg["worktree"], csha,
                   f"{stage_name} round-{attempt:02d} review")
    except RunnerError as e:
        # H2: a persistent reviewer modification of the product tree
        return _orphan_stop(
            state, cfg, cfg_stage, st, stage_name, attempt,
            kind="reviewer-modified-product", base=csha,
            head=head_sha(cfg["worktree"]),
            event="reviewer-modified-product", save=save,
            publisher=publisher)
    decision, _ = parse_review(rev, stage_name, attempt, csha)
    record(state, "review-decision", stage=stage_name, attempt=attempt,
           decision=decision)
    # B14 two-phase: persist the DECIDED state first, publish product +
    # evidence, and apply PASS/promotion/rework only after publication
    # succeeded.  A failure inside _finish_round leaves
    # ERROR/publish_pending with no promotion exposed.
    st["pending"] = dict(attempt=attempt, decision=decision, sha=csha,
                         validation_only=validation_only)
    st["status"] = "PUBLISH_PENDING"
    save(state)
    return _finish_round(state, cfg, cfg_stage, stage_name, attempt,
                         publisher=publisher, save=save)


def run_episode(state: dict, cfg: dict, *, launcher=launch_session,
                publisher=publish_round,
                save=None) -> str:
    """B7: autonomous loop — starts READY stages, drives rounds, bounded
    rework, auto-promotion; stops on HUMAN_REQUIRED / ERROR /
    CHECKPOINT_READY.  H5: a persisted ERROR stage is TERMINAL for the
    loop (deterministic stop, never a busy loop; explicit same-attempt
    retry = the `run` command).  Crash-resumable via persisted state
    (a persisted CANDIDATE_READY round resumes with the reviewer
    only)."""
    save = save or (lambda s: save_state_at(cfg["state_path"], s))
    if state["episode_status"] in ("HUMAN_REQUIRED", "CHECKPOINT_READY"):
        return state["episode_status"]
    if cfg["mode"] == "real":
        if state["episode_status"] not in ("A0_APPROVED", "RUNNING"):
            raise RunnerError(
                f"episode_status {state['episode_status']} does not "
                f"authorize the real loop (approve-a0 with a PASS "
                f"external review required)")
        _verify_approved_runner(state)          # B16, incl. continuation
    while True:
        stage = state["current_stage"]
        st = state["stages"][stage]
        if st["status"] == "READY":
            start_stage(state, cfg, stage)
            save(state)
        elif st["status"] in ("EXECUTING", "REWORK", "CANDIDATE_READY",
                              "PUBLISH_PENDING"):
            outcome = run_round(state, cfg, stage, launcher=launcher,
                                publisher=publisher, save=save)
            if outcome == "ERROR":
                record(state, "episode-stopped-error", stage=stage)
                save(state)
                return "ERROR"
            if state["episode_status"] in ("HUMAN_REQUIRED",
                                           "CHECKPOINT_READY"):
                return state["episode_status"]
            continue
        elif st["status"] == "ERROR":
            # H5: no automatic transition exists from ERROR — terminate
            # deterministically instead of spinning.  Recover by
            # inspecting state and retrying the same attempt with `run`.
            record(state, "episode-stopped-error-persisted", stage=stage)
            save(state)
            return "ERROR"
        else:
            raise RunnerError(f"stage {stage} status {st['status']} has "
                              f"no loop transition")
        if state["episode_status"] in ("HUMAN_REQUIRED",
                                       "CHECKPOINT_READY"):
            return state["episode_status"]


# ------------------------------------------------------------ top level
def cmd_init(args) -> None:
    if STATE_PATH.exists():
        print("state exists:", STATE_PATH)
        return
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    save_state_at(STATE_PATH, fresh_state(real_config(),
                                          episode_id=EPISODE_ID))
    print("initialized", STATE_PATH)


def _record_runner_commit(state: dict, cfg: dict) -> None:
    state["runner_commit"] = head_sha(REPO_ROOT)


def cmd_run_smoke(args) -> None:
    main = load_state(STATE_PATH)
    cfg = smoke_config()
    if SMOKE_STATE_PATH.exists():
        if not args.reset:
            raise RunnerError(f"smoke state exists ({SMOKE_STATE_PATH}); "
                              f"use --reset to archive it and rerun")
        bak = SMOKE_STATE_PATH.with_name(
            "smoke_state_archived_" + utc_now().replace(":", "")
            .replace("-", "") + ".json")
        SMOKE_STATE_PATH.replace(bak)
        print("archived previous smoke state ->", bak.name)
    runtime = STATE_DIR / cfg["mode"]        # rounds/contract snapshots
    if runtime.exists():
        # a fresh smoke must not inherit round artifacts from an older
        # run: stale execution_report.md files would flag every new
        # executor session as invalid (observed live on 2026-09-23)
        bak = runtime.with_name(
            cfg["mode"] + "_runtime_archived_"
            + utc_now().replace(":", "").replace("-", ""))
        runtime.replace(bak)
        print("archived previous smoke runtime ->", bak.name)
    state = fresh_state(cfg, episode_id=f"{EPISODE_ID}-SMOKE")
    state["episode_status"] = "RUNNING"      # smoke needs no A0 gate
    _record_runner_commit(state, cfg)
    # H4: a fresh smoke starts from the declared base — an existing
    # worktree at any other commit is refused
    wt = make_worktree(cfg, expected_head=cfg["base"])
    save_state_at(SMOKE_STATE_PATH, state)
    outcome = run_episode(state, cfg)
    if outcome != "CHECKPOINT_READY":
        raise RunnerError(f"smoke did not reach CHECKPOINT_READY "
                          f"(outcome={outcome}); inspect "
                          f"{SMOKE_STATE_PATH}")
    main["smoke"] = dict(status="PASS", branch=cfg["branch"],
                         runner_commit=state["runner_commit"],
                         stages={k: dict(status=v["status"],
                                         attempts=v["attempts"])
                                 for k, v in state["stages"].items()})
    main["episode_status"] = "A0_REVIEW"
    record(main, "smoke-complete", runner_commit=state["runner_commit"])
    save_state_at(STATE_PATH, main)
    print("SMOKE episode CHECKPOINT_READY — main state A0_REVIEW; "
          "evidence published under", EVIDENCE_ROOT / cfg["evidence_subdir"])


def approve_a0_from_text(state: dict, text: str,
                         review_path: str) -> None:
    """B4/B11: flip A0_REVIEW -> A0_APPROVED only from a PASS external
    review carrying a FULL 40-hex candidate binding exactly equal to
    the runner commit that produced the smoke."""
    if state["episode_status"] != "A0_REVIEW":
        raise RunnerError(f"episode_status {state['episode_status']}: "
                          f"A0 approval applies to A0_REVIEW only")
    runner_commit = state.get("smoke", {}).get("runner_commit")
    if not runner_commit:
        raise RunnerError("state has no smoke runner_commit to bind the "
                          "A0 approval to")
    text = text.replace("\r", "")
    m = re.search(r"^candidate:?\s*([0-9a-f]{40})\b", text, re.M) or \
        re.search(r"reviewed candidate:?\s*\*?\*?`?([0-9a-f]{40})",
                  text, re.I | re.M)
    dm = re.search(r"^Decision:?\s*(\S+)", text, re.M)
    if not dm or dm.group(1).strip().upper().rstrip(".") != "PASS":
        raise RunnerError("referenced review is not a PASS decision")
    if m is None:
        raise RunnerError("referenced review carries no 40-hex candidate "
                          "binding (required for A0 approval)")
    cand = m.group(1)
    if cand != runner_commit:
        raise RunnerError(f"review binds to candidate {cand[:12]} but the "
                          f"smoke ran runner commit "
                          f"{runner_commit[:12]}")
    # B16: freeze the APPROVED runner implementation — the committed
    # runner blob at the reviewed commit (EOL-safe git identity).  If
    # that commit is unavailable in this checkout (offline harnesses),
    # pin the executing file's blob and record that fact.
    try:
        runner_blob = _runner_blob_sha(runner_commit)
        blob_src = "commit"
    except RunnerError:
        runner_blob = _runner_blob_sha()
        blob_src = "executing-file"
    state["approved_runner"] = dict(
        commit=runner_commit, runner_blob=runner_blob,
        runner_blob_source=blob_src, review=review_path,
        approved_at=utc_now())
    state["episode_status"] = "A0_APPROVED"
    state["a0_review"] = dict(path=review_path, candidate=cand,
                              decision="PASS")
    record(state, "a0-approved", review=review_path)


def cmd_approve_a0(args) -> None:
    main = load_state(STATE_PATH)
    review = Path(args.review)
    if not review.is_absolute():
        review = (REPO_ROOT / review).resolve()
    approve_a0_from_text(main, review.read_text(encoding="utf-8"),
                         review.as_posix())
    save_state_at(STATE_PATH, main)
    print("A0_APPROVED (external review:", review.as_posix(), ")")


def _require_real_ready(state: dict) -> None:
    if state["episode_status"] not in ("A0_APPROVED", "RUNNING"):
        raise RunnerError(
            f"episode_status {state['episode_status']}: real execution "
            f"requires explicit A0 approval (approve-a0 with a PASS "
            f"external review bound to the runner commit)")
    _verify_approved_runner(state)      # B16: approved implementation only


def cmd_init_product(args) -> None:
    main = load_state(STATE_PATH)
    _require_real_ready(main)
    cfg = real_config()
    # H4: derive the expected HEAD from persisted state
    wt = make_worktree(cfg, expected_head=_expected_product_head(main, cfg))
    main["worktree"] = wt.as_posix()
    record(main, "product-initialized", branch=cfg["branch"])
    save_state_at(STATE_PATH, main)
    print("product worktree ready:", wt)


def cmd_start_stage(args) -> None:
    main = load_state(STATE_PATH)
    _require_real_ready(main)
    cfg = real_config()
    if not main.get("worktree"):
        cmd_init_product(argparse.Namespace())
        main = load_state(STATE_PATH)
    start_stage(main, cfg, args.stage.upper())
    save_state_at(STATE_PATH, main)
    print(f"stage {args.stage.upper()} EXECUTING — run `run-episode` to "
          f"drive autonomously")


def cmd_run(args) -> None:
    main = load_state(STATE_PATH)
    cfg = real_config()
    _require_real_ready(main)       # B16 + status gate on the retry path
    outcome = run_round(main, cfg, main["current_stage"])
    print(f"round outcome: {outcome}")


def cmd_run_episode(args) -> None:
    main = load_state(STATE_PATH)
    cfg = real_config()
    if not main.get("worktree"):
        _require_real_ready(main)
        cmd_init_product(argparse.Namespace())
        main = load_state(STATE_PATH)
    else:
        _require_real_ready(main)     # B16 also on plain continuation
    outcome = run_episode(main, cfg)
    print(f"episode loop ended: {outcome}")


def cmd_status(args) -> None:
    main = load_state(STATE_PATH)
    out = dict(episode_status=main["episode_status"],
               current_stage=main["current_stage"],
               smoke=main.get("smoke", {}).get("status", "n/a"),
               stages={k: dict(
                   status=v["status"], attempts=v["attempts"],
                   **({"orphan": v["orphan"]} if v.get("orphan") else {}))
                   for k, v in main["stages"].items()})
    if SMOKE_STATE_PATH.exists():
        sm = load_state(SMOKE_STATE_PATH)
        out["smoke_episode"] = dict(
            status=sm["episode_status"],
            stages={k: dict(status=v["status"], attempts=v["attempts"])
                    for k, v in sm["stages"].items()})
    print(json.dumps(out, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    p = sub.add_parser("run-smoke")
    p.add_argument("--reset", action="store_true")
    p = sub.add_parser("approve-a0")
    p.add_argument("--review", required=True)
    sub.add_parser("init-product")
    p = sub.add_parser("start-stage")
    p.add_argument("stage")
    sub.add_parser("run")
    sub.add_parser("run-episode")
    sub.add_parser("status")
    args = ap.parse_args()
    handlers = dict(init=cmd_init, **{
        "run-smoke": cmd_run_smoke, "approve-a0": cmd_approve_a0,
        "init-product": cmd_init_product, "start-stage": cmd_start_stage,
        "run": cmd_run, "run-episode": cmd_run_episode,
        "status": cmd_status})
    handlers[args.cmd](args)


if __name__ == "__main__":
    main()
