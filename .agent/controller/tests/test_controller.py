from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path


CONTROLLER_PATH = Path(__file__).resolve().parents[1] / "controller.py"
SPEC = importlib.util.spec_from_file_location("ads_controller", CONTROLLER_PATH)
assert SPEC and SPEC.loader
controller_module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = controller_module
SPEC.loader.exec_module(controller_module)

Config = controller_module.Config
Controller = controller_module.Controller
ControllerError = controller_module.ControllerError
validate_state = controller_module.validate_state
parse_allowed_paths = controller_module.parse_allowed_paths
path_is_allowed = controller_module.path_is_allowed


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed:\n{result.stderr}")
    return result.stdout


def base_state() -> dict[str, object]:
    return {
        "schema_version": "v1-alpha",
        "task_id": "ADS-DUMMY-001",
        "round": 1,
        "max_rounds": 3,
        "revision": 0,
        "status": "READY_FOR_EXECUTION",
        "zcode_session_id": None,
        "candidate_commit": None,
        "worker": None,
        "updated_at": None,
        "last_error": None,
    }


class StateValidationTests(unittest.TestCase):
    def test_rejects_more_than_three_rounds_in_policy(self) -> None:
        state = base_state()
        state["max_rounds"] = 4
        with self.assertRaisesRegex(ControllerError, "max_rounds"):
            validate_state(state)

    def test_allowed_path_parser_and_matcher(self) -> None:
        allowed = parse_allowed_paths(
            "# TASK\n\n## Scope\n\n### Allowed\n\n- `one.txt`\n- `pkg/`\n- `tests/test_*.py`\n\n### Do not modify\n"
        )
        self.assertTrue(path_is_allowed("one.txt", allowed))
        self.assertTrue(path_is_allowed("pkg/nested.py", allowed))
        self.assertTrue(path_is_allowed("tests/test_one.py", allowed))
        self.assertFalse(path_is_allowed("other.txt", allowed))


class TwoRoundIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.remote = self.root / "remote.git"
        self.repo = self.root / "control"
        self.worktrees = self.root / "worktrees"
        git(self.root, "init", "--bare", str(self.remote))
        git(self.root, "clone", str(self.remote), str(self.repo))
        git(self.repo, "switch", "-c", "control")
        git(self.repo, "config", "user.name", "Test Planner")
        git(self.repo, "config", "user.email", "planner@example.invalid")

        (self.repo / ".agent" / "prompts").mkdir(parents=True)
        (self.repo / ".agent" / "tasks" / "ADS-DUMMY-001" / "round-01").mkdir(parents=True)
        (self.repo / ".agent_runtime").mkdir()
        (self.repo / ".gitignore").write_text(".agent_runtime/\n", encoding="utf-8")
        (self.repo / "AGENTS.md").write_text("# Test agent rules\n", encoding="utf-8")
        (self.repo / ".agent" / "prompts" / "ZCODE_EXECUTOR.md").write_text(
            "# Test executor prompt\n", encoding="utf-8"
        )
        (self.repo / ".agent" / "tasks" / "ADS-DUMMY-001" / "round-01" / "TASK.md").write_text(
            "# TASK\n\n## Scope\n\n### Allowed\n\n- `dummy.txt`\n\n"
            "### Do not modify\n\n- everything else\n\nDUMMY_ROUND=1\n",
            encoding="utf-8",
        )
        (self.repo / ".agent" / "state.json").write_text(
            json.dumps(base_state(), indent=2) + "\n", encoding="utf-8"
        )
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "seed round 1")
        git(self.repo, "push", "-u", "origin", "control")

        fake = Path(__file__).resolve().parent / "fake_zcode.py"
        config_path = self.root / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "repository_path": str(self.repo),
                    "remote": "origin",
                    "control_branch": "control",
                    "task_branch_prefix": "agent-task/",
                    "worktree_root": str(self.worktrees),
                    "poll_interval_seconds": 0.01,
                    "worker_id": "test-worker",
                    "git_author_name": "Test Controller",
                    "git_author_email": "controller@example.invalid",
                    "zcode": {
                        "command": [sys.executable, str(fake)],
                        "mode": "yolo",
                        "timeout_seconds": 20,
                        "extra_args": [],
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        self.controller = Controller(Config.load(config_path))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def remote_json(self, path: str, branch: str = "control") -> dict[str, object]:
        raw = git(self.remote, "show", f"{branch}:{path}")
        return json.loads(raw)

    def test_two_rounds_claim_execute_resume_and_publish(self) -> None:
        self.assertEqual(self.controller.run_once(), "EXECUTED")
        round1 = self.remote_json(".agent/state.json")
        self.assertEqual(round1["status"], "AWAITING_REVIEW")
        self.assertEqual(round1["round"], 1)
        self.assertEqual(round1["zcode_session_id"], "fake-session-001")
        self.assertRegex(str(round1["candidate_commit"]), r"^[0-9a-f]{40}$")
        self.assertEqual(
            git(self.remote, "show", "agent-task/ADS-DUMMY-001:dummy.txt"), "round 1\n"
        )
        git(
            self.remote,
            "show",
            "control:.agent/tasks/ADS-DUMMY-001/round-01/evidence/process.json",
        )
        git(
            self.remote,
            "show",
            "control:.agent/tasks/ADS-DUMMY-001/round-01/EXECUTION_REPORT.md",
        )

        round2_dir = self.repo / ".agent" / "tasks" / "ADS-DUMMY-001" / "round-02"
        round2_dir.mkdir(parents=True)
        (round2_dir / "TASK.md").write_text(
            "# TASK\n\n## Scope\n\n### Allowed\n\n- `dummy.txt`\n\n"
            "### Do not modify\n\n- everything else\n\nDUMMY_ROUND=2\n",
            encoding="utf-8",
        )
        round1_dir = self.repo / ".agent" / "tasks" / "ADS-DUMMY-001" / "round-01"
        (round1_dir / "REVIEW.md").write_text(
            "# REVIEW\n\n## Decision\n\nPASS\n\n## Next Action\n\nContinue to round 2.\n",
            encoding="utf-8",
        )
        next_state = dict(round1)
        next_state.update(
            round=2,
            revision=int(round1["revision"]) + 1,
            status="READY_FOR_EXECUTION",
            worker=None,
            updated_at="2026-09-22T00:00:00Z",
            last_error=None,
        )
        (self.repo / ".agent" / "state.json").write_text(
            json.dumps(next_state, indent=2) + "\n", encoding="utf-8"
        )
        git(self.repo, "add", ".agent")
        git(self.repo, "commit", "-m", "review round 1 and request round 2")
        git(self.repo, "push", "origin", "control")

        self.assertEqual(self.controller.run_once(), "EXECUTED")
        round2 = self.remote_json(".agent/state.json")
        self.assertEqual(round2["status"], "AWAITING_REVIEW")
        self.assertEqual(round2["round"], 2)
        self.assertEqual(round2["zcode_session_id"], "fake-session-001")
        self.assertEqual(
            git(self.remote, "show", "agent-task/ADS-DUMMY-001:dummy.txt"),
            "round 1\nround 2\n",
        )

        process = self.remote_json(
            ".agent/tasks/ADS-DUMMY-001/round-02/evidence/process.json"
        )
        command = process["command"]
        self.assertIn("--resume", command)
        resume_index = command.index("--resume")
        self.assertEqual(command[resume_index + 1], "fake-session-001")

    def test_ready_round_above_cap_stops_without_executor(self) -> None:
        state_path = self.repo / ".agent" / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update(round=4, max_rounds=3, revision=1)
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        git(self.repo, "add", ".agent/state.json")
        git(self.repo, "commit", "-m", "request forbidden round 4")
        git(self.repo, "push", "origin", "control")

        self.assertEqual(self.controller.run_once(), "STOPPED_MAX_ROUNDS")
        stopped = self.remote_json(".agent/state.json")
        self.assertEqual(stopped["status"], "STOPPED_MAX_ROUNDS")
        self.assertIsNone(stopped["candidate_commit"])
        self.assertIn("exceeds max_rounds", stopped["last_error"])
        missing = subprocess.run(
            ["git", "--git-dir", str(self.remote), "show-ref", "--verify", "refs/heads/agent-task/ADS-DUMMY-001"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertNotEqual(missing.returncode, 0)

    def test_out_of_scope_change_is_not_pushed_as_candidate(self) -> None:
        task_path = (
            self.repo
            / ".agent"
            / "tasks"
            / "ADS-DUMMY-001"
            / "round-01"
            / "TASK.md"
        )
        task_path.write_text(
            "# TASK\n\n## Scope\n\n### Allowed\n\n- `dummy.txt`\n\n"
            "### Do not modify\n\n- everything else\n\nDUMMY_OUT_OF_SCOPE=1\n",
            encoding="utf-8",
        )
        git(self.repo, "add", str(task_path.relative_to(self.repo)))
        git(self.repo, "commit", "-m", "request out-of-scope fake change")
        git(self.repo, "push", "origin", "control")

        self.assertEqual(self.controller.run_once(), "EXECUTED")
        state = self.remote_json(".agent/state.json")
        self.assertEqual(state["status"], "ERROR")
        self.assertIn("outside TASK.md", state["last_error"])
        missing = subprocess.run(
            ["git", "--git-dir", str(self.remote), "show-ref", "--verify", "refs/heads/agent-task/ADS-DUMMY-001"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertNotEqual(missing.returncode, 0)

    def test_timeout_terminates_executor_before_publishing_error(self) -> None:
        task_path = (
            self.repo
            / ".agent"
            / "tasks"
            / "ADS-DUMMY-001"
            / "round-01"
            / "TASK.md"
        )
        task_path.write_text(
            "# TASK\n\n## Scope\n\n### Allowed\n\n- `dummy.txt`\n\n"
            "### Do not modify\n\n- everything else\n\nDUMMY_TIMEOUT=1\n",
            encoding="utf-8",
        )
        git(self.repo, "add", str(task_path.relative_to(self.repo)))
        git(self.repo, "commit", "-m", "request timeout fake task")
        git(self.repo, "push", "origin", "control")

        timeout_controller = Controller(
            replace(self.controller.config, zcode_timeout_seconds=0.2)
        )
        self.assertEqual(timeout_controller.run_once(), "EXECUTED")
        state = self.remote_json(".agent/state.json")
        self.assertEqual(state["status"], "ERROR")
        self.assertIn("timed out", state["last_error"])
        process = self.remote_json(
            ".agent/tasks/ADS-DUMMY-001/round-01/evidence/process.json"
        )
        self.assertTrue(process["timed_out"])
        self.assertTrue(process["terminated_after_timeout"])

        pid_path = (
            self.worktrees
            / "ADS-DUMMY-001"
            / ".agent_runtime"
            / "fake_pid.txt"
        )
        pid = int(pid_path.read_text(encoding="utf-8"))
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_missing_session_id_publishes_error(self) -> None:
        task_path = (
            self.repo
            / ".agent"
            / "tasks"
            / "ADS-DUMMY-001"
            / "round-01"
            / "TASK.md"
        )
        task_path.write_text(
            "# TASK\n\n## Scope\n\n### Allowed\n\n- `dummy.txt`\n\n"
            "### Do not modify\n\n- everything else\n\nDUMMY_NO_SESSION=1\n",
            encoding="utf-8",
        )
        git(self.repo, "add", str(task_path.relative_to(self.repo)))
        git(self.repo, "commit", "-m", "request missing-session fake task")
        git(self.repo, "push", "origin", "control")

        self.assertEqual(self.controller.run_once(), "EXECUTED")
        state = self.remote_json(".agent/state.json")
        self.assertEqual(state["status"], "ERROR")
        self.assertIn("did not return a session ID", state["last_error"])
        self.assertIsNone(state["zcode_session_id"])

    def test_candidate_mismatch_publishes_error_without_execution(self) -> None:
        state_path = self.repo / ".agent" / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["candidate_commit"] = "0" * 40
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        git(self.repo, "add", ".agent/state.json")
        git(self.repo, "commit", "-m", "set mismatched candidate")
        git(self.repo, "branch", "agent-task/ADS-DUMMY-001")
        git(self.repo, "push", "origin", "agent-task/ADS-DUMMY-001")
        git(self.repo, "push", "origin", "control")

        self.assertEqual(self.controller.run_once(), "EXECUTED")
        result = self.remote_json(".agent/state.json")
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("expected candidate", result["last_error"])


if __name__ == "__main__":
    unittest.main()
