# Phase 5 Block Unblock Test

## 本阶段做了什么

按开发文档的 `Phase 5` 目标，验证当需求不明确时，`scriptwriter` 是否会：

1. 主动 `block`
2. 清晰说明当前缺的决策信息
3. 在用户补充 comment 后被 `unblock`
4. 继续执行，并吸收补充后的约束

这一次阶段不再需要新增仓库代码，`Phase 4` 完成后的运行基线已经足够支撑 `block / unblock` 验证。

## 仓库内修改

本阶段提交到仓库的文件：

- `docs/phase5_block_unblock_test.md`

说明：

- 本阶段没有新增 Hermes 核心源码修改
- `Phase 4` 中已经落地的 tool-use / kanban_block 协议增强，在本阶段得到真实验证

## 测试任务

### 创建任务

```bash
hermes kanban create "写一个风格特别的短剧，人物和场景你自己看着办" --assignee scriptwriter
```

任务 id：

- `t_81c5253f`

### 期望

- worker 判断需求过泛
- 先给方向或问题
- 主动 `block`
- 等待用户补充

## 第一段验证：是否会主动 block

### 实际结果

`scriptwriter` 没有直接瞎写完整剧本，而是：

1. 先写入 4 个创意方向 comment
2. 然后将任务状态切到 `blocked`

comment 内容摘要：

- 方向 A：`赛博朋克寿司店`
- 方向 B：`凌晨三点的便利店`
- 方向 C：`县衙直播`
- 方向 D：`电梯里的三分钟`

block reason：

- `提出了4个创意方向（赛博朋克寿司店 / 凌晨三点的便利店 / 县衙直播 / 电梯里的三分钟），等用户选定方向后再展开完整剧本。`

### 结论

第一段通过：

- worker 能主动暂停
- block 原因清楚
- 中间方案通过 task comment 留在了线程里

## 第二段验证：模拟人工补充 + unblock

### 人工补充

按开发文档要求模拟用户介入：

```bash
hermes kanban comment t_81c5253f "场景是美发店，角色是老板和新员工，风格要荒诞搞笑。"
hermes kanban unblock t_81c5253f
```

### 实际结果

unblock 后任务经历了：

- `ready`
- `running`
- `done`

最终 `Latest summary`：

- `完成荒诞搞笑美发店短剧《理发师的自我修养》，6场戏3次反转：老板老王+新员工小李+离谱顾客的对手戏，包含"三种随便""被生活毒打的水温""左倾自由主义卷"等荒诞梗，收场以"请客AA"制造喜剧节奏。时长约3分30秒，无营销内容。`

`context` 中的结构化 metadata 也明确体现了补充条件：

- `setting: "美发店"`
- `characters: ["老王(老板)", "小李(新员工)", "顾客甲(大妈)"]`
- `genre: "荒诞喜剧"`

### worker 日志摘要

恢复执行后的关键行为是：

1. 重新读取任务上下文
2. 明确识别“用户已经明确方向：美发店场景，老板和新员工，荒诞搞笑风格”
3. 直接写入完整剧本文件 `剧本_荒诞美发店.md`
4. 调用 `kanban_complete(...)` 完成任务

## 事件链证据

`t_81c5253f` 的事件链如下：

1. `created`
2. `[run 12] claimed`
3. `[run 12] spawned`
4. `commented`（worker 提交 4 个方向）
5. `[run 12] blocked`
6. `commented`（模拟人工补充）
7. `unblocked`
8. `[run 13] claimed`
9. `[run 13] spawned`
10. `[run 13] completed`

这条链路说明：

- `block / unblock` 在真实 Hermes Kanban 中已生效
- respawn 后 worker 能继续同一任务，而不是另起一张新卡

## 本阶段结论

`Phase 5` 判定为通过。

通过依据：

- `scriptwriter` 在需求过泛时没有直接写终稿，而是先 `block`
- block 原因明确，且中间方向方案被保存到 comment 线程
- 用户补充 comment 后，`unblock` 能恢复任务
- 恢复后的输出吸收了：
  - `美发店`
  - `老板和新员工`
  - `荒诞搞笑`

## 残余风险

1. 本阶段主要验证了 `scriptwriter`，没有对 `novelist` 再做一轮 `block / unblock` 回归。

2. 当前验证是“单轮人工补充后恢复成功”。
   更复杂的多轮反复 block/unblock，还需要后续阶段或最终验收继续压测。

3. 本阶段依赖 `Phase 4` 已修复的 gateway 代理环境和 worker 协议增强。
   如果换一套全新机器环境，仍需要先把那部分运行基线补齐。

## 对下一阶段的意义

`Phase 6` 可以在更可靠的协作链路上继续推进：

- 需求不明确时，worker 已能暂停而不是乱写
- 用户补充后，worker 已能恢复并继续
- 这为后续 `Workspace`、项目资料目录、三层记忆写入提供了稳定的人机协作入口
