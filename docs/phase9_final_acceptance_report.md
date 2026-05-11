# Phase 9 最终完整功能验收报告

## 当前结论

截至 2026-05-11，`Phase 9` 的仓库内开发工作已经收口，自动化回归与仓库内隔离运行时的 exploratory live gate 也已经补齐并通过。

当前唯一阻塞项不是代码，而是总计划要求优先使用的正式门禁模型凭证不可用：

- `deepseek / deepseek-v4-flash`：`401 authentication_error`
- `xiaomi / mimo-v2.5`：`401 invalid_key`

因此：

- 本仓库内的 `Phase 9` 开发与 exploratory 验证已完成
- 外部总计划 `../hermes_text_agents_development_plan.md` 仍 **暂不更新为 Phase 9 完成**
- 只要补好有效的正式门禁凭证，再按相同隔离运行时纪律重跑正式 live gate，即可决定是否结项

## 本阶段完成了什么

### 1. 补齐最终验收的自动化契约

新增和补强了以下覆盖：

- `tests/test_text_agent_phase9_acceptance.py`
- `tests/tools/test_kanban_tool_runtime_toolset_env.py`
- `tests/tools/test_local_git_bash_resolution.py`
- `tests/tools/test_text_agent_workspace_tool.py`

覆盖重点：

1. 场景 A：剧本请求必须路由到 `scriptwriter`
2. 场景 A：任务体必须要求先给方向、写 `kanban_comment(...)`、再 `kanban_block(...)`
3. 场景 A：首轮不得直接产出完整 `scripts/ep*.md`
4. 场景 B：小说请求必须路由到 `novelist`
5. 场景 B：任务体必须要求先写计划、先 comment、再 block，且首轮不得直接铺满完整设定包
6. 场景 C：小说 IP 改编必须拆成 `novelist -> scriptwriter`
7. 场景 C：`scriptwriter` 任务必须显式引用配对的 `novelist` 项目路径与核心源文件
8. `oneshot --toolsets kanban` 必须真实桥接到 runtime toolset gating
9. Windows 本地 worker 必须优先解析 Git Bash，而不是误用 `C:\Windows\System32\bash.exe`

### 2. 修复 runtime-toolset gating 缺口

更新：

- `hermes_cli/oneshot.py`
- `tools/kanban_tools.py`
- `tools/text_agent_workspace_tool.py`

修复结果：

- `oneshot --toolsets kanban` 现在会写入 `HERMES_ACTIVE_TOOLSETS`
- `kanban` / `text_agent_workspace` tool 的 gating 能直接识别这一 runtime 桥接
- fresh runtime 不再需要额外手写 profile 级 `config.yaml` 才能让 orchestrator 拿到 Kanban tools

### 3. 收紧 orchestrator / worker 协议

更新：

- `plans/text_agent_profiles/orchestrator.SOUL.md`
- `plans/text_agent_profiles/scriptwriter.SOUL.md`
- `plans/text_agent_profiles/novelist.SOUL.md`
- `hermes_cli/text_agent_routing.py`

修复结果：

- orchestrator 创建 durable task 时，必须把 `workspace_kind="dir"` 和绝对 `workspace_path` 写进任务字段，而不只是写进正文
- `scriptwriter` 首轮交付被强制收紧为“方向选项 -> `kanban_comment(...)` -> `kanban_block(...)`”
- `novelist` 首轮交付被强制收紧为“计划/方向选项 -> `kanban_comment(...)` -> `kanban_block(...)`”
- 跨任务改编时，`scriptwriter` 任务体会显式引用上游 `novelist` 项目路径，并要求读取：
  - `01_worldbuilding.md`
  - `02_characters.md`
  - `03_plot_outline.md`
  - `04_chapter_outline.md`
  - `05_style_guide.md`
  - `feedback_log.md`

### 4. 修复 Windows 本地 worker 的 Git Bash 解析

更新：

- `tools/environments/local.py`

修复结果：

- Windows 下不再把 `C:\Windows\System32\bash.exe` 误当作 Git Bash
- 现在会优先从 `git.exe` 附近解析真实 Git Bash
- Git Bash 风格的 `/e/...` cwd 会在启动前转换回原生 Windows 路径
- LocalEnvironment 不再把这类 cwd 误判成“目录不存在”

## 仓库内修改文件

