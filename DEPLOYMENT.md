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

Bảng `cinema_videos` được tạo bởi cùng migration. Video mới có mã dạng `VD0125082026`, tăng dần theo số thứ tự trong kho Cinema. Để bật hai chế độ lưu, chạy thêm `supabase/cinema_retention.sql` một lần; migration này thêm `retention_mode` (`permanent` hoặc `temporary`) và `expires_at`. Bảng `users` tối thiểu cần `id`, `username`, `role`; bản nâng cấp ưu tiên cột `password_hash`. Backend vẫn đọc cột `password` cũ để cho phép đăng nhập lần đầu và tự nâng cấp sang PBKDF2 hash, sau đó nên xóa dữ liệu plaintext sau khi xác nhận migration thành công.

Nếu database đã bật RLS, cần tạo policy server-side phù hợp với cách backend kết nối. Không dùng service key trong bundle frontend.

## Tìm kiếm YouTube ổn định

Backend hiện có nhiều fallback không cần key: yt-dlp, YouTube Music structured search, YouTube HTML parser, accent-stripped variants, retry và deduplicate. Downloader cũng bật Node.js và `yt-dlp-ejs`; nếu một video vẫn trả `Sign in to confirm you’re not a bot`, có thể đặt `YOUTUBE_COOKIES_B64` từ file Netscape `cookies.txt` của tài khoản được phép truy cập. Không commit file cookies và không gửi cookie qua chat. Tuy nhiên YouTube có thể trả kết quả khác nhau theo IP/region của Render. Để kết quả ổn định cho các tên bài tiếng Việt như `cao ốc 20`, tạo một API key trong Google Cloud Console, bật **YouTube Data API v3**, rồi đặt `YOUTUBE_API_KEY` trong Render. Backend sẽ ưu tiên endpoint chính thức trước các fallback và không đưa key này ra frontend.

## LuNu Cinema và vòng đời Cloudinary

Sidebar có tab **LuNu Cinema** cho tài khoản admin. Tại đây admin tìm video YouTube, chọn video, chỉnh tên/kênh/mô tả, rồi backend tải MP4, upload vào `lunu_cinema/VD<ID+ngày>` và lưu metadata vào Supabase. Khi xóa bài hát hoặc video từ giao diện quản trị, backend sẽ xóa asset Cloudinary trước rồi mới xóa metadata Supabase; nếu Cloudinary lỗi, metadata không bị xóa dở dang.

## Lưu ý import YouTube

Endpoint import trả về trạng thái `queued`; Render xử lý tải yt-dlp, chuyển đổi FFmpeg, upload Cloudinary và insert Supabase ở background task. Dockerfile đã cài FFmpeg và Node.js; requirements đã thêm `yt-dlp-ejs` để xử lý YouTube challenge. Downloader không khóa cứng một format, thử các profile audio/video và báo rõ nếu video chỉ có hình ảnh hoặc bị YouTube chặn. Đây là mô hình đơn giản phù hợp thư viện cá nhân nhỏ. Nếu cần import nhiều bài hoặc retry bền vững sau restart, nên chuyển pipeline sang job queue/dịch vụ worker riêng thay vì phụ thuộc process web.

## Migration bắt buộc trước khi dùng tính năng mới

Mở Supabase SQL Editor và chạy toàn bộ `supabase/media_upgrade.sql`, sau đó chạy `supabase/cinema_retention.sql` nếu muốn bật video tạm, rồi chạy `supabase/media_requests_notifications.sql` nếu dùng đề xuất/thông báo. Sau đó Render cần redeploy để nhận Dockerfile/requirements mới. Không chạy nút **Khôi phục 188 bài** trước migration nếu muốn backend ghi thêm các trường media mới; bản import legacy đã được sửa để bỏ qua trường `legacyId` không tồn tại trong schema.

## Kiểm tra sau deploy

Mở `https://<render-domain>/api/health`; response cần có `ok: true`. Sau đó mở Vercel app, đăng nhập, kiểm tra tải library, phát một bài, mở queue, Lyrics Lab và thử command palette bằng `Ctrl/Cmd + K`. Khi thêm bài từ YouTube, UI phải hiển thị “Đã xếp hàng thành công” thay vì chờ cứng 15 giây. Với Cinema, hãy thử trước video ngắn hoặc chất lượng thấp; nếu nguồn vượt policy, UI sẽ nhận lỗi rõ ràng ngay từ bước preflight và backend không tiếp tục tải file hàng GiB.

## Khôi phục 188 bài hát từ catalog legacy

