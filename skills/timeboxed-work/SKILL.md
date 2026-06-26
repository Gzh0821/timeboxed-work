---
name: timeboxed-work
description: Work under an explicit time budget with deterministic deadline tracking, useful stretch work, scope control, and handoff. Use when the user asks for a timebox, fixed duration, deadline, work for N minutes/hours, use the full time, keep improving until the deadline, stop at a specific time, hard deadline, guarded deadline, 按固定时间工作, 工作 N 分钟/小时, 做满时间, 持续优化到点, 到点停止, 时间预算, or similar bounded-work requests.
---

# Timeboxed Work

Use this skill to keep agent work aligned with a user-specified wall-clock budget. `mode` controls deadline enforcement; `intent` controls whether to finish early or continue useful improvement work. This skill is not a hard real-time controller; hard stops require host or outer-supervisor support. `scripts/run_with_deadline.py` can only control child commands launched through it.

## Start Protocol

1. Create state before doing task work:
   ```bash
   python3 scripts/timebox.py start "<budget>" --mode soft --intent bounded
   ```
   Use `--mode guarded` only when the user asks for guarded deadline behavior. Use `--mode hard` only when the user explicitly says time is priority, must stop exactly on time, hard deadline, 硬截止, 必须准点停, or equivalent.
2. Use `--intent stretch` when the user asks to work/spend/use the full time, keep improving until the deadline, 做满时间, 持续优化到点, or when a fixed-duration request clearly means sustained effort rather than just an upper bound.
3. Convert relative budgets to an absolute `deadline_at` from the JSON output. Do not estimate the current time from memory.
4. If the request is ambiguous, choose a conservative interpretation and state it at the start, for example: default soft mode, bounded intent, wall-clock time counts while waiting, and work may finish early.

## Planning Protocol

Before doing substantive work, make a time-aware scope plan:

- Identify `must`, `should`, and `could` outcomes.
- Reserve the finalization buffer before allocating work time.
- Allocate rough time slices to the first useful `must` items, then `should`, then `could`.
- Set a checkpoint cadence: use `min(15 minutes, max(5 minutes, remaining work time / 4))`, or every phase boundary for short timeboxes.
- State the interpretation briefly: mode, intent, deadline, finalization buffer, and whether waiting counts. Waiting counts by default unless the user says otherwise.

At each checkpoint, compare progress with the plan. If behind, cut `could` first, then `should`, and protect a small verified `must` result plus handoff over a larger unfinished change.

## Intent

- `bounded` default: finish when the useful requested task is complete. Do not fill time with unrelated work. If work finishes early, report completion and stop.
- `stretch`: keep working until the timebox reaches finalization, as long as there is useful, low-risk improvement work. Do not invent unrelated work merely to consume time. If no valuable stretch work remains, finish early and say why.

Useful stretch work should follow this order:

1. correctness, safety, failing edge cases, and regressions
2. focused tests or validation gaps
3. cleanup that reduces real complexity without broad rewrites
4. documentation, examples, or handoff quality
5. small usability, performance, or polish improvements grounded in the task

In `stretch` intent, choose improvements that can fit the remaining safe window. Do not start broad refactors or risky changes near the finalization buffer.

## Checkpoints

Run `scripts/timebox.py check` before each phase:

- reading or exploring code
- editing files
- running tests, builds, or long scripts
- selecting stretch improvements
- cutting scope because progress is behind
- committing, pushing, or other handoff-sensitive actions
- writing the final summary

When `status` is `finalizing`, do not start broad new changes, even in `stretch` intent. Focus on validation, cleanup, notes, and handoff. When `status` is `expired`, stop starting work and produce a concise handoff.

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
python3 scripts/timebox.py start "1h" --intent stretch
python3 scripts/timebox.py start "3h15m" --mode guarded --intent stretch
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
