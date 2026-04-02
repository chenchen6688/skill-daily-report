# skill-daily-report

一个用于汇总 OpenClaw 聊天记录并生成工作日报的 skill。  
目标是把原始 session 对话，整理成**可读、可保存、可复盘**的结构化日报，并支持**多端分发策略**。

当前版本的多端策略是：

- **本地**：始终生成 markdown 日报
- **飞书**：支持直接推送日报全文
- **微信**：不依赖主动推送，改为“用户主动询问后返回全文”

这样做的原因很现实：

- 飞书适合**稳定主动推送**
- 微信在当前 `openclaw-weixin` 链路下，**主动推送存在兼容性/稳定性问题**
- 所以微信端采用**主动询问式获取全文**，能最大化保持功能一致，同时避免漏消息

---

# 一句话说明

这是一个把 **OpenClaw session 历史自动整理成日报** 的工具。  
适合每天和 OpenClaw 协作做事、想自动生成工作总结，并希望在不同终端上用不同分发策略的人。

---

# 当前能力

当前版本主打四件事：

- **本地可直接跑**
- **没有 API Key 也能用**
- **支持多端分发策略**
- **默认安全，不会乱发消息**

---

# 多端策略说明（重点）

## 1）本地端

无论是否启用外部推送，脚本都会先生成本地日报文件：

```bash
~/.openclaw/workspace/data/daily-reports/YYYY-MM-DD.md
```

这是所有分发方式的基础。

---

## 2）飞书端：直接推送全文

飞书端适合做**主动推送全文**。

当前实现方式：

- 若配置 `FEISHU_WEBHOOK_URL`
- 且 `ENABLE_FEISHU=true`
- 生成日报后会把**日报全文**直接 POST 到飞书 webhook

适合：

- 日报群
- 个人机器人通知
- 每晚固定时间自动收全文

---

## 3）微信端：主动询问获取全文

微信端目前**不建议依赖主动推送全文**。

原因是当前 `openclaw-weixin` 在部分环境下存在这样的问题：

- 用户从微信发消息给机器人：正常
- 机器人在同一微信上下文里回复：正常
- cron / sessions_send / announce 主动推送：可能失败或不稳定

所以当前推荐策略是：

- 日报照常生成
- 微信端保留一个**主动询问入口**
- 用户在微信里发送：

```text
日报
```

然后机器人返回当天日报全文。

你也可以把指令改成别的，比如：

```env
WECHAT_QUERY_COMMAND=今日日报
```

这样就变成在微信里发“今日日报”来取全文。

---

# 最快上手（推荐直接照抄）

## 1）克隆仓库

```bash
git clone git@github.com:chenchen6688/skill-daily-report.git
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
- **会输出一条适合微信端使用的“主动询问提示”**
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

---

# 多端配置示例

## 最小可用配置

保持下面这样就可以：

```env
ENABLE_FEISHU=false
ENABLE_GIT=false
WECHAT_QUERY_HINT_ENABLED=true
WECHAT_QUERY_COMMAND=日报
```

这样会：

- 只生成本地日报
- 给出微信端主动询问提示
- 不做外部发送

---

## 启用飞书全文推送

```env
ENABLE_FEISHU=true
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxx
WECHAT_QUERY_HINT_ENABLED=true
WECHAT_QUERY_COMMAND=日报
```

这样会：

- 本地生成日报
- 飞书直接收到全文
- 微信端通过“日报”主动询问获取全文

---

## 自定义微信端查询口令

```env
WECHAT_QUERY_HINT_ENABLED=true
WECHAT_QUERY_COMMAND=今日日报
```

此时微信端建议文案会变成：

> 在微信里发送“今日日报”获取全文。

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

# 运行结果会输出什么

脚本执行后一般会输出：

- sessions 目录
- 抓取到的字符数
- 日报保存路径
- 若启用飞书：推送结果
- 一条微信端建议提示，例如：

```text
今日日报已生成：2026-04-01
文件路径：~/.openclaw/workspace/data/daily-reports/2026-04-01.md
由于微信主动推送链路在部分环境下不稳定，建议你在微信里发送“日报”，再由机器人返回全文。
```

---

# 定时使用（推荐）

这个项目很适合接 OpenClaw cron 做定时任务。比如每天 23:00：

1. 自动运行日报脚本
2. 生成本地日报文件
3. 飞书直接收到全文
4. 微信侧通过主动询问口令获取全文

这种方式比“强行要求微信也主动推全文”更稳。

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
- 增加 **多端分发策略说明**
- 增加 **飞书全文推送能力（webhook 方式）**
- 增加 **微信主动询问式获取全文** 的产品化说明和配置项

---

# 当前限制

当前版本还不是终版，以下能力暂未完整实现：

- 真正的 Feishu 用户 ID 点对点消息发送（目前优先 webhook）
- 真正的 Git publisher
- 稳定的 cron 历史记录解析
- 周报 / 日期区间总结
- 更强的模板系统
- 更细粒度的内容归纳
- 微信端自动识别“日报”并回全文的对话侧实现（当前先把 skill 侧策略和输出补齐）

所以当前定位更适合描述为：

> **一个已经可用的通用 skill 雏形 / 本地日报工具 + 多端分发策略底座**

---

# 常见问题

## 1）为什么微信不直接主动推全文？

因为当前 `openclaw-weixin` 在部分环境下存在主动推送不稳定的问题。  
为了避免“系统显示已发送，但微信里实际没收到”，当前策略改为：

- 飞书直接推送全文
- 微信主动询问取全文

这是更稳的方案。

---

## 2）飞书为什么建议用 webhook？

因为 webhook 接入简单、稳定、清晰，适合日报这类单向通知。

---

## 3）没有 API Key 会报错吗？

不会直接挂，会自动走 fallback 基础日报模式。

---

## 4）为什么默认不 push Git？

这是故意的。  
为了避免测试时误推送代码，默认配置采用保守策略。

---

# 建议的后续演进方向

推荐后续逐步拆成：

- `collector`：读取 sessions / cron
- `cleaner`：清洗 metadata 和系统噪音
- `generator`：fallback / AI 增强
- `publisher`：Feishu / Git / webhook / 微信提示
- `templates`：日报 / 周报 / 项目总结模板
- `wechat-query-handler`：在微信端识别“日报”并自动回全文

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

> 一个把 OpenClaw session 历史自动整理成结构化工作日报的 skill，支持无 API Key fallback、本地优先，以及“飞书直接推全文 + 微信主动询问取全文”的多端分发策略。