Sau khi Render deploy commit mới và đã chạy `supabase/media_upgrade.sql`, đăng xuất rồi đăng nhập lại để nhận access token mới. Vào **Quản trị → Kho nhạc → Khôi phục 188 bài** và xác nhận. Backend sẽ đọc `backend/legacy_catalog.json`, bỏ trường `legacyId` không có trong schema, kiểm tra URL đã tồn tại, insert phần còn thiếu vào Supabase và trả về số lượng `imported/skipped`. Từ thời điểm đó 188 bài không còn chỉ là fallback mặc định mà trở thành các row quản lý được trong Supabase.

Nếu không muốn dùng giao diện, có thể chạy `supabase/import_legacy_songs.sql` trong Supabase SQL Editor. Trước khi chạy SQL, xác nhận kiểu của `songs.id`; file SQL đang dùng UUID deterministic tương thích với backend hiện tại. Không chạy đồng thời cả nút import và SQL nếu chưa kiểm tra duplicate theo `url`.

Trong **Quản trị → Kho nhạc**, nút **Sửa** cho phép đổi tên, ca sĩ, ảnh bìa và lyrics của mọi bài, bao gồm 188 bài legacy. API `PATCH /api/songs/{id}` không nhận trường `url`, nên link audio Cloudinary không bị thay đổi. Nút **Xóa** sẽ xóa asset Cloudinary trước rồi xóa row Supabase.

CORS đã được bổ sung cố định cho `https://lunu-music.vercel.app`, đồng thời vẫn nhận thêm các domain trong `CORS_ORIGINS`. Vì vậy lỗi `No 'Access-Control-Allow-Origin' header` trong console sẽ hết sau khi Render chạy đúng commit mới; nếu vẫn còn, kiểm tra Render đã redeploy và domain Vercel có đúng chính tả hay chưa.

## Nhập lyrics hàng loạt cho 188 bài

Trong **Quản trị → Kho nhạc**, khu vực **Nhập lyrics hàng loạt** có nút **Tải mẫu 188 bài**. Mẫu JSON chứa đúng UUID, tên và nghệ sĩ của từng row Supabase. Điền lyrics plain text vào trường `lyrics`, sau đó dán toàn bộ JSON vào ô nhập và bấm **Cập nhật lyrics**. Backend chỉ cập nhật cột `lyrics`; không nhận `url`, `media_key`, `source_id` hay Cloudinary public ID trong thao tác này.

Có thể dùng `supabase/lyrics_bulk_import_template.sql` thay cho giao diện. File này mặc định kết thúc bằng `ROLLBACK`; chỉ đổi thành `COMMIT` sau khi đã điền nội dung lyrics, chạy câu `SELECT COUNT(*)`, và kiểm tra kết quả. Không chạy file mẫu khi các trường lyrics vẫn rỗng vì nó sẽ không cập nhật dòng nào.

Lyrics phải là nội dung mà chủ dự án có quyền sử dụng, do người dùng cung cấp, hoặc thuộc phạm vi public domain/licensed. Hệ thống không tự động sao chép nguyên văn lyrics có bản quyền từ website bên thứ ba.

## Tìm lyrics từng bài trong Admin

Mỗi bài trong **Quản trị → Kho nhạc** có nút **Tìm lời**. Backend sẽ tra cứu theo tên bài và nghệ sĩ từ LRCLIB, trả tối đa năm kết quả có plain lyrics, rồi Admin xem trước trong popup. Chỉ khi bấm **Xác nhận và lưu lyrics**, frontend mới gọi endpoint cập nhật Supabase. Backend chỉ cập nhật `songs.lyrics`, vì vậy URL audio Cloudinary và mã media không bị ảnh hưởng.

LRCLIB yêu cầu client nhận diện bằng User-Agent và tôn trọng rate limit; tính năng này chỉ gọi theo từng thao tác Admin, không tự động quét 188 bài đồng thời. Nếu không có kết quả, hãy thử sửa tên bài/nghệ sĩ cho chính xác hoặc dùng khu vực nhập JSON/SQL hàng loạt với nội dung bạn có quyền sử dụng. Nguồn này có thể trả bản lyrics khác nhau hoặc không có bản ghi cho một số bài.

