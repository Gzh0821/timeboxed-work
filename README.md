# timeboxed-work

`timeboxed-work` 是一个让 AI agent 按固定时间预算工作的 skill。你可以要求 agent “工作 1 小时”“推进 3 小时 15 分钟”或“到 18:30 停止并交接”，它会把时间预算转换成明确截止时间，提前规划任务量，在关键阶段检查剩余时间，并在到点前后整理结果与交接信息。

English: `timeboxed-work` helps an AI agent plan, work, improve, and hand off within a wall-clock timebox.

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
- 希望小任务完成后继续做有价值的测试、优化、清理或细化，尽量用满给定时间。
- 希望长测试、构建或脚本在硬截止场景下不要无限运行。
- 希望把“还有多久”从主观估算改成脚本记录的确定性状态。
- 希望多个 session、agent 或 app 同时工作时，各自按自己的时间预算计时，互不混淆。

你可以这样提出请求：

```text
用 timeboxed-work 推进这个任务 90 分钟。
```

```text
用满 1 小时，主任务完成后继续优化和补测试，到时间再交接。
```

```text
工作到 18:30，时间到了就停止并交接。
```

```text
这是 hard deadline，必须准点停。先做 must，再做 should，来不及就停下交接。
```

```text
我会开两个 agent：A 做 45 分钟，B 做 2 小时。请分别计时，互不影响。
```

## 两种时间意图

- `bounded`：把时间当上限。任务完成后可以提前交付，不为了填满时间做无意义工作。
- `stretch`：把时间当目标工作时长。主任务完成后，继续做有价值、低风险、能在剩余时间内完成的改进，例如修边界问题、补测试、清理复杂代码、完善文档或优化交接质量。

如果你想让小任务也尽量用满时间，请说清楚“用满 N 分钟/小时”“持续优化到点”或“主任务完成后继续细化”。

## 工作模式

- `soft`：默认模式。时间是高优先级约束，但不会强行杀掉已经在运行的命令；到点后停止开启新工作并尽快总结。
- `guarded`：只对明显可能超时的长命令使用 deadline wrapper，例如全量测试、构建或长脚本。
- `hard`：仅在你明确要求“时间优先”“必须准点停”“硬截止”或 “hard deadline” 时使用。长命令会通过 wrapper 执行，到点可终止子进程。

## 多会话隔离

每个 timebox 都会有独立的 `timebox_id` 和状态文件。多个 session、agent 或 app 在同一个仓库里同时工作时，应该分别使用自己的 id 和状态文件，避免 A 的剩余时间被 B 读取或覆盖。

如果运行环境能提供 thread id、session id、agent name 或 app task id，skill 会优先使用它作为隔离标识；如果没有，脚本会在开始时生成一个唯一 id，并在后续检查中复用同一个状态文件。

## 注意事项

这个 skill 不是硬实时控制器。它能约束 agent 自己启动的工作流程，并能控制通过 wrapper 启动的子命令；如果你需要宿主环境级别的强制中断，还需要外层监督器或运行环境支持。

大任务会优先规划 `must / should / could`，并在过程中检查进度；如果时间不够，会裁掉低优先级范围，保护一个可验证的核心结果和清晰交接。等待审批或外部输入默认仍然计入墙钟时间，除非你明确说明不计入。

## License

Apache License 2.0. See [LICENSE](LICENSE).
