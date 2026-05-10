# Phase 2 SOUL Protocol

## 本阶段做了什么

按开发文档的 `Phase 2` 要求，为两个文本 worker 写入了可监管执行协议：

- `scriptwriter`
- `novelist`

本阶段完成了两类工作：

1. 在仓库中新增了可追溯的 worker SOUL 源文件，作为后续阶段维护的 prompt 基线。
2. 将这些协议同步到 WSL Ubuntu 中 Hermes 的真实 profile 路径，并执行职责边界测试。

本阶段没有修改 Hermes 核心源码，只修改了 profile 级 `SOUL.md`。

## 修改了哪些文件

### 仓库内

- `plans/text_agent_profiles/scriptwriter.SOUL.md`
- `plans/text_agent_profiles/novelist.SOUL.md`
- `docs/phase2_soul_protocol.md`

### WSL 运行环境内

- `~/.hermes/profiles/scriptwriter/SOUL.md`
- `~/.hermes/profiles/novelist/SOUL.md`

### 备份文件

- `~/.hermes/profiles/scriptwriter/SOUL.phase2.bak.md`
- `~/.hermes/profiles/novelist/SOUL.phase2.bak.md`

## 运行了哪些命令

```bash
hermes -p scriptwriter chat -q "你能写小说第十章吗？" -Q
hermes -p novelist chat -q "你能写短视频分镜脚本吗？" -Q
```

同步阶段还执行了只读检查与文件同步命令，用于：

- 查看 WSL 中当前 worker 的 `SOUL.md`
- 将仓库内的 Phase 2 prompt 文件复制到真实 profile 路径
- 备份同步前的 `SOUL.md`

## 协议内容概述

### 1. 通用 Worker Interaction Protocol

两个 worker 都写入了以下核心约束：

- 启动任务先读 context、description、comments、parent results、workspace path
- 长任务必须分阶段执行，不能一口气写完
- 每个阶段前后都要检查 comments
- 需求不清、资料不足、方向冲突时必须 block
- unblock 后必须重新读取上下文
- 高成本生成前要再次检查 comments
- 失败最多重试一次，仍失败则 comment + block
- 最终交付前必须自检

### 2. scriptwriter 专属规则

写入了明确边界：

- 负责：短视频脚本、短剧、搞笑反转、口播、分镜、可拍摄内容
- 不负责：长篇小说章节、小说续写、图片生成、视频剪辑、代码开发、报表

并写入阶段流程：

1. 需求复述
2. 先给创意方向
3. 检查用户反馈
4. 产出剧本初稿
5. 自检
6. 输出可拍摄终稿

### 3. novelist 专属规则

写入了明确边界：

- 负责：小说创意、世界观、人物设定、大纲、章节、正文、润色
- 不负责：短视频分镜、短视频脚本、图片生成、视频剪辑、代码开发、报表

并写入阶段流程：

1. 读取项目资料
2. 判断任务类型
3. 先产出写作计划
4. 长正文前检查 comments
5. 输出阶段结果
6. 更新项目文件
7. 自检一致性
8. 最终交付

另外还写入了上下文窗口管理规则，明确项目超过三章后不能默认读取全部正文。

## 测试了哪些功能

### 测试 1：scriptwriter 是否拒绝小说章节任务

命令：

```bash
hermes -p scriptwriter chat -q "你能写小说第十章吗？" -Q
```

结果摘要：

```text
很抱歉，我无法为你写小说第十章。
... 这应该交给专门负责小说创作的 `novelist` 角色来处理。
```

结论：

- `scriptwriter` 没有去直接写小说正文
- 明确建议转交给 `novelist`

### 测试 2：novelist 是否拒绝短视频分镜任务

命令：

```bash
hermes -p novelist chat -q "你能写短视频分镜脚本吗？" -Q
```

结果摘要：

```text
不能。我是小说家(novelist)...
短视频分镜脚本属于编剧(scriptwriter)的工作范畴，建议你找 scriptwriter 来处理这类任务。
```

结论：

- `novelist` 没有去产出分镜脚本
- 明确建议转交给 `scriptwriter`

## 测试结果摘要

| 测试项 | 结果 | 结论 |
|---|---|---|
| scriptwriter 拒绝小说章节 | 通过 | 建议转交 `novelist` |
| novelist 拒绝分镜脚本 | 通过 | 建议转交 `scriptwriter` |
| 通用协议已写入 | 通过 | 两个 worker 均具备阶段化与 comment/block 约束 |
| 上下文管理规则已写入 novelist | 通过 | 为后续长篇任务做准备 |

## 日志摘要

### scriptwriter

```text
很抱歉，我无法为你写小说第十章。
... 这应该交给专门负责小说创作的 `novelist` 角色来处理。
```

### novelist

```text
不能。我是小说家(novelist)...
短视频分镜脚本属于编剧(scriptwriter)的工作范畴，建议你找 scriptwriter 来处理这类任务。
```

## 未解决问题

1. 本阶段只验证了“串岗拒绝”与“协议文本已写入”，还没有验证 Kanban 真实执行时是否会按阶段检查 comments。
2. memory 规则和 workspace 路径已经写进 prompt，但相关目录尚未在 `Phase 6` 初始化。
3. `orchestrator` 还没有进入路由协议建设，当前仍只有最小身份定义。

## 下一阶段风险

1. `Phase 3` 会开始接触 Kanban 与 Dashboard 的真实联动，到时才会暴露协议是否真正影响 worker 执行行为。
2. 如果 Hermes 在 chat 模式和 Kanban worker 模式下系统提示拼接不同，`Phase 4` 可能还需要进一步加强“每阶段检查 comments”的措辞。
3. `novelist` 的上下文管理规则当前只是 prompt 约束，后续需要通过真实任务来验证是否有效。
