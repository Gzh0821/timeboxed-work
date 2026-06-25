# timeboxed-work

`timeboxed-work` is an agent skill for bounded wall-clock work. It helps an AI agent convert a user-specified time budget into an explicit deadline, check remaining time at key phases, and hand off cleanly when the timebox reaches its finalization window or expires.

The skill supports requests such as:

- "work for 1 hour"
- "push this forward for 3h15m"
- "stop at 18:30 and hand off"
- "按固定时间工作"
- "到点停止"

## Install

After publishing this repository to GitHub, install it with the Skills CLI:

```bash
npx skills add <owner>/<repo>
```

To install only this skill from a repository that contains multiple skills:

```bash
npx skills add <owner>/<repo> --skill timeboxed-work
```

To verify discovery from a local checkout:

```bash
npx skills add . --list
```

## What It Provides

- `soft` mode: default behavior; stop opening new work at the deadline and hand off without killing running commands.
- `guarded` mode: selectively wrap long commands that might overrun the remaining safe window.
- `hard` mode: use only for explicit hard-deadline requests; long commands should run through the deadline wrapper.
- Deterministic JSON timebox state via `scripts/timebox.py`.
- Optional child-process deadline control via `scripts/run_with_deadline.py`.

This skill is not a hard real-time controller. The wrapper can only control child commands launched through it; true hard stops require host or outer-supervisor support.

## Repository Layout

```text
skills/timeboxed-work/
├── SKILL.md
├── scripts/
│   ├── timebox.py
│   └── run_with_deadline.py
└── references/
    └── stop-policy.md

skills.sh.json
LICENSE
README.md
```

## Validation

The scripts use only the Python standard library. Useful local checks:

```bash
python3 -m py_compile \
  skills/timeboxed-work/scripts/timebox.py \
  skills/timeboxed-work/scripts/run_with_deadline.py

python3 skills/timeboxed-work/scripts/timebox.py start "3h15m" --state /private/tmp/timebox-test.json

python3 skills/timeboxed-work/scripts/run_with_deadline.py \
  --deadline "$(python3 -c 'import datetime; print((datetime.datetime.now().astimezone() + datetime.timedelta(seconds=2)).isoformat(timespec="seconds"))')" \
  --grace-seconds 0.2 \
  -- sleep 5
```

The deadline wrapper should return exit code `124` when it stops a command.

## License

Apache License 2.0. See [LICENSE](LICENSE).
