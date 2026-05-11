# Phase 8 失败恢复与成本控制

## 本阶段做了什么

按开发文档的 `Phase 8` 目标，这一阶段把“失败恢复与成本控制”从已有的 prompt 约束补成了可验证、可回归、可在 Windows 隔离运行时里复现的正式能力。

本阶段完成的核心点：

1. 收紧 `scriptwriter` / `novelist` 的继续写、续写、修订类任务规则
2. 把失败注释字段固定成可测试的明确项
3. 为 Phase 8 新增独立契约测试
4. 补齐 Windows 后台 worker 的 quiet 启动修复，避免 `prompt_toolkit` 在无控制台场景崩溃
5. 用仓库内隔离 `HERMES_HOME` + `HermesWorkspace` 完成一次真实 `novelist` 联调验收

## 仓库内修改

- 更新 `plans/text_agent_profiles/scriptwriter.SOUL.md`
- 更新 `plans/text_agent_profiles/novelist.SOUL.md`
- 更新 `hermes_cli/kanban_db.py`
- 新增 `tests/test_text_agent_phase8_contract.py`
- 更新 `tests/hermes_cli/test_kanban_core_functionality.py`
- 新增 `docs/phase8_failure_cost_control.md`

## 规则层补强

### 1. 失败恢复规则收口

两个 worker 现在都明确要求：

- 任意工具调用或生成失败，最多自动重试一次
- 第二次失败后不得继续重试
- 必须在 task comment 中写出四项固定字段：
  - `Failed stage`
  - `Failure reason`
  - `Completed partial work`
  - `Recommended next step`
- 需要人工判断时必须 `block`，不能假装完成

### 2. 成本控制规则收口

两个 worker 现在都明确要求：

- 长文本前先给计划 / 方向
- 交付必须有范围边界
- 不清楚续写锚点时，先 `block` 再等补资料

### 3. 继续写 / 修订任务澄清清单

`scriptwriter` 新增 `## Continuation Clarification`：

- 项目/系列名
- 要继续或修订的 episode / scene / section / draft
- 已批准素材的文件路径或摘要
- 必须吸收的修改意见 / 锁定约束

`novelist` 新增 `## Continuation Clarification`：

- 小说/项目名
- 要继续或修订的 chapter / section
- 已有素材的文件路径或摘要
- 必须继承的情节节拍 / 文风 / 最新反馈

## 自动化验证

### 运行命令

```powershell
& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m pytest -o addopts='' -p no:cacheprovider --basetemp .tmp_phase8_pytest_postfix tests\hermes_cli\test_kanban_core_functionality.py tests\hermes_cli\test_kanban_boards.py -k "default_spawn or max_retries"

& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m pytest -o addopts='' -p no:cacheprovider --basetemp .tmp_phase8_pytest_text tests\test_text_agent_phase8_contract.py tests\hermes_cli\test_kanban_cli.py tests\test_text_agent_routing.py tests\test_text_agent_workspace.py tests\tools\test_text_agent_workspace_tool.py
```

### 结果

- `tests/hermes_cli/test_kanban_core_functionality.py` + `tests/hermes_cli/test_kanban_boards.py`：
  - `8 passed`
- `tests/test_text_agent_phase8_contract.py`
  - `5 passed`
- `tests/hermes_cli/test_kanban_cli.py`
  - `40 passed`
- `tests/test_text_agent_routing.py`
  - `7 passed`
- `tests/test_text_agent_workspace.py`
  - `3 passed`
- `tests/tools/test_text_agent_workspace_tool.py`
  - `2 passed`

覆盖点包括：

1. Phase 8 契约文本存在且包含失败恢复 / 成本控制 / 续写澄清规则
2. Dispatcher 的 `--max-retries` 电路熔断仍然工作
3. `_default_spawn(...)` 现在会用 quiet chat 模式启动后台 worker
4. Phase 6 / Phase 7 的文本路由与 workspace 链路没有被带坏

## Windows 隔离联调

### 运行时约束

本阶段真实联调没有碰用户现有 `~/.hermes` / `profiles` / `kanban.db` / `HermesWorkspace`。

使用的是仓库内隔离运行时：

- runtime root：`tmp/phase8_runtime/20260511_170450`
- `HERMES_HOME`：`tmp/phase8_runtime/20260511_170450/hermes_home`
- workspace：`tmp/phase8_runtime/20260511_170450/HermesWorkspace`

使用的解释器与 provider：

- Python：`E:\ProgrammingSoftware\Anaconda\python.exe`
- provider：`alibaba`
- model：`qwen3.5-plus`

说明：

- 按本阶段实现计划，真实联调使用了 DashScope 路径
- 当前 shell 里的 `DASHSCOPE_API_KEY` / `DASHSCOPE_API_BASE` 带有外层双引号，联调脚本仅在隔离进程内做了 `Trim('"')`，没有修改用户持久环境
- 这次属于阶段级例外验证；后续阶段仍应回到总计划里优先的 `deepseek-v4-flash`

### 先暴露出的 Windows 问题

第一次联调任务：

- runtime：`tmp/phase8_runtime/20260511_165450`
- task：`t_76266535`

