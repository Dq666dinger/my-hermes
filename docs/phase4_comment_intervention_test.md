# Phase 4 Comment Intervention Test

## 本阶段做了什么

按开发文档的 `Phase 4` 目标，验证了两个文本 worker 在任务运行中追加 comment 后，能否在后续输出中吸收新要求：

- `scriptwriter`
- `novelist`

这一次阶段开发不只是“跑测试”，还处理了两个会直接阻断 Phase 4 的真实问题：

1. WSL 里的 Hermes gateway service 没有继承交互 shell 的代理环境，导致 gateway 拉起的 worker 访问 Xiaomi API 持续超时。
2. `mimo` 模型族没有吃到 Hermes 现有的 tool-use enforcement guidance，worker 容易输出一段中间 prose 后直接退出，触发 `protocol_violation`。

因此，本阶段同时完成了：

- comment 干预能力验证
- gateway 运行环境修复
- kanban worker 的 tool-use /阶段阻断提示加强

## 仓库内修改

本阶段提交到仓库的文件：

- `agent/prompt_builder.py`
- `plans/text_agent_profiles/scriptwriter.SOUL.md`
- `plans/text_agent_profiles/novelist.SOUL.md`
- `skills/devops/kanban-worker/SKILL.md`
- `website/docs/user-guide/skills/bundled/devops/devops-kanban-worker.md`
- `docs/phase4_comment_intervention_test.md`

### 关键代码改动

#### 1. `mimo` 纳入 tool-use enforcement

在 `agent/prompt_builder.py` 中，把 `mimo` 加入 `TOOL_USE_ENFORCEMENT_MODELS`，让 Xiaomi MiMo worker 也收到“必须真正调用工具，而不是只用 prose 说自己要做什么”的系统提示。

#### 2. Kanban guidance 明确禁止用 `clarify` 代替 `kanban_block`

在 `KANBAN_GUIDANCE` 的 `Do NOT` 段落中新增规则：

- Kanban 任务等待用户输入时，不要用 `clarify`
- 不要用 terminal prompt
- 不要只停在 plain prose
- 必须使用 `kanban_block(reason="...")`

#### 3. 两个文本 worker 的 SOUL 增强

给 `scriptwriter` / `novelist` 都补了这一类阶段规则：

- 如果已经产出了中间方案或计划，需要用户确认方向时：
  - 不要只输出 prose
  - 不要拿 `clarify` 代替
  - 当 `kanban_*` 工具可用时，先 `kanban_comment(...)`
  - 再 `kanban_block(reason="...")`

#### 4. `kanban-worker` 技能压缩

把 `skills/devops/kanban-worker/SKILL.md` 从长篇“案例集”压缩成了更短的执行备忘，避免对弱一点的 provider 增加不必要的 prompt 负担。

## WSL 运行时修复（未提交到仓库）

下面这些属于本机 WSL 环境修复，不在仓库提交里，但它们是本阶段能跑通的必要条件。

### 1. 修复 gateway service 的代理环境

交互 shell 中有：

- `HTTP_PROXY=http://127.0.0.1:7897`
- `HTTPS_PROXY=http://127.0.0.1:7897`

但 `systemctl --user show-environment` 最初没有这些变量，导致 gateway 拉起的 worker 超时，而同样的 `hermes -p <profile> chat -q "work kanban task ..."` 在交互 shell 中却能正常执行。

我做了两件事：

1. 写入 `~/.config/environment.d/hermes-proxy.conf`
2. 重启 `hermes-gateway.service`

修复后，gateway 拉起的 worker 不再因为 Xiaomi API 连接超时而直接失败。

### 2. 文本 worker 的运行时 profile 调整

为了让本阶段验证更稳定，我在 WSL 的 `scriptwriter` / `novelist` profile 上做了运行时调整：

- 模型切到 `mimo-v2-pro`
- `reasoning_effort` 改为 `low`
- `toolsets` 缩到 `[]`
- Xiaomi provider timeout 调整到 `180s`

这些改动都只在 WSL 本机 profile config 中，仓库里尚未维护对应模板文件。

## 测试任务 A：scriptwriter

### 测试指令

```bash
hermes kanban create "写一个美发店员工之间的搞笑短视频方案，要求多反转，不要营销" --assignee scriptwriter
hermes kanban comment <task-id> "把故事背景改成民国风理发店，反转更狠一点，结尾加一点小励志。"
```

### 关键成功样本

通过样本任务：

- `t_ae272a5f`

关键结果：

- `Latest summary` 明确写出：
  - `民国风理发店`
  - `5次反转`
  - `励志收场`
- worker comment 中给出了 3 个方向，并且方向描述已经吸收了：
  - `民国风`
  - `反转更狠`
  - `小励志`
- 最终 `kanban_complete(...)` 成功，任务状态为 `done`

任务摘要中的核心证据：

- `完成民国风理发店搞笑短视频剧本《剃头状元》`
- `含5次反转`
- `以"手艺从头开始，到头不散"励志收场`

结论：

- `scriptwriter` 已经能在任务运行中吸收追加 comment
- 吸收后的要求真实进入了最终交付，而不是只停留在中间说明

## 测试任务 B：novelist

### 测试指令

```bash
hermes kanban create "设计一部赛博修仙小说的主角、世界观和前三章大纲" --assignee novelist
hermes kanban comment <task-id> "主角不要开局太强，成长线要明显；女主外冷内热，不要工具人。"
```

### 关键成功样本

通过样本任务：

- `t_4b1c08e9`

关键结果：

- worker comment 中已经吸收新要求：
  - 男主是 `底层废灵根`
  - `起点：炼气一层都勉强`
  - `成长线：从废灵根 → ... → 逐步逆天`
  - 女主 `外冷`
  - 女主 `内热`
  - `不是工具人`
- worker 没有瞎写长正文，而是：
  - 先提交设计方案 comment
  - 再 `kanban_block(reason="...")`

任务 `Latest summary`：

- `已提交赛博修仙小说的设计方案（世界观、主角、前三章大纲方向），等待用户确认方向后再进行详细内容输出。`

结论：

- `novelist` 已经能在 comment 追加后吸收新约束
- 主角成长线和女主独立性都被正确写进设计方案
- 阶段化输出 + block 机制按预期工作

## 本阶段结论

`Phase 4` 判定为通过。

通过依据：

- `scriptwriter` 成功把 comment 吸收到最终剧本交付中
- `novelist` 成功把 comment 吸收到设计方案中，并通过 `kanban_block` 等待确认
- gateway worker 超时问题已经定位并修复
- `mimo` worker 的 tool-use 提示已经纳入正式代码

## 残余风险

1. `scriptwriter` 仍有一定波动性。
   在后续回归任务 `t_ef28bf9c` 中，`scriptwriter` 依然出现过一次只输出 prose 后退出的 `protocol_violation`。这说明 Xiaomi + 当前 prompt 组合仍不是 100% 稳定。

2. WSL profile config 的稳定化参数目前还是运行时本地配置。
   仓库里还没有对应的 profile config 模板或自动同步脚本。

3. `scriptwriter` 的“方向选择”阶段虽然已经能 comment + complete，但是否始终优先 `kanban_block`，还需要在 `Phase 5` 的 block/unblock 场景里继续压测。

## 对下一阶段的意义

`Phase 5` 现在可以在一个更真实的前提下继续做：

- gateway service 已能稳定访问模型
- worker 至少不再普遍卡死在启动超时
- `novelist` 的 block 行为已经出现成功样本
- `scriptwriter` 的中途 comment 吸收主链已经验证通过
