---
name: daily-report
description: 生成每日工作日报。从 OpenClaw 本地 sessions 提取对话内容生成日报，支持无 API Key fallback 与 OpenAI / Anthropic / MiniMax 增强总结。支持飞书和钉钉直接推送全文，也提供微信等通道可直接接入的日报查询脚本入口。
---

# 工作日报 (Daily Report)

这个 skill 提供两个核心入口：

## 1）生成日报

```bash
python3 ~/.openclaw/workspace/skills/daily-report/scripts/daily_report.py
```

指定日期：

```bash
python3 ~/.openclaw/workspace/skills/daily-report/scripts/daily_report.py 2026-04-01
```

输出文件：

```bash
~/.openclaw/workspace/data/daily-reports/YYYY-MM-DD.md
```

## 2）查询日报全文

用于微信等“用户主动询问”的场景：

```bash
python3 ~/.openclaw/workspace/skills/daily-report/scripts/query_report.py today
python3 ~/.openclaw/workspace/skills/daily-report/scripts/query_report.py yesterday
python3 ~/.openclaw/workspace/skills/daily-report/scripts/query_report.py 2026-04-01
```

如果日报不存在，查询脚本会自动先生成再返回。

## 接入建议

- **飞书**：在日报生成后直接推送全文
- **钉钉**：在日报生成后直接推送全文（可配置关键词）
- **微信**：在用户发送“日报”后调用 `query_report.py`，把 stdout 回给用户

## 配置

复制配置：

```bash
cp scripts/config.env.example scripts/config.env
```

最小配置：

```env
ENABLE_FEISHU=false
ENABLE_DINGTALK=false
ENABLE_GIT=false
WECHAT_QUERY_HINT_ENABLED=true
WECHAT_QUERY_COMMAND=日报
AUTOMATION_TIME=19:00
AUTOMATION_TZ=Asia/Shanghai
```

钉钉示例：

```env
ENABLE_DINGTALK=true
DINGTALK_WEBHOOK_URL=你的钉钉机器人 webhook
DINGTALK_KEYWORD=日报
```

## 说明

- 日报分析总结在**本地**完成
- 飞书 / 钉钉负责**主动接收全文**
- 微信负责**主动查询本地结果**
- 这样多个端拿到的是同一份日报，逻辑更简单也更稳
