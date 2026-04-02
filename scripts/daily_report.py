#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日工作报告生成器（多端版）
- 默认本地生成 markdown
- 支持外部 LLM（OpenAI / Anthropic / MiniMax）增强总结
- 无 API Key 时自动 fallback 到规则化日报
- 支持 Feishu 直接推送全文
- 支持生成微信端“主动询问式获取全文”的提示文案
"""

import os
import re
import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from urllib import request, error


NOISE_PATTERNS = [
    r"^🦞 OpenClaw ",
    r"^⚠️ Agent failed before reply:",
    r"^Logs: openclaw logs --follow",
    r"^📚 Context:",
    r"^🧵 Session:",
    r"^⚙️ Runtime:",
    r"^🪢 Queue:",
    r"^OpenClaw status$",
    r"^FAQ:",
    r"^Troubleshooting:",
    r"^Update available",
    r"^Next steps:",
    r"^Sender \(untrusted metadata\):",
    r"^Conversation info \(untrusted metadata\):",
    r"^Read HEARTBEAT\.md if it exists",
    r"^HEARTBEAT_OK$",
]

SUMMARY_HINTS = {
    "缺依赖": ["httpx", "module not found", "no module named"],
    "路径兼容": ["写死", "/users/mymac", "sessions 目录", "openclaw_sessions_dir", "openclaw_home"],
    "外部模型依赖": ["api key", "openai_api_key", "anthropic_api_key", "minimax_api_key", "外部 api", "外部模型"],
    "默认安全配置": ["enable_feishu=false", "enable_git=false", "默认关闭", "误发", "不碰飞书", "不碰 git"],
    "fallback 日报": ["fallback", "基础日报", "无 api key"],
    "通用 skill": ["通用 skill", "预留", "publisher", "cleaner", "collector", "模板", "通用化"],
    "试运行验证": ["试运行", "跑通", "运行一下", "看看有没有问题", "看看效果"],
    "文档配置": ["skill.md", "config.env", "config.env.example", "文档", "配置示例"],
    "本地生成": ["本地", "markdown", "日报已保存到", "daily-reports"],
}


def load_env_from_shell():
    zshrc = Path.home() / ".zshrc"
    if not zshrc.exists():
        return
    with open(zshrc, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("export ") and "=" in line:
                line = line[7:]
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and val and key not in os.environ:
                    os.environ[key] = val


load_env_from_shell()

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.env"
WORKSPACE = Path.home() / ".openclaw" / "workspace"
DATA_DIR = WORKSPACE / "data" / "daily-reports"


def load_config():
    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    config[key.strip()] = val.strip()
    return config


CONFIG = load_config()

FEISHU_USER_ID = os.environ.get("FEISHU_USER_ID", CONFIG.get("FEISHU_USER_ID", ""))
ENABLE_FEISHU = os.environ.get("ENABLE_FEISHU", CONFIG.get("ENABLE_FEISHU", "false")).lower() == "true"
ENABLE_GIT = os.environ.get("ENABLE_GIT", CONFIG.get("ENABLE_GIT", "false")).lower() == "true"
WECHAT_QUERY_HINT_ENABLED = os.environ.get("WECHAT_QUERY_HINT_ENABLED", CONFIG.get("WECHAT_QUERY_HINT_ENABLED", "true")).lower() == "true"
WECHAT_QUERY_COMMAND = os.environ.get("WECHAT_QUERY_COMMAND", CONFIG.get("WECHAT_QUERY_COMMAND", "日报")).strip() or "日报"
FEISHU_WEBHOOK_URL = os.environ.get("FEISHU_WEBHOOK_URL", CONFIG.get("FEISHU_WEBHOOK_URL", "")).strip()


def get_today_date():
    return datetime.now().strftime("%Y-%m-%d")


def get_sessions_dir():
    custom = os.environ.get("OPENCLAW_SESSIONS_DIR")
    if custom:
        return Path(custom).expanduser()
    openclaw_home = Path(os.environ.get("OPENCLAW_HOME", str(Path.home() / ".openclaw"))).expanduser()
    return openclaw_home / "agents" / "main" / "sessions"


def get_api_config():
    minimax_key = os.environ.get("MINIMAX_API_KEY", "")
    minimax_url = os.environ.get("MINIMAX_API_URL", "https://api.minimaxi.com")
    if minimax_key:
        return {
            "provider": "minimax",
            "key": minimax_key,
            "url": minimax_url,
            "model": os.environ.get("MINIMAX_MODEL", "MiniMax-M2.5")
        }

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "") or os.environ.get("CLAUDE_API_KEY", "")
    anthropic_url = (
        os.environ.get("ANTHROPIC_API_URL", "")
        or os.environ.get("ANTHROPIC_BASE_URL", "")
        or os.environ.get("CLAUDE_BASE_URL", "")
        or "https://api.anthropic.com"
    )
    if anthropic_key:
        return {
            "provider": "anthropic",
            "key": anthropic_key,
            "url": anthropic_url,
            "model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        }

    openai_key = os.environ.get("OPENAI_API_KEY", "") or os.environ.get("OPENAI_KEY", "")
    openai_url = (
        os.environ.get("OPENAI_API_URL", "")
        or os.environ.get("OPENAI_BASE_URL", "")
        or "https://api.openai.com/v1"
    )
    if openai_key:
        return {
            "provider": "openai",
            "key": openai_key,
            "url": openai_url,
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o")
        }

    return None


def get_cron_runs_for_date(start, end):
    try:
        result = subprocess.run(["openclaw", "status"], capture_output=True, text=True, timeout=20)
        if result.returncode != 0:
            return ""
    except Exception:
        return ""
    return ""


def get_cron_task_definitions():
    return ""


def strip_reply_tags(text):
    return re.sub(r"^\[\[\s*reply_to[^\]]*\]\]\s*", "", text).strip()


def strip_code_fences(text):
    text = re.sub(r"```json.*?```", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    return text


def strip_metadata_blobs(text):
    text = re.sub(r"Sender \(untrusted metadata\):.*?(?=\[[A-Z][a-z]{2}|$)", " ", text, flags=re.DOTALL)
    text = re.sub(r"Conversation info \(untrusted metadata\):.*?(?=\n\n|$)", " ", text, flags=re.DOTALL)
    text = re.sub(r"\{\s*\"label\":.*?\}\s*", " ", text, flags=re.DOTALL)
    text = re.sub(r"\{\s*\"message_id\":.*?\}\s*", " ", text, flags=re.DOTALL)
    return text


def clean_text(text):
    if not text:
        return ""
    text = text.replace("\u0000", " ")
    text = strip_reply_tags(text)
    text = strip_code_fences(text)
    text = strip_metadata_blobs(text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\[[A-Z][a-z]{2} .*?GMT\+\d+\]\s*", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_noise_text(text):
    if not text:
        return True
    stripped = text.strip()
    if not stripped:
        return True
    if stripped.startswith("[toolResult]") or "[toolResult]" in stripped:
        return True
    if stripped in {"你好", "可以", "没事，现在好了", "hello", "hi", "行 冲吧", "可以 执行吧 小小陈"}:
        return True
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, stripped, flags=re.IGNORECASE):
            return True
    if len(stripped) < 4:
        return True
    return False


def should_keep_line(text):
    text = clean_text(text)
    if not text or is_noise_text(text):
        return False
    return True


def get_sessions_for_date(target_date_str):
    sessions_dir = get_sessions_dir()

    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    yesterday = target_date - timedelta(days=1)

    start = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 0, 0)
    end = datetime(target_date.year, target_date.month, target_date.day, 23, 0, 0)

    print(f"时间范围: {start} ~ {end}")
    print(f"sessions 目录: {sessions_dir}")

    if not sessions_dir.exists():
        print("sessions 目录不存在")
        return ""

    all_jsonl_files = sorted(sessions_dir.glob("*.jsonl"))
    print(f"找到 {len(all_jsonl_files)} 个 session 文件")

    all_messages = []

    for session_file in all_jsonl_files:
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if not lines:
                continue

            has_content = False
            session_content = [f"\n=== {session_file.name} ===\n"]

            for line in lines:
                try:
                    msg = json.loads(line)
                    ts = msg.get("timestamp", "")
                    if not ts:
                        continue

                    msg_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    msg_time = msg_time.replace(tzinfo=None) + timedelta(hours=8)
                    if not (start <= msg_time <= end):
                        continue

                    if msg.get("type") != "message":
                        continue

                    message = msg.get("message", {})
                    role = message.get("role", "")
                    if role not in ("user", "assistant"):
                        continue

                    content = message.get("content", [])
                    text_parts = []
                    for c in content:
                        if c.get("type") == "text":
                            text = clean_text(c.get("text", ""))
                            if should_keep_line(text):
                                text_parts.append(text)

                    if text_parts:
                        text = " ".join(text_parts).strip()[:300]
                        if should_keep_line(text):
                            has_content = True
                            session_content.append(f"[{role}]: {text}")
                except Exception:
                    continue

            if has_content and len(session_content) > 1:
                all_messages.append("\n".join(session_content))

        except Exception as e:
            print(f"读取 {session_file.name} 失败: {e}")
            continue

    cron_runs = get_cron_runs_for_date(start, end)
    if cron_runs:
        all_messages.append(f"\n=== Cron任务执行记录 ===\n{cron_runs}")
    else:
        cron_defs = get_cron_task_definitions()
        if cron_defs:
            all_messages.append(f"\n=== Cron任务定义 ===\n{cron_defs}")

    return "\n\n".join(all_messages)


def extract_message_lines(sessions_content):
    lines = []
    for raw in sessions_content.splitlines():
        line = raw.strip()
        if line.startswith('[user]:') or line.startswith('[assistant]:'):
            lines.append(line)
    return lines


def infer_summary_facts(lines):
    joined = "\n".join(lines).lower()
    facts = []
    for label, keys in SUMMARY_HINTS.items():
        if any(k.lower() in joined for k in keys):
            facts.append(label)
    return facts


def summarize_lines(lines, limit=8):
    seen = set()
    result = []
    for line in lines:
        line = clean_text(line).strip(" -—:：")
        if not line or line in seen:
            continue
        seen.add(line)
        result.append(line)
        if len(result) >= limit:
            break
    return result


def build_rule_based_sections(facts):
    code_items = []
    problem_items = []
    todo_items = []
    other_items = []

    if "试运行验证" in facts:
        code_items.append("完成目标日报 skill 的本地试运行与可用性验证，确认当前仓库初始状态下无法直接稳定运行。")
    if "路径兼容" in facts:
        code_items.append("调整 sessions 路径读取方式，改为基于当前用户目录与可覆盖环境变量自动定位 OpenClaw 数据目录。")
        problem_items.append("定位并修复 session 路径写死导致的环境兼容问题，避免脚本在不同用户名或目录结构下失效。")
    if "缺依赖" in facts:
        problem_items.append("发现并补齐脚本运行所需的 httpx 依赖，解决最初无法执行的基础报错。")
    if "fallback 日报" in facts:
        code_items.append("增加无 API Key 场景下的 fallback 基础日报生成能力，保证在纯本地环境中也能产出日报文件。")
    if "默认安全配置" in facts:
        code_items.append("收敛默认配置策略，将 Feishu / Git 外部输出改为默认关闭，避免测试阶段误发消息或误推送。")
    if "文档配置" in facts:
        code_items.append("补充并修订 SKILL.md、config.env 与 config.env.example，使安装、配置和运行方式更适合通用 skill 使用。")
    if "本地生成" in facts:
        problem_items.append("确认当前版本在无外部模型凭证时，仍可稳定生成本地 markdown 日报作为降级结果。")
    if "外部模型依赖" in facts:
        problem_items.append("识别出增强总结仍依赖外部模型 API Key，未配置时会自动回退到基础日报模式。")
    if "通用 skill" in facts:
        todo_items.append("下一步继续围绕 cleaner、publisher、collector 与模板层做模块化拆分，降低后续扩展成本。")
        todo_items.append("后续可补充更细的内容归纳规则，并为周报、指定日期范围总结和多渠道发布预留接口。")

    if not code_items:
        code_items.append("今天主要完成了日报 skill 的本地适配、结构梳理与基础能力验证。")
    if not problem_items:
        problem_items.append("已完成基础问题排查，当前版本能够完成本地收集与日报落盘。")
    if not todo_items:
        todo_items.append("后续可继续增强为通用 skill，包括模型适配、输出通道抽象、模板化与更细的内容清洗。")

    return {
        "code": summarize_lines(code_items, limit=6),
        "problem": summarize_lines(problem_items, limit=6),
        "todo": summarize_lines(todo_items, limit=6),
        "other": summarize_lines(other_items, limit=6),
    }


def build_wechat_query_hint(target_date, report_file):
    if not WECHAT_QUERY_HINT_ENABLED:
        return ""
    return (
        f"\n\n---\n"
        f"## 微信端获取方式\n"
        f"由于微信通道的主动推送链路在部分环境下不稳定，建议在微信里主动发送 **{WECHAT_QUERY_COMMAND}** 获取 {target_date} 的日报全文。\n\n"
        f"已生成文件：`{report_file}`\n"
    )


def build_fallback_report(sessions_content, target_date):
    lines = extract_message_lines(sessions_content)
    user_lines = [x[7:].strip() for x in lines if x.startswith('[user]:')]
    assistant_lines = [x[12:].strip() for x in lines if x.startswith('[assistant]:')]
    merged_lines = [x for x in user_lines + assistant_lines if should_keep_line(x)]

    cron_section = []
    in_cron = False
    for raw in sessions_content.splitlines():
        line = raw.strip()
        if '=== Cron任务执行记录 ===' in line or '=== Cron任务定义 ===' in line:
            in_cron = True
            continue
        if in_cron and line.startswith('==='):
            in_cron = False
        if in_cron and line and should_keep_line(line):
            cron_section.append(clean_text(line))

    facts = infer_summary_facts(merged_lines)
    sections = build_rule_based_sections(facts)

    other_candidates = []
    if user_lines or assistant_lines:
        other_candidates.append(f"今日共整理用户侧关键信息 {len(user_lines)} 条，助手侧响应 {len(assistant_lines)} 条。")
    if not cron_section:
        other_candidates.append("今日未检测到可用的 Cron 执行记录，或当前实例没有配置相关定时任务。")
    other_candidates.extend(sections["other"])

    def bullets(items, empty_text):
        items = summarize_lines(items, limit=6)
        if not items:
            return f"- {empty_text}"
        return "\n".join(f"- {item[:180]}" for item in items)

    return f"""# {target_date} 工作日报

