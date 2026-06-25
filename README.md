# timeboxed-work

`timeboxed-work` 是一个让 AI agent 按固定时间预算工作的 skill。你可以要求 agent “工作 1 小时”“推进 3 小时 15 分钟”或“到 18:30 停止并交接”，它会把时间预算转换成明确截止时间，在关键阶段检查剩余时间，并在到点前后整理结果与交接信息。

English: `timeboxed-work` helps an AI agent work within a wall-clock timebox, stop opening new work near the deadline, and hand off clearly when time is up.

## 安装

使用 Skills CLI 安装：

```bash
npx skills add Gzh0821/timeboxed-work
```

如果只想明确安装这个 skill：

```bash
npx skills add Gzh0821/timeboxed-work --skill timeboxed-work
```

这是 private 仓库，安装者需要拥有 `Gzh0821/timeboxed-work` 的 GitHub 访问权限。

## 适合什么时候用

- 希望 agent 在固定时间内推进任务，而不是无限做下去。
- 希望 agent 到点停止并给出当前进展、剩余问题和下一步交接。
- 希望长测试、构建或脚本在硬截止场景下不要无限运行。
- 希望把“还有多久”从主观估算改成脚本记录的确定性状态。

你可以这样提出请求：

```text
用 timeboxed-work 推进这个任务 90 分钟。
```

```text
工作到 18:30，时间到了就停止并交接。
```

```text
这是 hard deadline，必须准点停。
```

## 工作模式

- `soft`：默认模式。时间是高优先级约束，但不会强行杀掉已经在运行的命令；到点后停止开启新工作并尽快总结。
- `guarded`：只对明显可能超时的长命令使用 deadline wrapper，例如全量测试、构建或长脚本。
- `hard`：仅在你明确要求“时间优先”“必须准点停”“硬截止”或 “hard deadline” 时使用。长命令会通过 wrapper 执行，到点可终止子进程。

## 注意事项

这个 skill 不是硬实时控制器。它能约束 agent 自己启动的工作流程，并能控制通过 wrapper 启动的子命令；如果你需要宿主环境级别的强制中断，还需要外层监督器或运行环境支持。

如果任务提前完成，agent 应该直接交付结果，不会为了填满时间做无意义工作。等待审批或外部输入默认仍然计入墙钟时间，除非你明确说明不计入。

## License

Apache License 2.0. See [LICENSE](LICENSE).
