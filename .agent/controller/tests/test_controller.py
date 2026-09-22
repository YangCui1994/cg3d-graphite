from __future__ import annotations

import importlib.util
import hashlib
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
EvidencePublicationError = controller_module.EvidencePublicationError
validate_published_evidence = controller_module.validate_published_evidence


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


class PublishedEvidenceValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "published_evidence"
        self.root.mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def manifest(self, files: list[dict[str, object]]) -> None:
        (self.root / "manifest.json").write_text(
            json.dumps({"schema_version": "v1", "files": files}),
            encoding="utf-8",
        )

    @staticmethod
    def entry(path: str) -> dict[str, object]:
        return {
            "path": path,
            "kind": "validation_log",
            "description": f"Evidence at {path}",
        }

    def test_valid_manifest_and_text_log(self) -> None:
        data = b"validation: PASS\n"
        (self.root / "level_a.log").write_bytes(data)
        self.manifest([self.entry("level_a.log")])

        bundle = validate_published_evidence(self.root)

        self.assertIsNotNone(bundle)
        assert bundle is not None
        self.assertEqual(bundle.files[0].relative_path, "level_a.log")
        self.assertEqual(bundle.files[0].size_bytes, len(data))
        self.assertEqual(bundle.files[0].sha256, hashlib.sha256(data).hexdigest())

    def test_missing_file_rejected(self) -> None:
        self.manifest([self.entry("missing.log")])
        with self.assertRaisesRegex(EvidencePublicationError, "does not exist"):
            validate_published_evidence(self.root)

    def test_unlisted_file_rejected(self) -> None:
        (self.root / "extra.log").write_text("extra", encoding="utf-8")
        self.manifest([])
        with self.assertRaisesRegex(EvidencePublicationError, "not listed"):
            validate_published_evidence(self.root)

    def test_path_traversal_rejected(self) -> None:
        self.manifest([self.entry("../outside.log")])
        with self.assertRaisesRegex(EvidencePublicationError, "path traversal"):
            validate_published_evidence(self.root)

    def test_absolute_path_rejected(self) -> None:
        self.manifest([self.entry("C:/outside.log")])
        with self.assertRaisesRegex(EvidencePublicationError, "absolute"):
            validate_published_evidence(self.root)

    def test_symlink_rejected(self) -> None:
        target = Path(self.temp.name) / "target.log"
        target.write_text("secret", encoding="utf-8")
        (self.root / "linked.log").symlink_to(target)
        self.manifest([self.entry("linked.log")])
        with self.assertRaisesRegex(EvidencePublicationError, "symlink"):
            validate_published_evidence(self.root)

    def test_unsupported_binary_extension_rejected(self) -> None:
        (self.root / "array.bin").write_bytes(b"binary")
        self.manifest([self.entry("array.bin")])
        with self.assertRaisesRegex(EvidencePublicationError, "unsupported extension"):
            validate_published_evidence(self.root)

    def test_directory_listed_as_evidence_rejected(self) -> None:
        (self.root / "directory.log").mkdir()
        self.manifest([self.entry("directory.log")])
        with self.assertRaisesRegex(EvidencePublicationError, "not a file"):
            validate_published_evidence(self.root)

    def test_single_file_limit_rejected(self) -> None:
        (self.root / "large.log").write_bytes(b"x" * (1024 * 1024 + 1))
        self.manifest([self.entry("large.log")])
        with self.assertRaisesRegex(EvidencePublicationError, "single-file limit"):
            validate_published_evidence(self.root)

    def test_total_size_limit_rejected(self) -> None:
        entries = []
        for index in range(6):
            name = f"part-{index}.log"
            (self.root / name).write_bytes(b"x" * (900 * 1024))
            entries.append(self.entry(name))
        self.manifest(entries)
        with self.assertRaisesRegex(EvidencePublicationError, "total-size limit"):
            validate_published_evidence(self.root)

    def test_file_count_limit_rejected(self) -> None:
        entries = [self.entry(f"file-{index}.log") for index in range(21)]
        self.manifest(entries)
        with self.assertRaisesRegex(EvidencePublicationError, "20-file limit"):
            validate_published_evidence(self.root)

    def test_duplicate_path_rejected(self) -> None:
        (self.root / "same.log").write_text("same", encoding="utf-8")
        self.manifest([self.entry("same.log"), self.entry("same.log")])
        with self.assertRaisesRegex(EvidencePublicationError, "duplicate"):
            validate_published_evidence(self.root)


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
            "control:.agent/tasks/ADS-DUMMY-001/round-01/evidence/controller/process.json",
        )
        missing_executor = subprocess.run(
            [
                "git",
                "--git-dir",
                str(self.remote),
                "cat-file",
                "-e",
                "control:.agent/tasks/ADS-DUMMY-001/round-01/evidence/executor/manifest.json",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertNotEqual(missing_executor.returncode, 0)
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
            ".agent/tasks/ADS-DUMMY-001/round-02/evidence/controller/process.json"
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
            ".agent/tasks/ADS-DUMMY-001/round-01/evidence/controller/process.json"
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

    def test_executor_evidence_end_to_end_publication_and_provenance(self) -> None:
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
            "### Do not modify\n\n- everything else\n\nDUMMY_PUBLISH_EVIDENCE=1\n",
            encoding="utf-8",
        )
        git(self.repo, "add", str(task_path.relative_to(self.repo)))
        git(self.repo, "commit", "-m", "request published evidence fake task")
        git(self.repo, "push", "origin", "control")

        self.assertEqual(self.controller.run_once(), "EXECUTED")
        state = self.remote_json(".agent/state.json")
        self.assertEqual(state["status"], "AWAITING_REVIEW")
        candidate = str(state["candidate_commit"])
        session_id = str(state["zcode_session_id"])
        prefix = ".agent/tasks/ADS-DUMMY-001/round-01/evidence"
        git(self.remote, "show", f"control:{prefix}/controller/process.json")
        manifest = self.remote_json(f"{prefix}/executor/manifest.json")
        self.assertEqual(manifest["schema_version"], "v1")
        log = git(self.remote, "show", f"control:{prefix}/executor/level_a.log")
        self.assertEqual(log, "level-a: PASS\n")
        provenance = self.remote_json(f"{prefix}/executor/provenance.json")
        self.assertEqual(provenance["task_id"], "ADS-DUMMY-001")
        self.assertEqual(provenance["round"], 1)
        self.assertEqual(provenance["candidate_commit"], candidate)
        self.assertEqual(provenance["zcode_session_id"], session_id)
        self.assertEqual(provenance["worker"], "test-worker")
        self.assertEqual(provenance["files"][0]["path"], "level_a.log")
        self.assertEqual(provenance["files"][0]["size_bytes"], len(log.encode()))
        self.assertEqual(
            provenance["files"][0]["sha256"], hashlib.sha256(log.encode()).hexdigest()
        )

    def test_evidence_publication_failure_preserves_candidate_and_sets_error(self) -> None:
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
            "### Do not modify\n\n- everything else\n\nDUMMY_PUBLISH_MISSING=1\n",
            encoding="utf-8",
        )
        git(self.repo, "add", str(task_path.relative_to(self.repo)))
        git(self.repo, "commit", "-m", "request invalid published evidence fake task")
        git(self.repo, "push", "origin", "control")

        self.assertEqual(self.controller.run_once(), "EXECUTED")
        state = self.remote_json(".agent/state.json")
        self.assertEqual(state["status"], "ERROR")
        self.assertRegex(str(state["candidate_commit"]), r"^[0-9a-f]{40}$")
        self.assertEqual(
            git(self.remote, "rev-parse", "agent-task/ADS-DUMMY-001"),
            str(state["candidate_commit"]) + "\n",
        )
        self.assertIn("evidence publication failure", str(state["last_error"]))
        self.assertIn("does not exist", str(state["last_error"]))
        prefix = ".agent/tasks/ADS-DUMMY-001/round-01/evidence"
        git(self.remote, "show", f"control:{prefix}/controller/process.json")
        missing_executor = subprocess.run(
            [
                "git",
                "--git-dir",
                str(self.remote),
                "cat-file",
                "-e",
                f"control:{prefix}/executor/manifest.json",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertNotEqual(missing_executor.returncode, 0)


if __name__ == "__main__":
    unittest.main()