### 一、定时任务执行记录
{bullets(cron_section[:6], '今日未发现定时任务执行记录。')}

### 二、代码编写
{bullets(sections['code'], '今天主要完成了日报 skill 的本地试运行、兼容性适配与基础能力打通。')}

### 三、问题解决
{bullets(sections['problem'], '已定位并处理部分基础运行问题，当前版本可完成本地收集与文件输出。')}

### 四、待解决问题
{bullets(sections['todo'], '后续可继续增强为通用 skill，包括模型适配、输出通道抽象、模板化与更细的内容清洗。')}

### 五、其他事项
{bullets(other_candidates[:6], '无。')}
"""


def analyze_minimax(prompt, api_key, api_url, model):
    import httpx
    url = api_url.rstrip('/') + "/v1/text/chatcompletion_v2"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096, "temperature": 0.7}
    resp = httpx.post(url, json=data, headers=headers, timeout=60)
    if resp.status_code == 200:
        result = resp.json()
        return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip() or "API Error: empty response"
    return f"API Error: {resp.status_code}"


def analyze_openai(prompt, api_key, api_url, model):
    import httpx
    url = api_url.rstrip('/') + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if "azure" in api_url.lower():
        headers = {"api-key": api_key, "Content-Type": "application/json"}
    data = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096, "temperature": 0.7}
    resp = httpx.post(url, json=data, headers=headers, timeout=60)
    if resp.status_code == 200:
        result = resp.json()
        return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip() or "API Error: empty response"
    return f"API Error: {resp.status_code}"


def analyze_anthropic(prompt, api_key, api_url, model):
    import httpx
    url = api_url.rstrip('/') + "/v1/messages"
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
    data = {"model": model, "max_tokens": 4096, "messages": [{"role": "user", "content": prompt}]}
    resp = httpx.post(url, json=data, headers=headers, timeout=60)
    if resp.status_code == 200:
        result = resp.json()
        content = result.get("content", [{}])
        if content:
            return content[0].get("text", "").strip() or "API Error: empty response"
    return f"API Error: {resp.status_code}"


def analyze_with_ai(sessions_content, target_date):
    api_config = get_api_config()
    if not api_config:
        print("未检测到外部 API Key，使用 fallback 模式生成基础日报")
        return build_fallback_report(sessions_content, target_date)

    provider = api_config["provider"]
    api_key = api_config["key"]
    api_url = api_config["url"]
    model = api_config["model"]
    print(f"使用 API: {provider} | Model: {model}")

    cron_info = ""
    for marker in ["Cron任务执行记录", "Cron任务定义"]:
        if marker in sessions_content:
            idx = sessions_content.find(f"=== {marker} ===")
            end_idx = sessions_content.find("===", idx + 20)
            cron_info = "\n" + sessions_content[idx:end_idx if end_idx > 0 else len(sessions_content)][:2000]
            break

    prompt = f"""请分析以下 OpenClaw 对话记录和定时任务信息，生成工作日报。

