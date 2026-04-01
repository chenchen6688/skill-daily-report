# skill-daily-report

一个用于汇总 OpenClaw 聊天记录并生成工作日报的 skill。

当前版本已经从“依赖特定环境、容易直接跑挂”的 demo，整理成一个**更适合作为通用 skill 雏形**的版本：

- 支持 **无 API Key fallback 模式**
- 默认只生成本地 markdown
- 默认关闭 Feishu / Git 外部输出，避免误发
- 支持通过环境变量适配不同 OpenClaw 目录
- 对原始 sessions 做基础清洗，降低 metadata / 系统噪音影响
- 在 fallback 模式下使用规则化模板生成更像日报的结构化内容

---

## 适用场景

- 想把 OpenClaw 每天的聊天和工作过程整理成日报
- 当前没有外部模型 API Key，但仍希望先跑出一个本地可用版本
- 想把 skill 做成更通用、可扩展、可继续接 publisher 的版本

---

## 当前能力

### 1. 本地 fallback 模式（默认推荐）

不需要配置任何外部模型 API Key。

脚本会：

1. 读取指定日期范围内的 OpenClaw sessions
2. 清洗部分系统噪音、metadata 和 reply tag
3. 基于规则模板生成结构化工作日报
4. 输出 markdown 到本地目录

默认输出路径：

```bash
~/.openclaw/workspace/data/daily-reports/YYYY-MM-DD.md
```

### 2. 外部 LLM 增强模式（可选）

如果配置了以下任意提供方的 Key：

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `MINIMAX_API_KEY`

则脚本会优先调用外部模型生成更自然的日报内容。

若调用失败，会自动回退到 fallback 模式。

---

## 快速开始

### 1. 运行脚本

```bash
python3 scripts/daily_report.py
```

指定日期：

```bash
python3 scripts/daily_report.py 2026-04-01
```

### 2. 配置文件

复制示例配置：

```bash
cp scripts/config.env.example scripts/config.env
```

最小本地模式推荐保留：

```env
ENABLE_FEISHU=false
ENABLE_GIT=false
```

---

## 配置项说明

### OpenClaw 路径适配

用于兼容不同机器、不同用户目录：

```bash
OPENCLAW_HOME=~/.openclaw
OPENCLAW_SESSIONS_DIR=~/.openclaw/agents/main/sessions
```

如果不配置，默认读取当前用户 home 下的 OpenClaw 目录。

### 外部输出

默认关闭：

```env
ENABLE_FEISHU=false
ENABLE_GIT=false
```

当前版本中 Feishu / Git publisher 仍是占位接口，未默认实现真实发送。

### 外部模型 API

支持以下环境变量：

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL=gpt-4o

ANTHROPIC_API_KEY=
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_MODEL=claude-sonnet-4-20250514

MINIMAX_API_KEY=
MINIMAX_API_URL=https://api.minimaxi.com
MINIMAX_MODEL=MiniMax-M2.5
```

优先级：

```text
MiniMax → Anthropic → OpenAI
```

---

## 这次整理修复了什么

### 运行层面

- 修复 sessions 路径写死为特定用户名的问题
- 修复缺少 `httpx` 依赖时脚本直接报错的问题
- 修复无外部 API Key 时无法产出任何结果的问题

### 默认配置层面

- 关闭默认 Feishu 推送
- 关闭默认 Git 推送
- 去掉潜在危险默认配置，减少测试阶段副作用

### 输出质量层面

- 增加 cleaner，过滤部分 metadata / reply tag / heartbeat / 状态噪音
- 将 fallback 模式从“直接拼原文”改成“规则化模板归纳”
- 让无模型场景下的日报更接近正式工作日报风格

### 文档层面

- 更新 `SKILL.md`
- 增加 `config.env.example`
- 说明 fallback / AI 增强 / 默认安全策略

---

## 当前限制

当前版本还不是终版，主要限制包括：

- Feishu publisher 尚未真正实现
- Git publisher 尚未真正实现
- Cron 执行记录尚未做稳定的 CLI 兼容解析
- fallback 规则仍可继续细化
- 暂未支持周报、日期范围总结、多模板输出

---

## 建议的后续演进方向

推荐逐步拆成以下模块：

- `collector`：读取 sessions / cron
- `cleaner`：清洗 metadata 和系统噪音
- `generator`：fallback / LLM 增强
- `publisher`：Feishu / Git / webhook
- `templates`：日报 / 周报 / 项目总结模板

这样后续可以低成本扩展成：

- 日报
- 周报
- 指定日期范围总结
- 项目工作总结
- 多渠道发布

---

## 适合作为 PR / fork 的方向

如果你想把它继续推进成更正式的版本，建议下一步优先做：

1. 抽离 cleaner / generator / publisher
2. 增加 README 中的测试样例
3. 接入真正的 Feishu publisher
4. 对 cron 执行记录做版本兼容适配
5. 增加周报 / 区间总结支持

---

## License / Attribution

请根据原仓库的授权方式与作者意图处理后续 fork / PR / 发布。
