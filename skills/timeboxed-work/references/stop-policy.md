# Stop Policy

Use this reference when the timebox reaches the finalization buffer, expires, or a command is stopped by `scripts/run_with_deadline.py`.

## Scope Control

- Confirm the `state_file` or `timebox_id` belongs to the current session, agent, or app before using remaining time.
- Protect a small verified `must` result over a larger unfinished result.
- If progress is behind plan, cut `could` items first, then `should` items.
- In `stretch` intent, continue only with useful, low-risk improvements that fit the remaining safe window.
- Stop stretch work before it creates more validation debt than the remaining time can close.

## Finalization Buffer

- Stop broad investigation and new feature work.
- Prefer already-started validation, small fixes for known breakages, and cleanup.
- Preserve the current state clearly if verification cannot finish.
- Avoid starting commands whose normal runtime can exceed the remaining time.
- In `stretch` intent, switch from improvement work to validation and handoff.

## Expired Timebox

- Stop opening new work.
- If a command is already running in `soft` mode, do not kill it solely because the timebox expired; summarize after it returns unless the user gave a hard deadline.
- In `guarded` or `hard` mode, use the wrapper only for commands launched through it.
- Make the final response a handoff, not a new plan.
- Do not keep working to satisfy `stretch` intent after expiration.
- Keep the state file for continuation; do not cleanup expired timeboxes unless the user explicitly says no continuation or audit trail is needed.

## Completion Cleanup

- Cleanup is allowed only when the task is complete, verification is done, user acceptance is not pending, no wrapped command was stopped, and no future session needs the timer state.
- If acceptance is required, keep the state until acceptance passes.
- Use `scripts/timebox.py cleanup --state "<state_file>"`; do not manually remove files.
- Cleanup must target only the current session's `state_file` or `timebox_id`.
- If cleanup is skipped because the state may be useful, include the state path in the handoff.

## Wrapper Termination Report

If `run_with_deadline.py` terminates a child command, include all of this in the final report:

- the exact command that was stopped
- whether it stopped before, at, or after `deadline_at`
- the remaining or overrun seconds from the wrapper summary
- the termination method, such as `terminated` or `killed`
- files changed before the stop
- tests, builds, checks, or reviews that did not complete
- the smallest useful next command or next step for continuation

Do not imply verification passed when a wrapped command timed out.
Do not cleanup the state after a wrapper timeout unless the user explicitly says to discard the run.
