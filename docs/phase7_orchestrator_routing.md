# Phase 7 Orchestrator 路由协议

## 本阶段做了什么

按开发文档的 `Phase 7` 目标，这一阶段把“文本总调度 Agent 能否把请求正确分流到 `scriptwriter` / `novelist`”从 SOUL 约定推进成了仓库内可验证的正式能力。

本阶段完成的核心点：

1. 新增可复用的文本请求路由模块
2. 将路由能力接到 `hermes kanban route-text-request`
3. 让 split 场景自动创建上下游依赖任务
4. 把 `orchestrator` 的 workspace 预建规则写回 SOUL 规范
5. 为中文高频场景补上更稳定的判定与项目命名测试

## 仓库内修改

- 新增 `hermes_cli/text_agent_routing.py`
- 更新 `hermes_cli/kanban.py`
- 更新 `plans/text_agent_profiles/orchestrator.SOUL.md`
- 新增 `tests/test_text_agent_routing.py`
- 更新 `tests/hermes_cli/test_kanban_cli.py`
- 新增 `docs/phase7_orchestrator_routing.md`

说明：

- `Phase 6` 已经提供了 `text_agent_workspace` 和项目模板能力
- `Phase 7` 在此基础上补齐“如何决定该把任务发给谁”

## 新增能力

### 1. 文本请求路由模块

`hermes_cli/text_agent_routing.py` 现在提供：

- `classify_text_request(...)`
- `default_project_name(...)`
- `plan_text_request(...)`

当前支持 4 类路由结果：

- `scriptwriter`
- `novelist`
- `split`
- `ambiguous`

### 2. CLI 路由入口

```bash
hermes kanban route-text-request "帮我做一个美发店员工之间的搞笑短视频脚本，要求多反转。"
```

支持：

- `--workspace-root`
- `--project-name`
- `--create`
- `--created-by`
- `--json`

其中：

- 预览模式只输出路由结果和拟创建任务
- `--create` 会真正创建 Kanban task
- `split` 场景下第二个任务会自动依赖第一个任务

### 3. 中文路由规则补强

这次专门补了两个容易在中文任务里误判的点：

1. 当请求里同时出现 `脚本/短剧/口播` 与 `大纲/人物设定` 时，不再一律判成 `ambiguous`
2. 中文请求默认项目名不再退化成 `text-project-<hash>`，而是保留可读的中文摘要

这能让：

- `shared_memory/project_index.md` 更可读
- `scriptwriter` / `novelist` 项目目录更容易人工识别
- orchestrator 的中文工作流更接近真实使用场景

## 验证

本阶段实际回归：

```bash
pytest -o addopts='' -p no:cacheprovider --basetemp .tmp_pytest tests/hermes_cli/test_kanban_cli.py -k "route_text_request or bootstrap_text_agent_workspace"
pytest -o addopts='' -p no:cacheprovider --basetemp .tmp_pytest tests/test_text_agent_workspace.py tests/tools/test_text_agent_workspace_tool.py tests/test_text_agent_routing.py
```

结果：

- `tests/hermes_cli/test_kanban_cli.py`: `4 passed`
- `tests/test_text_agent_workspace.py`: `3 passed`
- `tests/tools/test_text_agent_workspace_tool.py`: `2 passed`
- `tests/test_text_agent_routing.py`: `7 passed`

覆盖点包括：

1. 纯短视频脚本请求路由到 `scriptwriter`
2. 纯小说设定请求路由到 `novelist`
3. 小说 IP -> 短视频改编请求拆成 `split`
4. 歧义请求返回澄清而不是乱建任务
5. 中文项目名保持可读，不再退化成 hash
6. split 场景会同时创建两个项目工作区

## 本阶段结论

`Phase 7` 判定为完成。

完成依据：

1. orchestrator 路由规则已经落地为仓库代码，而不只是 SOUL 描述
2. CLI 可直接预览或创建 `scriptwriter` / `novelist` / `split` 任务
3. split 任务的依赖关系已经落地到 Kanban
4. 中文主要使用场景已有定向回归测试
5. workspace 与路由协议已经接通，可进入下一阶段的失败恢复与成本控制

## 残余风险

1. 当前路由仍是关键词+启发式规则，不是语义分类器。
2. 更复杂的跨媒体需求还可能需要后续阶段补充规则。
3. 这次主要验证了 CLI/模块链路，真正在线模型驱动的 orchestrator 人工验收仍应放到 `Phase 9` 总验收继续跑通。
