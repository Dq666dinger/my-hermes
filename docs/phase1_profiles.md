# Phase 1 Profiles

## 本阶段做了什么

按开发文档的 `Phase 1` 要求，在 WSL Ubuntu 中创建了三个最小 profile：

- `orchestrator`
- `scriptwriter`
- `novelist`

由于 `Phase 0` 已确认 `hermes profile create` 支持 `--clone`，本阶段采用文档中的“操作方案 A”，直接从当前 `default` profile 克隆出三套最小 profile。

创建后，为了通过 `Phase 1` 的身份识别测试，对三份 `SOUL.md` 做了最小化角色区分，只定义身份，不提前加入 `Phase 2` 的 Worker Interaction Protocol。

## 修改了哪些文件

### 仓库内

- `docs/phase1_profiles.md`

### WSL 运行环境内

- `~/.hermes/profiles/orchestrator/config.yaml`
- `~/.hermes/profiles/orchestrator/.env`
- `~/.hermes/profiles/orchestrator/SOUL.md`
- `~/.hermes/profiles/scriptwriter/config.yaml`
- `~/.hermes/profiles/scriptwriter/.env`
- `~/.hermes/profiles/scriptwriter/SOUL.md`
- `~/.hermes/profiles/novelist/config.yaml`
- `~/.hermes/profiles/novelist/.env`
- `~/.hermes/profiles/novelist/SOUL.md`

### 备份文件

- `~/.hermes/profiles/orchestrator/SOUL.phase1.bak.md`
- `~/.hermes/profiles/scriptwriter/SOUL.phase1.bak.md`
- `~/.hermes/profiles/novelist/SOUL.phase1.bak.md`

## 运行了哪些命令

```bash
hermes profile list
hermes profile create orchestrator --clone
hermes profile create scriptwriter --clone
hermes profile create novelist --clone

hermes -p orchestrator chat -q "你是谁？只回答你的角色名称。" -Q
hermes -p scriptwriter chat -q "你是谁？只回答你的角色名称。" -Q
hermes -p novelist chat -q "你是谁？只回答你的角色名称。" -Q
```

另外执行了若干只读检查命令，用于查看：

- 当前活动 profile
- `~/.hermes/profiles/` 目录
- 三个 profile 的 `SOUL.md`
- 三个 profile 的 `config.yaml`

## Profile 创建结果

### 是否创建成功

已成功创建：

- `orchestrator`
- `scriptwriter`
- `novelist`

`hermes profile list` 摘要：

```text
default
novelist
orchestrator
scriptwriter
```

### 是否使用 `--clone`

是。三个 profile 均通过 `--clone` 从 `default` 创建。

### Wrapper 脚本

创建过程中 Hermes 自动生成了别名入口：

- `~/.local/bin/orchestrator`
- `~/.local/bin/scriptwriter`
- `~/.local/bin/novelist`

## 各 Profile 的模型配置

当前三个 profile 的模型配置保持一致：

| Profile | Provider | Model | 说明 |
|---|---|---|---|
| orchestrator | xiaomi | `mimo-v2.5-pro` | 当前环境仅确认这一套可用配置 |
| scriptwriter | xiaomi | `mimo-v2.5-pro` | 先保证最小可用 |
| novelist | xiaomi | `mimo-v2.5-pro` | 先保证最小可用 |

说明：

- 开发文档给的是“模型建议”，不是硬性要求。
- 当前本机 Hermes 默认配置里已确认可用的是 `xiaomi / mimo-v2.5-pro`。
- 因此本阶段优先保证“三个 profile 独立存在且身份可区分”，暂不额外引入未经验证的新模型配置。

## 各 Profile 的 SOUL.md 路径

- `~/.hermes/profiles/orchestrator/SOUL.md`
- `~/.hermes/profiles/scriptwriter/SOUL.md`
- `~/.hermes/profiles/novelist/SOUL.md`

本阶段对它们做的是“最小身份化”改写：

- `orchestrator`：强调自己是任务分析、路由、拆解、分配角色
- `scriptwriter`：强调自己是剧本 / 短视频脚本方向
- `novelist`：强调自己是小说 / 世界观 / 长文本方向

## 测试了哪些功能

### 1. profile 是否存在

通过 `hermes profile list` 验证三个 profile 已存在。

### 2. 身份识别是否可区分

使用开发文档中的测试思路，分别执行：

```bash
hermes -p orchestrator chat -q "你是谁？只回答你的角色名称。" -Q
hermes -p scriptwriter chat -q "你是谁？只回答你的角色名称。" -Q
hermes -p novelist chat -q "你是谁？只回答你的角色名称。" -Q
```

最终结果：

```text
orchestrator
scriptwriter
novelist
```

## 测试结果摘要

| 测试项 | 结果 | 结论 |
|---|---|---|
| 三个 profile 创建 | 通过 | 已创建成功 |
| `--clone` 路径可用 | 通过 | 三个 profile 均由 `default` 克隆 |
| 身份回答可区分 | 通过 | 三个 profile 返回各自角色名称 |
| 最小角色边界建立 | 通过 | `scriptwriter` 与 `novelist` 不再共用同一身份 |

## 日志摘要

### 创建 profile

```text
Profile 'orchestrator' created at /home/lenovo/.hermes/profiles/orchestrator
Profile 'scriptwriter' created at /home/lenovo/.hermes/profiles/scriptwriter
Profile 'novelist' created at /home/lenovo/.hermes/profiles/novelist
```

### 身份测试

```text
orchestrator
scriptwriter
novelist
```

## 未解决问题

1. 三个 profile 当前仍共用同一模型配置 `mimo-v2.5-pro`，尚未做“便宜稳定 / 创意更强 / 长上下文稳定”的差异化模型划分。
2. 本阶段只做了最小身份区分，尚未写入 `Phase 2` 需要的 Worker Interaction Protocol。
3. 目前只验证了“角色名称识别”，还没有验证 `scriptwriter` 与 `novelist` 的任务边界拒答行为。

## 下一阶段风险

1. `Phase 2` 要修改三份 `SOUL.md`，必须在现有备份基础上继续谨慎演进，避免把协议和角色说明写乱。
2. `Phase 2` 的边界测试会真正暴露 `scriptwriter` / `novelist` 是否会串岗，需要更强的职责约束。
3. 后续若要做模型差异化配置，必须先确认当前环境中是否存在第二、第三套稳定可用模型，否则不要为“看起来合理”而强行改模型。
