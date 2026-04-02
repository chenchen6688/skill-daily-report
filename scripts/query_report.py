#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
读取本地已生成的日报全文。
用途：
- 微信等不适合主动推送全文的通道，可在用户主动发送“日报”时调用本脚本
- 输出指定日期或今天的日报全文
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw" / "workspace"
DATA_DIR = WORKSPACE / "data" / "daily-reports"


def normalize_date_arg(arg):
    if not arg or arg in {"today", "今日", "今天", "日报"}:
        return datetime.now().strftime("%Y-%m-%d")
    if arg in {"yesterday", "昨日", "昨天"}:
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    return arg


def read_report(date_str):
    report_file = DATA_DIR / f"{date_str}.md"
    if not report_file.exists():
        raise FileNotFoundError(f"未找到 {date_str} 的日报：{report_file}")
    return report_file, report_file.read_text(encoding="utf-8")


def main():
    raw = sys.argv[1].strip() if len(sys.argv) > 1 else "today"
    date_str = normalize_date_arg(raw)
    report_file, content = read_report(date_str)
    print(content)
    print(f"\n\n---\n文件路径：{report_file}")


if __name__ == "__main__":
    main()
