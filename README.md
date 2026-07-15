# 📡 Tin Công Nghệ Hàng Ngày

Website tổng hợp tin công nghệ mới nhất mỗi ngày từ các nguồn RSS **tiếng Anh và tiếng Nhật**, dùng **Gemini API** dịch tiêu đề + tóm tắt nội dung sang **tiếng Việt** (kèm link bài gốc để tham khảo), lưu vào SQLite để có thể xem lại tin cũ theo từng ngày.

## Cấu trúc

```
News/
├── app.py            # Web app (Flask)
├── fetch_news.py     # Script lấy tin từ RSS
├── summarizer.py     # Tóm tắt tiếng Việt bằng Gemini API
├── database.py       # SQLite helpers
├── .env              # GEMINI_API_KEY (tự tạo từ .env.example)
├── run_daily.sh      # Script cho cron chạy hàng ngày
├── requirements.txt
├── templates/index.html
├── static/style.css
└── data/
    ├── news.db       # Database (tự tạo)
    └── fetch.log     # Log khi chạy qua cron
```

## Nguồn tin

- **Tiếng Anh:** TechCrunch, The Verge, Ars Technica, Hacker News
- **Tiếng Nhật:** GIGAZINE, ITmedia NEWS, PC Watch (Impress)

Muốn thêm/bớt nguồn: sửa danh sách `FEEDS` trong `fetch_news.py`.

## Tóm tắt tiếng Việt (Gemini API)

Sau khi lấy tin, `summarizer.py` gửi các bài theo lô 10 bài lên Gemini (`gemini-2.5-flash`, structured outputs) để dịch tiêu đề và viết tóm tắt 2-3 câu tiếng Việt, lưu vào cột `title_vi` / `summary_vi`.

- Cần `GEMINI_API_KEY`: sao chép `.env.example` thành `.env` rồi điền key (lấy tại https://aistudio.google.com/apikey).
- Nếu thiếu key, bước tóm tắt **tự bỏ qua** (web hiển thị bản gốc); lần chạy sau có key sẽ tóm tắt bù các bài còn thiếu.
- Chạy riêng bước tóm tắt: `./venv/bin/python summarizer.py`

## Cài đặt

```bash
cd /Users/kaka/Program/News
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env   # rồi điền GEMINI_API_KEY
```

## Sử dụng

**1. Lấy tin (lần đầu hoặc bất cứ lúc nào):**

```bash
./venv/bin/python fetch_news.py
```

**2. Chạy web:**

```bash
./venv/bin/python app.py
```

Mở http://127.0.0.1:5001 — trang chủ hiển thị tin ngày mới nhất, sidebar bên trái cho phép xem lại tin các ngày trước, có nút lọc theo nguồn.

> Lưu ý macOS: dùng cổng 5001 vì cổng 5000 bị AirPlay Receiver chiếm sẵn (System Settings > General > AirDrop & Handoff), truy cập 127.0.0.1:5000 sẽ ra trang lỗi 403 của AirPlay chứ không phải app.

## Tự động cập nhật hàng ngày (cron)

Mở crontab:

```bash
crontab -e
```

Thêm dòng sau để chạy lúc **7:00 sáng mỗi ngày**:

```
0 7 * * * /Users/kaka/Program/News/run_daily.sh
```

Log mỗi lần chạy được ghi vào `data/fetch.log`.

> Lưu ý macOS: lần đầu cron chạy, hệ thống có thể hỏi quyền truy cập thư mục — chấp nhận là được. Máy phải đang bật tại thời điểm cron chạy; nếu máy ngủ, có thể đổi sang `launchd` (StartCalendarInterval) để chạy bù khi máy thức dậy.

## Ghi chú

- Bài viết được khử trùng lặp theo `link` — chạy script nhiều lần trong ngày không tạo bài trùng.
- Tin được nhóm theo **ngày lấy tin** (`fetched_date`), nên lịch sử xem lại chính là các ngày script đã chạy.
