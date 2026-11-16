# Tải nhạc khi YouTube từ chối IP máy chủ

YouTube có thể trả `403`, `429` hoặc yêu cầu xác minh đối với IP trung tâm dữ liệu. Cookie đúng định dạng không đảm bảo session còn dùng được. API key YouTube Data API chỉ giúp tìm kiếm, không cấp quyền tải audio và không sửa được chặn IP. Bản cập nhật này không cam kết gỡ chặn IP Render.

LuNu giữ thư viện, Cloudinary và tài khoản như trước. Có ba cách thêm nhạc:

1. **File từ thiết bị** trong Quản trị. LuNu chuẩn hóa file, upload Cloudinary, ghi Supabase và theo dõi tác vụ đến khi thành công. Không cần YouTube.
2. **Nguồn audio trực tiếp** từ Internet Archive hoặc Jamendo, theo quyền tải của nguồn. Jamendo cần `JAMENDO_CLIENT_ID`.
3. **YouTube** qua công cụ tải trên Render hoặc máy tải riêng. Chỉ thêm nội dung bạn có quyền tải và sử dụng.

## Cách nhanh: tải qua máy cá nhân

Cài Python, FFmpeg và Node trên máy của bạn. Từ thư mục repo:

```bash
python -m pip install 'yt-dlp[default]==2026.10.26' httpx
python scripts/import_youtube.py 'https://www.youtube.com/watch?v=VIDEO_ID' \
  --api https://lunu-music.onrender.com/api --username TEN_ADMIN
```

Công cụ hỏi mật khẩu bằng ô nhập ẩn, tải audio trên mạng của máy cá nhân, rồi upload qua API LuNu. Không đưa mật khẩu vào dòng lệnh. Có thể thêm `--title`, `--artist` và `--cookies /duong-dan/private.cookies.txt`. Đây là cách một lần, không cần mở cổng hoặc vận hành worker.

## Cách tự động: máy tải riêng

Chạy worker trên một máy/VPS do bạn quản lý, có IP truy cập được YouTube. Không đặt worker trên cùng IP đang bị chặn. Không cần cấp Supabase hay Cloudinary credentials cho worker.

```bash
cd backend
python -m venv .venv
# Linux/macOS; Windows dùng .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
# Cần ffmpeg, ffprobe và Node trong PATH.
# Đặt LUNU_MEDIA_WORKER_TOKEN bằng trình quản lý secret hoặc biến môi trường riêng.
# Sinh khóa: python -c 'import secrets; print(secrets.token_urlsafe(48))'
uvicorn media_worker:app --host 127.0.0.1 --port 8010 --workers 1
```

Đặt reverse proxy HTTPS trước worker. URL phải trỏ trực tiếp đến worker, không redirect. Worker chỉ nhận mã video YouTube 11 ký tự, không nhận URL tùy ý. Dùng một process, một tác vụ tải đồng thời; khi bận trả `429` và `Retry-After`. Thư mục tải được xóa sau khi truyền file.

Trong **Environment** của dịch vụ LuNu Music trên Render, đặt:

```dotenv
LUNU_MEDIA_WORKER_URL=https://dia-chi-worker-cua-ban
LUNU_MEDIA_WORKER_TOKEN=<cung-khoa-bi-mat-voi-worker>
LUNU_MEDIA_WORKER_TIMEOUT_SECONDS=600
```

Không thêm các giá trị này vào biến `VITE_*`, frontend hay Git. HTTP chỉ được phép cho localhost khi phát triển. Khóa cần ít nhất 32 ký tự. Không gửi cookie của bạn qua chat hoặc commit vào repo. Nếu cần cookie, chỉ cấu hình qua secret của máy thực sự tải YouTube. Mã nguồn worker không tự kế thừa cookie Render.

Sau khi deploy cấu hình, mở **Quản trị → Nguồn nhạc**, rồi chọn **YouTube**, tìm bài và thêm vào thư viện. Trạng thái “đã cấu hình” chỉ xác nhận cấu hình, không khẳng định worker đang khỏe hoặc YouTube cho phép tải. Kiểm thử một video bạn có quyền sử dụng để xác nhận toàn bộ luồng.

