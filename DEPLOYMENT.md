# LuNu Music — Deployment notes

## Frontend trên Vercel

Đặt **Root Directory** là repository root. Build command là `npm run build`, output directory là `dist`, và framework preset là Vite. Tạo biến môi trường `VITE_API_URL` với giá trị là URL backend Render có hậu tố `/api`, ví dụ `https://lunu-music-api.onrender.com/api`.

File `vercel.json` đã được thêm để history routing của Vue không trả về 404 khi người dùng refresh `/login` hoặc các route khác.

## Backend trên Render

Nếu Render dùng Docker, chọn thư mục `backend` làm Docker context hoặc cấu hình Dockerfile path là `backend/Dockerfile`. Container chạy FastAPI trên `0.0.0.0:${PORT}`; Render chỉ cần cung cấp biến `PORT` tự động.

Các biến bắt buộc:

| Biến | Giá trị |
|---|---|
| `SUPABASE_URL` | Project URL của Supabase |
| `SUPABASE_KEY` | Server-side key tương ứng với policy/schema hiện tại |
| `YOUTUBE_API_KEY` | **Khuyến nghị** — YouTube Data API v3 key để tìm kiếm ổn định, không phụ thuộc kết quả yt-dlp/YouTube theo IP Render |
| `YOUTUBE_COOKIES_B64` | Tùy chọn — cookies.txt Netscape được mã hóa base64 cho video bị YouTube yêu cầu xác minh |
| `LUNU_SONG_START_SEQUENCE` | Mặc định `199`, thứ tự đầu tiên sau 188 bài legacy |
| `CLOUDINARY_CLOUD_NAME` | Cloud name |
| `CLOUDINARY_API_KEY` | API key |
| `CLOUDINARY_API_SECRET` | API secret |
| `LUNU_AUTH_SECRET` | Chuỗi ngẫu nhiên dài, ổn định giữa các lần deploy |
| `CORS_ORIGINS` | Domain Vercel, phân cách bằng dấu phẩy; có thể thêm `http://localhost:5173` khi dev |

Không đưa `SUPABASE_KEY`, Cloudinary API secret hoặc `LUNU_AUTH_SECRET` vào Vercel/frontend. Frontend chỉ nhận `VITE_API_URL`.

## Supabase schema tương thích

Bảng `songs` hiện được backend sử dụng với các cột `id`, `title`, `artist`, `url`, `cover`, `lyrics`, đồng thời bản nâng cấp thêm `media_key`, `source_id`, `cloudinary_public_id`. Chạy file `supabase/media_upgrade.sql` một lần trước khi tải bài mới. Bản ghi legacy 188 bài vẫn giữ nguyên; bài mới mặc định bắt đầu từ `19925082026`, rồi tăng dần theo số thứ tự.

Bảng `cinema_videos` được tạo bởi cùng migration. Video mới có mã dạng `VD0125082026`, tăng dần theo số thứ tự trong kho Cinema. Bảng `users` tối thiểu cần `id`, `username`, `role`; bản nâng cấp ưu tiên cột `password_hash`. Backend vẫn đọc cột `password` cũ để cho phép đăng nhập lần đầu và tự nâng cấp sang PBKDF2 hash, sau đó nên xóa dữ liệu plaintext sau khi xác nhận migration thành công.

Nếu database đã bật RLS, cần tạo policy server-side phù hợp với cách backend kết nối. Không dùng service key trong bundle frontend.

## Tìm kiếm YouTube ổn định

Backend hiện có nhiều fallback không cần key: yt-dlp, YouTube Music structured search, YouTube HTML parser, accent-stripped variants, retry và deduplicate. Downloader cũng bật Node.js và `yt-dlp-ejs`; nếu một video vẫn trả `Sign in to confirm you’re not a bot`, có thể đặt `YOUTUBE_COOKIES_B64` từ file Netscape `cookies.txt` của tài khoản được phép truy cập. Không commit file cookies và không gửi cookie qua chat. Tuy nhiên YouTube có thể trả kết quả khác nhau theo IP/region của Render. Để kết quả ổn định cho các tên bài tiếng Việt như `cao ốc 20`, tạo một API key trong Google Cloud Console, bật **YouTube Data API v3**, rồi đặt `YOUTUBE_API_KEY` trong Render. Backend sẽ ưu tiên endpoint chính thức trước các fallback và không đưa key này ra frontend.

## LuNu Cinema và vòng đời Cloudinary

Sidebar có tab **LuNu Cinema** cho tài khoản admin. Tại đây admin tìm video YouTube, chọn video, chỉnh tên/kênh/mô tả, rồi backend tải MP4, upload vào `lunu_cinema/VD<ID+ngày>` và lưu metadata vào Supabase. Khi xóa bài hát hoặc video từ giao diện quản trị, backend sẽ xóa asset Cloudinary trước rồi mới xóa metadata Supabase; nếu Cloudinary lỗi, metadata không bị xóa dở dang.

