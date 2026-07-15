#!/usr/bin/env python3
"""Web app hiển thị tin công nghệ hàng ngày.

Chạy:  python3 app.py  rồi mở http://127.0.0.1:5000
"""
from datetime import date, datetime

from flask import Flask, abort, render_template

import database

app = Flask(__name__)
database.init_db()


@app.template_filter("vn_date")
def vn_date(date_str):
    """2026-06-12 -> 12/06/2026"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return date_str


@app.route("/")
def index():
    """Trang chủ: tin của ngày mới nhất có dữ liệu."""
    day = database.latest_date()
    if not day:
        return render_template("index.html", articles=[], day=None,
                               dates=[], is_today=False)
    return show_date(day)


@app.route("/date/<day>")
def show_date(day):
    try:
        datetime.strptime(day, "%Y-%m-%d")
    except ValueError:
        abort(404)
    articles = database.articles_by_date(day)
    dates = database.all_dates()
    sources = sorted({a["source"] for a in articles})
    return render_template(
        "index.html",
        articles=articles,
        day=day,
        dates=dates,
        sources=sources,
        is_today=(day == date.today().isoformat()),
    )


if __name__ == "__main__":
    # Cổng 5000 bị AirPlay Receiver của macOS chiếm sẵn -> dùng 5001
    app.run(debug=True, port=5001)
