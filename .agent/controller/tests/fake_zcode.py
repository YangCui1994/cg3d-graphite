#!/usr/bin/env python3
"""Tiny Z Code CLI stand-in used only by the controller integration test."""

from __future__ import annotations

import argparse
import json
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
    print(
        json.dumps(
            {
                "sessionId": "fake-session-001",
                "response": summary,
                "projection": {"status": "idle"},
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
