#!/usr/bin/env python3
"""Tiny Z Code CLI stand-in used only by the controller integration test."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--mode")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--resume")
    parser.add_argument("-p")
    args, _ = parser.parse_known_args()

    cwd = Path(args.cwd)
    task = (cwd / ".agent_runtime" / "TASK.md").read_text(encoding="utf-8")
    session_id = "fake-session-001"
    if "DUMMY_ROUND=1" in task:
        if args.resume:
            raise SystemExit("round 1 must start a fresh session")
        (cwd / "dummy.txt").write_text("round 1\n", encoding="utf-8")
        summary = "created dummy.txt"
    elif "DUMMY_ROUND=2" in task:
        if args.resume != "fake-session-001":
            raise SystemExit("round 2 must resume fake-session-001")
        with (cwd / "dummy.txt").open("a", encoding="utf-8") as handle:
            handle.write("round 2\n")
        summary = "appended round 2"
    elif "DUMMY_OUT_OF_SCOPE=1" in task:
        (cwd / "forbidden.txt").write_text("not allowed\n", encoding="utf-8")
        summary = "created forbidden.txt"
    elif "DUMMY_TIMEOUT=1" in task:
        (cwd / ".agent_runtime" / "fake_pid.txt").write_text(
            str(os.getpid()), encoding="utf-8"
        )
        print(json.dumps({"sessionId": "fake-session-001"}), flush=True)
        time.sleep(60)
        raise SystemExit("timeout test was not terminated")
    elif "DUMMY_NO_SESSION=1" in task:
        (cwd / "dummy.txt").write_text("no session\n", encoding="utf-8")
        summary = "completed without a session ID"
        session_id = None
    else:
        raise SystemExit("unknown dummy task")

    report = f"""# EXECUTION REPORT

## Task

- **Task ID:** `ADS-DUMMY-001`
- **Status:** `COMPLETED`

## Summary

{summary}.

## Validation

- **Command:** fake executor internal check
- **Status:** PASS
- **Exit code:** 0

## Suggested Next Action

Review the captured candidate and controller evidence.
"""
    (cwd / ".agent_runtime" / "execution_report.md").write_text(report, encoding="utf-8")
    envelope = {"response": summary, "projection": {"status": "idle"}}
    if session_id:
        envelope["sessionId"] = session_id
    print(json.dumps(envelope))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
