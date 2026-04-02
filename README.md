# skill-daily-report

一个基于 **OpenClaw 本地会话数据** 生成日报的 skill。

## 做了什么

这个仓库提供三类能力：

1. **生成日报**
   - 从本地 OpenClaw sessions 读取对话内容
   - 自动整理为 markdown 日报
   - 支持无 API Key fallback
   - 支持 OpenAI / Anthropic / MiniMax 增强总结

2. **多端推送**
   - **飞书**：支持直接推送日报全文
   - **钉钉**：支持直接推送日报全文

3. **微信查询**
   - 用户主动发送“日报 / 今日日报 / 昨天日报”等口令
   - 读取本地日报全文返回
   - 如果当天日报不存在，会自动先生成再返回

核心原则是：

> **日报分析在本地完成，渠道只负责推送或查询结果。**

---

## 仓库里有哪些入口

### 1）生成日报

```bash
python3 scripts/daily_report.py
```

指定日期：

```bash
python3 scripts/daily_report.py 2026-04-01
```

生成结果保存到：

```bash
~/.openclaw/workspace/data/daily-reports/YYYY-MM-DD.md
```

---

### 2）读取日报全文（给微信等通道接入）

读取今天的日报：

```bash
python3 scripts/query_report.py today
```

读取昨天的日报：

```bash
python3 scripts/query_report.py yesterday
```

读取指定日期：

```bash
python3 scripts/query_report.py 2026-04-01
```

---

## 怎么接入

### 方案一：只本地生成

```bash
python3 -m pip install --user -r requirements.txt
cp scripts/config.env.example scripts/config.env
python3 scripts/daily_report.py
```

---

### 方案二：接飞书全文推送

在本地创建并编辑：

```bash
scripts/config.env
```

填入：

```env
ENABLE_FEISHU=true
FEISHU_WEBHOOK_URL=你的飞书机器人 webhook
```

然后运行：

```bash
python3 scripts/daily_report.py
```

执行后：
- 本地会生成日报文件
- 飞书 webhook 会直接收到全文

如果你要做自动化，推荐把默认推送时间也写进本地配置：

```env
AUTOMATION_TIME=19:00
AUTOMATION_TZ=Asia/Shanghai
```

这样不同用户可以按自己的习惯改成：

```env
AUTOMATION_TIME=18:30
AUTOMATION_TZ=Asia/Shanghai
```

或者：

```env
AUTOMATION_TIME=21:00
AUTOMATION_TZ=Asia/Shanghai
```

---

### 方案三：接钉钉全文推送

在本地创建并编辑：

```bash
scripts/config.env
```

填入：

```env
ENABLE_DINGTALK=true
DINGTALK_WEBHOOK_URL=你的钉钉机器人 webhook
DINGTALK_KEYWORD=日报
```

说明：
- 如果钉钉机器人启用了关键词校验，`DINGTALK_KEYWORD` 必须和机器人配置一致
- 脚本会自动把关键词补到消息正文里，避免被钉钉拦截

然后运行：

```bash
python3 scripts/daily_report.py
```

执行后：
- 本地会生成日报文件
- 钉钉机器人会直接收到全文

---

### 方案四：接微信主动查询

推荐方式：

1. 先定时或手动生成日报
2. 在微信里让用户发送“日报”
3. OpenClaw 收到后调用：

```bash
python3 ~/.openclaw/workspace/skills/daily-report/scripts/query_report.py today
```

这个查询脚本支持更自然的说法：

- `日报`
- `今日日报`
- `今天日报`
- `昨天日报`
- `昨日报`
- `昨日日报`

并且：
- 如果当天日报已经存在 → 直接返回全文
- 如果当天日报不存在 → 先自动生成，再返回全文

---

## 自动化时间如何配置

这个仓库本身负责：
- 生成日报
- 推送飞书 / 钉钉
- 提供微信查询入口

**真正的定时执行建议交给 OpenClaw cron。**

推荐做法是：

1. 在本地 `scripts/config.env` 里写入你希望的默认时间

```env
AUTOMATION_TIME=19:00
AUTOMATION_TZ=Asia/Shanghai
```

2. 创建 OpenClaw cron 时，读取这个时间并转换成对应的 cron 表达式

例如：
- `19:00` → `0 19 * * *`
- `18:30` → `30 18 * * *`

也就是说，这个项目现在支持的是：

> **自动化时间可配置，但调度本身由 OpenClaw cron 承担。**

这样做的好处是：
- 不同用户可以保留自己的推送时间
- skill 仓库本身不需要硬编码某个固定时间
- 飞书 / 钉钉 / 微信逻辑不受影响

---

## 为什么要这样设计

因为 OpenClaw 的数据和日报生成逻辑都在本地：

- 原始对话在本地 sessions
- 分析总结在本地脚本
- 日报文件也在本地

所以正确的结构应该是：

- **本地负责生成结果**
- **飞书 / 钉钉负责主动接收结果**
- **微信负责按需查询结果**

这样能保证：

- 多个端拿到的是同一份日报
- 不需要在每个通道重复跑总结逻辑
- 微信链路不稳定时，仍然能稳定获取全文

---

## 最小配置

复制配置文件：

```bash
cp scripts/config.env.example scripts/config.env
```

最小可用配置：

```env
ENABLE_FEISHU=false
ENABLE_DINGTALK=false
ENABLE_GIT=false
WECHAT_QUERY_HINT_ENABLED=true
WECHAT_QUERY_COMMAND=日报
```

---

## 自动创建 / 更新定时任务

如果你希望根据 `config.env` 里的时间自动配置 OpenClaw cron，可以直接运行：

```bash
python3 scripts/setup_cron.py
```

这个脚本会：
- 读取 `AUTOMATION_TIME`
- 读取 `AUTOMATION_TZ`
- 检查是否启用了飞书 / 钉钉
- 自动创建或更新一个名为：

```text
daily-report-auto-delivery
```

的 OpenClaw cron 任务

例如：

```env
AUTOMATION_TIME=19:00
AUTOMATION_TZ=Asia/Shanghai
ENABLE_FEISHU=true
ENABLE_DINGTALK=true
```

运行：

```bash
python3 scripts/setup_cron.py
```

就会自动生成一个每天 19:00 执行的日报推送任务。

---

## 常见用法

### 生成今天日报

```bash
python3 scripts/daily_report.py
```

### 生成指定日期日报

```bash
python3 scripts/daily_report.py 2026-04-01
```

### 读取今天日报全文

```bash
python3 scripts/query_report.py today
```

### 读取昨天日报全文

```bash
python3 scripts/query_report.py yesterday
```

---

## 当前能力边界

当前仓库已经包含：

- 本地日报生成
- AI 增强总结
- Feishu webhook 全文推送
- DingTalk webhook 全文推送
- 微信查询脚本入口
- 配置示例

当前没有直接替你改掉的是：

- 某个具体 OpenClaw 会话里的“日报”口令路由规则本身

但仓库已经把**可直接接入的脚本入口**准备好了。接入方只需要把“日报”命令映射到 `query_report.py` 即可。

---

## 一句话总结

> 这是一个本地生成日报、支持飞书和钉钉直接推送全文，并支持微信通过主动查询返回本地日报全文的 OpenClaw skill。