当时 worker 被 dispatcher 拉起后，没有控制台窗口，直接在 `prompt_toolkit` 初始化时报错：

- `prompt_toolkit.output.win32.NoConsoleScreenBufferError`

这说明原来的后台 spawn 命令虽然能在类 Unix 场景工作，但在 Windows 无控制台 worker 场景并不安全。

本阶段因此补了 `hermes_cli/kanban_db.py`：

- 后台 worker 从 `chat -q` 改为 `chat -Q -q`
- 让 banner / spinner / prompt_toolkit 输出在后台 worker 中被抑制

### 最终通过的真实联调命令

隔离运行时里实际执行的关键命令如下：

```powershell
& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m pip install -e .

& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m hermes_cli.main profile create orchestrator --no-alias
& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m hermes_cli.main profile create scriptwriter --no-alias
& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m hermes_cli.main profile create novelist --no-alias

Copy-Item plans\text_agent_profiles\orchestrator.SOUL.md <isolated>\profiles\orchestrator\SOUL.md -Force
Copy-Item plans\text_agent_profiles\scriptwriter.SOUL.md <isolated>\profiles\scriptwriter\SOUL.md -Force
Copy-Item plans\text_agent_profiles\novelist.SOUL.md <isolated>\profiles\novelist\SOUL.md -Force

& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m hermes_cli.main kanban init
& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m hermes_cli.main kanban bootstrap-text-agent-workspace --root <isolated>\HermesWorkspace

& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m hermes_cli.main -p orchestrator chat -q "你是谁？只回答你的角色名称。" -Q --provider alibaba -m qwen3.5-plus
& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m hermes_cli.main -p scriptwriter chat -q "你是谁？只回答你的角色名称。" -Q --provider alibaba -m qwen3.5-plus
& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m hermes_cli.main -p novelist chat -q "你是谁？只回答你的角色名称。" -Q --provider alibaba -m qwen3.5-plus

& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m hermes_cli.main kanban create "继续写那个故事" --assignee novelist --workspace dir:<isolated>\HermesWorkspace --max-retries 1 --json
& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m hermes_cli.main kanban dispatch
& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m hermes_cli.main kanban show <task-id>
& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m hermes_cli.main kanban runs <task-id>
& 'E:\ProgrammingSoftware\Anaconda\python.exe' -m hermes_cli.main kanban log <task-id>
```

### 联调结果

身份冒烟：

- `orchestrator` -> `orchestrator`
- `scriptwriter` -> `scriptwriter`
- `novelist` -> `novelist`

真实 Phase 8 验证任务：

- task id：`t_9b7bd30f`
- title：`继续写那个故事`
- assignee：`novelist`
- `--max-retries 1`

最终状态：

- `blocked`

`show` / `runs` 摘要：

- dispatcher 只 spawn 了 `1` 次
- task 在 `56s` 内进入 `blocked`
- 没有进入无限重试
- 没有直接输出小说正文

worker 最终 block reason：

```text
任务标题是"继续写那个故事"，但工作区是空的——没有已有的小说项目、没有章节文件、没有评论说明。请告诉我：1）小说名称是什么？2）要继续哪个章节或段落？3）有没有之前写好的文件路径或内容摘要？4）有任何风格或情节上的要求吗？
```

这条结果满足 `Phase 8` 的通过标准：

1. `novelist` 没有瞎写正文
2. 任务被 `block`
3. block reason 明确索取了续写锚点
4. dispatcher 没有在失败后无限重试

### 日志摘要

最终通过任务 `t_9b7bd30f` 的 worker log 为空，这是预期结果：

- 因为后台 worker 现在以 quiet 模式运行
- 不再输出 prompt_toolkit banner / spinner
- 关键验收信息以 task 状态、event、run summary 为准

## 本阶段结论

`Phase 8` 判定为完成。

完成依据：

1. 失败恢复规则已经从泛化描述收紧成明确可检查字段
2. 成本控制规则已经覆盖“长文本前先计划”“交付范围边界”“不清楚续写就 block”
3. 新增了独立的 Phase 8 契约测试
4. Windows 后台 worker 的 quiet 启动问题已修复
5. 仓库内隔离运行时真实联调已经证明：
   - 身份正确
   - `novelist` 面对模糊续写会 `block`
   - 不会无限重试

## 未解决问题

1. 当前 shell 中的 `DASHSCOPE_API_KEY` 与 `DASHSCOPE_API_BASE` 仍然带有外层双引号。
   这次只在隔离进程里做了裁剪，没有修改用户环境本身。

2. 本阶段只对 `novelist` 跑了真实“模糊续写 -> block”联调。
   `scriptwriter` 的续写 / 修订类真实联调建议在 `Phase 9` 总验收补齐。

## 下一阶段风险

1. `Phase 9` 要做完整链路验收，必须覆盖：
   - `scriptwriter` 完整交付链路
   - `novelist` 完整交付链路
   - 跨任务改编链路

2. 如果后续验收要切回 `deepseek-v4-flash`，需要先确认当前 Windows 隔离运行时里对应 provider 可用，并保持与本阶段相同的隔离环境纪律。