## Lưu ý import YouTube

Endpoint import trả về trạng thái `queued`; Render xử lý tải yt-dlp, chuyển đổi FFmpeg, upload Cloudinary và insert Supabase ở background task. Dockerfile đã cài FFmpeg và Node.js; requirements đã thêm `yt-dlp-ejs` để xử lý YouTube challenge. Downloader không khóa cứng một format, thử các profile audio/video và báo rõ nếu video chỉ có hình ảnh hoặc bị YouTube chặn. Đây là mô hình đơn giản phù hợp thư viện cá nhân nhỏ. Nếu cần import nhiều bài hoặc retry bền vững sau restart, nên chuyển pipeline sang job queue/dịch vụ worker riêng thay vì phụ thuộc process web.

## Migration bắt buộc trước khi dùng tính năng mới

Mở Supabase SQL Editor và chạy toàn bộ `supabase/media_upgrade.sql`. Sau đó Render cần redeploy để nhận Dockerfile/requirements mới. Không chạy nút **Khôi phục 188 bài** trước migration nếu muốn backend ghi thêm các trường media mới; bản import legacy đã được sửa để bỏ qua trường `legacyId` không tồn tại trong schema.

## Kiểm tra sau deploy

Mở `https://<render-domain>/api/health`; response cần có `ok: true`. Sau đó mở Vercel app, đăng nhập, kiểm tra tải library, phát một bài, mở queue, Lyrics Lab và thử command palette bằng `Ctrl/Cmd + K`. Khi thêm bài từ YouTube, UI phải hiển thị “Đã xếp hàng thành công” thay vì chờ cứng 15 giây.

## Khôi phục 188 bài hát từ catalog legacy

Sau khi Render deploy commit mới và đã chạy `supabase/media_upgrade.sql`, đăng xuất rồi đăng nhập lại để nhận access token mới. Vào **Quản trị → Kho nhạc → Khôi phục 188 bài** và xác nhận. Backend sẽ đọc `backend/legacy_catalog.json`, bỏ trường `legacyId` không có trong schema, kiểm tra URL đã tồn tại, insert phần còn thiếu vào Supabase và trả về số lượng `imported/skipped`. Từ thời điểm đó 188 bài không còn chỉ là fallback mặc định mà trở thành các row quản lý được trong Supabase.

Nếu không muốn dùng giao diện, có thể chạy `supabase/import_legacy_songs.sql` trong Supabase SQL Editor. Trước khi chạy SQL, xác nhận kiểu của `songs.id`; file SQL đang dùng UUID deterministic tương thích với backend hiện tại. Không chạy đồng thời cả nút import và SQL nếu chưa kiểm tra duplicate theo `url`.

Trong **Quản trị → Kho nhạc**, nút **Sửa** cho phép đổi tên, ca sĩ, ảnh bìa và lyrics của mọi bài, bao gồm 188 bài legacy. API `PATCH /api/songs/{id}` không nhận trường `url`, nên link audio Cloudinary không bị thay đổi. Nút **Xóa** sẽ xóa asset Cloudinary trước rồi xóa row Supabase.

CORS đã được bổ sung cố định cho `https://lunu-music.vercel.app`, đồng thời vẫn nhận thêm các domain trong `CORS_ORIGINS`. Vì vậy lỗi `No 'Access-Control-Allow-Origin' header` trong console sẽ hết sau khi Render chạy đúng commit mới; nếu vẫn còn, kiểm tra Render đã redeploy và domain Vercel có đúng chính tả hay chưa.

## Nhập lyrics hàng loạt cho 188 bài

Trong **Quản trị → Kho nhạc**, khu vực **Nhập lyrics hàng loạt** có nút **Tải mẫu 188 bài**. Mẫu JSON chứa đúng UUID, tên và nghệ sĩ của từng row Supabase. Điền lyrics plain text vào trường `lyrics`, sau đó dán toàn bộ JSON vào ô nhập và bấm **Cập nhật lyrics**. Backend chỉ cập nhật cột `lyrics`; không nhận `url`, `media_key`, `source_id` hay Cloudinary public ID trong thao tác này.

Có thể dùng `supabase/lyrics_bulk_import_template.sql` thay cho giao diện. File này mặc định kết thúc bằng `ROLLBACK`; chỉ đổi thành `COMMIT` sau khi đã điền nội dung lyrics, chạy câu `SELECT COUNT(*)`, và kiểm tra kết quả. Không chạy file mẫu khi các trường lyrics vẫn rỗng vì nó sẽ không cập nhật dòng nào.

Lyrics phải là nội dung mà chủ dự án có quyền sử dụng, do người dùng cung cấp, hoặc thuộc phạm vi public domain/licensed. Hệ thống không tự động sao chép nguyên văn lyrics có bản quyền từ website bên thứ ba.
