#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
读取本地已生成的日报全文；如果日报不存在，则自动先生成再返回。
用途：
- 微信等不适合主动推送全文的通道，可在用户主动发送“日报”时调用本脚本
- 输出指定日期或今天的日报全文
"""

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw" / "workspace"
DATA_DIR = WORKSPACE / "data" / "daily-reports"
SCRIPT_DIR = Path(__file__).parent
GENERATOR = SCRIPT_DIR / "daily_report.py"

TODAY_ALIASES = {
    "today", "今日", "今天", "日报", "今日日报", "今天日报", "本日报", "本日总结"
}
YESTERDAY_ALIASES = {
    "yesterday", "昨日", "昨天", "昨日报", "昨天日报", "昨日日报"
}


def normalize_date_arg(arg):
    normalized = (arg or "").strip().lower()
    if not normalized or normalized in TODAY_ALIASES:
        return datetime.now().strftime("%Y-%m-%d")
    if normalized in YESTERDAY_ALIASES:
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    return arg


def ensure_report_exists(date_str):
    report_file = DATA_DIR / f"{date_str}.md"
    if report_file.exists():
        return report_file

    subprocess.run(
        ["python3", str(GENERATOR), date_str],
        check=True,
        cwd=str(WORKSPACE),
    )

    if not report_file.exists():
        raise FileNotFoundError(f"日报生成完成后仍未找到文件：{report_file}")
    return report_file


def read_report(date_str):
    report_file = ensure_report_exists(date_str)
    return report_file, report_file.read_text(encoding="utf-8")


def main():
    raw = sys.argv[1].strip() if len(sys.argv) > 1 else "today"
    date_str = normalize_date_arg(raw)
    report_file, content = read_report(date_str)
    print(content)
    print(f"\n\n---\n文件路径：{report_file}")


if __name__ == "__main__":
    main()
