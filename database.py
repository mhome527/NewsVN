"""SQLite helpers dùng chung cho web app và script lấy tin."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "news.db"


def get_conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                title        TEXT NOT NULL,
                link         TEXT NOT NULL UNIQUE,
                summary      TEXT,
                source       TEXT NOT NULL,
                published_at TEXT,
                fetched_date TEXT NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_fetched_date ON articles(fetched_date)"
        )
        cols = {row[1] for row in conn.execute("PRAGMA table_info(articles)")}
        if "title_vi" not in cols:
            conn.execute("ALTER TABLE articles ADD COLUMN title_vi TEXT")
            conn.execute("ALTER TABLE articles ADD COLUMN summary_vi TEXT")


def insert_article(conn, title, link, summary, source, published_at, fetched_date):
    """Thêm bài viết, bỏ qua nếu link đã tồn tại. Trả về True nếu thêm mới."""
    cur = conn.execute(
        """INSERT OR IGNORE INTO articles
           (title, link, summary, source, published_at, fetched_date)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (title, link, summary, source, published_at, fetched_date),
    )
    return cur.rowcount > 0


def articles_by_date(date_str):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM articles WHERE fetched_date = ?
               ORDER BY published_at DESC, id DESC""",
            (date_str,),
        ).fetchall()
    return rows


def all_dates():
    """Danh sách các ngày có tin, mới nhất trước, kèm số bài."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT fetched_date, COUNT(*) AS count FROM articles
               GROUP BY fetched_date ORDER BY fetched_date DESC"""
        ).fetchall()
    return rows


def latest_date():
    with get_conn() as conn:
        row = conn.execute("SELECT MAX(fetched_date) AS d FROM articles").fetchone()
    return row["d"] if row else None
