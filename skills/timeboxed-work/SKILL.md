---
name: timeboxed-work
description: Work under an explicit time budget with deterministic deadline tracking and handoff. Use when the user asks for a timebox, fixed duration, deadline, work for N minutes/hours, stop at a specific time, hard deadline, guarded deadline, 按固定时间工作, 工作 N 分钟/小时, 到点停止, 时间预算, or similar bounded-work requests.
---

# Timeboxed Work

Use this skill to keep agent work bounded by a user-specified wall-clock budget. This skill is not a hard real-time controller; hard stops require host or outer-supervisor support. `scripts/run_with_deadline.py` can only control child commands launched through it.

## Start Protocol

1. Create state before doing task work:
   ```bash
   python3 scripts/timebox.py start "<budget>" --mode soft
   ```
   Use `--mode guarded` only when the user asks for guarded deadline behavior. Use `--mode hard` only when the user explicitly says time is priority, must stop exactly on time, hard deadline, 硬截止, 必须准点停, or equivalent.
2. Convert relative budgets to an absolute `deadline_at` from the JSON output. Do not estimate the current time from memory.
3. If the request is ambiguous, choose the conservative interpretation and state it at the start, for example: default soft mode, wall-clock time counts while waiting, and work may finish early.
4. If work finishes early, stop and report. Do not fill the time with unrelated work.

## Checkpoints

Run `scripts/timebox.py check` before each phase:

- reading or exploring code
- editing files
- running tests, builds, or long scripts
- committing, pushing, or other handoff-sensitive actions
- writing the final summary

When `status` is `finalizing`, do not start broad new changes. Focus on validation, cleanup, notes, and handoff. When `status` is `expired`, stop starting work and produce a concise handoff.

Default finalization buffer:

- duration under 10 minutes: 1-2 minutes
- otherwise: `max(5 minutes, min(10 minutes, duration * 10%))`

## Modes

- `soft` default: treat time as a high-priority constraint, but do not wrap ordinary commands and do not kill running commands. At the deadline, stop starting new work and summarize as soon as practical.
- `guarded`: use `scripts/run_with_deadline.py` only for commands that may exceed the remaining safe window, such as full test suites, builds, large migrations, or long data scripts. Do not wrap normal short commands.
- `hard`: for explicit hard-deadline requests only. Long commands must run through `scripts/run_with_deadline.py` so the child process can be terminated at the deadline.

If `run_with_deadline.py` stops a command, the final report must name the stopped command, say how much time remained or how far past deadline it stopped, and list validations or work that did not finish. Read `references/stop-policy.md` when handling a stopped command or expired timebox.

## Script Usage

Start examples:

```bash
python3 scripts/timebox.py start "1h"
python3 scripts/timebox.py start "3h15m" --mode guarded
python3 scripts/timebox.py start "1小时20分钟"
python3 scripts/timebox.py start "until 18:30" --mode hard
```

Check and summarize:

```bash
python3 scripts/timebox.py check
python3 scripts/timebox.py summary
```

Wrap a long command only in `guarded` or `hard` mode:

```bash
python3 scripts/run_with_deadline.py --state work/timebox/timebox-state.json -- pytest
```

Waiting for approvals or external input counts against wall-clock time unless the user says otherwise.