- `hermes_cli/oneshot.py`
- `hermes_cli/text_agent_routing.py`
- `plans/text_agent_profiles/orchestrator.SOUL.md`
- `plans/text_agent_profiles/scriptwriter.SOUL.md`
- `plans/text_agent_profiles/novelist.SOUL.md`
- `tests/test_text_agent_phase9_acceptance.py`
- `tests/tools/test_kanban_tool_runtime_toolset_env.py`
- `tests/tools/test_local_git_bash_resolution.py`
- `tests/tools/test_text_agent_workspace_tool.py`
- `tools/kanban_tools.py`
- `tools/environments/local.py`
- `tools/text_agent_workspace_tool.py`
- `docs/phase9_final_acceptance_report.md`

## 自动化验证

### 运行命令

```powershell
& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m pytest -o addopts='' -p no:cacheprovider --basetemp .tmp_phase9_pytest_targeted tests\test_text_agent_phase9_acceptance.py tests\test_text_agent_routing.py tests\hermes_cli\test_kanban_cli.py -k "route_text_request or phase9"

& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m pytest -o addopts='' -p no:cacheprovider --basetemp .tmp_phase9_pytest_full tests\test_text_agent_phase8_contract.py tests\test_text_agent_phase9_acceptance.py tests\hermes_cli\test_kanban_cli.py tests\test_text_agent_routing.py tests\test_text_agent_workspace.py tests\tools\test_text_agent_workspace_tool.py tests\hermes_cli\test_kanban_core_functionality.py -k "max_retries or route_text_request or bootstrap_text_agent_workspace or phase8_contract or phase9 or text_agent"

& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m pytest -o addopts='' -p no:cacheprovider --basetemp .tmp_phase9_pytest_toolenv tests\tools\test_kanban_tool_runtime_toolset_env.py tests\tools\test_text_agent_workspace_tool.py tests\test_text_agent_phase9_acceptance.py tests\test_text_agent_routing.py -q

& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m pytest -o addopts='' -p no:cacheprovider --basetemp .tmp_phase9_pytest_final_round2 tests\tools\test_kanban_tool_runtime_toolset_env.py tests\tools\test_text_agent_workspace_tool.py tests\tools\test_local_git_bash_resolution.py tests\test_text_agent_phase9_acceptance.py tests\test_text_agent_routing.py tests\hermes_cli\test_kanban_cli.py tests\test_text_agent_phase8_contract.py -q
```

### 结果

- 定向回归：`5 passed`
- Phase 9 主体回归：`27 passed`
- runtime-toolset / workspace / routing 定向回归：`14 passed`
- 最新最终汇总回归：`63 passed`

覆盖面包括：

1. Phase 8 契约没有回退
2. Phase 9 三个场景的 routing / dependency / workspace 约束成立
3. CLI 的 `route-text-request` / `bootstrap-text-agent-workspace` 仍可用
4. `oneshot --toolsets kanban` 的 runtime 桥接已真实纳入回归
5. Windows Git Bash 解析与 cwd 归一化已纳入回归

## 隔离运行时联调

### 运行时纪律

所有 live 验证都使用仓库内隔离目录，未改写任何用户级：

- `~/.hermes`
- 已有 profiles
- 已有 `kanban.db`
- 已有 `HermesWorkspace`

### 正式门禁模型检查

按总计划约束优先检查：

1. `deepseek / deepseek-v4-flash`
2. `xiaomi / mimo-v2.5`（仅在 DeepSeek 不可用时回退）

实际结果：

- `deepseek-v4-flash`：`401 authentication_error`
- `mimo-v2.5`：`401 invalid_key`

这意味着 **正式门禁 live gate 目前只能停在凭证问题，不能继续判定代码通过或失败。**

### 非门禁 exploratory live gate

为完成仓库内开发验证，使用当前 shell 中可用的 DashScope 凭证，在隔离进程内做了 exploratory run：

- provider：`alibaba`
- model：`qwen3.5-plus`

说明：

- 当前 shell 的 `DASHSCOPE_API_KEY` / `DASHSCOPE_API_BASE` 外层带引号
- 仅在隔离进程内做了 `Trim('"')`
- 没有修改用户持久环境

## Exploratory Live Results

### 场景 A：剧本任务完整链路的首轮 gating

运行时：

- runtime：`tmp/phase9_runtime/20260511_181817`
- task：`t_38425864`

结果：

