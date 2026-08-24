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
| `CLOUDINARY_CLOUD_NAME` | Cloud name |
| `CLOUDINARY_API_KEY` | API key |
| `CLOUDINARY_API_SECRET` | API secret |
| `LUNU_AUTH_SECRET` | Chuỗi ngẫu nhiên dài, ổn định giữa các lần deploy |
| `CORS_ORIGINS` | Domain Vercel, phân cách bằng dấu phẩy; có thể thêm `http://localhost:5173` khi dev |

Không đưa `SUPABASE_KEY`, Cloudinary API secret hoặc `LUNU_AUTH_SECRET` vào Vercel/frontend. Frontend chỉ nhận `VITE_API_URL`.

## Supabase schema tương thích

Bảng `songs` hiện được backend sử dụng với các cột `id`, `title`, `artist`, `url`, `cover`, `lyrics`. Bảng `users` tối thiểu cần `id`, `username`, `role`; bản nâng cấp ưu tiên cột `password_hash`. Backend vẫn đọc cột `password` cũ để cho phép đăng nhập lần đầu và tự nâng cấp sang PBKDF2 hash, sau đó nên xóa dữ liệu plaintext sau khi xác nhận migration thành công.

Nếu database đã bật RLS, cần tạo policy server-side phù hợp với cách backend kết nối. Không dùng service key trong bundle frontend.

## Lưu ý import YouTube

Endpoint import trả về trạng thái `queued`; Render xử lý tải yt-dlp, chuyển đổi FFmpeg, upload Cloudinary và insert Supabase ở background task. Đây là mô hình đơn giản phù hợp thư viện cá nhân nhỏ. Nếu cần import nhiều bài hoặc retry bền vững sau restart, nên chuyển pipeline sang job queue/dịch vụ worker riêng thay vì phụ thuộc process web.

## Kiểm tra sau deploy

Mở `https://<render-domain>/api/health`; response cần có `ok: true`. Sau đó mở Vercel app, đăng nhập, kiểm tra tải library, phát một bài, mở queue, Lyrics Lab và thử command palette bằng `Ctrl/Cmd + K`. Khi thêm bài từ YouTube, UI phải hiển thị “Đã xếp hàng thành công” thay vì chờ cứng 15 giây.
