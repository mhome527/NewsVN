khi sửa source cần:
git pull code mới trên server rồi sudo systemctl restart newsvn (hoặc chỉ cần chạy lại fetch_news.py/summarizer.py qua cron, không cần restart web app vì không đổi gì liên quan tới app.py).

=================
Lệnh restart web app trên server:


sudo systemctl restart newsvn
Dùng khi bạn git pull code mới có đụng tới app.py, database.py, templates/, static/ (những thứ ảnh hưởng trực tiếp tới web app) — restart để gunicorn nạp lại code mới.

Không cần restart nếu chỉ sửa summarizer.py/fetch_news.py (như lần vừa rồi), vì 2 script đó chạy độc lập qua cron, không nằm trong tiến trình gunicorn đang chạy.

Kiểm tra lại sau khi restart:


sudo systemctl status newsvn

=================


Đây là các bước cài đặt và chạy project trên server Linux (Ubuntu/Debian), dùng repo vừa push lên GitHub.

1. Cài Python và lấy source

sudo apt update
sudo apt install -y python3 python3-venv python3-pip git

git clone git@github.com:mhome527/NewsVN.git
cd NewsVN
(Nếu server chưa có SSH key liên kết với GitHub, dùng URL HTTPS thay thế: git clone https://github.com/mhome527/NewsVN.git)

2. Tạo virtualenv và cài dependencies

python3 -m venv venv
./venv/bin/pip install -r requirements.txt
3. Cấu hình API key

cp .env.example .env
nano .env   # điền GEMINI_API_KEY=... (key thật, lấy tại https://aistudio.google.com/apikey)
4. Lấy tin lần đầu (tạo database + tóm tắt)

./venv/bin/python fetch_news.py
5. Chạy web app
Lưu ý quan trọng: trong app.py, app.run() mặc định chỉ bind vào 127.0.0.1 — nghĩa là nếu chạy python app.py trực tiếp, chỉ truy cập được từ chính server đó (curl localhost:5001), không truy cập được từ máy khác qua IP public. Có 2 cách:

Cách nhanh (test):


source venv/bin/activate
flask --app app run --host=0.0.0.0 --port=5001
Cách khuyến nghị cho production (chạy nền, tự khởi động lại khi crash/reboot server) — dùng gunicorn + systemd:


./venv/bin/pip install gunicorn
Tạo file /etc/systemd/system/newsvn.service:


[Unit]
Description=NewsVN Flask app
After=network.target

[Service]
User=<user_cua_ban>
WorkingDirectory=/path/to/NewsVN
ExecStart=/path/to/NewsVN/venv/bin/gunicorn -w 2 -b 0.0.0.0:5001 app:app
Restart=always

[Install]
WantedBy=multi-user.target


chạy lệnh sau:

sudo systemctl daemon-reload
sudo systemctl enable --now newsvn
sudo systemctl status newsvn


6. Mở port trên firewall

sudo ufw allow 5001/tcp
(Nếu server thuê từ AWS/GCP/DigitalOcean... nhớ mở thêm port 5001 trong Security Group / Firewall Rules của nhà cung cấp cloud.)

7. Tự động lấy tin hàng ngày (cron)
run_daily.sh đã tự đọc .env sẵn:


crontab -e
Thêm dòng chạy lúc 7h sáng:


0 7 * * * /path/to/NewsVN/run_daily.sh
8. (Tùy chọn) Gắn domain + HTTPS
Nếu muốn truy cập qua domain thay vì IP:5001, đặt Nginx làm reverse proxy trỏ về 127.0.0.1:5001 rồi dùng certbot xin SSL — nói tôi biết nếu bạn muốn cấu hình phần này chi tiết.

Sau khi chạy xong bước 5, mở http://<IP_server>:5001 (hoặc domain nếu đã cấu hình Nginx) để xem trang tin.