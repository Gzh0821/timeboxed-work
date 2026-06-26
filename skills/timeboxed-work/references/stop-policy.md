# Stop Policy

Use this reference when the timebox reaches the finalization buffer, expires, or a command is stopped by `scripts/run_with_deadline.py`.

## Scope Control

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
