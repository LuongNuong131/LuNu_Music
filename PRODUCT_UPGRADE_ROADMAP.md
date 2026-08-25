# LuNu Music — Product Upgrade Roadmap

## Định hướng sản phẩm

LuNu Music được định vị như một **personal music operating system**: một không gian nghe nhạc riêng tư, đẹp, nhanh và có khả năng quản lý toàn bộ media. Khác biệt cốt lõi nằm ở sự kết hợp giữa thư viện nhạc cá nhân, quản trị nội dung Cloudinary/Supabase, lyrics plain text, global player và LuNu Cinema trong cùng một trải nghiệm nhất quán.

## Đợt nâng cấp hiện tại

| Hạng mục | Trạng thái | Giá trị sản phẩm |
|---|---:|---|
| Personal Rotation | Đã triển khai | Tạo vòng nghe đề xuất từ bài yêu thích và lịch sử nghe, không cần API recommendation đắt tiền |
| Playlist workspace | Đã triển khai | Tạo, chọn, xóa playlist; thêm/xóa bài; phát cả playlist; lưu bền vững trên thiết bị |
| Command Palette playlist routing | Đã triển khai | Tìm playlist bằng `Ctrl/Cmd + K` và mở đúng bộ sưu tập |
| Plain lyrics | Đã triển khai | Hiển thị lyrics nguyên văn, không phụ thuộc LRC timestamp |
| Admin lyrics sync | Đã triển khai | Xác nhận và cập nhật lyrics trực tiếp vào Supabase, giữ nguyên audio Cloudinary |
| Scroll-preserving updates | Đã triển khai | Quản trị 188 bài liên tục mà không bị reload về đầu trang |

## Đợt tiếp theo nên triển khai

### 1. Cloud-backed user library

Chuyển favorites, history và playlists từ localStorage sang Supabase theo user ID, đồng thời giữ local cache để app vẫn hoạt động khi mất mạng. Đây là bước quan trọng để trải nghiệm cá nhân không bị mất khi đổi trình duyệt hoặc thiết bị.

### 2. Discovery nâng cao

Bổ sung bộ lọc theo nghệ sĩ, album, mood và thời lượng; tạo smart playlist như “Nghe lại”, “Chưa nghe”, “Top nghệ sĩ” và “Lyrics có sẵn”. Recommendation hiện tại là lớp giao diện đầu tiên; lớp tiếp theo nên dựa trên các event nghe nhạc thực tế.

### 3. Player chuyên nghiệp

Thêm sleep timer, crossfade, gapless transition, playback history chi tiết, phím tắt hiển thị trong Command Palette và trạng thái tải audio rõ ràng. Các tính năng này tạo khác biệt lớn nhưng không thay đổi backend media hiện tại.

### 4. Social layer có kiểm soát

Cho phép chia sẻ playlist bằng link read-only, tạo ảnh share card và xuất danh sách bài hát. Không nên mở public upload ngay; mọi nội dung vẫn đi qua admin moderation để bảo vệ chất lượng thư viện.

### 5. Operations console

Thêm dashboard admin với số lượng bài hát, lyrics coverage, lỗi Cloudinary, import jobs, trạng thái Cinema và nhật ký thao tác. Đây là nền tảng để vận hành một thư viện lớn thay vì chỉ sửa từng bản ghi.

## Nguyên tắc kỹ thuật

LuNu Music phải giữ nguyên một global audio state, cập nhật danh sách tại chỗ thay vì reload toàn trang, không đưa secret server-side lên Vercel, không thay đổi audio URL khi sửa metadata, và mọi thao tác xóa media phải hoàn thành Cloudinary lifecycle trước khi xóa metadata Supabase.

Các tính năng sử dụng nguồn bên ngoài phải có timeout, trạng thái loading, trạng thái empty và thông báo lỗi cụ thể. Các nội dung lyrics có bản quyền chỉ được lưu hoặc hiển thị khi ứng dụng có quyền sử dụng hoặc người dùng xác nhận quyền sử dụng phù hợp.
