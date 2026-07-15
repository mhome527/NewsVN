#!/usr/bin/env python3
"""Lấy tin công nghệ mới nhất từ các nguồn RSS và lưu vào SQLite.

Chạy thủ công:  python3 fetch_news.py
Chạy tự động hàng ngày qua cron (xem README.md).
"""
import html
import re
import time
from datetime import date, datetime

import feedparser

from database import get_conn, init_db, insert_article

# Chỉ dùng nguồn tiếng Anh hoặc tiếng Nhật; nội dung được tóm tắt
# sang tiếng Việt bằng Gemini API (xem summarizer.py).
FEEDS = [
    ("TechCrunch", "https://techcrunch.com/feed/"),
    ("The Verge", "https://www.theverge.com/rss/index.xml"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
    ("Hacker News", "https://news.ycombinator.com/rss"),
    ("GIGAZINE", "https://gigazine.net/news/rss_2.0/"),
    ("ITmedia NEWS", "https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml"),
    ("PC Watch (Impress)", "https://www.watch.impress.co.jp/data/rss/1.0/ipw/feed.rdf"),
]

MAX_PER_FEED = 20
SUMMARY_MAX_LEN = 400


def clean_summary(raw):
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > SUMMARY_MAX_LEN:
        text = text[:SUMMARY_MAX_LEN].rsplit(" ", 1)[0] + "…"
    return text


def entry_published(entry):
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            return datetime.fromtimestamp(time.mktime(parsed)).isoformat(sep=" ")
    return ""


def fetch_all():
    init_db()
    today = date.today().isoformat()
    total_new = 0

    with get_conn() as conn:
        for source, url in FEEDS:
            try:
                feed = feedparser.parse(url)
            except Exception as e:
                print(f"[LỖI] {source}: {e}")
                continue

            if feed.bozo and not feed.entries:
                print(f"[LỖI] {source}: không đọc được feed ({feed.bozo_exception})")
                continue

            added = 0
            for entry in feed.entries[:MAX_PER_FEED]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                if not title or not link:
                    continue
                if insert_article(
                    conn,
                    title=title,
                    link=link,
                    summary=clean_summary(entry.get("summary", "")),
                    source=source,
                    published_at=entry_published(entry),
                    fetched_date=today,
                ):
                    added += 1
            total_new += added
            print(f"[OK] {source}: {added} bài mới / {len(feed.entries)} bài trong feed")

    print(f"\nXong! Tổng cộng {total_new} bài mới được lưu cho ngày {today}.")


if __name__ == "__main__":
    fetch_all()
    from summarizer import summarize_pending
    summarize_pending()
