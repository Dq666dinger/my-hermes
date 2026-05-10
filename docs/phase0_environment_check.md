# Phase 0 Environment Check

## 本阶段做了什么

按开发文档的 `Phase 0` 要求，对 WSL Ubuntu 中已安装的 Hermes 做了真实环境核验，重点确认了：

- Hermes 版本与命令入口可用。
- `profile create` 的真实参数。
- `kanban` 的真实子命令与 `create` 参数。
- `dashboard` 的帮助参数与实际可访问性。
- 当前环境中会影响后续文本多 Agent 开发的已知风险。

## 修改了哪些文件

- `docs/phase0_environment_check.md`
- `../hermes_text_agents_development_plan.md`（补充阶段进度标注）

## 运行了哪些命令

```bash
hermes --version
hermes version
hermes doctor
hermes profile create --help
hermes kanban --help
hermes kanban create --help
hermes dashboard --help
hermes dashboard --no-open --port 9121
curl --noproxy "*" http://127.0.0.1:9121/
```

说明：

- 实际核验是在 `WSL Ubuntu` 中运行。
- `dashboard` 采用显式端口 `9121` 做可访问性探针，避免默认端口上的历史进程干扰判断。

## 测试了哪些功能

### 1. Hermes 可用性

`hermes --version` 与 `hermes version` 都可用。

日志摘要：

```text
Hermes Agent v0.13.0 (2026.5.7)
Project: /home/lenovo/.hermes/hermes-agent
Python: 3.11.15
OpenAI SDK: 2.36.0
Up to date
```

### 2. 配置健康检查

`hermes doctor` 可正常运行，未发现会阻断当前文本框架开发的致命错误。

关键结论：

- 已存在 `~/.hermes/.env`、`~/.hermes/config.yaml`、`~/.hermes/SOUL.md`、`state.db`
- `kanban` 工具在当前环境可用
- 可选问题包括：
  - `rg` 未安装
  - Playwright Chromium 未安装
  - `tinker-atropos` submodule 未初始化
  - 若干可选认证/外部工具未配置

这些问题目前不会阻断本期“纯文本 worker + Kanban + Dashboard”的主线开发。

### 3. Profile 创建能力

`hermes profile create --help` 结果确认：

```text
usage: hermes profile create [-h] [--clone] [--clone-all]
                             [--clone-from SOURCE] [--no-alias] [--no-skills]
                             profile_name
```

结论：

- 支持 `--clone`
- 支持 `--clone-all`
- 支持 `--clone-from SOURCE`

这意味着 `Phase 1` 可以优先走文档中的“操作方案 A”。

### 4. Kanban 能力

`hermes kanban --help` 结果确认，当前环境支持以下关键动作：

- `init`
- `create`
- `list`
- `show`
- `assign`
- `comment`
- `block`
- `unblock`
- `tail`
- `runs`
- `heartbeat`
- `context`
- `dispatch`
- `watch`
- `stats`

`hermes kanban create --help` 进一步确认：

```text
--assignee ASSIGNEE   Profile name to assign
```

结论：

- 创建任务时使用的是 `--assignee`
- 不是 `--assign`

### 5. Dashboard 能力

`hermes dashboard --help` 结果确认：

```text
usage: hermes dashboard [-h] [--port PORT] [--host HOST] [--no-open]
                        [--insecure] [--tui] [--stop] [--status]
```

帮助信息给出的默认访问地址对应：

- `host`: `127.0.0.1`
- `port`: `9119`

实际可访问性探针结果：

- 在 `9121` 端口临时启动 `hermes dashboard --no-open --port 9121`
- 对 `http://127.0.0.1:9121/` 发起 GET 请求
- 返回 `HTTP/1.1 200 OK`
- 返回体为 dashboard HTML 页面

日志摘要：

```text
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Server: uvicorn

<!doctype html>
<html lang="en">
```

结论：

- Dashboard 可启动
- Dashboard 可访问

## 测试结果摘要

| 测试项 | 结果 | 结论 |
|---|---|---|
| Hermes 可用 | 通过 | 可输出版本信息 |
| 配置健康 | 通过 | 无阻断性问题 |
| Profile 命令可用 | 通过 | 支持 `--clone` |
| Kanban 命令可用 | 通过 | 支持 `comment/block/unblock/tail/context/runs` |
| Kanban 创建参数确认 | 通过 | 使用 `--assignee` |
| Dashboard 可启动 | 通过 | `9121` 探针返回 `200 OK` |

## 本机实际可用参数记录

### Profile

- `hermes profile create <name> --clone`
- `hermes profile create <name> --clone-all`
- `hermes profile create <name> --clone-from <source>`

### Kanban

- 初始化：`hermes kanban init`
- 创建：`hermes kanban create "<title>" --assignee <profile>`
- 追踪：`hermes kanban tail <task-id>`
- 评论：`hermes kanban comment <task-id> "<comment>"`
- 阻塞：`hermes kanban block <task-id>`
- 解除阻塞：`hermes kanban unblock <task-id>`
- 查看上下文：`hermes kanban context <task-id>`
- 查看运行历史：`hermes kanban runs <task-id>`

### Dashboard

- 默认帮助参数：`--host 127.0.0.1 --port 9119`
- 本阶段验证端口：`9121`

## 未解决问题

1. `hermes doctor` 报告 `rg` 未安装，后续某些本机搜索路径会走降级逻辑。
2. `hermes doctor` 报告 Playwright Chromium 未安装，但这不影响当前文本任务框架。
3. `hermes doctor` 报告 `tinker-atropos` submodule 缺失，当前阶段暂未证明会阻断文本 worker 流程。
4. `dashboard` 默认端口 `9119` 在当前会话探针里未给出稳定成功结果；显式端口 `9121` 已验证可用。进入 `Phase 3` 时建议明确指定端口并复测。
5. `hermes dashboard --status` / `--stop` 在当前环境下表现不稳定，本阶段未将其作为验收依据。

## 下一阶段风险

1. `Phase 1` 创建 profile 时，需要避免直接污染默认 `~/.hermes` 主配置，优先采用可回滚策略。
2. 后续每个 profile 的 `SOUL.md` 改造前都要先备份，严格满足开发文档第 12 节要求。
3. 进入 `Phase 3` 时，dashboard 与 gateway 的长期运行方式需要进一步确认，尤其是端口、现有进程和状态检查行为。
4. `kanban` 虽然命令面已确认，但真实 worker 调度与 dashboard 联动仍需在后续阶段实际验证，不能把 help 输出当成功能完成。
