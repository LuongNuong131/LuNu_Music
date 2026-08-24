# PROJECT AUDIT — LuNu Music

**Ngày audit:** 25/08/2026  
**Phạm vi:** Frontend Vue 3 + Vite, backend FastAPI, Supabase, Cloudinary, YouTube/yt-dlp, lyrics local persistence, player, queue, command palette và cấu hình triển khai.

## 1. Tóm tắt điều hành

Repository hiện tại là một ứng dụng Vue 3/Vite nhỏ, có nền tảng UI và các module lyrics tương đối rõ ràng, nhưng đang ở trạng thái **prototype chưa liên kết hoàn chỉnh**. Frontend build sạch và backend có thể compile cú pháp, tuy nhiên luồng người dùng chính chưa hoạt động xuyên suốt: card bài hát chỉ ghi log thay vì gọi player, auth store và router dùng hai khóa localStorage khác nhau, còn backend thiếu import bắt buộc `os` và có các vấn đề bảo mật nghiêm trọng quanh mật khẩu, CORS và quyền quản trị.

Kiến trúc hiện tại chưa có một player state trung tâm. `PlayerBar.vue` sở hữu audio element và toàn bộ playback state cục bộ; `PlayerView.vue` lại chứa một player cũ độc lập; `App.vue` mount `NowPlayingView` bên ngoài trong khi `PlayerBar.vue` tiếp tục mount một instance khác. Điều này tạo nguy cơ duplicate overlay, state phân mảnh và khó mở rộng queue/history/favorites.

## 2. Bản đồ repository thực tế

| Khu vực | File chính | Vai trò hiện tại | Đánh giá |
|---|---|---|---|
| App shell | `src/App.vue` | Login gate, sidebar, main content, player overlays | Có orchestration nhưng mount trùng Now Playing |
| Auth | `src/store/appState.js`, `src/views/Login.vue`, `src/router/index.js` | User localStorage + login API | Store dùng `lunu_user`, router dùng `isLoggedIn`; contract lệch |
| Library | `src/components/MainView.vue`, `src/data/songs.js` | Render danh sách bài | Card play chưa nối player; data module cần kiểm tra API sync |
| Player | `src/components/PlayerBar.vue` | Audio element duy nhất được phát hiện; state local | Chưa centralize; error/playback event xử lý thiếu |
| Legacy player | `src/views/PlayerView.vue` | Player screen cũ, TODO play/pause | Dead/conflicting architecture |
| Lyrics | `src/services/lyricsService.js`, `src/composables/useLyrics.js`, `src/components/LyricsManager.vue`, `src/components/NowPlayingView.vue` | Parse LRC/plain, local override, offset, inventory | Tách module tốt; cần giữ khi refactor player |
| Queue | `src/components/QueuePanel.vue` | Hiển thị/thao tác queue qua props/events | Cần kiểm tra nguồn state trung tâm |
| Admin | `src/views/AdminView.vue`, `src/components/DiscordBotSearch.vue` | CRUD users/songs + YouTube search | Thiếu auth/role enforcement server-side |
| API | `src/services/api.js` | Fetch các endpoint `/api/...` | `API_BASE_URL` cần xác định; HTTP errors chưa thống nhất |
| Backend | `backend/main.py` | FastAPI + yt-dlp + Cloudinary + Supabase | Single-file; thiếu validation/auth/security và import `os` |
| Styling | `src/style.css`, component scoped CSS | Dark glassmorphism prototype | Có nền tảng tốt nhưng còn thiếu hệ thống responsive/accessibility nhất quán |

## 3. Data flow hiện tại

```text
Login.vue
  └─ api.login() → FastAPI /api/login → Supabase users
       └─ loginUser() → localStorage[lunu_user]

App.vue
  └─ authState.user ? Main shell : Login
       ├─ MainView → songs reactive array
       ├─ PlayerBar → local audio + local playback refs
       ├─ NowPlayingView (instance A)
       ├─ PlayerBar → NowPlayingView (instance B)
       └─ QueuePanel / CommandPalette → event chain chưa có một player store chuẩn

AdminView
  ├─ api.getSongs()/getUsers()
  ├─ api.searchYoutube()
  ├─ api.addSong() → FastAPI background task
  └─ api.deleteSong()/deleteUser()

Lyrics
  └─ currentSong → useLyrics() → lyricsService → localStorage[lunu_lyrics_v1]
```

