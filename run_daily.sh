#!/bin/bash
# Script cho cron chạy hàng ngày: lấy tin mới, tóm tắt tiếng Việt và ghi log.
cd "$(dirname "$0")"
# Cron không có env của shell — nạp GEMINI_API_KEY từ file .env nếu có
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi
./venv/bin/python fetch_news.py >> data/fetch.log 2>&1
