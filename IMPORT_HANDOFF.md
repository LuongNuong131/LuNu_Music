# LuNu Music — Import workflow handoff

## Đã sửa đúng logic yêu cầu

Luồng mới là **tìm YouTube → chọn video → sửa tên bài và ca sĩ trên web → gửi video ID cùng metadata → Render tải audio bằng yt-dlp và FFmpeg → upload MP3 lên Cloudinary → lấy `secure_url` → ghi metadata vào Supabase → frontend polling trạng thái → refresh thư viện**.

Component `DiscordBotSearch.vue` không còn thêm bài ngay từ kết quả tìm kiếm. Người dùng phải chọn một video, chỉnh `title` và `artist`, sau đó bấm **Tải MP3 & thêm vào thư viện**. Frontend gửi đủ `video_id`, `title`, `artist`, `cover`, `lyrics` lên backend.

Backend trả về `202` kèm `job_id`. Job được theo dõi qua `/api/songs/import-jobs/{job_id}` với các trạng thái `queued`, `processing`, `completed` hoặc `failed`. Khi completed, frontend mới emit sự kiện refresh, vì vậy không còn lỗi refresh quá sớm trước khi Cloudinary/Supabase hoàn tất.

## Các lỗi cũ đã được xử lý

| Lỗi | Cách sửa |
|---|---|
| UI chỉ gửi video ID | Gửi cả title/artist do người dùng nhập |
| Backend tự lấy title/uploader của YouTube | Dùng metadata đã được người dùng xác nhận trên web |
| Không biết download có thành công không | Thêm job status polling và error message cụ thể |
| Upload xong nhưng UI refresh trước khi insert DB | Chỉ refresh khi job `completed` |
| Tải lại cùng video tạo metadata cũ hoặc duplicate khó đoán | Cloudinary dùng public ID theo video ID; Supabase update metadata nếu URL đã tồn tại |
| Lỗi FFmpeg/file MP3 khó đọc | Kiểm tra file `.mp3` sau yt-dlp và báo rõ lỗi FFmpeg/Render |

## Trạng thái deploy đã kiểm tra

Live Render đã trả đúng CORS cho origin `https://lunu-music.vercel.app`. Endpoint search live trả HTTP 200. Endpoint add mới được deploy và khi gọi không có token trả HTTP 401 `Cần đăng nhập để tiếp tục`, chứng minh route tồn tại và đang được bảo vệ.

## Cách sử dụng

Đăng xuất rồi đăng nhập lại trên [lunu-music.vercel.app](https://lunu-music.vercel.app) để chắc chắn dùng access token mới. Vào **Quản trị → Kho nhạc**, nhập tên bài vào ô tìm kiếm và bấm **Tìm kiếm**. Chọn video YouTube đúng bản muốn lấy. Ở màn hình **Chỉnh sửa thông tin trước khi lưu**, nhập lại tên bài hát và ca sĩ nếu cần, rồi bấm **Tải MP3 & thêm vào thư viện**.

UI sẽ hiển thị các bước đang chạy: gửi lên Render, tải MP3, upload Cloudinary và ghi Supabase. Khi hoàn tất, bài hát xuất hiện trong danh sách với đúng title/artist đã nhập. Nếu thất bại, UI hiển thị nguyên nhân backend trả về thay vì chỉ báo lỗi chung.

## Kiểm thử đã chạy

| Kiểm tra | Kết quả |
|---|---|
| Catalog legacy | 188 record, 188 URL unique |
| Mock download → Cloudinary → Supabase | PASS; metadata web được giữ nguyên |
| `npm run build` | PASS |
| `python3 -m py_compile backend/main.py` | PASS |
| Live CORS với Vercel origin | PASS |
| Live search | HTTP 200 |
| Live add không token | HTTP 401 như thiết kế bảo mật |

Commit mới nhất: `e47c44a` trên branch `master`.