## 4. Player, auth và persistence

| Hạng mục | Hiện trạng | Rủi ro |
|---|---|---|
| Audio ownership | `PlayerBar.vue` có `<audio>` duy nhất được phát hiện | Tốt ở mức DOM nhưng state không trung tâm |
| Playback state | `isPlaying`, `currentTime`, `duration`, `volume` là refs cục bộ | Queue, keyboard, media session và các view khác không thể đồng bộ đáng tin cậy |
| Current song | Nhận từ parent nhưng không thấy một player store thống nhất | Card, command palette và queue dễ bị “chỉ hiển thị” |
| Auto-play | Watch current song gọi `audio.play()` | Có thể bị browser autoplay policy; lỗi bị nuốt |
| Ended behavior | Repeat one cục bộ; các mode khác đẩy `next` | Chưa có repeat all/off hoàn chỉnh ở core |
| Error handling | `.catch(() => {})` ở play | Che lỗi runtime và không có trạng thái cho người dùng |
| Auth key | Store: `lunu_user`; router: `isLoggedIn` | Có thể bị redirect sai sau login/reload |
| User security | Password gửi/so khớp plaintext trong Supabase | Critical: lộ credential và không an toàn cho production |
| Lyrics persistence | localStorage có version key, parse và request token | Tương đối tốt; cần xử lý JSON hỏng có cảnh báo |
| Songs persistence | Backend dùng Supabase; frontend còn data module | Cần một nguồn dữ liệu thật, tránh mock/static fallback không chủ ý |

## 5. Backend và deployment audit

### 5.1 Lỗi trực tiếp

`backend/main.py` gọi `os.getenv`, `os.path.join` và `os.path.exists` nhưng không import `os`. Python compile vẫn pass vì đây là lỗi runtime khi module khởi tạo Cloudinary hoặc khi download, vì vậy cần sửa ngay.

Endpoint `POST /api/songs/add` trả về `{ "message": ... }`, trong khi frontend và các component admin có xu hướng kiểm tra `success`. Contract nên thống nhất với response model rõ ràng, có `job_id` hoặc trạng thái xử lý để UI không phải đoán.

`src/services/api.js` sử dụng `API_BASE_URL` nhưng file hiện tại không có phần khai báo trong nội dung đã audit. Đây là lỗi runtime khi gọi login, user hoặc song APIs nếu không được inject ở phần file khác.

### 5.2 Phân loại rủi ro

