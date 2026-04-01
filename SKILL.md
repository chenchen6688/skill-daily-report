---
name: daily-report
description: 生成每日工作日报。从 OpenClaw sessions 提取对话记录，支持无 API Key 的基础日报模式；若配置 OpenAI / Anthropic / MiniMax，可生成更自然的 AI 增强版日报。可后续扩展到飞书、Git 或其他发布通道。当用户请求以下内容时触发：(1) 生成工作日报 (2) 生成日报 (3) 日报 (4) daily report (5) 工作总结
---

# 工作日报 (Daily Report)

从 OpenClaw sessions 提取对话内容，生成每日工作日报。

## 当前特性

- 默认只生成本地 markdown
- **无 API Key 也能运行**（fallback 基础日报）
- 支持外部 LLM 增强总结：OpenAI / Anthropic / MiniMax
- 默认关闭 Feishu / Git 外部输出，避免误发
- 预留 `OPENCLAW_HOME`、`OPENCLAW_SESSIONS_DIR` 以适配不同环境

## 快速使用

```bash
python3 ~/.openclaw/workspace/skills/daily-report/scripts/daily_report.py
```

指定日期：

```bash
python3 ~/.openclaw/workspace/skills/daily-report/scripts/daily_report.py 2026-04-01
```

输出文件默认保存到：

```bash
~/.openclaw/workspace/data/daily-reports/YYYY-MM-DD.md
```

## 配置

复制示例配置：

```bash
cp scripts/config.env.example scripts/config.env
```

然后按需修改 `scripts/config.env`。

### 最小本地模式（默认推荐）

```bash
ENABLE_FEISHU=false
ENABLE_GIT=false
```

即使不配置任何 API Key，也会自动生成基础日报。

### 启用 AI 增强总结（可选）

支持以下任一提供方：

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `MINIMAX_API_KEY`

优先级：**MiniMax → Anthropic → OpenAI**

## 环境变量

### OpenClaw 路径适配

```bash
OPENCLAW_HOME=~/.openclaw
OPENCLAW_SESSIONS_DIR=~/.openclaw/agents/main/sessions
```

如果不配置，脚本会自动使用当前用户 home 下的默认 OpenClaw 路径。

## 输出模式说明

### 1) Fallback 基础日报模式

当没有检测到外部 API Key 时，脚本会：

- 读取指定日期范围内的 sessions
- 清洗并提取用户/助手消息
- 生成结构化 markdown 日报

适合：
- 本地测试
- 通用 skill 底座
- 没有外部模型凭证的环境

### 2) AI 增强模式

当存在外部模型 API Key 时，脚本会把清洗后的内容交给模型生成更自然的日报。

适合：
- 想要更像“人写的”总结
- 后续飞书推送或正式归档

## 当前限制

- 当前版本的 Feishu / Git 发布逻辑仍保留为占位接口，未默认启用
- Cron 执行记录暂未做强绑定 CLI 解析，以避免不同 OpenClaw 版本差异导致失败
- fallback 模式已可用，但文案质量仍可继续优化

## 建议的后续扩展

推荐将能力逐步拆成：

- collector：读取 sessions / cron
- cleaner：清洗噪音、过滤系统消息
- generator：fallback / LLM 增强
- publisher：Feishu / Git / webhook

这样后续可以低成本扩展为：

- 日报
- 周报
- 项目总结
- 指定日期范围总结
- 多渠道发布
