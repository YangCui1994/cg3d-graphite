#!/usr/bin/env python3
"""Minimal Git-backed controller for Agent Development System V1.

The controller is deliberately mechanical. It claims READY work, invokes a
headless executor in a task worktree, captures independent Git/process facts,
and publishes the result for human/ChatGPT review. It never decides PASS and
never merges a candidate.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


STATE_PATH = Path(".agent/state.json")
TASKS_ROOT = Path(".agent/tasks")
RUNTIME_DIR = Path(".agent_runtime")
HARD_MAX_ROUNDS = 3
SCHEMA_VERSION = "v1-alpha"
READY = "READY_FOR_EXECUTION"
TERMINAL_OR_WAITING_STATUSES = {
    "DRAFT",
    "RUNNING",
    "AWAITING_REVIEW",
    "CLOSED",
    "HUMAN_REQUIRED",
    "STOPPED_MAX_ROUNDS",
    "ERROR",
}
ALL_STATUSES = TERMINAL_OR_WAITING_STATUSES | {READY}
TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


class ControllerError(RuntimeError):
    """A deterministic controller or repository precondition failed."""


@dataclass(frozen=True)
class Config:
    repository_path: Path
    remote: str
    control_branch: str
    task_branch_prefix: str
    worktree_root: Path
    poll_interval_seconds: float
    worker_id: str
    git_author_name: str
    git_author_email: str
    zcode_command: tuple[str, ...]
    zcode_mode: str
    zcode_timeout_seconds: float
    zcode_extra_args: tuple[str, ...]

    @classmethod
    def load(cls, path: Path) -> "Config":
        raw = json.loads(path.read_text(encoding="utf-8"))
        base = path.resolve().parent

        def resolve(value: str) -> Path:
            candidate = Path(value)
            return candidate.resolve() if candidate.is_absolute() else (base / candidate).resolve()

        zcode = raw["zcode"]
        command = tuple(str(part) for part in zcode["command"])
        if not command:
            raise ControllerError("zcode.command must contain at least one argument")

        config = cls(
            repository_path=resolve(raw["repository_path"]),
            remote=str(raw.get("remote", "origin")),
            control_branch=str(raw["control_branch"]),
            task_branch_prefix=str(raw.get("task_branch_prefix", "agent-task/")),
            worktree_root=resolve(raw["worktree_root"]),
            poll_interval_seconds=float(raw.get("poll_interval_seconds", 15)),
            worker_id=str(raw["worker_id"]),
            git_author_name=str(raw.get("git_author_name", "ADS Controller")),
            git_author_email=str(raw.get("git_author_email", "ads-controller@local.invalid")),
            zcode_command=command,
            zcode_mode=str(zcode.get("mode", "yolo")),
            zcode_timeout_seconds=float(zcode.get("timeout_seconds", 7200)),
            zcode_extra_args=tuple(str(part) for part in zcode.get("extra_args", [])),
        )
        if config.poll_interval_seconds <= 0:
            raise ControllerError("poll_interval_seconds must be positive")
        if config.zcode_timeout_seconds <= 0:
            raise ControllerError("zcode.timeout_seconds must be positive")
        if not config.worker_id.strip():
            raise ControllerError("worker_id must not be empty")
        return config


@dataclass
class ProcessResult:
    command: list[str]
    started_at: str
    finished_at: str
    elapsed_seconds: float
    exit_code: int | None
    timed_out: bool
    terminated_after_timeout: bool
    stdout: str
    stderr: str
    envelope: dict[str, Any] | None

    @property
    def session_id(self) -> str | None:
        if not self.envelope:
            return None
        value = self.envelope.get("sessionId")
        return value if isinstance(value, str) and value else None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def task_dir(state: dict[str, Any]) -> Path:
    return TASKS_ROOT / str(state["task_id"]) / f"round-{int(state['round']):02d}"


def task_file(state: dict[str, Any]) -> Path:
    return task_dir(state) / "TASK.md"


def task_branch(state: dict[str, Any], prefix: str) -> str:
    return f"{prefix}{state['task_id']}"


def parse_allowed_paths(task_text: str) -> tuple[str, ...]:
    """Read exact path entries from TASK.md's `### Allowed` bullet list."""
    in_allowed = False
    paths: list[str] = []
    for line in task_text.splitlines():
        stripped = line.strip()
        if stripped == "### Allowed":
            in_allowed = True
            continue
        if in_allowed and stripped.startswith("#"):
            break
        if not in_allowed:
            continue
        match = re.fullmatch(r"-\s+`([^`]+)`(?:\s+.*)?", stripped)
        if not match:
            continue
        value = match.group(1).replace("\\", "/").strip()
        if not value or value.startswith("/") or ".." in Path(value).parts:
            raise ControllerError(f"invalid allowed path in TASK.md: {value!r}")
        paths.append(value)
    if not paths:
        raise ControllerError("TASK.md must contain backtick paths under `### Allowed`")
    return tuple(paths)


