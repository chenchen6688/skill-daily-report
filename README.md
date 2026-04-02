# 📝 skill-daily-report

一个基于 **OpenClaw 本地会话数据** 生成日报的 skill。

## ✨ 它能做什么

- 🧠 **本地生成日报**
- 📮 **飞书推送全文**
- 🦾 **钉钉推送全文**
- 💬 **微信发“日报”查全文**
- ⏰ **按配置自动创建 cron**

一句话：

> **本地负责总结，渠道负责发送或查询。**

---

## 🚀 3 个核心入口

### 1）生成日报

```bash
python3 scripts/daily_report.py
```

指定日期：

```bash
python3 scripts/daily_report.py 2026-04-01
```

---

### 2）查询日报（给微信接）

```bash
python3 scripts/query_report.py today
python3 scripts/query_report.py yesterday
python3 scripts/query_report.py 2026-04-01
```

支持这些说法：
- `日报`
- `今日日报`
- `今天日报`
- `昨天日报`
- `昨日报`
- `昨日日报`

如果日报不存在，会**先自动生成再返回**。

---

### 3）自动创建 / 更新定时任务

```bash
python3 scripts/setup_cron.py
```

它会读取：
- `AUTOMATION_TIME`
- `AUTOMATION_TZ`

然后自动创建或更新 OpenClaw cron。

---

# ⚡ 最推荐的使用方式

## 方案 A：只本地生成

在 **daily-report 项目目录下** 执行：

```bash
python3 -m pip install --user -r requirements.txt
cp scripts/config.env.example scripts/config.env
open -e scripts/config.env
python3 scripts/daily_report.py
```

---

## 方案 B：飞书推送

在 `scripts/config.env` 里填：

```env
ENABLE_FEISHU=true
FEISHU_WEBHOOK_URL=你的飞书机器人 webhook
```

然后执行：

```bash
python3 scripts/daily_report.py
```

---

## 方案 C：钉钉推送

在 `scripts/config.env` 里填：

```env
ENABLE_DINGTALK=true
DINGTALK_WEBHOOK_URL=你的钉钉机器人 webhook
DINGTALK_KEYWORD=日报
```

说明：
- 如果钉钉机器人有关键词校验，`DINGTALK_KEYWORD` 要和钉钉配置一致
- 脚本会自动把关键词补进消息

然后执行：

```bash
python3 scripts/daily_report.py
```

---

## 方案 D：微信查询

让 OpenClaw 在收到“日报”后调用：

```bash
python3 ~/.openclaw/workspace/skills/daily-report/scripts/query_report.py today
```

如果要查昨天：

```bash
python3 ~/.openclaw/workspace/skills/daily-report/scripts/query_report.py yesterday
```

---

## 方案 E：自动化（推荐）

在 `scripts/config.env` 里填：

```env
ENABLE_FEISHU=true
FEISHU_WEBHOOK_URL=你的飞书机器人 webhook

ENABLE_DINGTALK=true
DINGTALK_WEBHOOK_URL=你的钉钉机器人 webhook
DINGTALK_KEYWORD=日报

WECHAT_QUERY_HINT_ENABLED=true
WECHAT_QUERY_COMMAND=日报

AUTOMATION_TIME=19:00
AUTOMATION_TZ=Asia/Shanghai
```

然后执行：

```bash
python3 scripts/setup_cron.py
```

效果：
- ⏰ 按时间自动生成日报
- 📮 自动推飞书
- 🦾 自动推钉钉
- 💬 微信继续按需查询

---

# ⚙️ 配置文件说明

## 生效文件

```bash
scripts/config.env
```

## 模板文件

```bash
scripts/config.env.example
```

注意：
- `config.env.example` 是模板，**不生效**
- `config.env` 才是你本地真正生效的配置

---

# 🧩 最常用配置项

### 飞书

```env
ENABLE_FEISHU=true
FEISHU_WEBHOOK_URL=
```

### 钉钉

```env
ENABLE_DINGTALK=true
DINGTALK_WEBHOOK_URL=
DINGTALK_KEYWORD=日报
```

### 微信

```env
WECHAT_QUERY_HINT_ENABLED=true
WECHAT_QUERY_COMMAND=日报
```

### 自动化时间

```env
AUTOMATION_TIME=19:00
AUTOMATION_TZ=Asia/Shanghai
```

---

# 🤔 为什么这样设计

因为：
- OpenClaw 对话数据在本地
- 总结逻辑在本地
- 日报文件也在本地

所以最合理的方式就是：

- 🧠 本地生成
- 📮 飞书 / 钉钉推送
- 💬 微信查询

这样：
- 多端拿到的是同一份日报
- 不用每个渠道都重新总结
- 微信链路不稳时也不影响结果

---

# ✅ 当前已支持

- 本地日报生成
- AI 增强总结
- Feishu webhook 推送
- DingTalk webhook 推送
- 微信查询脚本
- 自动创建 / 更新 OpenClaw cron

---

# 一句话总结

> 一个本地生成日报、支持飞书和钉钉推送、支持微信查询、支持自动配置定时任务的 OpenClaw skill。
