#!/usr/bin/env python3
"""Deterministic wall-clock timebox state for Codex skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


STATUS_ACTIVE = "active"
STATUS_FINALIZING = "finalizing"
STATUS_EXPIRED = "expired"

DEFAULT_RELATIVE_STATE = Path("work") / "timebox" / "timebox-state.json"
TMP_BASE = Path("/private/tmp/codex-timebox")


class TimeboxError(ValueError):
    pass


def now_local() -> datetime:
    return datetime.now().astimezone()


def parse_datetime(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise TimeboxError(f"invalid datetime: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=now_local().tzinfo)
    return parsed.astimezone()


def format_dt(value: datetime) -> str:
    return value.astimezone().isoformat(timespec="seconds")


def parse_duration_seconds(text: str) -> int:
    value = text.strip().lower()
    if not value:
        raise TimeboxError("empty duration")

    unit_seconds = {
        "h": 3600,
        "hr": 3600,
        "hrs": 3600,
        "hour": 3600,
        "hours": 3600,
        "小时": 3600,
        "钟头": 3600,
        "m": 60,
        "min": 60,
        "mins": 60,
        "minute": 60,
        "minutes": 60,
        "分钟": 60,
        "分": 60,
        "s": 1,
        "sec": 1,
        "secs": 1,
        "second": 1,
        "seconds": 1,
        "秒": 1,
    }
    pattern = re.compile(
        r"(?P<number>\d+(?:\.\d+)?)\s*"
        r"(?P<unit>hours?|hrs?|h|minutes?|mins?|m|seconds?|secs?|s|小时|钟头|分钟|分|秒)"
    )

    total = 0.0
    pos = 0
    matched = False
    for match in pattern.finditer(value):
        if value[pos : match.start()].strip():
            raise TimeboxError(f"could not parse duration near: {value[pos:match.start()]!r}")
        matched = True
        total += float(match.group("number")) * unit_seconds[match.group("unit")]
        pos = match.end()

    if not matched or value[pos:].strip():
        raise TimeboxError(f"could not parse duration: {text!r}")

    seconds = int(round(total))
    if seconds <= 0:
        raise TimeboxError("duration must be greater than zero")
    return seconds


def parse_until_deadline(text: str, now: datetime) -> datetime | None:
    value = text.strip().lower()
    prefixes = ("until", "by", "before", "截止到", "截止", "到")
    for prefix in prefixes:
        if value.startswith(prefix):
            value = value[len(prefix) :].strip()
            break
    else:
        return None

    match = re.fullmatch(r"(?P<hour>\d{1,2}):(?P<minute>\d{2})(?::(?P<second>\d{2}))?", value)
    if not match:
        try:
            return parse_datetime(value)
        except TimeboxError as exc:
            raise TimeboxError(f"could not parse deadline: {text!r}") from exc

    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    second = int(match.group("second") or "0")
    if hour > 23 or minute > 59 or second > 59:
        raise TimeboxError(f"invalid clock time: {text!r}")

    deadline = now.replace(hour=hour, minute=minute, second=second, microsecond=0)
    if deadline <= now:
        deadline += timedelta(days=1)
    return deadline


def parse_budget(text: str, now: datetime) -> tuple[datetime, int, str]:
    deadline = parse_until_deadline(text, now)
    if deadline is not None:
        duration_seconds = max(1, int(round((deadline - now).total_seconds())))
        return deadline, duration_seconds, "deadline"

    duration_seconds = parse_duration_seconds(text)
    return now + timedelta(seconds=duration_seconds), duration_seconds, "duration"


def default_buffer_seconds(duration_seconds: int) -> int:
    if duration_seconds < 600:
        return int(min(120, max(60, round(duration_seconds * 0.2))))
    return int(max(300, min(600, round(duration_seconds * 0.1))))


def status_for(remaining_seconds: int, buffer_seconds: int) -> str:
    if remaining_seconds <= 0:
        return STATUS_EXPIRED
    if remaining_seconds <= buffer_seconds:
        return STATUS_FINALIZING
    return STATUS_ACTIVE


def workspace_path(value: str | None) -> Path:
    return Path(value).expanduser().resolve() if value else Path.cwd().resolve()


def workspace_state_path(workspace: Path) -> Path:
    return workspace / DEFAULT_RELATIVE_STATE


def tmp_state_path(workspace: Path) -> Path:
    digest = hashlib.sha256(str(workspace).encode("utf-8")).hexdigest()[:16]
    return TMP_BASE / digest / "timebox-state.json"


def choose_existing_state_path(workspace: Path, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    candidate = workspace_state_path(workspace)
    if candidate.exists():
        return candidate
    return tmp_state_path(workspace)


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".timebox-", suffix=".json", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def write_state(workspace: Path, explicit: str | None, data: dict[str, Any]) -> Path:
    if explicit:
        path = Path(explicit).expanduser().resolve()
        write_json_atomic(path, data)
        return path

    candidate = workspace_state_path(workspace)
    try:
        write_json_atomic(candidate, data)
        return candidate
    except OSError:
        fallback = tmp_state_path(workspace)
        write_json_atomic(fallback, data)
        return fallback


def load_state(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise TimeboxError(f"timebox state not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TimeboxError(f"invalid timebox state JSON: {path}") from exc


def enrich_state(state: dict[str, Any], check_time: datetime, state_path: Path) -> dict[str, Any]:
    deadline = parse_datetime(str(state["deadline_at"]))
    started = parse_datetime(str(state["started_at"]))
    remaining = int(round((deadline - check_time).total_seconds()))
    elapsed = max(0, int(round((check_time - started).total_seconds())))
    buffer_seconds = int(state.get("finalization_buffer_seconds", 0))
    enriched = dict(state)
    enriched.update(
        {
            "now": format_dt(check_time),
            "remaining_seconds": remaining,
            "elapsed_seconds": elapsed,
            "status": status_for(remaining, buffer_seconds),
            "state_file": str(state_path),
        }
    )
    return enriched


def cmd_start(args: argparse.Namespace) -> int:
    if args.mode not in {"soft", "guarded", "hard"}:
        raise TimeboxError(f"invalid mode: {args.mode}")

    start_time = now_local()
    deadline, duration_seconds, budget_kind = parse_budget(args.budget, start_time)
    buffer_seconds = args.finalization_buffer_seconds
    if buffer_seconds is None:
        buffer_seconds = default_buffer_seconds(duration_seconds)
    if buffer_seconds < 0:
        raise TimeboxError("finalization buffer must not be negative")

    state: dict[str, Any] = {
        "started_at": format_dt(start_time),
        "deadline_at": format_dt(deadline),
        "duration_seconds": duration_seconds,
        "remaining_seconds": int(round((deadline - start_time).total_seconds())),
        "mode": args.mode,
        "finalization_buffer_seconds": int(buffer_seconds),
        "status": status_for(duration_seconds, int(buffer_seconds)),
        "budget": args.budget,
        "budget_kind": budget_kind,
        "timezone": start_time.tzname(),
    }
    workspace = workspace_path(args.workspace)
    path = write_state(workspace, args.state, state)
    state["state_file"] = str(path)
    print(json.dumps(state, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    path = choose_existing_state_path(workspace, args.state)
    state = enrich_state(load_state(path), now_local(), path)
    print(json.dumps(state, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    workspace = workspace_path(args.workspace)
    path = choose_existing_state_path(workspace, args.state)
    state = enrich_state(load_state(path), now_local(), path)
    deadline = parse_datetime(str(state["deadline_at"]))
    state["overrun_seconds"] = max(0, int(round((now_local() - deadline).total_seconds())))
    print(json.dumps(state, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create and inspect deterministic timebox state.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="start a new timebox")
    start.add_argument("budget", help='duration like "90m" or deadline like "until 18:30"')
    start.add_argument("--mode", choices=["soft", "guarded", "hard"], default="soft")
    start.add_argument("--workspace", help="workspace root for work/timebox state")
    start.add_argument("--state", help="explicit state file path")
    start.add_argument("--finalization-buffer-seconds", type=int)
    start.set_defaults(func=cmd_start)

    for name, help_text, func in (
        ("check", "check current timebox state", cmd_check),
        ("summary", "print current timebox summary", cmd_summary),
    ):
        sub = subparsers.add_parser(name, help=help_text)
        sub.add_argument("--workspace", help="workspace root for work/timebox state")
        sub.add_argument("--state", help="explicit state file path")
        sub.set_defaults(func=func)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except TimeboxError as exc:
        print(json.dumps({"error": str(exc), "status": "error"}, sort_keys=True, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