格式要求：
- 主标题：# YYYY-MM-DD 工作日报
- 副标题使用中文数字：一、二、三、四、五
- 关键信息加粗
- 每项内容精简到1-5句话
- 忽略系统横幅、状态信息、metadata、heartbeat 提示和纯错误噪音，重点总结实际工作内容、问题定位与后续计划

输出格式：

# {target_date} 工作日报

### 一、定时任务执行记录
- 列出定时任务执行结果

### 二、代码编写
- 列出编写的代码

### 三、问题解决
- 列出解决的问题

### 四、待解决问题
- 列出待解决的问题

### 五、其他事项
- 列出其他重要事项

{cron_info}

对话记录：
{sessions_content[:25000]}
"""

    try:
        if provider == "minimax":
            return analyze_minimax(prompt, api_key, api_url, model)
        if provider == "openai":
            return analyze_openai(prompt, api_key, api_url, model)
        if provider == "anthropic":
            return analyze_anthropic(prompt, api_key, api_url, model)
        return build_fallback_report(sessions_content, target_date)
    except Exception as e:
        print(f"调用外部模型失败，回退到 fallback 模式: {e}")
        return build_fallback_report(sessions_content, target_date)


def save_report(content, date=None):
    if date is None:
        date = get_today_date()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    report_file = DATA_DIR / f"{date}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(content)
    return report_file


def send_to_feishu(content, target_date):
    if not ENABLE_FEISHU:
        print("飞书推送已禁用")
        return True

    if FEISHU_WEBHOOK_URL:
        payload = json.dumps({"msg_type": "text", "content": {"text": content}}, ensure_ascii=False).encode("utf-8")
        req = request.Request(FEISHU_WEBHOOK_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with request.urlopen(req, timeout=20) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                print(f"飞书 webhook 推送成功: HTTP {resp.status} | {body[:300]}")
                return True
        except error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore") if hasattr(e, 'read') else ''
            print(f"飞书 webhook 推送失败: HTTP {e.code} | {body[:300]}")
            return False
        except Exception as e:
            print(f"飞书 webhook 推送失败: {e}")
            return False

    if FEISHU_USER_ID:
        print(f"已启用 Feishu 推送，但当前仅配置了 FEISHU_USER_ID={FEISHU_USER_ID}。建议补充 FEISHU_WEBHOOK_URL 以直接推送 {target_date} 日报全文。")
        return False

    print("已启用 Feishu 推送，但未配置 FEISHU_WEBHOOK_URL 或 FEISHU_USER_ID，跳过发送")
    return False


def build_wechat_query_message(target_date, report_file):
    return (
        f"今日日报已生成：{target_date}\n"
        f"文件路径：{report_file}\n"
        f"由于微信主动推送链路在部分环境下不稳定，建议你在微信里发送“{WECHAT_QUERY_COMMAND}”，再由机器人返回全文。"
    )


def push_to_git(target_date):
    if not ENABLE_GIT:
        print("Git 推送已禁用")
        return True
    print("当前版本保留 Git publisher 接口，但默认未实现推送逻辑")
    return False


def main():
    target_date = datetime.now().strftime("%Y-%m-%d")
    if len(sys.argv) > 1:
        target_date = sys.argv[1]

    print(f"生成 {target_date} 的工作日报...")
    print(f"飞书: {ENABLE_FEISHU} | Git: {ENABLE_GIT} | 微信主动询问提示: {WECHAT_QUERY_HINT_ENABLED}")

    sessions_content = get_sessions_for_date(target_date)
    print(f"获取到 {len(sessions_content)} 字符")

    report = analyze_with_ai(sessions_content, target_date)
    report_file = save_report(report, target_date)
    print(f"日报已保存到: {report_file}")

    report_with_hint = report + build_wechat_query_hint(target_date, report_file)

    if ENABLE_FEISHU:
        send_to_feishu(report_with_hint, target_date)

    print("微信端建议提示：")
    print(build_wechat_query_message(target_date, report_file))

    if ENABLE_GIT:
        push_to_git(target_date)

    return report_with_hint


if __name__ == "__main__":
    main()