def path_is_allowed(path: str, allowed_paths: tuple[str, ...]) -> bool:
    normalized = path.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    for allowed in allowed_paths:
        candidate = allowed[2:] if allowed.startswith("./") else allowed
        if candidate == ".":
            return True
        if any(character in candidate for character in "*?["):
            if fnmatch.fnmatchcase(normalized, candidate):
                return True
            continue
        prefix = candidate.rstrip("/")
        if normalized == prefix or normalized.startswith(prefix + "/"):
            return True
    return False


def validate_state(state: dict[str, Any], *, operational: bool = False) -> None:
    required = {
        "schema_version",
        "task_id",
        "round",
        "max_rounds",
        "revision",
        "status",
        "zcode_session_id",
        "candidate_commit",
        "worker",
        "updated_at",
        "last_error",
    }
    missing = sorted(required - state.keys())
    if missing:
        raise ControllerError(f"state.json is missing fields: {', '.join(missing)}")
    if state["schema_version"] != SCHEMA_VERSION:
        raise ControllerError(f"unsupported schema_version: {state['schema_version']!r}")
    if state["status"] not in ALL_STATUSES:
        raise ControllerError(f"unsupported status: {state['status']!r}")
    if not isinstance(state["revision"], int) or state["revision"] < 0:
        raise ControllerError("revision must be a non-negative integer")
    if not isinstance(state["max_rounds"], int) or not 1 <= state["max_rounds"] <= HARD_MAX_ROUNDS:
        raise ControllerError(f"max_rounds must be between 1 and {HARD_MAX_ROUNDS}")
    if not isinstance(state["round"], int) or state["round"] < 0:
        raise ControllerError("round must be a non-negative integer")
    for field in ("zcode_session_id", "candidate_commit", "worker", "updated_at", "last_error"):
        if state[field] is not None and not isinstance(state[field], str):
            raise ControllerError(f"{field} must be a string or null")

    if operational or state["status"] != "DRAFT":
        if not isinstance(state["task_id"], str) or not TASK_ID_RE.fullmatch(state["task_id"]):
            raise ControllerError("task_id must use only letters, digits, dot, underscore, and hyphen")
        if state["round"] < 1:
            raise ControllerError("an active task must have round >= 1")
    elif state["task_id"] is not None:
        if not isinstance(state["task_id"], str) or not TASK_ID_RE.fullmatch(state["task_id"]):
            raise ControllerError("draft task_id has an invalid format")