Tài liệu nguồn: [LRCLIB API Documentation](https://lrclib.net/docs) và [Musixmatch Content Restrictions](https://docs.musixmatch.com/content-restrictions). Musixmatch là lựa chọn thương mại được cấp phép nếu cần nguồn ổn định và quyền lưu trữ phù hợp; không tự động scrape Genius, Musixmatch web hoặc các trang lyrics khác để né giới hạn truy cập.

## LuNu Tea Room, đề xuất media và thông báo

LuNu Tea Room cho phép thành viên đăng nhập xem các video đã được lưu; chỉ admin được tìm/import/xóa trực tiếp. User gửi yêu cầu tại mục **Đề xuất media**. User có thể tìm một video YouTube, chọn loại **Bài hát MP3** hoặc **Video MP4**, nhập tên/ca sĩ hoặc kênh, rồi gửi cho admin. Admin xem hàng đợi, người gửi, metadata và dung lượng file sau khi pipeline tải xong, sau đó duyệt hoặc từ chối. Kết quả được gửi về trung tâm **Thông báo**.

Trước khi bật workflow này, chạy `supabase/media_requests_notifications.sql` một lần trong Supabase SQL Editor. Migration giả định `public.users.id` là kiểu `uuid`, giống ID mà backend đang dùng để xác thực. Nếu schema users của bạn dùng kiểu khác, cần đổi kiểu khóa ngoại tương ứng trước khi chạy migration.

Để tìm theo tên kênh YouTube ổn định, đặt `YOUTUBE_API_KEY` ở Render. Luồng tìm video vẫn có các fallback hiện có. Backend `backend/Dockerfile` dùng Node 22 vì phiên bản yt-dlp-ejs hiện tại yêu cầu Node tối thiểu 22; Render phải build đúng Dockerfile backend sau commit mới.

Nếu yt-dlp vẫn báo `Only images are available`, nguyên nhân là YouTube đã trả về metadata hình ảnh nhưng không cấp audio/video stream cho IP hoặc phiên làm việc của Render. Đổi format selector không thể tạo stream bị thiếu. Chỉ dùng cookies Netscape của tài khoản có quyền truy cập nội dung khi cần, không commit cookies và không gửi cookies qua chat. Với nội dung do bạn sở hữu, lựa chọn ổn định hơn là upload file MP3/MP4 trực tiếp qua một kênh server-side được kiểm soát, thay vì phụ thuộc extractor YouTube.

Để bảo vệ Render khỏi bị restart khi gặp video hàng GiB, Cinema chỉ chọn video tối đa 480p/360p và áp dụng preflight mặc định 450 MiB (`LUNU_RENDER_MAX_DOWNLOAD_BYTES`). Nếu nguồn vượt mức này, job sẽ dừng có chủ đích với hướng dẫn chọn chất lượng thấp hơn hoặc upload file từ máy cá nhân, thay vì tải gần xong rồi làm đầy tài nguyên của instance. Có thể kiểm tra policy sau deploy tại `/api/health`; response phải có `video_pipeline: preflight-450mb-chunked`.

### Video import và cover mặc định

Cinema video import truyền `postprocessors=[]` cho yt-dlp để không chạy hậu xử lý `FFmpegExtractAudio` của luồng bài hát. Video được giữ ở dạng MP4 sau khi tải. Backend luôn dùng `upload_large()` theo chunk 20 MiB cho video. Nếu Cloudinary trả lỗi giới hạn chính xác 100 MiB của plan, backend tự dùng FFmpeg tạo bản MP4 tương thích dưới khoảng 92 MiB rồi upload bản đó; job sẽ hiển thị rõ các trạng thái `đang nén` và `đang upload bản tương thích`. Vì vậy tài khoản Cloudinary chưa hỗ trợ file gốc trên 100 MiB vẫn có thể lưu video sau khi giảm bitrate, còn tài khoản hỗ trợ giới hạn cao hơn sẽ giữ luồng upload chunk cho file gốc. Media mới được ghi với cover mặc định `/images/ChoCiu.jpg`; thumbnail YouTube chỉ dùng để xem trước trong giao diện tìm kiếm. Sau thay đổi này, Render cần build lại từ `backend/Dockerfile` mới và phải có gói `ffmpeg` (Dockerfile hiện đã cài).

Nếu Supabase chưa có bảng `media_proposals` hoặc `notifications`, hãy chạy `supabase/media_requests_notifications.sql` một lần. Nếu đang dùng chế độ video tạm, cũng phải chạy `supabase/cinema_retention.sql`. Backend cleanup tự động kiểm tra định kỳ trong process, cleanup ngay khi mở thư viện, và admin có nút **Dọn video hết hạn** để chạy thủ công. Frontend hiện xử lý graceful fallback và không spam lỗi khi migration chưa sẵn sàng.

### Chẩn đoán lỗi `413 Request Entity Too Large` khi tải MP3

Nếu log audio hiển thị `Error parsing server response (413)` kèm HTML `nginx`, Cloudinary đã từ chối request upload vì file MP3 vượt giới hạn của endpoint hoặc plan. Phần `Expecting value` chỉ là lỗi phụ do SDK cố đọc trang HTML 413 như JSON. Backend mới nhận diện cả dạng lỗi Nginx 413, thử upload chunk và nếu bị giới hạn sẽ dùng FFmpeg nén lại MP3 dưới ngưỡng an toàn trước khi upload thường. Job phải hiển thị lần lượt `đang upload ... theo chunk`, `đang nén MP3`, `đang upload bản tương thích`, rồi `đang ghi metadata vào Supabase`.

### Chẩn đoán lỗi `Maximum is 104857600`

Nếu log hiển thị `File size too large. Got ... Maximum is 104857600`, đó là giới hạn 100 MiB của Cloudinary plan hoặc endpoint upload thường. Bản backend mới sẽ thử upload chunk, nhận diện lỗi này, nén video xuống dưới giới hạn rồi upload lại. Log thành công phải có các bước sau theo thứ tự: video tải xong, `đang upload ... theo chunk`, nếu plan từ chối thì `đang nén video`, sau đó `đang upload bản tương thích` và cuối cùng ghi metadata Supabase. Nếu sau deploy không thấy các câu trạng thái mới mà vẫn lỗi ngay ở 100 MiB, Render chưa chạy đúng commit hoặc đang dùng sai Root Directory/Dockerfile; hãy kiểm tra commit deploy là commit mới nhất trên `master` và dùng **Clear build cache & deploy**.

## Account Center và user profile

Tính năng **Hồ sơ** dùng migration `supabase/user_profiles.sql`, bổ sung `display_name`, `avatar_url`, `bio` và `updated_at` vào bảng `users` theo kiểu additive. Chạy migration một lần trong Supabase SQL Editor trước khi lưu profile. Nếu chưa chạy migration, tài khoản cũ vẫn đăng nhập được nhưng thao tác lưu profile sẽ báo cần bật profile schema.

Frontend chỉ gọi các API profile thông qua backend Render: `GET /api/me`, `PATCH /api/me/profile`, `POST /api/me/avatar` và `POST /api/me/password`. Avatar được upload server-side lên Cloudinary, giới hạn 5 MiB và chỉ nhận JPG, PNG hoặc WebP; không đưa Cloudinary secret ra Vercel. Admin có thể xem và cập nhật display name, avatar URL, bio và role trong tab **Tài khoản**.

Lớp Account Center được tách khỏi player. Không sửa `PlayerBar.vue`, `src/store/playerState.js`, audio element, queue cá nhân hoặc URL media khi triển khai profile. Sau khi Vercel deploy, user có thể mở mục **Hồ sơ**; nếu profile schema chưa được migrate, app vẫn giữ dữ liệu auth cũ và hiển thị hướng dẫn rõ ràng.

## Listening Room

Listening Room dùng migration `supabase/listening_rooms.sql`, tạo `listening_rooms` và `room_members` mà không thay đổi bảng `songs`, `cinema_videos`, player state hoặc queue cá nhân. Chạy migration một lần trong Supabase SQL Editor trước khi tạo phòng.

Frontend có workspace **Phòng nghe** với tạo phòng private/public, invite code, giới hạn thành viên, tham gia/rời phòng, chuyển host khi host rời, queue phòng và trạng thái playback. User chỉ đồng bộ bài phòng vào player sau khi bấm **Đồng bộ bài này vào player của tôi**; việc mở hoặc tham gia phòng không tự động đổi bài đang phát.

Các API room gồm `GET /api/rooms`, `POST /api/rooms`, `POST /api/rooms/join`, `GET /api/rooms/{id}`, `PATCH /api/rooms/{id}/state`, `PATCH /api/rooms/{id}`, `POST /api/rooms/{id}/leave` và `POST /api/rooms/{id}/close`. Polling hiện tại dùng chu kỳ thưa để cập nhật room state; khi realtime channel được triển khai sau này, channel chỉ thay thế lớp truyền state, không thay đổi player core.

### Playback sync update

Host broadcast trạng thái room khi bài, play/pause, queue hoặc vị trí thay đổi theo chu kỳ ngắn; thành viên chỉ nhận và áp dụng khi đã bật **Đồng bộ với phòng**. State dùng `state_version`, `updated_at`, `position_seconds` và server-time calculation để tránh áp dụng state cũ và giảm drift. Khi host dừng, thành viên đã opt-in sẽ pause; khi host đổi bài, thành viên sẽ tải bài mới vào player hiện tại.

Luồng hiện tại dùng polling fallback khoảng 2,5 giây, chưa phải Supabase Realtime/WebSocket. Đây là quyết định an toàn tạm thời để không đưa connection lifecycle mới vào player core. Khi bổ sung Realtime, chỉ thay transport của room state, không thay đổi audio element hoặc queue cá nhân.
