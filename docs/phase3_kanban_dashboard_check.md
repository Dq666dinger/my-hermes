# Phase 3 Kanban Dashboard Check

## 本阶段做了什么

按开发文档的 `Phase 3` 要求，完成了 Hermes 原生 Kanban 与 Dashboard 的最小可用验证：

1. 显式执行 `hermes kanban init`
2. 确认 gateway 已运行
3. 确认当前 Kanban board 状态
4. 创建测试任务并分配给 `scriptwriter`
5. 用 CLI 验证 `list / show / tail / runs`
6. 临时拉起 dashboard，并通过 kanban dashboard 插件 API 验证任务卡、详情、事件和运行记录可见

本阶段没有修改 Hermes 核心源码，也没有修改 profile prompt，仅做环境验证与文档沉淀。

## 修改了哪些文件

- `docs/phase3_kanban_dashboard_check.md`

## 运行了哪些命令

```bash
hermes kanban boards list
hermes kanban stats
hermes kanban init
hermes gateway status

hermes kanban create "测试：写一个美发店搞笑短视频方案" --assignee scriptwriter --json
hermes kanban list
hermes kanban show t_fcf7915b
hermes kanban tail t_fcf7915b
hermes kanban runs t_fcf7915b

hermes dashboard --no-open --port 9121
GET /api/plugins/kanban/board
GET /api/plugins/kanban/tasks/t_fcf7915b
```

说明：

- Dashboard 仍使用显式端口 `9121` 做验证，避免默认端口在当前环境中的不稳定表现。
- 当前终端环境不适合做人眼浏览器点检，因此 dashboard 侧验证使用官方内建插件 API 作为等价证据。

## 当前环境状态

### Gateway

`hermes gateway status` 结果表明：

- user gateway service 已运行
- systemd linger 已启用
- gateway 运行时长正常

虽然 status 输出提示“installed gateway service definition is outdated”，但不影响本阶段的 Kanban worker 调度验证。

### Kanban Board

`hermes kanban boards list` 结果：

```text
● default  Default
Current board: default
```

说明当前系统使用 `default` board，满足本阶段最小验证条件。

### 初始化结果

`hermes kanban init` 输出：

```text
Kanban DB initialized at /home/lenovo/.hermes/kanban.db
Discovered 4 profile(s) on disk:
  default
  novelist
  orchestrator
  scriptwriter
```

结论：

- Kanban 数据库初始化成功
- `Phase 1` 创建的三个 profile 已被 Kanban 正常识别

## 测试任务

创建命令：

```bash
hermes kanban create "测试：写一个美发店搞笑短视频方案" --assignee scriptwriter --json
```

创建结果：

```json
{
  "id": "t_fcf7915b",
  "title": "测试：写一个美发店搞笑短视频方案",
  "assignee": "scriptwriter",
  "status": "ready"
}
```

任务 id：

- `t_fcf7915b`

## CLI 验证结果

### 1. list

`hermes kanban list` 输出摘要：

```text
▶ t_fcf7915b  ready     scriptwriter          测试：写一个美发店搞笑短视频方案
```

结论：

- 任务创建成功
- assignee 正确为 `scriptwriter`

### 2. show

初次 `show` 时任务处于 `ready`，随后等待 dispatcher tick 后再次查看，任务进入 `running`：

```text
Task t_fcf7915b: 测试：写一个美发店搞笑短视频方案
  status:    running
  assignee:  scriptwriter
  workspace: scratch @ /home/lenovo/.hermes/kanban/workspaces/t_fcf7915b
```

事件摘要：

```text
[2026-05-10 20:52] created
[2026-05-10 20:53] [run 1] claimed
[2026-05-10 20:53] [run 1] spawned
```

结论：

- gateway 内嵌 dispatcher 已成功 claim 并 spawn 该任务
- 任务真实进入运行态

### 3. tail

`timeout 5s hermes kanban tail t_fcf7915b` 输出摘要：

```text
Tailing events for t_fcf7915b. Ctrl-C to stop.
[2026-05-10 20:52] created {'assignee': 'scriptwriter', 'status': 'ready', 'parents': [], 'tenant': None, 'skills': None}
```

结论：

- `tail` 能看到任务事件流

### 4. runs

等待 dispatcher 捡起任务后，`hermes kanban runs t_fcf7915b` 输出摘要：

```text
#    OUTCOME       PROFILE            ELAPSED  STARTED
  1  (running)     scriptwriter            3m  2026-05-10 20:53
```

结论：

- 任务运行历史可见
- 当前存在 `scriptwriter` 的 active run

## Dashboard 验证结果

### 启动方式

使用：

```bash
hermes dashboard --no-open --port 9121
```

### 插件 API 验证

读取：

- `GET http://127.0.0.1:9121/api/plugins/kanban/board`
- `GET http://127.0.0.1:9121/api/plugins/kanban/tasks/t_fcf7915b`

返回摘要：

```text
columns={"ready":0,"running":1,"done":0,"todo":0,"triage":0,"blocked":0}
found={"column":"running","id":"t_fcf7915b","assignee":"scriptwriter","status":"running"}
task_status=running
task_assignee=scriptwriter
comments=0
events=3
runs=1
```

等价结论：

1. Dashboard Kanban 页面可读到 board 数据
2. 测试任务位于 `running` 列
3. assignee 显示为 `scriptwriter`
4. task detail API 可读到事件与 runs

这足以证明：

- 任务出现在 dashboard
- dashboard 可读到任务详情
- dashboard 可读到事件流和运行记录

## 测试结果摘要

| 测试项 | 结果 | 结论 |
|---|---|---|
| `hermes kanban init` | 通过 | 数据库初始化成功 |
| gateway 可用 | 通过 | dispatcher 可 claim/spawn 任务 |
| 任务创建 | 通过 | assignee=`scriptwriter` |
| `hermes kanban list` | 通过 | 能列出测试任务 |
| `hermes kanban tail` | 通过 | 能看到事件 |
| Dashboard 可启动 | 通过 | `9121` 临时实例可提供 API |
| Dashboard board 可见任务 | 通过 | 任务位于 `running` 列 |
| Dashboard 详情可见 | 通过 | `events=3`, `runs=1` |

## 未解决问题

1. `hermes dashboard --status` 仍然会把当前检查进程误算进去，不适合作为可靠验收依据。
2. 默认 dashboard 端口 `9119` 在当前环境中仍未作为本阶段主验证端口使用。
3. 本阶段使用的是 dashboard 插件 API 验证，而不是人工浏览器点击截图。

## 下一阶段风险

1. `Phase 4` 会真正验证 comment 微调是否生效，届时需要观察 worker 是否能在阶段检查点吸收反馈。
2. 当前测试任务 `t_fcf7915b` 仍处于运行中，后续阶段应避免和它混淆，建议使用新的测试任务 id。
3. `Phase 4` 起将开始验证 prompt 约束是否真正作用于 worker 的 Kanban 执行路径，而不只是 chat 路径。
