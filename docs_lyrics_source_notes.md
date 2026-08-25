# Ghi chú nguồn lyrics

- Musixmatch Pro API tự mô tả là cơ sở dữ liệu music data được cấp phép, nhưng tài liệu Content Restrictions cho biết API có thể không trả lyrics body khi nội dung bị hạn chế; cần key/plan và phải tuân thủ giới hạn nội dung.
- LRCLIB docs mô tả API miễn phí, không cần API key, có rate limiting và yêu cầu client nhận diện bằng User-Agent; tài liệu có endpoint `GET /api/get` với artist_name, track_name, album_name, duration.
- LuNu Music chỉ nên dùng LRCLIB để tìm kiếm/xem trước theo yêu cầu admin, không chạy cào hàng loạt nền hoặc bỏ qua rate limit. Việc lưu lyrics lâu dài cần do chủ dự án xác nhận và chịu trách nhiệm về quyền sử dụng.
- Thiết kế dự kiến: backend gọi nguồn với User-Agent rõ ràng, trả plainLyrics/syncedLyrics đã chuyển về plain text, frontend hiển thị popup preview, admin bấm xác nhận mới PATCH cột `songs.lyrics`; không cập nhật URL Cloudinary.
