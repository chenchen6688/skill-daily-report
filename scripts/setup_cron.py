#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据 config.env 中的自动化时间配置，创建或更新 OpenClaw cron。

目标：
- 让使用者只改 config.env
- 然后运行一次 setup_cron.py
- 就能自动得到对应时间的日报推送任务
"""

import json
import os
import re
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.env"
WORKSPACE = Path.home() / ".openclaw" / "workspace"
DAILY_SCRIPT = str((SCRIPT_DIR / "daily_report.py").resolve())
CRON_JOB_NAME = "daily-report-auto-delivery"


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


def parse_time_to_cron(value):
    raw = (value or "19:00").strip()
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", raw)
    if not m:
        raise ValueError(f"AUTOMATION_TIME 格式错误：{raw}，应为 HH:MM")
    hour = int(m.group(1))
    minute = int(m.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"AUTOMATION_TIME 超出范围：{raw}")
    return f"{minute} {hour} * * *"


def run_json(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(WORKSPACE))
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or f"command failed: {' '.join(cmd)}")
    return json.loads(result.stdout)


def detect_channels(cfg):
    enable_feishu = str(cfg.get("ENABLE_FEISHU", "false")).lower() == "true"
    enable_dingtalk = str(cfg.get("ENABLE_DINGTALK", "false")).lower() == "true"
    return enable_feishu, enable_dingtalk


def build_prompt(enable_feishu, enable_dingtalk):
    targets = []
    if enable_feishu:
        targets.append("飞书 webhook 推送成功")
    if enable_dingtalk:
        targets.append("钉钉 webhook 推送成功")
    target_text = "、".join(targets) if targets else "外部推送状态"

    return (
        "请完成以下任务：\n"
        f"1. 运行本地日报脚本，生成今天的日报：`python3 {DAILY_SCRIPT}`\n"
        "2. 确认日报文件已生成\n"
        f"3. 确认 {target_text}\n"
        "4. 如果执行失败，输出失败原因\n\n"
        "注意：这是由 daily-report/setup_cron.py 创建或更新的自动化日报推送任务。"
    )


def main():
    cfg = load_config()
    cron_expr = parse_time_to_cron(cfg.get("AUTOMATION_TIME", "19:00"))
    tz = cfg.get("AUTOMATION_TZ", "Asia/Shanghai").strip() or "Asia/Shanghai"
    enable_feishu, enable_dingtalk = detect_channels(cfg)

    payload = {
        "kind": "agentTurn",
        "message": build_prompt(enable_feishu, enable_dingtalk),
        "timeoutSeconds": 180,
    }

    job = {
        "name": CRON_JOB_NAME,
        "schedule": {"kind": "cron", "expr": cron_expr, "tz": tz},
        "payload": payload,
        "sessionTarget": "isolated",
        "delivery": {"mode": "none"},
        "enabled": True,
    }

    jobs = run_json(["openclaw", "cron", "list", "--json"])
    matched = None
    for item in jobs.get("jobs", []):
        if item.get("name") == CRON_JOB_NAME:
            matched = item
            break

    if matched:
        result = run_json([
            "openclaw", "cron", "update", matched["id"],
            "--json", json.dumps({
                "schedule": job["schedule"],
                "payload": job["payload"],
                "sessionTarget": job["sessionTarget"],
                "delivery": job["delivery"],
                "enabled": True,
            }, ensure_ascii=False)
        ])
        print(json.dumps({
            "action": "updated",
            "jobId": matched["id"],
            "name": CRON_JOB_NAME,
            "cron": cron_expr,
            "tz": tz,
            "channels": {
                "feishu": enable_feishu,
                "dingtalk": enable_dingtalk,
            },
            "result": result,
        }, ensure_ascii=False, indent=2))
    else:
        result = run_json(["openclaw", "cron", "add", "--json", json.dumps(job, ensure_ascii=False)])
        print(json.dumps({
            "action": "created",
            "name": CRON_JOB_NAME,
            "cron": cron_expr,
            "tz": tz,
            "channels": {
                "feishu": enable_feishu,
                "dingtalk": enable_dingtalk,
            },
            "result": result,
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
