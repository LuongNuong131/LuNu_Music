# LuNu Music — Legacy catalog restoration handoff

## Trạng thái hiện tại

Đã đưa toàn bộ **188 bài hát** từ catalog dự án cũ vào repository, chuẩn hóa metadata và tạo URL Cloudinary deterministic. Catalog đã được kiểm tra: 188 record, 188 URL unique, 3 record có lyrics sẵn trong file legacy.

Backend Render đã được sửa để luôn cho phép origin `https://lunu-music.vercel.app`, đồng thời đã thêm endpoint `POST /api/songs/import-legacy`. Frontend Vercel đã nhận bundle mới sau commit `a3a05ba`; CORS live hiện đã trả đúng `Access-Control-Allow-Origin: https://lunu-music.vercel.app`. Endpoint restore live cũng đã tồn tại và trả `401 Cần đăng nhập` khi gọi không có token, chứng minh route đang chạy và được bảo vệ.

Hiện Supabase vẫn đang trả `[]` vì **chưa có thao tác import với quyền admin**. Mình không tự ý ghi trực tiếp vào database khi chưa có access token/admin credential của bạn.

## Cách đưa 188 bài vào Supabase

Sau khi mở [lunu-music.vercel.app](https://lunu-music.vercel.app), hãy đăng xuất nếu trình duyệt còn phiên cũ, sau đó đăng nhập lại để frontend nhận access token mới. Vào **Quản trị → Kho nhạc → Khôi phục 188 bài**, xác nhận một lần và chờ thông báo kết quả. Backend sẽ kiểm tra URL trùng trước khi insert, nên bấm lại không tạo duplicate theo URL.

Nếu nút báo `401`, tài khoản hiện tại chưa có token mới hoặc không có role `admin`; hãy đăng xuất/đăng nhập lại bằng tài khoản admin. Nếu báo `403`, tài khoản đăng nhập không phải admin. Nếu báo lỗi `password_hash` hoặc `users`, cần áp dụng SQL migration trong phần tiếp theo.

## SQL dự phòng trong Supabase

Repository chứa:

| File | Mục đích |
|---|---|
| `supabase/import_legacy_songs.sql` | SQL insert/upsert đủ 188 record, dùng UUID deterministic |
| `supabase/legacy_songs.json` | Catalog chuẩn hóa |
| `backend/legacy_catalog.json` | Catalog được đóng gói vào Render để endpoint restore đọc |
| `src/data/legacyCatalog.js` | Fallback frontend để app vẫn hiển thị catalog khi API chưa có dữ liệu |
| `scripts/prepare_legacy_catalog.mjs` | Script tái tạo các file từ `legacy_songs.js` |

Chỉ chạy SQL sau khi xác nhận kiểu `songs.id` tương thích UUID. Nếu bảng đang dùng integer identity, dùng nút restore trong app; backend có fallback insert để Supabase tự sinh id nếu UUID không tương thích.

## Cấp tài khoản

Endpoint cấp tài khoản đã được bảo vệ bằng signed access token và role admin. Form **Quản trị → Tài khoản** yêu cầu username tối thiểu 2 ký tự và password tối thiểu 8 ký tự. Backend ưu tiên cột `password_hash`; nếu schema cũ chưa có cột này, backend fallback lưu PBKDF2 hash vào cột `password` để tương thích, không lưu plaintext mới.

Tài khoản admin đầu tiên phải tồn tại sẵn trong bảng `users`. Nếu không còn admin nào, cần tạo/reset một admin trực tiếp trong Supabase hoặc gửi cho mình schema hiện tại của bảng `users` để mình viết migration chính xác; không nên gửi service key lên chat.

## Kiểm thử

| Kiểm tra | Kết quả |
|---|---|
| Legacy catalog count | PASS — 188 |
| URL uniqueness | PASS — 188 unique |
| Frontend `npm run build` | PASS |
| Backend `py_compile` | PASS |
| Live `/api/health` | PASS |
| Live CORS với Vercel origin | PASS sau Render deploy |
| Live restore route | PASS — protected, unauthenticated request trả 401 |
| Live songs before import | 0 rows — chờ admin thực hiện restore |
