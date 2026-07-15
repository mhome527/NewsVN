"""Dịch và tóm tắt bài viết sang tiếng Việt bằng Gemini API.

Cần biến môi trường GEMINI_API_KEY. Nếu thiếu, bước tóm tắt được bỏ qua
và web hiển thị nội dung gốc; lần chạy sau có key sẽ tóm tắt bù.
"""
import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from database import get_conn

load_dotenv()

MODEL = "gemini-3.1-flash-lite"
BATCH_SIZE = 10
MAX_PER_RUN = 20

SYSTEM_PROMPT = (
    "Bạn là biên tập viên tin công nghệ. Với mỗi bài báo (tiếng Anh hoặc tiếng Nhật) "
    "được cung cấp, hãy dịch tiêu đề sang tiếng Việt tự nhiên và viết tóm tắt nội dung "
    "bằng tiếng Việt trong 2-3 câu, dễ hiểu với độc giả phổ thông. "
    "Giữ nguyên tên riêng, tên sản phẩm, tên công ty."
)


class ArticleSummary(BaseModel):
    id: int
    title_vi: str
    summary_vi: str


class SummaryBatch(BaseModel):
    articles: list[ArticleSummary]


def pending_articles(conn, limit=MAX_PER_RUN):
    return conn.execute(
        """SELECT id, title, summary, source FROM articles WHERE summary_vi IS NULL
           ORDER BY published_at DESC, id DESC LIMIT ?""",
        (limit,),
    ).fetchall()


def summarize_batch(client, rows):
    payload = [
        {"id": r["id"], "source": r["source"], "title": r["title"], "summary": r["summary"] or ""}
        for r in rows
    ]
    response = client.models.generate_content(
        model=MODEL,
        contents=(
            "Dịch tiêu đề và tóm tắt các bài báo sau sang tiếng Việt. "
            "Trả về đúng id của từng bài:\n\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
        ),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=SummaryBatch,
        ),
    )
    return response.parsed.articles


def summarize_pending():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[BỎ QUA] Chưa đặt GEMINI_API_KEY — không tóm tắt tiếng Việt.")
        return

    client = genai.Client(api_key=api_key)
    with get_conn() as conn:
        rows = pending_articles(conn)
        if not rows:
            print("[OK] Không có bài nào cần tóm tắt.")
            return
        print(f"Tóm tắt {len(rows)} bài bằng Gemini ({MODEL})...")

        done = 0
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            try:
                results = summarize_batch(client, batch)
            except errors.APIError as e:
                print(f"[LỖI] Gemini API: {e}")
                break
            valid_ids = {r["id"] for r in batch}
            for item in results:
                if item.id not in valid_ids:
                    continue
                conn.execute(
                    "UPDATE articles SET title_vi = ?, summary_vi = ? WHERE id = ?",
                    (item.title_vi, item.summary_vi, item.id),
                )
                done += 1
            conn.commit()
            print(f"  ... {done}/{len(rows)} bài")

        print(f"[OK] Đã tóm tắt {done} bài.")


if __name__ == "__main__":
    summarize_pending()
