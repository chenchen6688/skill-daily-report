# skill-daily-report

一个基于 **OpenClaw 本地会话数据** 生成日报的 skill，支持多端分发：

- **飞书**：直接推送日报全文
- **钉钉**：直接推送日报全文
- **微信**：通过主动查询返回日报全文

核心原则：

> **日报分析在本地完成，渠道只负责推送或查询结果。**

---

# 一、这个项目能做什么

这个仓库提供四类能力：

## 1）本地生成日报

从 OpenClaw 本地 sessions 提取对话内容，自动整理为 markdown 日报。

支持：
- 无 API Key fallback
- OpenAI / Anthropic / MiniMax 增强总结

## 2）飞书推送日报全文

生成日报后，可直接通过飞书 webhook 把全文推送出去。

## 3）钉钉推送日报全文

生成日报后，可直接通过钉钉机器人 webhook 把全文推送出去。

## 4）微信主动查询日报全文

用户在微信里发送：
- `日报`
- `今日日报`
- `今天日报`
- `昨天日报`
- `昨日报`
- `昨日日报`

然后由 OpenClaw 调用本仓库的查询脚本，直接把本地日报全文返回给用户。

如果当天日报还没生成，查询脚本会先自动生成再返回。

---

# 二、仓库里有哪些入口

## 1）生成日报

生成今天日报：

```bash
python3 scripts/daily_report.py
```

生成指定日期日报：

```bash
python3 scripts/daily_report.py 2026-04-01
```

生成后的文件位置：

```bash
~/.openclaw/workspace/data/daily-reports/YYYY-MM-DD.md
```

---

## 2）查询日报全文

用于微信等“主动查询”场景。

读取今天日报：

```bash
python3 scripts/query_report.py today
```

读取昨天日报：

```bash
python3 scripts/query_report.py yesterday
```

读取指定日期日报：

```bash
python3 scripts/query_report.py 2026-04-01
```

说明：
- 如果日报文件已存在 → 直接返回全文
- 如果日报文件不存在 → 自动先生成，再返回全文

---

## 3）自动创建 / 更新定时任务

如果你希望根据配置里的时间自动创建 OpenClaw cron，可以运行：

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

的 OpenClaw cron 任务。

---

# 三、最推荐的接入方式

## 方案 A：只本地生成

适合先把日报跑起来。

### 第一步：安装依赖

```bash
python3 -m pip install --user -r requirements.txt
```

### 第二步：在 **daily-report 项目目录下** 复制配置文件

```bash
cp scripts/config.env.example scripts/config.env
```

说明：以上命令需要在 `daily-report` 项目目录内执行。

### 第三步：直接运行

```bash
python3 scripts/daily_report.py
```

---

## 方案 B：飞书全文推送

### 第一步：在 **daily-report 项目目录下** 复制配置文件

```bash
cp scripts/config.env.example scripts/config.env
```

说明：以上命令需要在 `daily-report` 项目目录内执行。

### 第二步：编辑本地配置

编辑：

```bash
scripts/config.env
```

填入：

```env
ENABLE_FEISHU=true
FEISHU_WEBHOOK_URL=你的飞书机器人 webhook
```

### 第三步：运行日报脚本

```bash
python3 scripts/daily_report.py
```

效果：
- 本地生成日报文件
- 飞书 webhook 收到全文

---

## 方案 C：钉钉全文推送

### 第一步：在 **daily-report 项目目录下** 复制配置文件

```bash
cp scripts/config.env.example scripts/config.env
```

说明：以上命令需要在 `daily-report` 项目目录内执行。

### 第二步：编辑本地配置

编辑：

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
- 如果钉钉机器人配置了关键词校验，`DINGTALK_KEYWORD` 必须和钉钉机器人要求一致
- 脚本会自动把关键词补到消息内容里，避免被钉钉拦截

### 第三步：运行日报脚本

```bash
python3 scripts/daily_report.py
```

效果：
- 本地生成日报文件
- 钉钉机器人收到全文

---

## 方案 D：微信主动查询

推荐方式：

1. 先手动或定时生成日报
2. 在微信里让用户发送“日报”或类似口令
3. OpenClaw 收到后调用：

```bash
python3 ~/.openclaw/workspace/skills/daily-report/scripts/query_report.py today
```

如果要查昨天：

```bash
python3 ~/.openclaw/workspace/skills/daily-report/scripts/query_report.py yesterday
```

如果要查指定日期：

```bash
python3 ~/.openclaw/workspace/skills/daily-report/scripts/query_report.py 2026-04-01
```

说明：
- 今天没生成 → 会先生成再返回
- 今天已生成 → 直接返回全文

---

## 方案 E：自动化推送（推荐）

这是最完整的使用方式。

### 第一步：在 **daily-report 项目目录下** 复制配置文件

```bash
cp scripts/config.env.example scripts/config.env
```

说明：以上命令需要在 `daily-report` 项目目录内执行。

### 第二步：编辑本地配置

例如：

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

### 第三步：自动创建 / 更新 cron

```bash
python3 scripts/setup_cron.py
```

效果：
- 每天在你配置的时间自动生成日报
- 自动推送到飞书 / 钉钉
- 微信仍然通过主动查询获取全文

---

# 四、配置说明

配置文件位置：

```bash
scripts/config.env
```

这是**本地配置文件**，一般不建议提交到公开仓库。  
仓库里应该保留的是：

```bash
scripts/config.env.example
```

真实的 webhook / token / 私有配置，应该只放在你本地的 `config.env` 中。

---

## 常用配置项

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

### 微信查询

```env
WECHAT_QUERY_HINT_ENABLED=true
WECHAT_QUERY_COMMAND=日报
```

### 自动化时间

```env
AUTOMATION_TIME=19:00
AUTOMATION_TZ=Asia/Shanghai
```

不同用户可以改成不同时间，例如：

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

# 五、为什么这样设计

因为 OpenClaw 的数据和日报生成逻辑都在本地：

- 原始对话在本地 sessions
- 分析总结在本地脚本
- 日报文件也在本地

所以合理的结构应该是：

- **本地负责生成结果**
- **飞书 / 钉钉负责主动接收结果**
- **微信负责按需查询结果**

这样做的好处：

- 多个端拿到的是同一份日报
- 不需要在每个通道重复跑总结逻辑
- 微信通道不稳定时，也不影响日报获取
- 推送时间可以由每个用户自己配置

---

# 六、典型使用流程

## 日常自动化流程

1. OpenClaw cron 到点执行
2. 调用 `daily_report.py`
3. 在本地生成日报文件
4. 自动推送飞书 / 钉钉
5. 微信侧如果用户发“日报”，调用 `query_report.py` 返回全文

---

## 手动查询流程

1. 用户在微信发 `日报`
2. OpenClaw 调用 `query_report.py today`
3. 如果今天日报不存在，先自动生成
4. 返回日报全文

---

# 七、当前能力边界

当前仓库已经包含：

- 本地日报生成
- AI 增强总结
- Feishu webhook 全文推送
- DingTalk webhook 全文推送
- 微信查询脚本入口
- 自动生成 / 更新 OpenClaw cron 的脚本
- 配置示例

当前没有直接替你改掉的是：

- 某个具体 OpenClaw 会话里的“日报”口令路由规则本身

但仓库已经把**可直接接入的脚本入口**准备好了。接入方只需要把“日报”命令映射到 `query_report.py` 即可。

---

# 八、一句话总结

> 这是一个本地生成日报、支持飞书和钉钉直接推送全文、支持微信主动查询全文，并支持按本地配置自动创建 OpenClaw cron 的 OpenClaw skill。