Khi đã cấu hình worker, backend không tự quay lại IP Render nếu worker lỗi. Lỗi kết nối, xác thực, máy bận hoặc file không đầy đủ được báo riêng; file hỏng không được upload.

## Công cụ tải trên Render

Phiên bản yt-dlp được chốt ở `2026.10.26`, EJS `0.8.0`; Node và FFmpeg có trong Docker image. Mặc định để yt-dlp chọn player client (`YOUTUBE_PLAYER_CLIENTS=default`). Không cần tải mã EJS từ GitHub lúc chạy. Khi gặp dấu hiệu bị chặn, backend dừng thử các client khác và tạm nghỉ 900 giây. Có thể điều chỉnh `YOUTUBE_COOLDOWN_SECONDS`, tối thiểu 30 giây.

Cooldown và trạng thái import nằm trong bộ nhớ từng process. Chúng mất khi restart/deploy và không phải hàng đợi bền vững. Không deploy giữa lúc đang import. Tệp từ worker bị giới hạn theo `LUNU_AUDIO_UPLOAD_MAX_BYTES` hoặc `LUNU_RENDER_MAX_DOWNLOAD_BYTES`; không có tự retry upload sau restart.

## Kiểm tra

```bash
npm ci
npx playwright install chromium
npm test
npm run build
python -m pip install -r backend/requirements-dev.txt
python -m pytest backend/tests -q
```

Nếu dùng Chromium hệ thống, đặt `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/duong-dan/chromium`. Các kiểm thử dùng audio giả lập và worker cục bộ; không tải YouTube, đăng nhập tài khoản thật hay ghi dữ liệu production.

## Khi log báo cookie đã hết hiệu lực

`valid_format: true` chỉ xác nhận định dạng file, không kiểm tra phiên đăng nhập. Nếu yt-dlp cảnh báo `The provided YouTube account cookies are no longer valid`, LuNu sẽ đánh dấu phiên bị từ chối và thử tải công khai đúng một lần. Phiên cũ không được sử dụng lại trong process đó. Nếu YouTube vẫn yêu cầu xác minh thì không có thay đổi giao diện hay API key tìm kiếm nào tự tạo được phiên hợp lệ.

Cập nhật cookie trực tiếp trong [Environment của LuNu trên Render](https://dashboard.render.com/web/srv-da67mpjl550s73ae4fc0/env), không gửi cookie vào chat hoặc GitHub:

1. Mở một cửa sổ ẩn danh và đăng nhập YouTube.
2. Trong cùng tab, mở `https://www.youtube.com/robots.txt`. Chỉ giữ một tab ẩn danh này.
3. Export cookie của `youtube.com` ở định dạng Netscape bằng công cụ trình duyệt phù hợp, rồi đóng cửa sổ ẩn danh để phiên export không tiếp tục bị trình duyệt xoay vòng.
4. Trong Render → Environment → Secret Files, thay nội dung file được trỏ bởi `YOUTUBE_COOKIES_PATH`. Nếu đang dùng `YOUTUBE_COOKIES_B64`, cập nhật biến đó thay vì Secret File; base64 có ưu tiên cao hơn file.
5. Lưu và deploy lại. Thử thêm đúng một bài, rồi kiểm tra thông báo kết quả.

Nguồn: [hướng dẫn export cookie hiện tại của yt-dlp](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies). Cookie hợp lệ vẫn không bảo đảm IP trung tâm dữ liệu được YouTube chấp nhận.

Dành cho vận hành: `LUNU_YOUTUBE_STARTUP_PROBE=<video-id>` bật một phép thử tải/transcode vào thư mục tạm khi process khởi động. Phép thử không upload Cloudinary và không ghi Supabase. Kết quả đã lược bỏ dữ liệu nhạy cảm xuất hiện ở `/api/health` → `youtube_probe`. Mặc định không chạy; xóa giá trị biến và deploy sau khi chẩn đoán để tránh chạy lại ở lần restart tiếp theo.