class Controller:
    def __init__(self, config: Config):
        self.config = config
        self.repo = config.repository_path
        self.local_run_root = self.repo / RUNTIME_DIR / "controller-runs"

    def log(self, message: str) -> None:
        print(f"[{utc_now()}] {message}", flush=True)

    def _run(
        self,
        command: Iterable[str],
        *,
        cwd: Path | None = None,
        check: bool = True,
        timeout: float | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        result = subprocess.run(
            list(command),
            cwd=str(cwd or self.repo),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env=env,
        )
        if check and result.returncode != 0:
            rendered = " ".join(command)
            detail = (result.stderr or result.stdout).strip()
            raise ControllerError(f"command failed ({result.returncode}): {rendered}\n{detail}")
        return result

    def _git(self, *args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
        return self._run(["git", *args], cwd=cwd, check=check)

    def _commit(self, message: str, *, cwd: Path, paths: Iterable[Path] | None = None) -> bool:
        if paths is None:
            self._git("add", "-A", cwd=cwd)
        else:
            path_args = [str(path).replace(os.sep, "/") for path in paths]
            self._git("add", "--", *path_args, cwd=cwd)
        staged = self._git("diff", "--cached", "--quiet", cwd=cwd, check=False)
        if staged.returncode == 0:
            return False
        if staged.returncode != 1:
            raise ControllerError("unable to inspect staged changes")
        self._git(
            "-c",
            f"user.name={self.config.git_author_name}",
            "-c",
            f"user.email={self.config.git_author_email}",
            "commit",
            "-m",
            message,
            cwd=cwd,
        )
        return True

    def _ensure_repo(self) -> None:
        if not (self.repo / ".git").exists():
            raise ControllerError(f"repository_path is not a Git clone: {self.repo}")
        current = self._git("branch", "--show-current").stdout.strip()
        if current != self.config.control_branch:
            raise ControllerError(
                f"controller clone must have {self.config.control_branch!r} checked out; current branch is {current!r}"
            )

    def _fetch_control(self) -> tuple[str, dict[str, Any]]:
        self._git("fetch", "--quiet", self.config.remote, self.config.control_branch)
        remote_ref = f"refs/remotes/{self.config.remote}/{self.config.control_branch}"
        sha = self._git("rev-parse", remote_ref).stdout.strip()
        raw = self._git("show", f"{sha}:{STATE_PATH.as_posix()}").stdout
        state = json.loads(raw)
        validate_state(state)
        return sha, state

    def _sync_control_to(self, sha: str) -> None:
        dirty = self._git("status", "--porcelain").stdout.strip()
        if dirty:
            raise ControllerError("controller clone is dirty; refusing to mix local edits with control-state commits")
        self._git("merge", "--ff-only", sha)

    def _write_state(self, state: dict[str, Any]) -> None:
        path = self.repo / STATE_PATH
        path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def _push_control(self) -> None:
        self._git("push", self.config.remote, f"HEAD:refs/heads/{self.config.control_branch}")

    def _claim(self, ready_sha: str, state: dict[str, Any]) -> dict[str, Any]:
        self._sync_control_to(ready_sha)
        expected_task = self.repo / task_file(state)
        if not expected_task.is_file():
            raise ControllerError(f"task file does not exist: {task_file(state).as_posix()}")

        claimed = dict(state)
        claimed.update(
            status="RUNNING",
            revision=state["revision"] + 1,
            worker=self.config.worker_id,
            updated_at=utc_now(),
            last_error=None,
        )
        self._write_state(claimed)
        self._commit(
            f"agent({state['task_id']}): claim round {state['round']}",
            cwd=self.repo,
            paths=[STATE_PATH],
        )
        self._push_control()
        self.log(f"claimed {state['task_id']} round {state['round']}")
        return claimed

    def _stop_at_round_limit(self, ready_sha: str, state: dict[str, Any]) -> None:
        self._sync_control_to(ready_sha)
        stopped = dict(state)
        stopped.update(
            status="STOPPED_MAX_ROUNDS",
            revision=state["revision"] + 1,
            worker=None,
            updated_at=utc_now(),
            last_error=f"round {state['round']} exceeds max_rounds {state['max_rounds']}",
        )
        self._write_state(stopped)
        self._commit(
            f"agent({state['task_id']}): stop at round limit",
            cwd=self.repo,
            paths=[STATE_PATH],
        )
        self._push_control()

    def _remote_branch_sha(self, branch: str) -> str | None:
        remote_ref = f"refs/heads/{branch}"
        result = self._git(
            "ls-remote",
            "--exit-code",
            "--heads",
            self.config.remote,
            remote_ref,
            check=False,
        )
        if result.returncode == 2:
            return None
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise ControllerError(f"unable to inspect remote task branch {branch!r}: {detail}")
        sha = result.stdout.split()[0]
        tracking_ref = f"refs/remotes/{self.config.remote}/{branch}"
        self._git(
            "fetch",
            "--quiet",
            self.config.remote,
            f"+{remote_ref}:{tracking_ref}",
        )
        return sha

    def _prepare_worktree(self, state: dict[str, Any], ready_sha: str) -> Path:
        branch = task_branch(state, self.config.task_branch_prefix)
        if branch == self.config.control_branch:
            raise ControllerError("task branch must differ from the control branch")
        self._git("check-ref-format", "--branch", branch)
        self.config.worktree_root.mkdir(parents=True, exist_ok=True)
        path = self.config.worktree_root / str(state["task_id"])

        remote_sha = self._remote_branch_sha(branch)
        expected_candidate = state.get("candidate_commit")
        if remote_sha and not expected_candidate:
            raise ControllerError(
                f"remote task branch {branch!r} exists but state has no candidate_commit"
            )
        if remote_sha and remote_sha != expected_candidate:
            raise ControllerError(
                f"remote task branch {branch!r} is at {remote_sha}, expected candidate {expected_candidate}"
            )
        if expected_candidate and not remote_sha:
            raise ControllerError(
                f"state names candidate {expected_candidate}, but remote task branch {branch!r} is missing"
            )
        if state["round"] > 1 and not expected_candidate:
            raise ControllerError("rounds after Round 1 require the reviewed candidate_commit")

        if path.exists():
            if not (path / ".git").exists():
                raise ControllerError(f"existing worktree path is not a Git worktree: {path}")
            current_branch = self._git("branch", "--show-current", cwd=path).stdout.strip()
            if current_branch != branch:
                raise ControllerError(f"worktree {path} is on {current_branch!r}, expected {branch!r}")
            local_sha = self._git("rev-parse", "HEAD", cwd=path).stdout.strip()
            if remote_sha and local_sha != remote_sha:
                raise ControllerError(
                    f"local task branch {branch!r} differs from remote; manual reconciliation is required"
                )
        else:
            local_branch = self._git("show-ref", "--verify", f"refs/heads/{branch}", check=False)
            if local_branch.returncode == 0:
                self._git("worktree", "add", str(path), branch)
            elif remote_sha:
                self._git("branch", branch, f"refs/remotes/{self.config.remote}/{branch}")
                self._git("worktree", "add", str(path), branch)
            else:
                self._git("worktree", "add", "-b", branch, str(path), ready_sha)

        dirty = self._git("status", "--porcelain", cwd=path).stdout.strip()
        if dirty:
            raise ControllerError(f"task worktree is dirty before execution:\n{dirty}")
        return path

    def _materialize_task(self, state: dict[str, Any], worktree: Path) -> None:
        source = self.repo / task_file(state)
        runtime = worktree / RUNTIME_DIR
        runtime.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, runtime / "TASK.md")
        old_report = runtime / "execution_report.md"
        if old_report.exists():
            old_report.unlink()

    def _changed_paths(self, worktree: Path, before_head: str) -> tuple[str, ...]:
        tracked = self._git(
            "diff", "--name-only", "-z", before_head, cwd=worktree
        ).stdout.split("\0")
        untracked = self._git(
            "ls-files", "--others", "--exclude-standard", "-z", cwd=worktree
        ).stdout.split("\0")
        return tuple(sorted({path for path in [*tracked, *untracked] if path}))

    def _enforce_allowed_paths(
        self,
        state: dict[str, Any],
        worktree: Path,
        before_head: str,
        run_dir: Path,
    ) -> None:
        task_text = (self.repo / task_file(state)).read_text(encoding="utf-8")
        allowed = parse_allowed_paths(task_text)
        changed = self._changed_paths(worktree, before_head)
        (run_dir / "observed-changed-paths.txt").write_text(
            "".join(f"{path}\n" for path in changed), encoding="utf-8"
        )
        violations = [path for path in changed if not path_is_allowed(path, allowed)]
        if violations:
            rendered = ", ".join(violations)
            raise ControllerError(f"executor changed paths outside TASK.md `### Allowed`: {rendered}")

    def _executor_command(self, state: dict[str, Any], worktree: Path) -> list[str]:
        prompt = (
            "Read AGENTS.md, .agent/prompts/ZCODE_EXECUTOR.md, and "
            ".agent_runtime/TASK.md. Execute only that task and write "
            ".agent_runtime/execution_report.md. Do not merge any branch."
        )
        command = [
            *self.config.zcode_command,
            "--cwd",
            str(worktree),
            "--mode",
            self.config.zcode_mode,
            "--json",
            *self.config.zcode_extra_args,
        ]
        session_id = state.get("zcode_session_id")
        if session_id:
            command.extend(["--resume", session_id])
        command.extend(["-p", prompt])
        return command

    @staticmethod
    def _parse_envelope(stdout: str) -> dict[str, Any] | None:
        candidates = [stdout.strip(), *reversed([line.strip() for line in stdout.splitlines() if line.strip()])]
        for candidate in candidates:
            try:
                value = json.loads(candidate)
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(value, dict):
                return value
        return None

    def _invoke_executor(self, state: dict[str, Any], worktree: Path) -> ProcessResult:
        command = self._executor_command(state, worktree)
        started_wall = utc_now()
        started = time.monotonic()
        timed_out = False
        terminated_after_timeout = False
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        popen_options: dict[str, Any] = {}
        if os.name == "nt":
            popen_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            popen_options["start_new_session"] = True

        process = subprocess.Popen(
            command,
            cwd=str(worktree),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            **popen_options,
        )
        try:
            stdout, stderr = process.communicate(timeout=self.config.zcode_timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                if process.poll() is None:
                    process.kill()
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            stdout, stderr = process.communicate()
            terminated_after_timeout = process.poll() is not None
            if not terminated_after_timeout:
                raise ControllerError("executor remained alive after timeout cleanup")

        return ProcessResult(
            command=command,
            started_at=started_wall,
            finished_at=utc_now(),
            elapsed_seconds=round(time.monotonic() - started, 3),
            exit_code=process.returncode,
            timed_out=timed_out,
            terminated_after_timeout=terminated_after_timeout,
            stdout=stdout,
            stderr=stderr,
            envelope=self._parse_envelope(stdout),
        )

    def _new_run_dir(self, state: dict[str, Any]) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = self.local_run_root / f"{state['task_id']}-r{state['round']:02d}-{stamp}"
        suffix = 1
        while path.exists():
            path = self.local_run_root / f"{state['task_id']}-r{state['round']:02d}-{stamp}-{suffix}"
            suffix += 1
        path.mkdir(parents=True)
        return path

    def _capture_process(self, result: ProcessResult, run_dir: Path, *, before_head: str, worktree: Path) -> None:
        (run_dir / "zcode.stdout.json").write_text(result.stdout, encoding="utf-8")
        (run_dir / "zcode.stderr.txt").write_text(result.stderr, encoding="utf-8")
        process = {
            "command": result.command,
            "cwd": str(worktree),
            "started_at": result.started_at,
            "finished_at": result.finished_at,
            "elapsed_seconds": result.elapsed_seconds,
            "exit_code": result.exit_code,
            "timed_out": result.timed_out,
            "terminated_after_timeout": result.terminated_after_timeout,
            "envelope_parsed": result.envelope is not None,
            "session_id": result.session_id,
            "before_head": before_head,
        }
        (run_dir / "process.json").write_text(
            json.dumps(process, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    def _capture_git_after(self, worktree: Path, run_dir: Path, before_head: str, candidate: str) -> None:
        commands = {
            "git-status.txt": ("status", "--short", "--branch"),
            "changed-files.txt": ("diff", "--name-status", f"{before_head}..{candidate}"),
            "git-diff-stat.txt": ("diff", "--stat", f"{before_head}..{candidate}"),
            "git-diff.patch": ("diff", "--no-ext-diff", f"{before_head}..{candidate}"),
            "candidate-show.txt": ("show", "--no-ext-diff", "--stat", "--oneline", candidate),
        }
        for filename, args in commands.items():
            output = self._git(*args, cwd=worktree).stdout
            (run_dir / filename).write_text(output, encoding="utf-8")
        (run_dir / "candidate-commit.txt").write_text(candidate + "\n", encoding="utf-8")

    def _capture_uncommitted_git(self, worktree: Path, run_dir: Path, before_head: str) -> None:
        commands = {
            "git-status.txt": ("status", "--short", "--branch"),
            "changed-files.txt": ("diff", "--name-status", before_head),
            "git-diff-stat.txt": ("diff", "--stat", before_head),
            "git-diff.patch": ("diff", "--no-ext-diff", before_head),
        }
        for filename, args in commands.items():
            output = self._git(*args, cwd=worktree).stdout
            (run_dir / filename).write_text(output, encoding="utf-8")

    def _commit_candidate(self, state: dict[str, Any], worktree: Path) -> str:
        self._commit(
            f"agent({state['task_id']}): round {state['round']} execution",
            cwd=worktree,
            paths=None,
        )
        candidate = self._git("rev-parse", "HEAD", cwd=worktree).stdout.strip()
        branch = task_branch(state, self.config.task_branch_prefix)
        self._git("push", self.config.remote, f"HEAD:refs/heads/{branch}", cwd=worktree)
        return candidate

    def _publish(
        self,
        claimed: dict[str, Any],
        *,
        run_dir: Path,
        report_source: Path | None,
        candidate: str | None,
        session_id: str | None,
        error: str | None,
    ) -> None:
        remote_sha, remote_state = self._fetch_control()
        if (
            remote_state["task_id"] != claimed["task_id"]
            or remote_state["round"] != claimed["round"]
            or remote_state["status"] != "RUNNING"
            or remote_state["worker"] != self.config.worker_id
        ):
            raise ControllerError("control state changed while the task was running; refusing to overwrite it")
        self._sync_control_to(remote_sha)

        destination = self.repo / task_dir(claimed)
        evidence_destination = destination / "evidence"
        if evidence_destination.exists():
            raise ControllerError(f"evidence destination already exists: {evidence_destination}")
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copytree(run_dir, evidence_destination)
        tracked_paths: list[Path] = [task_dir(claimed) / "evidence"]

        if report_source and report_source.is_file():
            shutil.copyfile(report_source, destination / "EXECUTION_REPORT.md")
            tracked_paths.append(task_dir(claimed) / "EXECUTION_REPORT.md")

        final_state = dict(remote_state)
        final_state.update(
            status="ERROR" if error else "AWAITING_REVIEW",
            revision=remote_state["revision"] + 1,
            zcode_session_id=session_id or remote_state.get("zcode_session_id"),
            candidate_commit=candidate or remote_state.get("candidate_commit"),
            worker=None,
            updated_at=utc_now(),
            last_error=error,
        )
        self._write_state(final_state)
        tracked_paths.append(STATE_PATH)
        self._commit(
            f"agent({claimed['task_id']}): publish round {claimed['round']} evidence",
            cwd=self.repo,
            paths=tracked_paths,
        )
        self._push_control()
        self.log(
            f"published {claimed['task_id']} round {claimed['round']} as {final_state['status']}"
        )

    def _execute_claimed(self, claimed: dict[str, Any], ready_sha: str) -> None:
        run_dir = self._new_run_dir(claimed)
        worktree: Path | None = None
        report: Path | None = None
        candidate: str | None = None
        session_id: str | None = claimed.get("zcode_session_id")
        error: str | None = None
        before_head = "UNKNOWN"

        try:
            worktree = self._prepare_worktree(claimed, ready_sha)
            self._materialize_task(claimed, worktree)
            before_head = self._git("rev-parse", "HEAD", cwd=worktree).stdout.strip()
            (run_dir / "git-before.txt").write_text(
                self._git("status", "--short", "--branch", cwd=worktree).stdout,
                encoding="utf-8",
            )
            result = self._invoke_executor(claimed, worktree)
            self._capture_process(result, run_dir, before_head=before_head, worktree=worktree)
            session_id = result.session_id or session_id
            report = worktree / RUNTIME_DIR / "execution_report.md"

            failures: list[str] = []
            if result.timed_out:
                failures.append(f"Z Code timed out after {self.config.zcode_timeout_seconds:g} seconds")
            elif result.exit_code != 0:
                failures.append(f"Z Code exited with code {result.exit_code}")
            if result.envelope is None:
                failures.append("Z Code stdout did not contain a JSON envelope")
            expected_session = claimed.get("zcode_session_id")
            if expected_session and result.session_id != expected_session:
                failures.append(
                    "Z Code resume did not return the expected session ID "
                    f"{expected_session!r}"
                )
            elif not expected_session and not result.session_id:
                failures.append("Z Code did not return a session ID for the parent task")
            if not report.is_file():
                failures.append("Z Code did not write .agent_runtime/execution_report.md")

            self._enforce_allowed_paths(claimed, worktree, before_head, run_dir)
            candidate = self._commit_candidate(claimed, worktree)
            self._capture_git_after(worktree, run_dir, before_head, candidate)
            if failures:
                error = "; ".join(failures)
        except Exception as exc:  # preserve evidence and move the claimed task to ERROR
            error = f"{type(exc).__name__}: {exc}"
            (run_dir / "controller-error.txt").write_text(error + "\n", encoding="utf-8")
            if worktree is not None and before_head != "UNKNOWN":
                try:
                    self._capture_uncommitted_git(worktree, run_dir, before_head)
                except Exception as capture_exc:
                    (run_dir / "git-capture-error.txt").write_text(
                        f"{type(capture_exc).__name__}: {capture_exc}\n", encoding="utf-8"
                    )

        self._publish(
            claimed,
            run_dir=run_dir,
            report_source=report,
            candidate=candidate,
            session_id=session_id,
            error=error,
        )

    def run_once(self) -> str:
        self._ensure_repo()
        remote_sha, state = self._fetch_control()
        if state["status"] != READY:
            self.log(f"no work: status is {state['status']}")
            return "NO_WORK"

        validate_state(state, operational=True)
        if state["round"] > state["max_rounds"]:
            self._stop_at_round_limit(remote_sha, state)
            self.log(f"stopped {state['task_id']} at max round limit")
            return "STOPPED_MAX_ROUNDS"

        claimed = self._claim(remote_sha, state)
        self._execute_claimed(claimed, remote_sha)
        return "EXECUTED"

    def run_forever(self) -> None:
        self.log(
            f"watching {self.config.remote}/{self.config.control_branch} every "
            f"{self.config.poll_interval_seconds:g}s"
        )
        while True:
            try:
                self.run_once()
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                self.log(f"poll failed: {type(exc).__name__}: {exc}")
            time.sleep(self.config.poll_interval_seconds)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path, help="path to controller JSON config")
    parser.add_argument("--once", action="store_true", help="poll once, then exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = Config.load(args.config)
        controller = Controller(config)
        if args.once:
            controller.run_once()
        else:
            controller.run_forever()
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"controller error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
