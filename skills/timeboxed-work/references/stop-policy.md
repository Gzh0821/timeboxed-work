# Stop Policy

Use this reference when the timebox reaches the finalization buffer, expires, or a command is stopped by `scripts/run_with_deadline.py`.

## Finalization Buffer

- Stop broad investigation and new feature work.
- Prefer already-started validation, small fixes for known breakages, and cleanup.
- Preserve the current state clearly if verification cannot finish.
- Avoid starting commands whose normal runtime can exceed the remaining time.

## Expired Timebox

- Stop opening new work.
- If a command is already running in `soft` mode, do not kill it solely because the timebox expired; summarize after it returns unless the user gave a hard deadline.
- In `guarded` or `hard` mode, use the wrapper only for commands launched through it.
- Make the final response a handoff, not a new plan.

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
