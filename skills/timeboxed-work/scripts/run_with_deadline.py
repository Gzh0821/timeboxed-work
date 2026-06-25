#!/usr/bin/env python3
"""Run a child command until a deadline, then terminate it."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


TIMEOUT_EXIT_CODE = 124
USAGE_EXIT_CODE = 2


class DeadlineError(ValueError):
    pass


def now_local() -> datetime:
    return datetime.now().astimezone()


def format_dt(value: datetime) -> str:
    return value.astimezone().isoformat(timespec="seconds")


def parse_datetime(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise DeadlineError(f"invalid deadline datetime: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=now_local().tzinfo)
    return parsed.astimezone()


def load_deadline_from_state(path: Path) -> datetime:
    try:
        with path.open("r", encoding="utf-8") as handle:
            state = json.load(handle)
    except FileNotFoundError as exc:
        raise DeadlineError(f"state file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DeadlineError(f"invalid state JSON: {path}") from exc
    try:
        return parse_datetime(str(state["deadline_at"]))
    except KeyError as exc:
        raise DeadlineError(f"state file has no deadline_at: {path}") from exc


def resolve_deadline(args: argparse.Namespace) -> datetime:
    if bool(args.deadline) == bool(args.state):
        raise DeadlineError("provide exactly one of --deadline or --state")
    if args.deadline:
        return parse_datetime(args.deadline)
    return load_deadline_from_state(Path(args.state).expanduser().resolve())


def signal_process_group(proc: subprocess.Popen[Any], sig: int) -> None:
    try:
        os.killpg(proc.pid, sig)
    except ProcessLookupError:
        return
    except OSError:
        if sig == signal.SIGTERM:
            proc.terminate()
        else:
            proc.kill()


def write_summary(summary: dict[str, Any], summary_file: str | None) -> None:
    rendered = json.dumps(summary, indent=2, sort_keys=True)
    print(rendered, file=sys.stderr)
    if summary_file:
        path = Path(summary_file).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n", encoding="utf-8")


def build_summary(
    *,
    command: list[str],
    deadline: datetime,
    started_at: datetime,
    ended_at: datetime,
    exit_code: int,
    timed_out: bool,
    termination: str,
    signal_sent: str | None,
) -> dict[str, Any]:
    remaining_at_end = int(round((deadline - ended_at).total_seconds()))
    return {
        "command": command,
        "deadline_at": format_dt(deadline),
        "started_at": format_dt(started_at),
        "ended_at": format_dt(ended_at),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "termination": termination,
        "signal_sent": signal_sent,
        "remaining_seconds_at_end": remaining_at_end,
        "overrun_seconds": max(0, -remaining_at_end),
        "status": "timed_out" if timed_out else "completed",
    }


def run_child(args: argparse.Namespace) -> int:
    if not args.command:
        raise DeadlineError("missing child command after --")
    deadline = resolve_deadline(args)
    start = now_local()
    seconds_until_deadline = (deadline - start).total_seconds()
    command = list(args.command)

    if seconds_until_deadline <= 0:
        summary = build_summary(
            command=command,
            deadline=deadline,
            started_at=start,
            ended_at=start,
            exit_code=TIMEOUT_EXIT_CODE,
            timed_out=True,
            termination="not_started_deadline_passed",
            signal_sent=None,
        )
        write_summary(summary, args.summary_file)
        return TIMEOUT_EXIT_CODE

    proc = subprocess.Popen(command, start_new_session=True)
    termination = "completed"
    signal_sent = None
    exit_code = 0
    timed_out = False
    try:
        exit_code = proc.wait(timeout=seconds_until_deadline)
    except subprocess.TimeoutExpired:
        timed_out = True
        signal_sent = "SIGTERM"
        termination = "terminated"
        signal_process_group(proc, signal.SIGTERM)
        try:
            proc.wait(timeout=args.grace_seconds)
        except subprocess.TimeoutExpired:
            signal_sent = "SIGKILL"
            termination = "killed"
            signal_process_group(proc, signal.SIGKILL)
            proc.wait()
        exit_code = TIMEOUT_EXIT_CODE
    except KeyboardInterrupt:
        signal_sent = "SIGTERM"
        termination = "interrupted"
        signal_process_group(proc, signal.SIGTERM)
        try:
            proc.wait(timeout=args.grace_seconds)
        except subprocess.TimeoutExpired:
            signal_sent = "SIGKILL"
            termination = "interrupted_killed"
            signal_process_group(proc, signal.SIGKILL)
            proc.wait()
        exit_code = 130
        timed_out = False

    # Give process accounting a stable end timestamp after any signal handling.
    time.sleep(0)
    end = now_local()
    summary = build_summary(
        command=command,
        deadline=deadline,
        started_at=start,
        ended_at=end,
        exit_code=exit_code,
        timed_out=timed_out,
        termination=termination,
        signal_sent=signal_sent,
    )
    write_summary(summary, args.summary_file)
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a child command with a deadline.")
    parser.add_argument("--deadline", help="absolute ISO deadline")
    parser.add_argument("--state", help="timebox state JSON with deadline_at")
    parser.add_argument("--grace-seconds", type=float, default=5.0)
    parser.add_argument("--summary-file", help="optional path to also write JSON summary")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="child command, usually after --")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if args.grace_seconds < 0:
        print(json.dumps({"error": "grace seconds must not be negative", "status": "error"}), file=sys.stderr)
        return USAGE_EXIT_CODE
    try:
        return run_child(args)
    except DeadlineError as exc:
        print(json.dumps({"error": str(exc), "status": "error"}, sort_keys=True), file=sys.stderr)
        return USAGE_EXIT_CODE


if __name__ == "__main__":
    raise SystemExit(main())