| Mức | Khu vực | File/vị trí | Vấn đề | Tác động | Hướng xử lý |
|---|---|---|---|---|---|
| CRITICAL | Runtime | `backend/main.py` | Thiếu `import os` | Config/download có thể crash khi chạy | Bổ sung import, startup validation |
| CRITICAL | Security | `backend/main.py:191-203` | Lưu và so sánh password plaintext | Lộ toàn bộ credential nếu DB bị đọc | Chuyển sang Supabase Auth hoặc hash mạnh; migrate dữ liệu |
| CRITICAL | Security | `backend/main.py:17-23` | `allow_origins=["*"]` đi cùng credentials | CORS sai và mở rộng bề mặt truy cập | Dùng allowlist domain Vercel/local dev |
| CRITICAL | Authorization | tất cả admin routes | Không xác thực session/role server-side | Bất kỳ client nào có thể gọi CRUD | Thêm auth token/JWT và role dependency |
| HIGH | Functional | `MainView.vue:28-32` | `handlePlay` chỉ `console.log` | Không thể phát bài từ library | Nối vào player store |
| HIGH | Architecture | `PlayerBar.vue`, `PlayerView.vue` | Hai player implementation | State và behavior xung đột | Giữ một player core duy nhất, loại legacy route |
| HIGH | UX | `App.vue:19`, `PlayerBar.vue:18` | Mount hai `NowPlayingView` | Duplicate overlay và event ambiguity | Mount đúng một instance |
| HIGH | Auth | `appState.js`, `router/index.js` | Hai nguồn truth localStorage | Redirect/login không nhất quán | Một auth store + router guard dùng cùng state |
| HIGH | API | `src/services/api.js` | Không thống nhất HTTP error và base URL | Lỗi mạng bị biến thành mảng rỗng, khó debug | Typed-ish response helpers, env validation, error state |
| HIGH | Download | `backend/main.py:97-146` | Background task in-process, temp file theo video id | Không bền trên Render restart; collision/race risk | Job status + idempotency; cân nhắc queue/storage bền vững |
| HIGH | Cloudinary | `backend/main.py:114-121` | Upload audio như resource_type video, không lưu public_id | Khó delete/cleanup, xử lý tài nguyên không rõ | Chuẩn hóa upload resource type và metadata |
| MEDIUM | Data | `backend/main.py:148-156` | GET errors trả `[]` | UI tưởng là thư viện rỗng | HTTP status/error envelope thống nhất |
| MEDIUM | Validation | `AddSongRequest`, `UserRequest` | Chưa giới hạn input/normalize | Abuse, duplicate, query bẩn | Pydantic validators, unique constraints |
| MEDIUM | Performance | `get_songs()` | Select `*`, không sort/paginate | Tốn băng thông khi thư viện lớn | Chỉ trả field cần thiết, pagination |
| MEDIUM | Accessibility | nhiều component | Title/aria/keyboard chưa nhất quán | Khó dùng bằng bàn phím/screen reader | Focus states, aria labels, dialog semantics |
| MEDIUM | Responsive | global/component styles | Player, queue và modal phụ thuộc viewport | Trải nghiệm mobile không ổn định | Mobile-first layout và safe areas |
| UX | Player | `PlayerBar.vue` | Play error bị nuốt, chưa có buffering/error UI | Người dùng không biết vì sao không phát | Hiển thị trạng thái và retry |
| UX | Library | `MainView.vue` | Không có search/filter/favorite/empty loading | Khám phá thư viện kém | Thêm header, stats, filter và skeleton/empty state |
| PERFORMANCE | Audio | `PlayerBar.vue` | Không có preload policy, media session | Chuyển bài và lock-screen controls yếu | Chuẩn hóa event lifecycle |
| ARCHITECTURE | State | toàn app | Chưa có single source of truth cho queue/player | Tăng chi phí bảo trì | Composable/store player trung tâm |

## 6. Baseline verification

Các lệnh đã chạy trước implementation:

| Kiểm tra | Kết quả | Ghi chú |
|---|---|---|
| `npm install --no-audit --no-fund` | PASS | Dependencies cài thành công |
| `npm run build` | PASS | Vite build 57 modules, không có compile error |
| `python3 -m py_compile backend/main.py` | PASS | Chỉ kiểm tra cú pháp; không bắt lỗi name resolution/runtime |
| `git diff --check` | PASS tại baseline | Sẽ chạy lại sau mỗi đợt sửa |

Build sạch **không đồng nghĩa runtime sạch**; các lỗi `os` chưa được thực thi bởi `py_compile`, còn các lỗi wiring chỉ xuất hiện khi tương tác trong trình duyệt.

## 7. Chiến lược implementation được chọn

Trước hết sẽ sửa các lỗi có ảnh hưởng trực tiếp đến runtime và security, sau đó tạo một player composable duy nhất sở hữu audio element/state, nối tất cả card/queue/command palette vào cùng API, giữ nguyên lyrics service/composable, và cuối cùng thay lớp visual bằng design system premium có responsive states rõ ràng. Không rewrite mù quáng và không đổi Vue, FastAPI, Supabase hay Cloudinary.

Các phần cần backend credential thật hoặc migration Supabase sẽ được code theo biến môi trường và SQL/schema rõ ràng; không đưa secret vào frontend. Việc xóa hoặc thay đổi password model trên production cần chạy migration riêng sau khi người dùng xác nhận database schema hiện tại.

## 8. Definition of done

Ứng dụng được xem là hoàn tất ở phạm vi code hiện tại khi frontend build sạch, backend import/startup ổn định ở chế độ thiếu credentials với health response rõ ràng, player có một audio element và một state source, library play được bài thật, queue/repeat/shuffle/lyrics hoạt động nhất quán, admin routes không mở công khai, giao diện responsive và có loading/error/empty states, đồng thời có hướng dẫn biến môi trường cho Vercel/Render/Supabase/Cloudinary.
