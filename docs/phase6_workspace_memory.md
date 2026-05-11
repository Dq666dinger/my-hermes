# Phase 6 Workspace 与三层记忆

## 本阶段做了什么

按开发文档的 `Phase 6` 目标，这一阶段把“文本 worker 的持久化 workspace、项目目录、三层记忆、项目索引”从约定和临时脚本，推进成了仓库内可复用、可测试、可被 worker 调用的正式能力。

本阶段完成的核心点：

1. Workspace 初始化不再依赖手工 `mkdir`
2. `scriptwriter` / `novelist` 项目模板可以自动创建
3. `shared_memory/project_index.md` 可以自动写入和更新
4. 项目级 `feedback_log.md` 可以通过统一接口追加
5. 长期偏好/部门记忆可以通过统一接口追加
6. SOUL 规则里明确要求优先使用统一工具而不是自由拼文件

## 仓库内修改

- 新增 `hermes_cli/text_agent_workspace.py`
- 新增 `tools/text_agent_workspace_tool.py`
- 更新 `hermes_cli/kanban.py`
- 更新 `hermes_cli/commands.py`
- 更新 `toolsets.py`
- 更新 `scripts/bootstrap_text_agent_workspace.py`
- 更新 `plans/text_agent_profiles/scriptwriter.SOUL.md`
- 更新 `plans/text_agent_profiles/novelist.SOUL.md`
- 更新 `plans/text_agent_profiles/orchestrator.SOUL.md`
- 新增 `tests/test_text_agent_workspace.py`
- 新增 `tests/tools/test_text_agent_workspace_tool.py`
- 更新 `tests/hermes_cli/test_kanban_cli.py`
- 新增 `docs/phase6_workspace_memory.md`

## 新增能力

### 1. CLI 初始化 Workspace

```bash
hermes kanban bootstrap-text-agent-workspace
```

支持：

- `--root`
- `--force`
- `--json`

该命令会初始化：

- `shared_memory/`
- `scriptwriter/memory/`
- `scriptwriter/projects/_template/`
- `novelist/memory/`
- `novelist/projects/_template/`

### 2. 统一的文本工作区模块

`hermes_cli/text_agent_workspace.py` 现在提供了可复用能力：

- `bootstrap_workspace(...)`
- `resolve_workspace_root(...)`
- `ensure_project(...)`
- `upsert_project_index(...)`
- `append_feedback_log(...)`
- `append_memory_note(...)`
- `inspect_workspace(...)`

这些能力补上了 `Phase 6` 真正缺的部分：不仅能建空目录，还能把项目目录、项目索引和记忆文件真正联动起来。

### 3. Worker 可直接调用的工具

新增工具：

```text
text_agent_workspace
```

可执行动作：

- `inspect`
- `ensure_project`
- `append_feedback`
- `append_memory_note`

它被挂到 `kanban` toolset 下，只在 Kanban worker / orchestrator 场景暴露，不会污染普通聊天会话。

### 4. SOUL 规范与实现对齐

`scriptwriter`、`novelist`、`orchestrator` 的计划版 SOUL 规则已经补充：

- 当 `text_agent_workspace` 工具可用时，优先用它处理项目目录、`project_index.md`、`feedback_log.md`、长期记忆写入
- 避免每次任务都手写一套 Markdown 结构

## 验证

本阶段实际回归：

```bash
pytest -o addopts='' --basetemp .pytest_tmp -p no:cacheprovider tests/test_bootstrap_text_agent_workspace.py tests/test_text_agent_workspace.py
pytest -o addopts='' --basetemp .pytest_tmp_tool -p no:cacheprovider tests/tools/test_text_agent_workspace_tool.py
```

结果：

- `tests/test_bootstrap_text_agent_workspace.py`: `3 passed`
- `tests/test_text_agent_workspace.py`: `3 passed`
- `tests/tools/test_text_agent_workspace_tool.py`: `2 passed`

覆盖点包括：

1. Workspace 基础结构创建
2. 项目目录自动创建
3. `project_index.md` 自动更新
4. `feedback_log.md` 追加
5. 长期记忆文件追加
6. `text_agent_workspace` 工具在 kanban 场景可见且可调用

## 本阶段结论

`Phase 6` 判定为完成。

完成依据：

1. Workspace 初始化能力已正式接入 CLI
2. 项目模板不再只是仓库样板，而是可按项目自动创建
3. 三层记忆中的共享记忆、部门记忆、项目记忆已经有统一写入入口
4. Worker/orchestrator 已有可调用工具，不再只能依赖自由文件编辑
5. 对应能力已有模块级和工具级回归测试

## 残余说明

本阶段完成的是“基础设施与可执行接口”。  
真正基于在线模型的长链路人工验收，仍应放在后续阶段的集成测试中完成，但这不再阻塞 `Phase 6` 关闭。
