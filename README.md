# skill-daily-report

一个用于汇总 OpenClaw 聊天记录并生成工作日报的 skill。  
目标是把原始 session 对话，整理成**可读、可保存、可复盘**的结构化日报。

当前版本主打三件事：

- **本地可直接跑**
- **没有 API Key 也能用**
- **默认安全，不会乱发消息**

---

# 一句话说明

这是一个把 **OpenClaw session 历史自动整理成日报** 的工具。  
适合每天和 OpenClaw 协作做事、想自动生成工作总结的人。

---

# 适合谁用

适合：

- 已经在使用 OpenClaw 的用户
- 想把每天和 AI 的协作过程整理成日报的人
- 没有外部模型 API Key，但也想先本地跑起来的人
- 想继续扩展成周报 / 飞书推送 / 微信提醒 / Git 归档的人

---

# 最快上手（推荐直接照抄）

## 1）克隆仓库

```bash
git clone https://github.com/chenchen6688/skill-daily-report.git
cd skill-daily-report
```

## 2）安装依赖

```bash
python3 -m pip install --user -r requirements.txt
```

## 3）复制配置文件

```bash
cp scripts/config.env.example scripts/config.env
```

## 4）直接运行

```bash
python3 scripts/daily_report.py
```

运行成功后，会在这里生成日报：

```bash
~/.openclaw/workspace/data/daily-reports/YYYY-MM-DD.md
```

查看今天的日报：

```bash
cat ~/.openclaw/workspace/data/daily-reports/$(date +%F).md
```

---

# 指定日期生成日报

例如生成 2026-04-01 的日报：

```bash
python3 scripts/daily_report.py 2026-04-01
```

查看结果：

```bash
cat ~/.openclaw/workspace/data/daily-reports/2026-04-01.md
```

---

# 它默认会做什么

当前默认行为：

- 读取 OpenClaw sessions
- 整理当天内容
- 生成本地 markdown 日报
- **不会默认发飞书**
- **不会默认推 Git**
- **没有 API Key 也能跑**

也就是说：

> 默认是“本地优先、安全优先、先跑起来再说”。

---

# 使用前提（很重要）

这个工具不是纯独立脚本，它依赖 **OpenClaw 的本地 session 数据**。

所以你本机至少需要：

- 已安装并使用过 OpenClaw
- 本机存在 session 数据
- Python 3 可用

默认读取的 sessions 目录是：

```bash
~/.openclaw/agents/main/sessions
```

如果你从没使用过 OpenClaw，或者这个目录里没有会话数据，那就没有东西可总结。

---

# 没有 API Key 能不能用？

**可以。**

这是这个项目这次重点改造的地方之一。

## 当前逻辑

### 没有外部模型 Key
自动走 **fallback 模式**：
- 不调用外部模型
- 本地规则化生成日报
- 依然能产出 markdown 文件

### 有外部模型 Key
会优先尝试调用外部模型生成更自然的日报内容。

支持：

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `MINIMAX_API_KEY`

优先级：

```text
MiniMax → Anthropic → OpenAI
```

---

# 配置说明

## 默认配置文件

```bash
scripts/config.env
```

## 推荐做法

复制模板：

```bash
cp scripts/config.env.example scripts/config.env
```

然后按需修改。

## 最小可用配置

保持下面这样就可以：

```env
ENABLE_FEISHU=false
ENABLE_GIT=false
```

---

# 如果 OpenClaw 不在默认目录怎么办

可以通过环境变量覆盖：

## 方式 1：指定 OpenClaw 根目录

```bash
export OPENCLAW_HOME=~/.openclaw
```

## 方式 2：直接指定 sessions 目录

```bash
export OPENCLAW_SESSIONS_DIR=~/.openclaw/agents/main/sessions
```

然后再运行：

```bash
python3 scripts/daily_report.py
```

---

# 如果你想启用 AI 增强版日报

可以在 shell 环境里配置任意一种模型提供方。

## OpenAI

```bash
export OPENAI_API_KEY=your_key
export OPENAI_MODEL=gpt-4o
```

## Anthropic

```bash
export ANTHROPIC_API_KEY=your_key
export ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

## MiniMax

```bash
export MINIMAX_API_KEY=your_key
export MINIMAX_MODEL=MiniMax-M2.5
```

然后重新运行：

```bash
python3 scripts/daily_report.py
```

---

# 现在的推荐使用方式

我建议你把它当成：

> **一个本地优先的 OpenClaw 日报生成器**

最适合当前版本的使用方式是：

- 手动运行生成日报
- 或每天定时生成日报并提醒自己查看

而不是一上来就期待它是一个成熟的一键全自动发布系统。

---

# 定时使用（推荐）

这个项目很适合接 OpenClaw cron 做定时任务。  
比如每天 23:00：

1. 自动运行日报脚本
2. 生成本地日报文件
3. 通过微信或其他通道提醒“今日日报已生成”

这种方式比“直接自动发送全文”更稳，也更适合当前版本。

---

# 当前版本已经解决的问题

这次整理主要解决了以下问题：

- 修复 sessions 路径写死到特定用户名的问题
- 增加 `OPENCLAW_HOME` / `OPENCLAW_SESSIONS_DIR` 支持
- 增加无 API Key fallback 模式
- 默认关闭 Feishu / Git 外部输出
- 增加 cleaner，降低 metadata / reply tag / heartbeat 等噪音影响
- 将 fallback 输出改成规则化模板，而不是原文硬拼
- 增加 `config.env.example`、`README.md`、`requirements.txt`、`.gitignore`

---

# 当前限制

当前版本还不是终版，以下能力暂未完整实现：

- 真正的 Feishu publisher
- 真正的 Git publisher
- 稳定的 cron 历史记录解析
- 周报 / 日期区间总结
- 更强的模板系统
- 更细粒度的内容归纳

所以当前定位更适合描述为：

> **一个已经可用的通用 skill 雏形 / 本地日报工具**

---

# 常见问题

## 1）运行了但没生成内容
先检查：

```bash
ls ~/.openclaw/agents/main/sessions
```

如果这里没有 session 文件，那就没有素材可总结。

---

## 2）我的 OpenClaw 不在默认目录
设置：

```bash
export OPENCLAW_HOME=你的目录
```

或：

```bash
export OPENCLAW_SESSIONS_DIR=你的sessions目录
```

---

## 3）没有 API Key 会报错吗？
不会直接挂，会自动走 fallback 基础日报模式。

---

## 4）为什么默认不发飞书 / 不 push Git？
这是故意的。  
为了避免测试时误发消息、误推送代码，默认配置采用保守策略。

---

# 建议的后续演进方向

推荐后续逐步拆成：

- `collector`：读取 sessions / cron
- `cleaner`：清洗 metadata 和系统噪音
- `generator`：fallback / AI 增强
- `publisher`：Feishu / Git / webhook / 微信提醒
- `templates`：日报 / 周报 / 项目总结模板

这样后续可以低成本扩展成：

- 日报
- 周报
- 指定日期范围总结
- 项目工作总结
- 多渠道发布

---

# 如果你想自己长期维护

建议至少保留这些文件：

```text
README.md
SKILL.md
requirements.txt
scripts/daily_report.py
scripts/config.env.example
```

并将本地专用配置放在：

```text
scripts/config.env
```

不要把私人 key、私人 ID 或本地配置直接提交到公开仓库。

---

# 一句话总结

> 一个把 OpenClaw session 历史自动整理成结构化工作日报的 skill，支持无 API Key fallback、本地优先和后续多渠道扩展。