- orchestrator 正确创建 `scriptwriter` durable task
- task row 正确落成 `workspace_kind=dir`
- `scriptwriter` 首轮输出 1 条方向选择 comment
- 随后任务进入 `blocked`
- 首轮没有直接产出完整 `scripts/ep*.md`
- 仓库内只留下轻量 scaffolding

结论：

- 场景 A 的“先方向、再完整剧本”的首轮强约束已生效

### 场景 B：小说任务完整链路的首轮 gating

运行时：

- runtime：`tmp/phase9_runtime/20260511_190955`
- task：`t_7bb67b18`

结果：

- orchestrator 正确创建 `novelist` durable task
- `novelist` 先写了 1 条 comment，提供 3 个方向选项
- 随后任务进入 `blocked`
- block reason 明确要求用户选择方向
- 项目目录只保留轻量 scaffolding：
  - `01_worldbuilding.md`
  - `02_characters.md`
  - `03_plot_outline.md`
  - `04_chapter_outline.md`
- 没有在首轮直接铺满完整 worldbuilding / character / plot package

结论：

- 场景 B 的“先计划/方向、再长文本设定包”的首轮强约束已生效

### 场景 C：跨任务协作

运行时：

- runtime：`tmp/phase9_runtime/20260511_191245`
- novelist task：`t_ee67ee69`
- scriptwriter task：`t_35fc1157`

结果：

- orchestrator 正确拆成 `novelist -> scriptwriter` 两个任务
- `scriptwriter` 任务对 `novelist` 任务存在依赖
- `scriptwriter` 任务体显式引用了上游 `novelist` 项目路径
- `scriptwriter` 任务体显式要求读取 `01_worldbuilding.md`、`02_characters.md`、`03_plot_outline.md`
- dispatch 后仅 `novelist` 先运行
- `novelist` 首轮提供 3 个方向选项并进入 `blocked`
- `scriptwriter` 保持 `todo`，没有越过依赖提前开写

结论：

- 场景 C 的拆分、依赖、source-path 引用、上游先行 gating 全部成立

## 手动配置需求

当前只剩 1 类需要手动处理的外部条件：**正式门禁模型凭证**。

请确认并配置以下至少一套可用凭证：

1. 优先：`deepseek`
   - 环境变量：`DEEPSEEK_API_KEY`
   - 默认 base URL：`https://api.deepseek.com/v1`
2. 回退：`xiaomi`
   - 环境变量：`XIAOMI_API_KEY`
   - 默认 base URL：`https://api.xiaomimimo.com/v1`

如果你本地还需要覆盖 base URL，对应入口是：

- `DEEPSEEK_BASE_URL`
- `XIAOMI_BASE_URL`

## 凭证就绪后的收口动作

一旦你把有效凭证配好，我这边只需要再做一轮正式门禁验证：

1. 在 fresh isolated runtime 里重跑 `orchestrator / scriptwriter / novelist` 身份冒烟
2. 用正式门禁模型重跑 Phase 9 live gate
3. 若通过，再更新 `../hermes_text_agents_development_plan.md`，把 `Phase 9` 标记完成

## 本机正式 Gate 脚本

如果当前执行环境不允许代你把私有仓库内容发送到第三方 `DeepSeek` / `Xiaomi` 模型接口，可以直接在你自己的 PowerShell 中运行：

```powershell
& 'E:\ProgrammingWork\Harmes\my-hermes\scripts\phase9_formal_gate.ps1'
```

脚本行为：

1. 自动创建 fresh isolated runtime 到 `tmp/phase9_runtime/<timestamp>/`
2. 自动优先测试 `deepseek-v4-flash`
3. 只有 `deepseek-v4-flash` 不可用时才回退到 `mimo-v2.5`
4. 不会使用任何 `pro` 模型
5. 自动执行 Phase 9 的正式 A / B / C 场景
6. 自动输出 `formal_phase9_summary.json`

跑完后，把 summary JSON 路径或内容回传即可继续收口。

## 当前判断

当前最准确的状态是：

- **代码侧**：已完成
- **自动化回归**：已通过，最新为 `63 passed`
- **仓库内 exploratory live gate**：A / B / C 三个场景均已通过
- **正式结项**：仅被 `deepseek` / `xiaomi` 凭证问题阻塞

因此，`Phase 9` 现在不是“还要继续开发”，而是“等你补正式门禁凭证后做最后一轮收口验证”。
